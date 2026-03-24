from copy import deepcopy
import html
import hmac
import json
import os
import re
import time
import uuid
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import streamlit as st

import config
import dropbox_storage


def apply_readable_app_styles():
    """Apply minimal, high-contrast readability styles."""

    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"],
        .stApp {
            background: #0f1115 !important;
        }

        header,
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        .stAppDeployButton,
        [data-testid="stAppDeployButton"],
        [data-testid="manage-app-button"],
        #stStreamlitMainMenu,
        div[class*="viewerBadge"],
        div[class*="profileContainer"],
        div[class*="profilePreview"],
        div[class*="StatusWidget"],
        a[class*="viewerBadge"],
        iframe[title="streamlit_app_badge"],
        footer {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            position: fixed !important;
            z-index: -9999 !important;
        }

        .block-container {
            max-width: 900px;
            padding-top: 2.4rem;
            padding-bottom: 1.8rem;
        }

        .stApp,
        .stApp p,
        .stApp li,
        .stApp label,
        .stApp span,
        .stApp div {
            color: #f3f4f6;
            font-family: "Trebuchet MS", "Segoe UI", sans-serif;
        }

        [data-testid="stChatMessage"] {
            display: flex;
            align-items: flex-start;
            gap: 0.55rem;
            background: #171a21 !important;
            border: 1px solid #2a2f3a;
            border-radius: 16px;
            padding: 0.5rem 0.65rem 0.55rem;
            margin-top: 0.35rem;
            overflow: visible;
        }

        [data-testid="stChatMessageAvatarUser"],
        [data-testid="stChatMessageAvatarAssistant"] {
            flex: 0 0 auto;
            margin-top: 0.08rem;
        }

        [data-testid="stChatMessageContent"],
        [data-testid="stChatMessageContent"] p,
        [data-testid="stChatMessageContent"] div {
            color: #f3f4f6 !important;
            font-size: 1.03rem;
            line-height: 1.72;
            padding-top: 0 !important;
            margin-top: 0 !important;
            overflow-wrap: anywhere;
            word-break: break-word;
            white-space: pre-wrap;
            max-width: 100%;
        }

        [data-testid="stChatMessageContent"] {
            flex: 1 1 auto;
        }

        [data-testid="stChatMessageContent"] p:first-child,
        [data-testid="stChatMessageContent"] div:first-child {
            margin-top: 0 !important;
        }

        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] div,
        [data-testid="stMarkdownContainer"] span {
            color: #f3f4f6 !important;
            overflow-wrap: anywhere;
            word-break: break-word;
            white-space: pre-wrap;
            max-width: 100%;
        }

        [data-testid="stChatInput"] {
            background: #171a21 !important;
            border: 1px solid #2a2f3a;
            border-radius: 10px;
            padding-top: 0.05rem;
            box-shadow: none !important;
        }

        [data-testid="stChatInput"] > div,
        [data-testid="stChatInput"] > div > div,
        [data-testid="stChatInput"] > div > div > div {
            background: #171a21 !important;
        }

        [data-testid="stChatInput"] textarea,
        [data-testid="stTextInput"] input {
            background: #171a21 !important;
            border: none !important;
            color: #f3f4f6 !important;
            caret-color: #f3f4f6 !important;
            font-size: 1rem !important;
            line-height: 1.55 !important;
            box-shadow: none !important;
        }

        .stButton button,
        .stLinkButton a {
            background: #171a21 !important;
            color: #f3f4f6 !important;
            border: 1px solid #2f3642 !important;
            border-radius: 999px;
            min-height: 2rem;
            padding: 0.1rem 0.8rem;
            font-size: 0.9rem;
            text-decoration: none !important;
        }

        .stButton button[kind="secondary"],
        [data-testid="stBaseButton-secondary"] {
            color: #d6dae1 !important;
        }

        .survey-return-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            box-sizing: border-box;
            min-height: 2rem;
            padding: 0.1rem 0.8rem;
            margin-bottom: 0.35rem;
            border: 1px solid #2f3642;
            border-radius: 999px;
            background: #171a21;
            color: #d6dae1 !important;
            text-decoration: none !important;
            font-size: 0.9rem;
            line-height: 1.2;
        }

        .survey-return-button:hover,
        .survey-return-button:focus,
        .survey-return-button:active {
            color: #eef2f7 !important;
            border-color: #434c5c;
        }

        .survey-return-reminder {
            margin: 0 0 0.45rem;
            color: #c9d0db !important;
            font-size: 0.88rem;
            line-height: 1.4;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # JS fallback to hide Streamlit Cloud badge (CSS class names change per build)
    st.components.v1.html(
        """
        <script>
        const hide = () => {
            const root = window.parent.document;
            root.querySelectorAll('*').forEach(el => {
                const txt = (el.textContent || '').toLowerCase();
                if (/marta-morando|created by|hosted with|manage app/.test(txt) && txt.length < 120) {
                    el.style.setProperty('display', 'none', 'important');
                }
            });
            // Remove links pointing to the Streamlit user profile
            root.querySelectorAll('a').forEach(el => {
                if (/marta-morando|share\.streamlit\.io\/user/i.test(el.href || '')) {
                    el.remove();
                }
            });
            // Also hide fixed-position elements in the bottom-right corner
            root.querySelectorAll('div, a, button, iframe').forEach(el => {
                const s = window.parent.getComputedStyle(el);
                if (s.position === 'fixed' && parseInt(s.bottom) < 60 && parseInt(s.right) < 60) {
                    el.style.setProperty('display', 'none', 'important');
                }
            });
        };
        hide();
        new MutationObserver(hide).observe(window.parent.document.body,
            {childList: true, subtree: true});
        </script>
        """,
        height=0,
    )


# Simple password screen for respondents (note: only very basic authentication!)
# Based on https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso
# To add advanced respondent authentication to the interview application, see
# https://docs.streamlit.io/develop/concepts/connections/authentication)
def is_valid_username(username):
    """Allow simple file-safe usernames for surveys and direct links."""

    username = (username or "").strip()
    if not username:
        return False

    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    return all(char in allowed for char in username)


def sanitize_username(username):
    """Return a file-safe username or None when nothing usable is available."""

    username = (username or "").strip()
    if not username or username.startswith("${"):
        return None

    if is_valid_username(username):
        return username

    sanitized = re.sub(r"[^A-Za-z0-9_-]", "_", username).strip("_")
    return sanitized or None


def get_query_param(name):
    """Return a single query-parameter value as a stripped string."""

    if not name:
        return None

    try:
        value = st.query_params.get(name, None)
    except Exception:
        value = st.experimental_get_query_params().get(name, None)

    if isinstance(value, list):
        value = value[0] if value else None

    if value is None:
        return None

    value = str(value).strip()
    return value or None


def get_cached_qualtrics_response_id():
    """Return the Qualtrics ResponseID from URL params, cached in session."""

    cache_key = "_cached_qrid"
    qrid = get_query_param("qrid") or get_query_param("respondent_id")

    if qrid and not qrid.startswith("${"):
        st.session_state[cache_key] = qrid
        return qrid

    cached = st.session_state.get(cache_key)
    if cached and not str(cached).startswith("${"):
        return str(cached).strip()

    return None


def get_survey_return_url(*, completion=False):
    """Build the URL to return the respondent to Qualtrics.

    Always passes interview_status and response_id as URL params so that
    Qualtrics can capture them as embedded data.  A Branch element in the
    survey flow then skips the respondent past the AI interview block
    when interview_status == "completed".
    """

    base_url = getattr(config, "DEFAULT_SURVEY_RETURN_URL", None)
    if not base_url:
        return None

    parsed = urlparse(base_url)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))

    qrid = get_cached_qualtrics_response_id()
    if qrid:
        params["response_id"] = qrid

    username = st.session_state.get("username", "").strip()
    if username:
        params["interview_username"] = username

    params["interview_status"] = "completed"

    return urlunparse(parsed._replace(query=urlencode(params)))


def has_survey_return_target():
    """Return whether the app can send the respondent back to a survey."""

    return bool(get_survey_return_url())


def render_survey_return_control(label="Back to survey", *, completion=False):
    """Render a survey-return control.

    At completion: show a link button directly.
    During interview: first click reveals a reminder + link button.
    Uses st.link_button which reliably navigates (opens in a new tab).
    """

    href = get_survey_return_url(completion=completion)
    if not href:
        return False

    # At completion, show the link button directly
    if completion:
        st.link_button(label, href)
        return True

    # During the interview: first click → show reminder + link button
    confirm_key = "survey_return_confirmed"
    if not st.session_state.get(confirm_key, False):
        if st.button(label, key="survey_return_initial", type="secondary"):
            st.session_state[confirm_key] = True
            st.rerun()
        return True

    reminder_text = getattr(config, "SURVEY_RETURN_REMINDER", "").strip()
    if reminder_text:
        st.caption(reminder_text)

    st.link_button("Click to go back to the survey", href)
    return True


def validate_login_credentials(username, password):
    """Validate respondent credentials for either random IDs or secrets-based logins."""

    username = (username or "").strip()
    password = (password or "").strip()

    if config.RANDOM_IDS:
        try:
            username_int = int(username)
            password_int = int(password)
        except ValueError:
            return False, "Username and password must be integers.", username

        password_correct = password_int == (
            config.RANDOM_IDS_PW_ALPHA + username_int * config.RANDOM_IDS_PW_BETA
        )
    else:
        if not is_valid_username(username):
            return (
                False,
                "Username must contain only letters, numbers, underscores, or hyphens.",
                username,
            )

        password_correct = username in st.secrets.passwords and hmac.compare_digest(
            password,
            st.secrets.passwords[username],
        )

    if password_correct:
        return True, None, username

    return False, "User or password incorrect.", username


def get_direct_launch_username():
    """Return a username from URL parameters for direct-launch survey handoffs."""

    query_names = [
        getattr(config, "URL_USERNAME_PARAM", "username"),
        "respondent_id",
        "rid",
    ]

    for query_name in query_names:
        username = get_query_param(query_name)
        if username and not username.startswith("${"):
            return username

    return None


def initialize_survey_username():
    """Populate session username from the survey link or an anonymous fallback."""

    existing_username = sanitize_username(st.session_state.get("username"))
    if existing_username:
        st.session_state.username = existing_username
        return existing_username

    survey_username = sanitize_username(get_direct_launch_username())
    if survey_username:
        st.session_state.username = survey_username
        return survey_username

    if getattr(config, "REQUIRE_USERNAME_INPUT", True):
        return None

    anonymous_username = f"anon_{uuid.uuid4().hex[:8]}"
    st.session_state.username = anonymous_username
    return anonymous_username


def apply_url_login_if_available():
    """Authenticate from query parameters when enabled in config.py."""

    if (
        not config.LOGINS
        or not getattr(config, "ALLOW_URL_LOGIN", False)
        or st.session_state.get("password_correct", False)
    ):
        return False

    username = get_direct_launch_username()
    password = get_query_param(getattr(config, "URL_PASSWORD_PARAM", "password"))

    if not username or not password:
        return False

    password_correct, login_error, username = validate_login_credentials(
        username, password
    )
    st.session_state.username = username
    st.session_state.password_correct = password_correct

    if password_correct:
        st.session_state.pop("login_error", None)
        return True

    st.session_state["login_error"] = login_error
    return False


def render_completion_redirect():
    """Render a return-to-survey link after interview completion."""

    render_survey_return_control("Back to survey", completion=True)


def check_password():
    """Check credentials entered via Streamlit widgets.

    This function renders a simple login form (username + password) and checks the
    submitted credentials against either:

    - a random-ID scheme (when config.RANDOM_IDS is True), or
    - a username/password mapping stored in st.secrets.passwords.

    The actual validation happens in the password_entered callback, which:

    - validates integer-based IDs if config.RANDOM_IDS is True,
    - sets st.session_state.password_correct to True or False,
    - stores any validation error message in st.session_state.login_error,
    - deletes st.session_state.password after checking.

    Any error messages are displayed directly below the login form on the next
    rerun of the app.

    Returns
    -------
    tuple[bool, str]
        A tuple (password_correct, username), where:

        - password_correct is True if the user has already entered correct
          credentials in the current session; otherwise False.
        - username is the current value of st.session_state.username (may be
          an empty string if the user has not entered it yet).

    Notes
    -----
    This function is designed to be called near the top of the Streamlit app script.
    It does not call st.stop() for validation errors; instead, it re-renders the
    login form with an error message.
    """

    def login_form():
        """Render the login form to collect username and password."""
        survey_username = sanitize_username(get_direct_launch_username())
        if survey_username:
            st.session_state.username = survey_username

        with st.form("Credentials"):
            if not survey_username:
                st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Validate username and password and update session state.

        Side effects
        ------------
        - Validates integer-based IDs if config.RANDOM_IDS is True.
        - Sets st.session_state.password_correct to True or False.
        - Stores error messages in st.session_state["login_error"].
        - Deletes st.session_state.password from session state.
        """
        # Clear any previous error
        st.session_state.pop("login_error", None)

        # Store username without whitespaces
        st.session_state.username = (st.session_state.get("username") or "").strip()

        password_correct, login_error, username = validate_login_credentials(
            st.session_state.get("username"),
            st.session_state.get("password"),
        )
        st.session_state.username = username
        st.session_state.password_correct = password_correct

        if password_correct:
            st.session_state.pop("login_error", None)
        else:
            st.session_state["login_error"] = login_error

        # Don't store password in session state
        st.session_state.pop("password", None)

    # If already logged in
    if st.session_state.get("password_correct", False):
        return True, st.session_state.username
    # Otherwise, try URL-based login first if enabled
    if apply_url_login_if_available():
        return True, st.session_state.username
    # Otherwise show login form
    login_form()

    # Show any error directly under the form
    if "login_error" in st.session_state:
        st.error(st.session_state.login_error)

    return False, st.session_state.get("username", "")


def add_messages_to_api_kwargs(api, client_kwargs):
    """Adds messages from streamlit session state to client kwargs in a format suitable
    for the specified API.

    Different LLM APIs have different conventions for passing conversation history and
    system prompts. This function creates a deep copy of the provided kwargs and
    messages, and modifies them as needed.

    - OpenAI: Stores st.session_state.messages as "input" and prepends a developer
      message to include the system prompt.
    - Azure: Stores st.session_state.messages as "messages" and prepends a system
      message to include the system prompt.
    - Google: Stores st.session_state.messages as "contents", prepends a dummy "Hello"
      user message, renames "assistant" role to "model", and restructures message
      content into the {"parts": [{"text": ...}]} format.
    - Anthropic: Stores st.session_state.messages as "messages" and prepends a dummy
      "Hello" user message (required by the API to have a user message before the first
      assistant response).

    Parameters
    ----------
    api : str
        The API identifier: "openai", "azure", "google", or "anthropic".
    client_kwargs : dict
        Keyword arguments intended for the API call, expected to contain a
        "messages" key with a list of message dictionaries.

    Returns
    -------
    dict
        A deep copy of client_kwargs with API-specific transformations applied.

    Raises
    ------
    ValueError
        If api is not one of the supported values.
    """

    # Copy client kwargs and add messages from session state
    client_kwargs_transformed = deepcopy(client_kwargs)
    client_kwargs_transformed["messages"] = deepcopy(st.session_state.messages)

    # For the OpenAI API, rename "messages" to "input" and add system prompt
    if api == "openai":
        client_kwargs_transformed["input"] = client_kwargs_transformed.pop("messages")
        client_kwargs_transformed["input"].insert(
            0, {"role": "developer", "content": config.SYSTEM_PROMPT}
        )

    # For the Azure API, add system prompt
    elif api == "azure":
        client_kwargs_transformed["messages"].insert(
            0, {"role": "system", "content": config.SYSTEM_PROMPT}
        )

    # For the Google API, rename "messages" to "contents", add required initial user
    # message, and restructure messages
    elif api == "google":
        client_kwargs_transformed["contents"] = client_kwargs_transformed.pop(
            "messages"
        )
        client_kwargs_transformed["contents"].insert(
            0, {"role": "user", "content": "Hello"}
        )

        # Rename "assistant" role to "model" and restructure content
        for message in client_kwargs_transformed["contents"]:
            role = message.get("role")
            if role == "assistant":
                message["role"] = "model"
            message["parts"] = [{"text": message.pop("content")}]

    # For the Anthropic API, add required initial user message
    elif api == "anthropic":
        client_kwargs_transformed["messages"].insert(
            0, {"role": "user", "content": "Hello"}
        )

    else:
        raise ValueError(f"Unknown API: {api}")

    return client_kwargs_transformed


def iter_text_deltas(client, client_kwargs):
    """Yield text deltas from the configured chat API.

    This is a generator that abstracts over different providers (OpenAI, Anthropic,
    Google, and Azure) and yields chunks of text as they arrive from the streaming API.

    Parameters
    ----------
    client
        A client instance corresponding to the selected API:
        - OpenAI client if config.API == "openai"
        - Anthropic client if config.API == "anthropic"
        - Google client if config.API == "google"
        - Azure client if config.API == "azure"
    client_kwargs : dict
        Keyword arguments passed directly to the underlying streaming method
        (e.g. client.chat.completions.create(**client_kwargs)).

    Yields
    ------
    str
        Successive pieces of the message text (deltas) as they are streamed.

    Raises
    ------
    ValueError
        If config.API is not one of "openai", "anthropic", "google", or
        "azure".
    """

    # Transform messages in client kwargs as needed for different APIs
    client_kwargs_transformed = add_messages_to_api_kwargs(config.API, client_kwargs)

    # OpenAI API
    if config.API == "openai":
        stream = client.responses.create(**client_kwargs_transformed)
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta

    # Anthropic API
    elif config.API == "anthropic":
        with client.messages.stream(**client_kwargs_transformed) as stream:
            for delta in stream.text_stream:
                if delta:
                    yield delta

    # Google API
    elif config.API == "google":
        for chunk in client.models.generate_content_stream(**client_kwargs_transformed):
            delta = getattr(chunk, "text", None)
            if delta:
                yield delta

    # Azure API
    elif config.API == "azure":
        for update in client.complete(**client_kwargs_transformed):
            if getattr(update, "choices", None):
                delta = update.choices[0].delta.content
                if delta:
                    yield delta
    else:
        raise ValueError(f"Unknown API: {config.API}")


def stream_response(client, client_kwargs, message_placeholder, minimum_characters=5):
    """Stream a chat response and update a Streamlit placeholder.

    This function uses :func:`iter_text_deltas` to stream text from the chat API and
    progressively updates a `st.empty()` placeholder in the UI. It optionally stops
    early if a closing code defined in config.CLOSING_MESSAGES appears in the
    streamed text.

    Parameters
    ----------
    client
        Chat client instance (OpenAI, Anthropic, or Azure).
    client_kwargs : dict
        Keyword arguments used to initiate the streaming API call, including the
        messages to send.
    message_placeholder : streamlit.delta_generator.DeltaGenerator
        A placeholder created by st.empty() or similar, used to render the
        streaming text via .markdown(...).
    minimum_characters : int, optional
        Minimum number of characters to accumulate before rendering any text, to
        avoid quickly flashing short control codes. Default is 5.

    Returns
    -------
    str
        The full interviewer message assembled from all streamed deltas.

    Side effects
    ------------
    - Updates the Streamlit UI via message_placeholder.markdown(...).
    - May clear the placeholder with message_placeholder.empty() if a closing
      code is detected.
    """

    # Initialise message of interviewer
    message_interviewer = ""
    stopped_on_code = False

    # Store closing codes once to avoid repeated lookups
    closing_codes = config.CLOSING_MESSAGES.keys()

    # Iterate over text deltas from the chat API
    for delta in iter_text_deltas(client, client_kwargs):
        message_interviewer += delta

        # Start displaying once minimum characters reached (to avoid displaying codes)
        if len(message_interviewer) > minimum_characters:
            message_placeholder.markdown(message_interviewer + "▌")

        # Early exit on closing code
        if any(code in message_interviewer for code in closing_codes):
            message_placeholder.empty()
            stopped_on_code = True
            break

    # Final render (no cursor) only if we didn't stop on a code
    if not stopped_on_code and message_interviewer:
        message_placeholder.markdown(message_interviewer)

    return message_interviewer


# Functions to load and save backups, transcripts, and metadata:


# Dropbox path prefix for all interview data
DROPBOX_BASE_PATH = "/projects/consulting/survey/ai_interview/interview_data"


def load_backup(backups_directory):
    """Load backup data for the current user, from Dropbox if enabled or from disk.

    The backup is expected to be a JSON file named <username>.json. The structure is:

    .. code-block:: json

        {
          "messages": [...],
          "start_time": <float>,
          "times": [...],
          "num_text_and_voice_answers": [<int>, <int>]
        }

    If the file does not exist or cannot be read, sensible defaults for a new
    interview session are returned.

    Parameters
    ----------
    backups_directory : str | os.PathLike
        Directory where backup JSON files are stored (used for local storage).

    Returns
    -------
    tuple
        A 4-tuple (messages, start_time, times, num_text_and_voice_answers).
    """

    # Try to load backup data if it exists
    try:

        # --- DROPBOX STORAGE ---
        if dropbox_storage.is_dropbox_enabled():
            dropbox_path = f"{DROPBOX_BASE_PATH}/backups/{st.session_state.username}.json"
            data = dropbox_storage.download_json(dropbox_path)
            if data is None and not dropbox_storage.is_dropbox_enabled():
                with open(
                    os.path.join(
                        backups_directory,
                        f"{st.session_state.username}.json",
                    ),
                    "r",
                ) as f:
                    data = json.load(f)
            elif data is None:
                raise FileNotFoundError("No backup found in Dropbox")

        # --- LOCAL STORAGE (original behaviour) ---
        else:
            with open(
                os.path.join(
                    backups_directory,
                    f"{st.session_state.username}.json",
                ),
                "r",
            ) as f:
                data = json.load(f)

        # Number of user answers given by text vs voice input
        num_text_and_voice_answers = data["num_text_and_voice_answers"]

        # Start time
        start_time = data["start_time"]

        # The next element contains information on times spent using the dashboard
        times = data["times"]

        # The remaining items are messages
        messages = data["messages"]

        # Check if at least one message from "assistant" is in backup. If yes, return
        # all messages until and including the last assistant message.
        # If not, return empty lists for start of interview.
        if any(message["role"] == "assistant" for message in messages):
            last_assistant_index = (
                len(messages)
                - 1
                - [message["role"] == "assistant" for message in messages[::-1]].index(
                    True
                )
            )
            messages = messages[: last_assistant_index + 1]
        else:
            messages = []
            start_time = time.time()
            times = []
            num_text_and_voice_answers = [0, 0]

    # If no backup data exists, return empty lists for start of interview
    except Exception:
        messages = []
        start_time = time.time()
        times = []
        num_text_and_voice_answers = [0, 0]

    return messages, start_time, times, num_text_and_voice_answers


def save_backup(backups_directory, admin_alias):
    """Save the most recent interview data as a JSON backup.

    Saves to Dropbox if enabled, otherwise saves to local disk.

    Parameters
    ----------
    backups_directory : str | os.PathLike
        Directory where the backup JSON file should be written (local storage).
    admin_alias : str
        Username for which backups should be suppressed.

    Returns
    -------
    None
    """

    # Don't store data for admin alias
    if st.session_state.username != admin_alias:
        # Empty dictionary
        data = {}

        # Add messages
        data["messages"] = st.session_state.messages.copy()

        # Add start time
        data["start_time"] = st.session_state.start_time

        # Add time spent using dashboard for interview across different logins
        current_time = time.time()
        times = st.session_state.times_previous_attempts + [
            (current_time - st.session_state.start_time_current_login) / 60
        ]
        data["times"] = times

        # Add number of answers through text and voice inputs
        data["num_text_and_voice_answers"] = st.session_state.num_text_and_voice_answers

        # --- Also save a running transcript after every message ---
        transcript_text = f"Respondent ID: {st.session_state.username}\n\n"
        for message in st.session_state.messages:
            if message["role"] == "assistant" and any(
                code in message["content"]
                for code in config.CLOSING_MESSAGES.keys()
            ):
                continue
            elif message["role"] == "assistant":
                transcript_text += f"Interviewer: {message['content']}\n\n"
            elif message["role"] == "user":
                transcript_text += f"Respondent: {message['content']}\n\n"

        # --- DROPBOX STORAGE ---
        if dropbox_storage.is_dropbox_enabled():
            dropbox_path = f"{DROPBOX_BASE_PATH}/backups/{st.session_state.username}.json"
            transcript_path = (
                f"{DROPBOX_BASE_PATH}/transcripts/{st.session_state.username}.txt"
            )
            backup_saved = dropbox_storage.upload_json(data, dropbox_path)
            transcript_saved = dropbox_storage.upload_text(
                transcript_text, transcript_path
            )
            if backup_saved and transcript_saved:
                return

        # --- LOCAL STORAGE (original behaviour) ---
        # Save running transcript locally
        transcripts_dir = config.TRANSCRIPTS_DIRECTORY
        os.makedirs(transcripts_dir, exist_ok=True)
        with open(
            os.path.join(transcripts_dir, f"{st.session_state.username}.txt"),
            "w",
        ) as tf:
            tf.write(transcript_text)

        with open(
            os.path.join(
                backups_directory,
                f"{st.session_state.username}.json",
            ),
            "w",
        ) as f:
            json.dump(data, f)



def save_metadata(metadata_directory, api_kwargs, admin_alias):
    """Save interview metadata (timing, message counts, API params).

    Saves to Dropbox if enabled, otherwise saves to local disk.

    Parameters
    ----------
    metadata_directory : str | os.PathLike
        Directory where the metadata `.txt` file will be written (local storage).
    api_kwargs : dict
        Keyword arguments used in API call.
    admin_alias : str
        Username for which no metadata should be stored.

    Returns
    -------
    None
    """

    # Don't store data for admin alias
    if st.session_state.username != admin_alias:

        # Count messages
        user_messages = 0
        assistant_messages = 0
        for message in st.session_state.messages:
            if message["role"] == "assistant" and any(
                code in message["content"]
                for code in config.CLOSING_MESSAGES.keys()
            ):
                continue
            elif message["role"] == "assistant":
                assistant_messages += 1
            elif message["role"] == "user":
                user_messages += 1

        # Build metadata text
        current_time = time.time()
        times = st.session_state.times_previous_attempts + [
            (current_time - st.session_state.start_time_current_login) / 60
        ]

        times_str = [f"{d:.2f}" for d in times]
        total_time = sum(times)

        if len(times) > 1:
            times_display = " + ".join(times_str) + f" = {total_time:.2f}"
        else:
            times_display = times_str[0]

        api_kwargs_text = json.dumps(
            {
                k: (
                    {sk: sv for sk, sv in v.items() if sk != "system_instruction"}
                    if k == "config" and isinstance(v, dict) and len(v) > 1
                    else v
                )
                for k, v in api_kwargs.items()
                if k != "system"
                and not (
                    k == "config"
                    and isinstance(v, dict)
                    and len(v) == 1
                    and "system_instruction" in v
                )
            },
            indent=2,
        )

        external_response_id = get_query_param("respondent_id")
        # Discard unresolved Qualtrics piped-text literals (e.g. ${e://Field/ResponseID})
        if external_response_id and external_response_id.startswith("${"):
            external_response_id = None
        survey_return_url_supplied = bool(
            get_query_param(getattr(config, "RETURN_URL_PARAM", "return_url"))
        )
        external_context_lines = []
        if external_response_id:
            external_context_lines.append(
                f"External survey response ID: {external_response_id}"
            )
        if survey_return_url_supplied:
            external_context_lines.append("Survey return URL supplied: yes")
        external_context_text = (
            "\n".join(external_context_lines) + "\n\n---\n\n"
            if external_context_lines
            else ""
        )

        meta_text = f"""Respondent ID: {st.session_state.username}

Start time (UTC): {time.strftime('%d/%m/%Y %H:%M:%S', time.gmtime(st.session_state.start_time))}
End time (UTC): {time.strftime('%d/%m/%Y %H:%M:%S', time.gmtime(current_time))}
Interview duration (multiple logins are separated by '+'): {times_display} minutes
Text answers given by respondent: {st.session_state.num_text_and_voice_answers[0]}
Voice answers given by respondent: {st.session_state.num_text_and_voice_answers[1]}
Total respondent messages: {user_messages}
Total interviewer messages: {assistant_messages}

---

{external_context_text}API call parameters (excluding messages and system prompt):

{api_kwargs_text}

---

System prompt:

{config.SYSTEM_PROMPT}
"""

        # --- DROPBOX STORAGE ---
        if dropbox_storage.is_dropbox_enabled():
            metadata_path = (
                f"{DROPBOX_BASE_PATH}/metadata/{st.session_state.username}.txt"
            )
            if dropbox_storage.upload_text(meta_text, metadata_path):
                return

        # --- LOCAL STORAGE (original behaviour) ---
        os.makedirs(metadata_directory, exist_ok=True)
        with open(
            os.path.join(
                metadata_directory,
                f"{st.session_state.username}.txt",
            ),
            "w",
        ) as d:
            d.write(meta_text)


def save_transcript_and_metadata(
    transcripts_directory,
    metadata_directory,
    api_kwargs,
    admin_alias,
):
    """Write the interview transcript and metadata.

    Saves to Dropbox if enabled, otherwise saves to local disk.

    Parameters
    ----------
    transcripts_directory : str | os.PathLike
        Directory where the transcript `.txt` file will be written (local storage).
    metadata_directory : str | os.PathLike
        Directory where the metadata `.txt` file will be written (local storage).
    api_kwargs : dict
        Keyword arguments used in API call.
    admin_alias : str
        Username for which no transcript or metadata should be stored.

    Returns
    -------
    None
    """

    # Don't store data for admin alias
    if st.session_state.username != admin_alias:

        # --- Build transcript text ---
        transcript_text = f"Respondent ID: {st.session_state.username}\n\n"
        for message in st.session_state.messages:
            if message["role"] == "assistant" and any(
                code in message["content"]
                for code in config.CLOSING_MESSAGES.keys()
            ):
                # Skip messages with codes
                continue
            elif message["role"] == "assistant":
                transcript_text += f"Interviewer: {message['content']}\n\n"
            elif message["role"] == "user":
                transcript_text += f"Respondent: {message['content']}\n\n"

        # --- Save transcript ---
        # --- DROPBOX STORAGE ---
        if dropbox_storage.is_dropbox_enabled():
            transcript_path = (
                f"{DROPBOX_BASE_PATH}/transcripts/{st.session_state.username}.txt"
            )
            transcript_saved = dropbox_storage.upload_text(
                transcript_text, transcript_path
            )
            if not transcript_saved:
                # Fall back to local storage
                with open(
                    os.path.join(
                        transcripts_directory,
                        f"{st.session_state.username}.txt",
                    ),
                    "w",
                ) as f:
                    f.write(transcript_text)
        else:
            # --- LOCAL STORAGE (original behaviour) ---
            with open(
                os.path.join(
                    transcripts_directory,
                    f"{st.session_state.username}.txt",
                ),
                "w",
            ) as f:
                f.write(transcript_text)

        # --- Save metadata ---
        save_metadata(metadata_directory, api_kwargs, admin_alias)


def backup_contains_closing_code(messages):
    """Return True when any assistant message contains a configured closing code."""

    return any(
        message.get("role") == "assistant"
        and any(
            code in message.get("content", "") for code in config.CLOSING_MESSAGES.keys()
        )
        for message in messages
    )


def is_interview_completed(metadata_directory, backups_directory):
    """Check whether the interview has finished for the current user."""

    username = st.session_state.username

    if dropbox_storage.is_dropbox_enabled():
        metadata_path = f"{DROPBOX_BASE_PATH}/metadata/{username}.txt"
        if dropbox_storage.file_exists(metadata_path):
            return True

        backup_path = f"{DROPBOX_BASE_PATH}/backups/{username}.json"
        backup_data = dropbox_storage.download_json(backup_path) or {}
        return backup_contains_closing_code(backup_data.get("messages", []))

    metadata_path = os.path.join(metadata_directory, f"{username}.txt")
    if os.path.exists(metadata_path):
        return True

    backup_path = os.path.join(backups_directory, f"{username}.json")
    try:
        with open(backup_path, "r") as f:
            backup_data = json.load(f)
    except Exception:
        return False

    return backup_contains_closing_code(backup_data.get("messages", []))


def is_transcript_saved(transcripts_directory):
    """Check whether a transcript for the current user already exists.

    Checks Dropbox if enabled, otherwise checks local disk.

    Parameters
    ----------
    transcripts_directory : str | os.PathLike
        Directory where transcript `.txt` files are stored (local storage).

    Returns
    -------
    bool
        True if the transcript exists, False otherwise.
    """

    # --- DROPBOX STORAGE ---
    if dropbox_storage.is_dropbox_enabled():
        dropbox_path = f"{DROPBOX_BASE_PATH}/transcripts/{st.session_state.username}.txt"
        return dropbox_storage.file_exists(dropbox_path)

    # --- LOCAL STORAGE (original behaviour) ---
    else:
        path = os.path.join(transcripts_directory, f"{st.session_state.username}.txt")
        return os.path.exists(path)
