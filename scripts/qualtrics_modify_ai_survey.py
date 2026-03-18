#!/usr/bin/env python3
"""Modify a Qualtrics survey to add an AI interview handoff block.

This script is intentionally stdlib-only so it can run inside the existing
`interviews` conda environment without adding new dependencies.

Environment variables
---------------------
QUALTRICS_API_TOKEN
    Qualtrics API token.
QUALTRICS_BASE_URL
    Brand API root, for example:
    https://fra1.qualtrics.com/API/v3

Typical usage
-------------
1. Export your credentials:

   PowerShell:
   $env:QUALTRICS_API_TOKEN = "..."
   $env:QUALTRICS_BASE_URL = "https://<datacenter>.qualtrics.com/API/v3"

2. Dry-run the modification:

   python scripts/qualtrics_modify_ai_survey.py `
       --survey-name AI_survey `
       --interview-url https://YOUR-INTERVIEW-APP-URL `
       --dry-run

3. Apply it:

   python scripts/qualtrics_modify_ai_survey.py `
       --survey-name AI_survey `
       --interview-url https://YOUR-INTERVIEW-APP-URL

Notes
-----
- This script adds embedded-data field definitions and an interview-launch block.
- It does not generate a random ID in Survey Flow; you still need to create a
  `Random_ID` value in Qualtrics, typically via Survey Flow.
- It uses the survey endpoints documented by Qualtrics/Postman:
  `/surveys`, `/surveys/{surveyId}/embeddeddatafields`,
  `/survey-definitions/{surveyId}?format=qsf`,
  `/survey-definitions/{surveyId}/blocks`, and
  `/survey-definitions/{surveyId}/questions?blockId=...`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request


DEFAULT_SURVEY_NAME = "AI_survey"
DEFAULT_BLOCK_DESCRIPTION = "AI Interview"
DEFAULT_QUESTION_TAG = "AIInterviewStart"


class QualtricsError(RuntimeError):
    """Raised when a Qualtrics API call fails."""


@dataclass
class SurveyMatch:
    survey_id: str
    survey_name: str


class QualtricsClient:
    """Small Qualtrics API client using urllib."""

    def __init__(self, base_url: str, api_token: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token.strip()
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        payload: Any | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{parse.urlencode(query, doseq=True)}"

        headers = {
            "Accept": "application/json",
            "X-API-TOKEN": self.api_token,
        }
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(url=url, data=data, method=method, headers=headers)

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise QualtricsError(
                f"{method} {path} failed with HTTP {exc.code}: {body}"
            ) from exc
        except error.URLError as exc:
            raise QualtricsError(f"{method} {path} failed: {exc.reason}") from exc

        try:
            parsed_body = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise QualtricsError(
                f"{method} {path} returned non-JSON content: {raw[:400]}"
            ) from exc

        meta = parsed_body.get("meta", {})
        http_status = str(meta.get("httpStatus", ""))
        if http_status and not http_status.startswith(("2", "3")):
            raise QualtricsError(
                f"{method} {path} returned unexpected status {http_status}: {raw[:400]}"
            )

        return parsed_body

    def list_surveys(self) -> list[dict[str, Any]]:
        """Return all accessible surveys."""

        surveys: list[dict[str, Any]] = []
        offset = 0

        while True:
            response = self._request("GET", "/surveys", query={"offset": offset})
            result = response.get("result", {})
            elements = result.get("elements", [])
            surveys.extend(elements)

            next_page = result.get("nextPage") or response.get("nextPage")
            if not next_page:
                break

            next_query = parse.urlparse(next_page).query
            next_offset = parse.parse_qs(next_query).get("offset", [])
            if not next_offset:
                break
            offset = int(next_offset[0])

        return surveys

    def find_survey_by_name(self, survey_name: str) -> SurveyMatch:
        """Find one survey by exact name."""

        matches = []
        for survey in self.list_surveys():
            name = survey.get("name") or survey.get("SurveyName") or ""
            survey_id = survey.get("id") or survey.get("SurveyID")
            if survey_id and name == survey_name:
                matches.append(SurveyMatch(survey_id=survey_id, survey_name=name))

        if not matches:
            raise QualtricsError(
                f"No survey named {survey_name!r} was found in your Qualtrics account."
            )
        if len(matches) > 1:
            ids = ", ".join(match.survey_id for match in matches)
            raise QualtricsError(
                f"Multiple surveys named {survey_name!r} were found: {ids}. "
                "Rename the survey or pass a unique survey name."
            )
        return matches[0]

    def get_survey_definition(self, survey_id: str) -> dict[str, Any]:
        """Fetch the full survey definition as QSF-like JSON."""

        response = self._request(
            "GET", f"/survey-definitions/{survey_id}", query={"format": "qsf"}
        )
        return response["result"]

    def insert_embedded_data_fields(
        self, survey_id: str, fields: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Insert embedded data field definitions, with payload fallbacks."""

        candidate_payloads = [
            {"embeddedData": fields},
            {"EmbeddedData": fields},
            {"fields": fields},
            fields,
        ]

        last_error: Exception | None = None
        for payload in candidate_payloads:
            try:
                return self._request(
                    "POST",
                    f"/surveys/{survey_id}/embeddeddatafields",
                    payload=payload,
                )
            except QualtricsError as exc:
                last_error = exc

        assert last_error is not None
        raise QualtricsError(
            "Unable to insert embedded data fields with the attempted payload "
            f"shapes. Last error: {last_error}"
        )

    def create_block(self, survey_id: str, description: str) -> str:
        """Create a new standard block and return its block ID."""

        candidate_payloads = [
            {
                "Type": "Standard",
                "SubType": "",
                "Description": description,
                "BlockElements": [],
                "Options": {
                    "BlockLocking": "false",
                    "RandomizeQuestions": "false",
                    "BlockVisibility": "Expanded",
                },
            },
            {"Description": description},
        ]

        last_error: Exception | None = None
        for payload in candidate_payloads:
            try:
                response = self._request(
                    "POST", f"/survey-definitions/{survey_id}/blocks", payload=payload
                )
                result = response.get("result", {})
                block_id = (
                    result.get("BlockID")
                    or result.get("blockId")
                    or result.get("ID")
                    or result.get("id")
                )
                if block_id:
                    return str(block_id)
            except QualtricsError as exc:
                last_error = exc

        if last_error is not None:
            raise QualtricsError(
                f"Unable to create block {description!r}. Last error: {last_error}"
            )

        raise QualtricsError("Block creation returned no block ID.")

    def create_descriptive_text_question(
        self,
        survey_id: str,
        block_id: str,
        html: str,
        *,
        export_tag: str,
        description: str,
    ) -> str:
        """Create a DB/Text-Graphic question in a given block."""

        candidate_payloads = [
            {
                "QuestionText": html,
                "DataExportTag": export_tag,
                "QuestionType": "DB",
                "Selector": "TB",
                "Configuration": {
                    "QuestionDescriptionOption": "UseText",
                },
                "QuestionDescription": description[:100],
                "ChoiceOrder": [],
                "Validation": {"Settings": {"Type": "None"}},
                "Language": [],
                "NextChoiceId": 4,
                "NextAnswerId": 1,
            },
            {
                "QuestionText": html,
                "QuestionType": "DB",
                "Selector": "TB",
                "Configuration": {
                    "QuestionDescriptionOption": "UseText",
                },
            },
        ]

        last_error: Exception | None = None
        for payload in candidate_payloads:
            try:
                response = self._request(
                    "POST",
                    f"/survey-definitions/{survey_id}/questions",
                    query={"blockId": block_id},
                    payload=payload,
                )
                result = response.get("result", {})
                question_id = (
                    result.get("QuestionID")
                    or result.get("questionId")
                    or result.get("ID")
                    or result.get("id")
                )
                if question_id:
                    return str(question_id)
            except QualtricsError as exc:
                last_error = exc

        if last_error is not None:
            raise QualtricsError(
                f"Unable to create question in block {block_id}. Last error: {last_error}"
            )

        raise QualtricsError("Question creation returned no question ID.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Modify a Qualtrics survey to add an AI interview block."
    )
    parser.add_argument(
        "--survey-name",
        default=DEFAULT_SURVEY_NAME,
        help=f"Exact Qualtrics survey name. Default: {DEFAULT_SURVEY_NAME}",
    )
    parser.add_argument(
        "--interview-url",
        help="Base URL of the hosted Streamlit interview app.",
    )
    parser.add_argument(
        "--return-url",
        help=(
            "Optional URL to send participants back to after the interview. "
            "It will be URL-encoded before being embedded in the launch link."
        ),
    )
    parser.add_argument(
        "--alpha",
        type=int,
        default=123,
        help="Password intercept used in password = alpha + beta * Random_ID.",
    )
    parser.add_argument(
        "--beta",
        type=int,
        default=5,
        help="Password slope used in password = alpha + beta * Random_ID.",
    )
    parser.add_argument(
        "--block-description",
        default=DEFAULT_BLOCK_DESCRIPTION,
        help=f"Qualtrics block description. Default: {DEFAULT_BLOCK_DESCRIPTION}",
    )
    parser.add_argument(
        "--question-tag",
        default=DEFAULT_QUESTION_TAG,
        help=f"Data export tag for the instruction question. Default: {DEFAULT_QUESTION_TAG}",
    )
    parser.add_argument(
        "--dump-definition",
        help="If set, save the current survey definition JSON to this path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show intended actions without making any API changes.",
    )
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise QualtricsError(f"Missing required environment variable: {name}")
    return value


def get_blocks_from_qsf(qsf_definition: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract block definitions keyed by block ID from a QSF survey definition."""

    for element in qsf_definition.get("SurveyElements", []):
        if element.get("Element") != "BL":
            continue
        payload = element.get("Payload", {})
        blocks: dict[str, dict[str, Any]] = {}
        for maybe_block in payload.values():
            if isinstance(maybe_block, dict) and maybe_block.get("ID"):
                blocks[maybe_block["ID"]] = maybe_block
        if blocks:
            return blocks
    return {}


def get_questions_from_qsf(
    qsf_definition: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Extract question payloads keyed by QuestionID."""

    questions: dict[str, dict[str, Any]] = {}
    for element in qsf_definition.get("SurveyElements", []):
        if element.get("Element") != "SQ":
            continue
        question_id = element.get("PrimaryAttribute")
        payload = element.get("Payload", {})
        if question_id and payload:
            questions[question_id] = payload
    return questions


def find_block_by_description(
    blocks: dict[str, dict[str, Any]], description: str
) -> tuple[str, dict[str, Any]] | None:
    for block_id, block in blocks.items():
        if block.get("Description") == description:
            return block_id, block
    return None


def block_has_question_tag(
    block: dict[str, Any],
    questions: dict[str, dict[str, Any]],
    export_tag: str,
) -> bool:
    for block_element in block.get("BlockElements", []):
        if block_element.get("Type") != "Question":
            continue
        question_id = block_element.get("QuestionID")
        payload = questions.get(question_id, {})
        if payload.get("DataExportTag") == export_tag:
            return True
    return False


def build_launch_url(
    interview_url: str,
    *,
    alpha: int,
    beta: int,
    return_url: str | None,
) -> str:
    """Build the interview launch URL using Qualtrics piped text."""

    interview_url = interview_url.strip()
    if not interview_url:
        raise QualtricsError("--interview-url is required unless you only dump the survey.")

    parsed = parse.urlparse(interview_url)
    existing_query = parsed.query

    query_parts = []
    if existing_query:
        query_parts.append(existing_query)

    query_parts.extend(
        [
            "username=${e://Field/Random_ID}",
            f"password=$e{{ {alpha} + e://Field/Random_ID * {beta} }}",
            "response_id=${e://Field/Random_ID}",
        ]
    )

    if return_url:
        query_parts.append(f"return_url={parse.quote(return_url, safe='')}")

    rebuilt = parsed._replace(query="&".join(query_parts))
    return parse.urlunparse(rebuilt)


def build_instruction_html(launch_url: str, alpha: int, beta: int) -> str:
    """Build Qualtrics HTML for the AI interview instruction question."""

    password_expr = f"$e{{ {alpha} + e://Field/Random_ID * {beta} }}"
    return textwrap.dedent(
        f"""
        <div>
          <p>You are now moving to the AI interview portion of the study.</p>
          <p><strong><a href="{launch_url}" target="_blank" rel="noopener">Open the AI interview</a></strong></p>
          <p>The interview opens in a new tab. Keep this survey tab open so you can return when the interview is finished.</p>
          <p>If the automatic sign-in does not work, use these fallback login details:</p>
          <p>
            Username: ${{e://Field/Random_ID}}<br>
            Password: {password_expr}
          </p>
          <p>When the interview ends, return to this survey and continue.</p>
        </div>
        """
    ).strip()


def ensure_ai_interview_handoff(args: argparse.Namespace) -> None:
    base_url = require_env("QUALTRICS_BASE_URL")
    api_token = require_env("QUALTRICS_API_TOKEN")
    client = QualtricsClient(base_url=base_url, api_token=api_token)

    survey = client.find_survey_by_name(args.survey_name)
    print(f"Survey matched: {survey.survey_name} ({survey.survey_id})")

    definition = client.get_survey_definition(survey.survey_id)
    if args.dump_definition:
        with open(args.dump_definition, "w", encoding="utf-8") as handle:
            json.dump(definition, handle, indent=2)
        print(f"Survey definition written to {args.dump_definition}")

    if not args.interview_url:
        return

    launch_url = build_launch_url(
        args.interview_url,
        alpha=args.alpha,
        beta=args.beta,
        return_url=args.return_url,
    )
    instruction_html = build_instruction_html(launch_url, args.alpha, args.beta)

    blocks = get_blocks_from_qsf(definition)
    questions = get_questions_from_qsf(definition)

    existing_block = find_block_by_description(blocks, args.block_description)
    if existing_block:
        block_id, block = existing_block
        print(f"Block already exists: {args.block_description} ({block_id})")
    else:
        block_id = ""
        block = {}
        print(f"Block will be created: {args.block_description}")

    embedded_fields = [
        {"key": "Random_ID", "type": "numberSet"},
        {"key": "interview_username", "type": "textSet"},
        {"key": "interview_status", "type": "textSet"},
    ]

    if args.dry_run:
        print("Dry run only. No API changes were made.")
        print("Would insert embedded data fields:")
        print(json.dumps(embedded_fields, indent=2))
        if not existing_block:
            print(f"Would create block: {args.block_description}")
        if not block or not block_has_question_tag(block, questions, args.question_tag):
            print(f"Would create descriptive text question with tag: {args.question_tag}")
        print("Interview launch URL:")
        print(launch_url)
        return

    try:
        client.insert_embedded_data_fields(survey.survey_id, embedded_fields)
        print("Embedded data field definitions inserted or updated.")
    except QualtricsError as exc:
        print(
            "Warning: embedded data field insertion failed. "
            "The block can still be added, but ensure these fields exist in Qualtrics:\n"
            "  - Random_ID\n"
            "  - interview_username\n"
            "  - interview_status\n"
            f"Details: {exc}",
            file=sys.stderr,
        )

    if not block_id:
        block_id = client.create_block(survey.survey_id, args.block_description)
        print(f"Created block {args.block_description} ({block_id})")

        definition = client.get_survey_definition(survey.survey_id)
        blocks = get_blocks_from_qsf(definition)
        questions = get_questions_from_qsf(definition)
        existing_block = find_block_by_description(blocks, args.block_description)
        if existing_block:
            _, block = existing_block

    if block and block_has_question_tag(block, questions, args.question_tag):
        print(
            f"Question with DataExportTag {args.question_tag} already exists in block {block_id}."
        )
    else:
        question_id = client.create_descriptive_text_question(
            survey.survey_id,
            block_id,
            instruction_html,
            export_tag=args.question_tag,
            description=args.block_description,
        )
        print(f"Created descriptive text question {question_id} in block {block_id}.")

    print()
    print("Next step required in Qualtrics:")
    print(
        "Create or confirm a Survey Flow element that sets Random_ID, for example "
        "${rand://int/1:100000000}. The API call above defines the field but does "
        "not create the random-number assignment in Survey Flow."
    )


def main() -> int:
    try:
        args = parse_args()
        ensure_ai_interview_handoff(args)
    except QualtricsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
