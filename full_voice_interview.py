# Additional application for running full voice AI-led interviews
#
# AI interviewer: voice
# Respondent: voice input
#
# This interview version only supports the OpenAI API.
# Before running the file with `streamlit run full_voice_interview.py`, adjust MODEL in
# config.py, e.g. to "gpt-audio-2025-08-28" or similar, and set API = "openai".

import base64
import os
import random
import time
import warnings
from io import BytesIO
from copy import deepcopy

import dropbox_storage
import streamlit as st
from openai import OpenAI
from scipy.io import wavfile

import config
from utils import (
    apply_readable_app_styles,
    check_password,
    has_survey_return_target,
    initialize_survey_username,
    is_valid_username,
    load_backup,
    is_interview_completed,
    render_completion_redirect,
    render_survey_return_control,
    save_backup,
    save_transcript_and_metadata,
)


# Helper function
def get_wav_duration(audio_bytes):
    """Get duration of WAV audio from raw bytes."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sample_rate, data = wavfile.read(BytesIO(audio_bytes))
    return len(data) / sample_rate


#
# 1. Set up interview environment
#

# Set page title and icon
st.set_page_config(
    page_title="Interview",
    page_icon=config.AVATAR_INTERVIEWER,
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": None,
    },
)
dropbox_storage.show_dropbox_warning_if_needed()
apply_readable_app_styles()

# Do not show Streamlit audio player when playing back interviewer audio
st.markdown(
    """
    <style>
    audio {
      display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Check if login screen is enabled
if config.LOGINS:
    # Check password (displays login screen)
    pwd_correct, username = check_password()
    if not pwd_correct:
        st.stop()
    else:
        st.session_state.username = username
# Otherwise ask the respondent to enter a username without password
else:
    # Until username confirmed, show the input and stop
    if "username" not in st.session_state:
        if initialize_survey_username():
            st.rerun()

        username_input = st.text_input(
            "Please enter a username to start the interview:",
            key="username_input",
        )
        if not username_input:
            # User hasn't typed anything yet, just render the page
            st.stop()
        if not is_valid_username(username_input):
            st.warning(
                "Username must contain only letters, numbers, underscores, or hyphens."
            )
            st.stop()

        # Save non-empty username and rerun
        st.session_state.username = username_input.strip()
        st.rerun()

# Directories
if not os.path.exists(config.TRANSCRIPTS_DIRECTORY):
    os.makedirs(config.TRANSCRIPTS_DIRECTORY)
if not os.path.exists(config.METADATA_DIRECTORY):
    os.makedirs(config.METADATA_DIRECTORY)
if not os.path.exists(config.BACKUPS_DIRECTORY):
    os.makedirs(config.BACKUPS_DIRECTORY)

# Check if interview has been completed and, if so, only display closing message
interview_previously_completed = is_interview_completed(
    config.METADATA_DIRECTORY, config.BACKUPS_DIRECTORY
)
if "messages" not in st.session_state and interview_previously_completed:
    st.session_state.messages = []
    st.session_state.interview_active = False

    code_found = False
    try:
        messages, _, _, _ = load_backup(backups_directory=config.BACKUPS_DIRECTORY)
    except Exception:
        messages = []

    # Display closing message
    for code in config.CLOSING_MESSAGES.keys():
        if any(
            code in message["content"]
            for message in messages
            if message["role"] == "assistant"
        ):
            code_found = True
            closing_message = config.CLOSING_MESSAGES[code]
            break

    if not code_found:
        closing_message = "The interview has already been completed."

    st.session_state.interview_active = False
    st.markdown(closing_message)
    render_completion_redirect()
    st.stop()

# If interview has not yet been completed, initialise session states
if "interview_active" not in st.session_state:
    st.session_state.interview_active = True

# Start time for this login
if "start_time_current_login" not in st.session_state:
    st.session_state.start_time_current_login = time.time()

# Initialise messages, times using dashboard, and the number of voice and text answers
if "messages" not in st.session_state:
    # Returns [], time.time(), [], [0, 0] if no data in the backup directory is found
    (
        st.session_state.messages,
        st.session_state.start_time,
        st.session_state.times_previous_attempts,
        st.session_state.num_text_and_voice_answers,
    ) = load_backup(backups_directory=config.BACKUPS_DIRECTORY)

# Transcription of voice input
if "transcription_done" not in st.session_state:
    st.session_state.transcription_done = False
if "last_transcription" not in st.session_state:
    st.session_state.last_transcription = ""

# Key for voice input element
if "voice_input_key" not in st.session_state:
    st.session_state.voice_input_key = random.uniform(0, 1)

# API client
if config.API == "openai":
    client = OpenAI(api_key=st.secrets["KEY_OPENAI"])
else:
    raise ValueError("Only the OpenAI API is currently supported for this interview.")

# Initialise API kwargs
if isinstance(config.ADDITIONAL_API_KWARGS, dict):
    api_kwargs = deepcopy(config.ADDITIONAL_API_KWARGS)
else:
    raise ValueError(
        "ADDITIONAL_API_KWARGS must be specified as a dictionary in config.py, either empty or containing valid additional API parameters."
    )
api_kwargs["messages"] = st.session_state.messages
api_kwargs["model"] = config.MODEL
api_kwargs["modalities"] = ["text", "audio"]
api_kwargs["audio"] = {"voice": config.VOICE, "format": "wav"}


#
# 2. Display first message or previous conversation
#

# Define a container for the chat history
transcript_container = st.container()

# In case the interview history is still empty, pass system prompt to model and
# generate the first message
if not st.session_state.messages and st.session_state.interview_active:
    with transcript_container:
        st.session_state.messages.append(
            {"role": "system", "content": config.SYSTEM_PROMPT}
        )
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            message_placeholder = st.empty()
            message_placeholder.markdown("Interviewer thinking ...")

            completion_response = client.chat.completions.create(**api_kwargs)

            interviewer_message_audio_api = completion_response.choices[
                0
            ].message.audio.data
            interviewer_message_id = completion_response.choices[0].message.audio.id
            interviewer_message_transcript = completion_response.choices[
                0
            ].message.audio.transcript

            # Transform WAV base64 string to bytes
            audio_bytes = base64.b64decode(interviewer_message_audio_api)

            # Determine duration of WAV
            interviewer_message_duration = get_wav_duration(audio_bytes)

            message_placeholder.empty()
            message_placeholder.markdown("Interviewer speaking ...")
            st.audio(audio_bytes, format="audio/wav", autoplay=True)

            time.sleep(interviewer_message_duration + 0.5)
            message_placeholder.empty()
            message_placeholder.markdown(interviewer_message_transcript)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": interviewer_message_transcript,
            "audio": {"id": interviewer_message_id},
        }
    )

    # Store interview data up to here to signal it has started
    save_backup(
        backups_directory=config.BACKUPS_DIRECTORY, admin_alias=config.ADMIN_ALIAS
    )

    st.rerun()

# Otherwise, display the previous conversation
else:
    with transcript_container:
        # Don't display initial system message
        for message in st.session_state.messages[1:]:
            if message["role"] == "assistant":
                avatar = config.AVATAR_INTERVIEWER
            elif message["role"] == "user":
                avatar = config.AVATAR_RESPONDENT
            else:
                continue

            # Only display messages without codes
            if not any(code in message["content"] for code in config.CLOSING_MESSAGES):
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])

if not st.session_state.interview_active and is_interview_completed(
    config.METADATA_DIRECTORY, config.BACKUPS_DIRECTORY
):
    render_completion_redirect()


#
# 3. Main chat if interview is active
#

if st.session_state.interview_active:

    response_container = st.container()
    survey_return_available = has_survey_return_target()

    if survey_return_available:
        try:
            save_backup(
                backups_directory=config.BACKUPS_DIRECTORY,
                admin_alias=config.ADMIN_ALIAS,
            )
        except Exception:
            pass

    with response_container:
        voice_input_element = st.empty()
        audio_response = voice_input_element.audio_input(
            label=config.VOICE_INPUT_INSTRUCTIONS,
            key=st.session_state.voice_input_key,
        )
        if survey_return_available:
            action_spacer, action_col = st.columns([5.6, 2.1])
            with action_col:
                render_survey_return_control("Back to survey")

    # Only if we have new audio
    if audio_response:

        with transcript_container:
            voice_input_element.empty()
            transcription_placeholder = st.empty()

            # Only call the transcription API once per recording
            if not st.session_state.transcription_done:
                # Show "processing" message
                transcription_placeholder.markdown("__Processing voice response ...__")

                # Obtain transcription from the audio input
                user_transcription = client.audio.transcriptions.create(
                    model=config.MODEL_TRANSCRIPTION,
                    file=audio_response,
                ).text

                # Cache transcription in session_state to reuse it on reruns
                st.session_state.last_transcription = user_transcription
                st.session_state.transcription_done = True

                transcription_placeholder.empty()
            else:
                # On reruns (e.g. after button clicks), reuse cached transcription
                user_transcription = st.session_state.last_transcription
                transcription_placeholder.empty()

            # Show transcription to respondent
            with st.chat_message("user", avatar=config.AVATAR_RESPONDENT):
                st.markdown(user_transcription)

            # Ask to accept or reject
            col_accept, col_reject = st.columns([1, 1])
            accept_button_placeholder = col_accept.empty()
            reject_button_placeholder = col_reject.empty()

            # Now create the buttons inside those placeholders
            accept_clicked = accept_button_placeholder.button(
                "Proceed with this answer"
            )
            reject_clicked = reject_button_placeholder.button("Re-record answer")

            if reject_clicked or accept_clicked:
                # Reset flag so a new recording will be transcribed again
                st.session_state.transcription_done = False
                accept_button_placeholder.empty()
                reject_button_placeholder.empty()

            # If user rejects, reset audio input and rerun
            if reject_clicked:
                st.session_state.voice_input_key = random.uniform(0, 1)
                st.rerun()

            # If user accepts, then proceed with the language model call
            if accept_clicked:

                # Add the user’s message to the conversation
                st.session_state.messages.append(
                    {"role": "user", "content": user_transcription}
                )

                # Track that a voice answer was given
                st.session_state.num_text_and_voice_answers[1] += 1

                # Generate interviewer response
                with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
                    message_placeholder = st.empty()
                    message_placeholder.markdown("Interviewer thinking ...")

                    completion_response = client.chat.completions.create(**api_kwargs)

                    interviewer_message_audio_api = completion_response.choices[
                        0
                    ].message.audio.data
                    interviewer_message_id = completion_response.choices[
                        0
                    ].message.audio.id
                    interviewer_message_transcript = completion_response.choices[
                        0
                    ].message.audio.transcript

                    # Check for any closing codes
                    for code in config.CLOSING_MESSAGES.keys():
                        if code in interviewer_message_transcript:
                            # Closing
                            st.session_state.interview_active = False
                            closing_message = config.CLOSING_MESSAGES[code]

                            # Generate the pre-written closing message from config.py
                            # with a simple TTS model
                            closing_audio_buffer = BytesIO()
                            with client.audio.speech.with_streaming_response.create(
                                model="gpt-4o-mini-tts",
                                voice=config.VOICE,
                                input=closing_message,
                                response_format="wav",
                                instructions="Please speak slowly to conclude an interview.",
                            ) as response:
                                for chunk in response.iter_bytes():
                                    closing_audio_buffer.write(chunk)

                            closing_audio_bytes = closing_audio_buffer.getvalue()

                            # Determine duration of WAV
                            closing_message_duration = get_wav_duration(
                                closing_audio_bytes
                            )

                            # Play closing message
                            message_placeholder.empty()
                            message_placeholder.markdown("Interviewer speaking ...")
                            st.audio(
                                closing_audio_bytes,
                                format="audio/wav",
                                autoplay=True,
                            )

                            # Wait for audio duration + small buffer
                            time.sleep(closing_message_duration + 0.5)
                            message_placeholder.empty()
                            message_placeholder.markdown(closing_message)

                            # Log everything
                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": interviewer_message_transcript,
                                    "audio": {"id": interviewer_message_id},
                                }
                            )
                            st.session_state.messages.append(
                                {"role": "assistant", "content": closing_message}
                            )

                            # Store final transcript and backup
                            save_transcript_and_metadata(
                                transcripts_directory=config.TRANSCRIPTS_DIRECTORY,
                                metadata_directory=config.METADATA_DIRECTORY,
                                api_kwargs=api_kwargs,
                                admin_alias=config.ADMIN_ALIAS,
                            )
                            save_backup(
                                backups_directory=config.BACKUPS_DIRECTORY,
                                admin_alias=config.ADMIN_ALIAS,
                            )

                            st.rerun()

                    # If no closing code was found in message, proceed as normal

                    # Transform WAV base64 string to bytes
                    audio_bytes = base64.b64decode(interviewer_message_audio_api)

                    # Determine duration of WAV
                    interviewer_message_duration = get_wav_duration(audio_bytes)

                    message_placeholder.empty()
                    message_placeholder.markdown("Interviewer speaking ...")
                    st.audio(audio_bytes, format="audio/wav", autoplay=True)
                    time.sleep(interviewer_message_duration + 0.5)
                    message_placeholder.empty()
                    message_placeholder.markdown(interviewer_message_transcript)

                    # Append interviewer’s message
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": interviewer_message_transcript,
                            "audio": {"id": interviewer_message_id},
                        }
                    )

                    # Attempt a backup save but continue interview if writing fails
                    try:
                        save_backup(
                            backups_directory=config.BACKUPS_DIRECTORY,
                            admin_alias=config.ADMIN_ALIAS,
                        )
                    except Exception:
                        pass

                # Refresh to show a new voice_input element
                st.session_state.voice_input_key = random.uniform(0, 1)
                st.rerun()
