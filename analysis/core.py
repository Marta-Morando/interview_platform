import json
import os
import re
import time
from copy import deepcopy

import pandas as pd


def load_file_paths(file_directory, extension=".txt"):
    """Collect file paths from a directory.

    Parameters
    ----------
    file_directory : str | os.PathLike
        Root directory to search for files.
    extension : str, optional
        File extension to filter by. Default is ".txt".

    Returns
    -------
    list[str]
        List of absolute paths to text files.
    """
    file_paths = []
    for root, _, files in os.walk(file_directory):
        for file in files:
            if file.endswith(extension):
                file_paths.append(os.path.abspath(os.path.join(root, file)))
    return file_paths


def respond(
    prompt,
    model,
    client,
    system=None,
    text=None,
    conversation_history=None,
    additional_api_kwargs=None,
):
    """Send a prompt to a chat model and return the response text.

    This function abstracts over different client functions (OpenAI, Anthropic, Google,
    Azure) based on a simple string test on client.

    Parameters
    ----------
    prompt : str
        The main user prompt to send to the model.
    model : str
        Model identifier (e.g. "gpt-5-mini").
    client
        Model client instance (OpenAI, Anthropic, Google, Azure).
    system : str, optional
        Optional system message / instructions to prepend to the conversation.
    text : str, optional
        Optional text to be appended to the prompt, separated by a delimiter.
    conversation_history : list[dict], optional
        Previous messages in chat-format, e.g.
        [{"role": "user", "content": "..."}, ...].
    additional_api_kwargs : dict, optional
        Additional keyword arguments passed through to the underlying API call.

    Returns
    -------
    str
        The model's response text.

    Raises
    ------
    ValueError
        If the client type cannot be inferred from str(client).
    """

    # Create client kwargs dictionary
    if additional_api_kwargs:
        client_kwargs = deepcopy(additional_api_kwargs)
    else:
        client_kwargs = {}

    # Add model to client kwargs
    client_kwargs["model"] = model

    # Prompt combined with text (if any)
    full_prompt = prompt + (f"\n\n---\n\n{text}" if text else "")

    # Create messages list including conversation history (if any)
    messages = []
    if conversation_history:
        messages += conversation_history

    # Determine client type, format messages accordingly, and call API
    client_str = str(client).lower()
    if "azure" in client_str:

        messages.append({"role": "user", "content": full_prompt})

        # Azure client expects system message as part of messages
        if system and not any(m.get("role") == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": system})

        client_kwargs["messages"] = messages

        response = client.complete(**client_kwargs)
        response_text = response.choices[0].message.content

    elif "openai" in client_str:

        messages.append({"role": "user", "content": full_prompt})

        # Add system message as part of messages
        if system and not any(m.get("role") == "developer" for m in messages):
            messages.insert(0, {"role": "developer", "content": system})

        client_kwargs["input"] = messages

        response = client.responses.create(**client_kwargs)
        response_text = response.output_text

    elif "anthropic" in client_str:

        messages.append({"role": "user", "content": full_prompt})

        # Anthropic client expects system message as argument
        if system:
            client_kwargs["system"] = system

        client_kwargs["messages"] = messages

        response = client.messages.create(**client_kwargs)
        response_text = "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        )

    elif "google" in client_str:

        messages.append({"role": "user", "parts": [{"text": full_prompt}]})

        # Google client expects system message as part of a config dictionary
        if system:
            # Add system instructions (if no config dictionary exists yet, create one,
            # otherwise add to existing one)
            client_kwargs.setdefault("config", {})["system_instruction"] = system

        client_kwargs["contents"] = messages

        response = client.models.generate_content(**client_kwargs)
        response_text = response.text

    else:
        raise ValueError(f"Unknown API client: {client!r}")

    return response_text


def verstehen(text, system, model, client, additional_api_kwargs=None):
    """Explore a long text through an interactive chat with a language model.

    Implements a loop: The user types a question in the terminal or notebook asking
    about the text, the model responds, the user can ask a follow-up question, etc.
    The chat ends when typing "quit".

    Parameters
    ----------
    text : str
        The main text/document that the model should consider when answering.
    system : str
        System instructions for the model (role / behaviour).
    model : str
        Model identifier.
    client
        Model client instance.
    additional_api_kwargs : dict, optional
        Additional arguments forwarded to respond() and the underlying API.

    Returns
    -------
    None
        This function prints to stdout and does not return a value.
    """
    conversation_history = []
    user_input = ""

    while user_input.lower() != "quit":
        user_input = input("\nYou: ")
        print(f"\nYou: {user_input}")  # delete if not using Jupyter Notebooks
        if user_input.lower() == "quit":
            break

        # Text added outside of respond() here to ensure it remains in the conversation
        # history after the first turn of the chat
        if not conversation_history:
            user_input = user_input + f"\n\n---\n\n{text}"

        tic = time.time()

        if not conversation_history:
            response_text = respond(
                prompt=user_input,
                model=model,
                client=client,
                system=system,
                additional_api_kwargs=additional_api_kwargs,
            )
        else:
            response_text = respond(
                prompt=user_input,
                model=model,
                client=client,
                system=system,
                conversation_history=conversation_history,
                additional_api_kwargs=additional_api_kwargs,
            )

        toc = time.time()
        print(f"\n\n{model} (time elapsed: {toc - tic:.0f} seconds): {response_text}")

        if "google" in str(client).lower():
            conversation_history.append(
                {"role": "user", "parts": [{"text": user_input}]}
            )
            conversation_history.append(
                {"role": "model", "parts": [{"text": response_text}]}
            )

        else:
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response_text})


def label_text(
    text,
    prompt,
    model,
    client,
    system=None,
    additional_api_kwargs=None,
):
    """Label a single text using a language model.

    The model is prompted with prompt and text, and is expected to return
    a JSON object of the form::

        {"reasoning": "...", "label": 0 or 1}

    Optionally wrapped in Markdown-style code fences.

    Parameters
    ----------
    text : str
        The text/document to be labelled.
    prompt : str
        The labelling instruction, e.g. asking whether a concept is present.
    model : str
        Model identifier.
    client
        Model client instance.
    system : str, optional
        Optional system instructions for the model.
    additional_api_kwargs : dict, optional
        Extra keyword arguments forwarded to respond().

    Returns
    -------
    tuple[str, int | None]
        A tuple (reasoning, label) where:

        - reasoning is either the model's explanation or the raw response
          if JSON parsing fails.
        - label is an integer label if parsing succeeds, otherwise None.
    """
    response_str = respond(
        prompt=prompt,
        model=model,
        client=client,
        system=system,
        text=text,
        additional_api_kwargs=additional_api_kwargs,
    )

    # Check if easily parsable JSON is present in the response
    try:
        # Extract content from optional fenced code block
        match = re.search(
            r"```(?:json)?\s*(.*?)\s*```",
            response_str,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if match:
            response_str = match.group(1).strip()
        else:
            response_str = response_str.strip()

        # 1) Try strict JSON on the whole string
        try:
            response_obj = json.loads(response_str)
        # 2) Fallback: Allow text before/after JSON object by decoding from first "{"
        except json.JSONDecodeError:
            start = response_str.find("{")
            if start == -1:
                raise
            response_obj, _ = json.JSONDecoder().raw_decode(response_str[start:])

        # Separate reasoning and label
        reasoning = response_obj["reasoning"]
        label = int(response_obj["label"])

    # If no easily parsable JSON is found in the LLM answer, store the full text
    # in the reasoning string for later manual review.
    except Exception:
        reasoning = response_str
        label = None

    return reasoning, label


def label_texts(
    file_paths,
    prompt,
    system,
    model,
    additional_api_kwargs,
    client,
    attempts=5,
):
    """Label a list of text files and return a DataFrame of results.

    Each text file is read from disk and labelled via label_text().
    Failed API calls are retried up to attempts times.

    Parameters
    ----------
    file_paths : list[str]
        List of file paths to text files.
    prompt : str
        Labelling instruction to pass to label_text().
    system : str
        System message / instructions for the model.
    model : str
        Model identifier.
    additional_api_kwargs : dict
        Extra keyword arguments to pass on to label_text() and the API.
    client
        Model client instance.
    attempts : int, optional
        Maximum number of attempts per text on API failure. Default is 5.

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by file_paths with columns "reasoning" and "label".
    """
    labels = pd.DataFrame({"reasoning": None, "label": None}, index=file_paths)

    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        fails = 0
        done = False
        reasoning, label = None, None

        while not done and fails < attempts:
            try:
                reasoning, label = label_text(
                    text=text,
                    prompt=prompt,
                    model=model,
                    client=client,
                    system=system,
                    additional_api_kwargs=additional_api_kwargs,
                )
                done = True
            except Exception:
                idx = file_paths.index(file_path) + 1
                total = len(file_paths)
                print(
                    f"API call failed {fails + 1} time(s) for text file number "
                    f"{idx} out of {total}, retrying..."
                )
                time.sleep(3)
                fails += 1

        labels.loc[file_path, "reasoning"] = reasoning
        labels.loc[file_path, "label"] = label

    return labels
