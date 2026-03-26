"""Language detection helper for the interview app."""

import streamlit as st
from ui_strings import STRINGS


def get_lang():
    """Return the active language code from the URL query parameter."""
    return st.query_params.get("lang", "en")


def get_string(key):
    """Look up a UI string for the active language, falling back to English."""
    lang = get_lang()
    return STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))
