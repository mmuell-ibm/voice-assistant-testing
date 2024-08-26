import os
import base64
import io
from typing import List
from pydub import AudioSegment  # Library for manipulating audio files
from ibm_watson import (
    AssistantV2,
    SpeechToTextV1,
    TextToSpeechV1,
)  # IBM Watson services for assistant, speech-to-text, and text-to-speech
from ibm_cloud_sdk_core.authenticators import (
    IAMAuthenticator,
)  # Authenticator for IBM Cloud services
from dotenv import load_dotenv  # Library to load environment variables from a .env file
import urllib3  # Library for handling HTTP requests

# Disable SSL warnings for insecure connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from a .env file
load_dotenv()

# Retrieve environment variables for API keys and service URLs
ASSISTANT_API_KEY: str = os.getenv("ASSISTANT_API_KEY")  # API key for Watson Assistant
ASSISTANT_URL: str = os.getenv("ASSISTANT_URL")  # URL for Watson Assistant service
ASSISTANT_ID: str = os.getenv("ASSISTANT_ID")  # Watson Assistant ID

STT_API_KEY: str = os.getenv("STT_API_KEY")  # API key for Speech to Text service
STT_URL: str = os.getenv("STT_URL")  # URL for Speech to Text service
TTS_API_KEY: str = os.getenv("TTS_API_KEY")  # API key for Text to Speech service
TTS_URL: str = os.getenv("TTS_URL")  # URL for Text to Speech service

TTS_MODEL: str = os.getenv("TTS_MODEL")  # Text to Speech model
STT_MODEL: str = os.getenv("STT_MODEL")  # Speech to Text model

# Create an authenticator object for Watson Assistant using the API key
assistant_authenticator = IAMAuthenticator(ASSISTANT_API_KEY)
# Instantiate the AssistantV2 object with the authenticator and version information
assistant = AssistantV2(version="2023-06-15", authenticator=assistant_authenticator)
# Set the service URL for Watson Assistant
assistant.set_service_url(ASSISTANT_URL)
# Disable SSL verification (use with caution in production environments)
assistant.set_disable_ssl_verification(True)

# Create an authenticator object for Speech to Text using the API key
stt_authenticator = IAMAuthenticator(STT_API_KEY)
# Instantiate the SpeechToTextV1 object with the authenticator
speech_to_text = SpeechToTextV1(authenticator=stt_authenticator)
# Set the service URL for Speech to Text
speech_to_text.set_service_url(STT_URL)
speech_to_text.set_disable_ssl_verification(True)

# Create an authenticator object for Text to Speech using the API key
tts_authenticator = IAMAuthenticator(TTS_API_KEY)
# Instantiate the TextToSpeechV1 object with the authenticator
text_to_speech = TextToSpeechV1(authenticator=tts_authenticator)
# Set the service URL for Text to Speech
text_to_speech.set_service_url(TTS_URL)
text_to_speech.set_disable_ssl_verification(True)


def transcribe_audio(encoded_audio: str) -> str:
    """
    Transcribe audio from a base64 encoded string using IBM Watson Speech to Text.

    Args:
        encoded_audio (str): Base64 encoded audio data.

    Returns:
        str: Transcribed text from the audio.
    """
    # Decode the base64 encoded audio data
    audio_data = base64.b64decode(encoded_audio)
    # Open the audio data in binary mode and pass it to the Speech to Text service
    with io.BytesIO(audio_data) as audio_file:
        stt_result = speech_to_text.recognize(
            audio=audio_file,
            content_type="audio/wav",
            smart_formatting=True,
            model=STT_MODEL,
        ).get_result()
    # Extract and return the transcript from the Speech to Text service response
    try:
        transcript = stt_result["results"][0]["alternatives"][0]["transcript"]
    except (IndexError, KeyError):
        print(stt_result)
        return "Transcription failed"
    return transcript


def query_assistant(text: str, session_id: str) -> str:
    """
    Query Watson Assistant with text input and return the response.

    Args:
        text (str): Input text to send to Watson Assistant.
        session_id (str): Session ID for the Watson Assistant interaction.

    Returns:
        str: Response text from Watson Assistant.
    """
    # Send the text input to Watson Assistant and get the response
    response = assistant.message(
        assistant_id=ASSISTANT_ID, session_id=session_id, input={"text": text}
    ).get_result()
    # Extract and return the assistant's response text
    assistant_response = ""
    for response_item in response["output"]["generic"]:
        if response_item["response_type"] == "text":
            assistant_response += response_item["text"] + " "
    return assistant_response


def synthesize_speech(text: str) -> str:
    """
    Convert text to speech using IBM Watson Text to Speech and return the audio as a base64 encoded string.

    Args:
        text (str): Text to convert to speech.

    Returns:
        str: Base64 encoded audio data.
    """
    # Send the text to the Text to Speech service and get the audio content
    response = text_to_speech.synthesize(
        text, accept="audio/wav", voice=TTS_MODEL
    ).get_result()
    # Encode the audio content as base64
    audio_base64 = base64.b64encode(response.content).decode("utf-8")
    return audio_base64


def merge_recordings(recordings: List[bytes]) -> str:
    """
    Merge multiple audio recordings into a single audio file and return the combined audio as a base64 encoded string.

    Args:
        recordings (List[bytes]): List of audio recordings as byte data.

    Returns:
        str: Base64 encoded combined audio data.
    """
    combined = AudioSegment.empty()  # Create an empty audio segment
    for recording in recordings:
        # Convert bytes to AudioSegment
        audio_segment = AudioSegment.from_file(io.BytesIO(recording), format="wav")
        combined += audio_segment  # Add each recording to the combined audio segment

    # Export the combined audio segment to a BytesIO object
    output_buffer = io.BytesIO()
    combined.export(output_buffer, format="wav")

    # Encode the combined audio as base64
    audio_base64 = base64.b64encode(output_buffer.getvalue()).decode("utf-8")
    return audio_base64


def create_session_id() -> str:
    """
    Create a new session for Watson Assistant and return the session ID.

    Returns:
        str: Watson Assistant session ID.
    """
    return assistant.create_session(assistant_id=ASSISTANT_ID).get_result()[
        "session_id"
    ]
