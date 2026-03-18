"""
Dropbox storage helper for the interview platform.

When Dropbox credentials are set in `.streamlit/secrets.toml`, this module
saves and loads transcripts, metadata, and backups to/from Dropbox instead
of the local filesystem. This ensures data persists even if the cloud
server reboots.

Supported credentials:
- `DROPBOX_ACCESS_TOKEN`
- `DROPBOX_REFRESH_TOKEN` together with `DROPBOX_APP_KEY`
- optional `DROPBOX_APP_SECRET`

If Dropbox authentication fails, the app falls back to local storage so a
local test run does not crash.
"""

import json
import dropbox
import streamlit as st


_DROPBOX_CLIENT = None
_DROPBOX_STATUS_CHECKED = False
_DROPBOX_AVAILABLE = False


def _show_dropbox_warning():
    """Warn once per session that Dropbox storage is unavailable."""
    try:
        if not st.session_state.get("_dropbox_warning_shown", False):
            st.session_state["_dropbox_warning_message"] = (
                "Dropbox storage is disabled because the configured token is "
                "invalid or expired. The app is using local storage instead. "
                "Update `.streamlit/secrets.toml` with a new Dropbox access "
                "token or, preferably, a refresh token."
            )
            st.warning(st.session_state["_dropbox_warning_message"])
            st.session_state["_dropbox_warning_shown"] = True
    except Exception:
        pass


def show_dropbox_warning_if_needed():
    """Render the Dropbox warning again on reruns if it was previously triggered."""
    warning_message = st.session_state.get("_dropbox_warning_message", None)
    if warning_message:
        st.warning(warning_message)


def _disable_dropbox():
    """Disable Dropbox storage after an authentication failure."""
    global _DROPBOX_CLIENT, _DROPBOX_STATUS_CHECKED, _DROPBOX_AVAILABLE
    _DROPBOX_CLIENT = None
    _DROPBOX_STATUS_CHECKED = True
    _DROPBOX_AVAILABLE = False
    _show_dropbox_warning()


def _build_dropbox_client():
    """Build a Dropbox client from Streamlit secrets."""
    access_token = st.secrets.get("DROPBOX_ACCESS_TOKEN", None)
    refresh_token = st.secrets.get("DROPBOX_REFRESH_TOKEN", None)
    app_key = st.secrets.get("DROPBOX_APP_KEY", None)
    app_secret = st.secrets.get("DROPBOX_APP_SECRET", None)

    if refresh_token and app_key:
        kwargs = {
            "oauth2_refresh_token": refresh_token,
            "app_key": app_key,
        }
        if access_token:
            kwargs["oauth2_access_token"] = access_token
        if app_secret:
            kwargs["app_secret"] = app_secret
        return dropbox.Dropbox(**kwargs)

    if access_token:
        return dropbox.Dropbox(access_token)

    return None


def get_dropbox_client():
    """Return a validated Dropbox client if configured, else None."""
    global _DROPBOX_CLIENT, _DROPBOX_STATUS_CHECKED, _DROPBOX_AVAILABLE

    if _DROPBOX_STATUS_CHECKED:
        return _DROPBOX_CLIENT if _DROPBOX_AVAILABLE else None

    dbx = _build_dropbox_client()
    if dbx is None:
        _DROPBOX_STATUS_CHECKED = True
        _DROPBOX_AVAILABLE = False
        return None

    try:
        dbx.users_get_current_account()
    except dropbox.exceptions.AuthError:
        _disable_dropbox()
        return None

    _DROPBOX_CLIENT = dbx
    _DROPBOX_STATUS_CHECKED = True
    _DROPBOX_AVAILABLE = True
    return _DROPBOX_CLIENT


def is_dropbox_enabled():
    """Check whether Dropbox storage is configured."""
    return get_dropbox_client() is not None


def upload_text(content, dropbox_path):
    """Upload text content to Dropbox.

    Parameters
    ----------
    content : str
        The text content to upload.
    dropbox_path : str
        The full path in Dropbox (e.g. "/interview_data/transcripts/user1.txt").
    """
    dbx = get_dropbox_client()
    if dbx:
        try:
            dbx.files_upload(
                content.encode("utf-8"),
                dropbox_path,
                mode=dropbox.files.WriteMode.overwrite,
            )
            return True
        except dropbox.exceptions.AuthError:
            _disable_dropbox()
    return False


def upload_json(data, dropbox_path):
    """Upload a JSON-serializable object to Dropbox.

    Parameters
    ----------
    data : dict or list
        The data to serialize and upload.
    dropbox_path : str
        The full path in Dropbox (e.g. "/interview_data/backups/user1.json").
    """
    dbx = get_dropbox_client()
    if dbx:
        content = json.dumps(data)
        try:
            dbx.files_upload(
                content.encode("utf-8"),
                dropbox_path,
                mode=dropbox.files.WriteMode.overwrite,
            )
            return True
        except dropbox.exceptions.AuthError:
            _disable_dropbox()
    return False


def download_text(dropbox_path):
    """Download text content from Dropbox.

    Parameters
    ----------
    dropbox_path : str
        The full path in Dropbox.

    Returns
    -------
    str or None
        The file content as a string, or None if the file doesn't exist.
    """
    dbx = get_dropbox_client()
    if dbx:
        try:
            _, response = dbx.files_download(dropbox_path)
            return response.content.decode("utf-8")
        except dropbox.exceptions.AuthError:
            _disable_dropbox()
            return None
        except dropbox.exceptions.ApiError:
            return None
    return None


def download_json(dropbox_path):
    """Download and parse a JSON file from Dropbox.

    Parameters
    ----------
    dropbox_path : str
        The full path in Dropbox.

    Returns
    -------
    dict or None
        The parsed JSON data, or None if the file doesn't exist.
    """
    content = download_text(dropbox_path)
    if content:
        return json.loads(content)
    return None


def file_exists(dropbox_path):
    """Check whether a file exists in Dropbox.

    Parameters
    ----------
    dropbox_path : str
        The full path in Dropbox.

    Returns
    -------
    bool
        True if the file exists, False otherwise.
    """
    dbx = get_dropbox_client()
    if dbx:
        try:
            dbx.files_get_metadata(dropbox_path)
            return True
        except dropbox.exceptions.AuthError:
            _disable_dropbox()
            return False
        except dropbox.exceptions.ApiError:
            return False
    return False
