from dash import Dash, dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from app_utils import AppUtils
import layout
import json
import io
import zipfile
import os
import base64
from pydub import AudioSegment
from voice_utils import merge_recordings
from typing import Any, Dict, List, Optional, Tuple

# Create Dash app
app = Dash(__name__)

# Define the app layout
app.layout = layout.create_layout()


@app.callback(
    Output("table", "data"),
    Output("table", "dropdown"),
    Output("convo-path-dropdown", "options"),
    Output("data-store", "data"),
    Output("recording-store", "data"),
    Input("add-row-btn", "n_clicks"),
    Input("add-convo-path-btn", "n_clicks"),
    Input("transcribe-btn", "n_clicks"),
    Input("query-btn", "n_clicks"),
    Input("gen-btn", "n_clicks"),
    Input("voice-dropdown", "value"),
    Input("convo-path-dropdown", "value"),
    State("convo-path-dropdown", "options"),
    State("new-convo-path-name", "value"),
    State("table", "data"),
    State("table", "dropdown"),
    State("data-store", "data"),
    State("voice-store", "data"),
    State("recording-store", "data"),
)
def update_table_and_dropdowns(
    n_clicks_add_row: Optional[int],
    n_clicks_add_convo_path: Optional[int],
    n_clicks_transcribe: Optional[int],
    n_clicks_query: Optional[int],
    n_clicks_gen: Optional[int],
    voice_dropdown: Optional[str],
    convo_path_dropdown_value: Optional[str],
    convo_path_dropdown_options: List[Dict[str, Any]],
    new_convo_path_name: Optional[str],
    table_data: List[Dict[str, Any]],
    table_dropdown: List[Dict[str, Any]],
    data_store: Dict[str, Any],
    voice_store: Dict[str, Any],
    recording_store: Dict[str, Any],
) -> Tuple[
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    Dict[str, Any],
    Dict[str, Any],
]:
    """
    Update the table and dropdowns based on user interactions.

    Args:
        n_clicks_add_row (Optional[int]): Number of clicks on the 'add-row-btn'.
        n_clicks_add_convo_path (Optional[int]): Number of clicks on the 'add-convo-path-btn'.
        n_clicks_transcribe (Optional[int]): Number of clicks on the 'transcribe-btn'.
        n_clicks_query (Optional[int]): Number of clicks on the 'query-btn'.
        n_clicks_gen (Optional[int]): Number of clicks on the 'gen-btn'.
        voice_dropdown (Optional[str]): Selected value from the 'voice-dropdown'.
        convo_path_dropdown_value (Optional[str]): Selected value from the 'convo-path-dropdown'.
        convo_path_dropdown_options (List[Dict[str, Any]]): Options for the conversation path dropdown.
        new_convo_path_name (Optional[str]): New conversation path name input by the user.
        table_data (List[Dict[str, Any]]): Current data in the table.
        table_dropdown (List[Dict[str, Any]]): Dropdown options for the table.
        data_store (Dict[str, Any]): Data store dictionary.
        voice_store (Dict[str, Any]): Voice store dictionary.
        recording_store (Dict[str, Any]): Recording store dictionary.

    Returns:
        Tuple[
            List[Dict[str, Any]],
            List[Dict[str, Any]],
            List[Dict[str, Any]],
            Dict[str, Any],
            Dict[str, Any]
        ]: Updated table data, table dropdowns, conversation path options, data store, and recording store.
    """
    utils = AppUtils(
        voice_dropdown,
        convo_path_dropdown_value,
        convo_path_dropdown_options,
        new_convo_path_name,
        table_data,
        table_dropdown,
        data_store,
        voice_store,
        recording_store,
    )

    # Run updates based on input and state values
    utils.run_updates()

    # Generate and return the output
    return utils.generate_output()


@app.callback(
    Output("upload-popup", "displayed"),
    Output("voice-dropdown", "options"),
    Output("voice-store", "data"),
    Input("voice-upload", "contents"),
    State("voice-upload", "filename"),
    State("voice-store", "data"),
    State("voice-dropdown", "options"),
)
def upload_voice(
    zip_contents: Optional[str],
    zip_filename: Optional[str],
    voice_store: Dict[str, Any],
    voice_options: List[Dict[str, str]],
) -> Tuple[bool, List[Dict[str, str]], Dict[str, Any]]:
    """
    Handle the upload and processing of voice files from a zip archive.

    Args:
        zip_contents (Optional[str]): Base64 encoded contents of the uploaded zip file.
        zip_filename (Optional[str]): Filename of the uploaded zip file.
        voice_store (Dict[str, Any]): Current voice store dictionary.
        voice_options (List[Dict[str, str]]): Current options for the voice dropdown.

    Returns:
        Tuple[bool, List[Dict[str, str]], Dict[str, Any]]:
            - bool: Whether the upload was successful.
            - List[Dict[str, str]]: Updated voice dropdown options.
            - Dict[str, Any]: Updated voice store dictionary.
    """
    if zip_contents is not None and zip_filename.endswith(".zip"):
        content_type, content_string = zip_contents.split(",")
        decoded = io.BytesIO(base64.b64decode(content_string))
        display_name = zip_filename[:-4]
        voice_store[display_name] = {}
        upload_dir = "uploaded_files"
        zip_dir = display_name
        zip_path = os.path.join(upload_dir, zip_dir)

        with zipfile.ZipFile(decoded, "r") as zip_ref:
            zip_ref.extractall(upload_dir)

        for file_name in os.listdir(zip_path):
            file_path = os.path.join(zip_path, file_name)
            if file_name.endswith(".wav") or file_name.endswith(".m4a"):
                # Convert .m4a files to .wav if necessary
                if file_name.endswith(".m4a"):
                    audio = AudioSegment.from_file(file_path, format="m4a")
                    wav_path = file_path.replace(".m4a", ".wav")
                    audio.export(wav_path, format="wav")
                    file_path = wav_path
                    file_name = file_name.replace(".m4a", ".wav")

                encoded_wav = base64.b64encode(open(file_path, "rb").read()).decode(
                    "utf-8"
                )
                voice_store[display_name][file_name] = encoded_wav

        voice_options.append({"label": display_name, "value": display_name})

        return True, voice_options, voice_store

    return False, voice_options, voice_store


@app.callback(
    Output("response-download", "data"),
    Output("data-store", "data", allow_duplicate=True),
    Input("table", "active_cell"),
    State("recording-store", "data"),
    State("convo-path-dropdown", "value"),
    State("table", "data"),
    State("data-store", "data"),
    prevent_initial_call="initial_duplicate",
)
def download_file(
    active_cell: Optional[Dict[str, Any]],
    recording_store: Dict[str, Any],
    convo_path: str,
    table_data: List[Dict[str, Any]],
    data_store: Dict[str, Any],
) -> Tuple[Optional[bytes], Dict[str, Any]]:
    """
    Handle the download of a specific file based on the active cell in the table.

    Args:
        active_cell (Optional[Dict[str, Any]]): Information about the currently active cell in the table.
        recording_store (Dict[str, Any]): Current recording store dictionary.
        convo_path (str): Selected conversation path.
        table_data (List[Dict[str, Any]]): Current data in the table.
        data_store (Dict[str, Any]): Current data store dictionary.

    Returns:
        Tuple[Optional[bytes], Dict[str, Any]]:
            - Optional[bytes]: File data to be downloaded, or None if no file is selected.
            - Dict[str, Any]: Updated data store dictionary.
    """
    if active_cell:
        data_store[convo_path] = table_data
        if active_cell["column_id"] == "Assistant Response Recording":
            row = active_cell["row"]
            file_data = recording_store[convo_path][str(row)]
            file_data = base64.b64decode(file_data)
            convo_path_name = f"convo_path_{convo_path}"
            row_name = f"row_{row}"
            output_filename = f"{convo_path_name}_{row_name}.wav"
            return dcc.send_bytes(file_data, output_filename), data_store
    return None, data_store


@app.callback(
    Output("merged-download", "data"),
    Input("merge-btn", "n_clicks"),
    State("recording-store", "data"),
    State("voice-store", "data"),
    State("convo-path-dropdown", "value"),
    State("voice-dropdown", "value"),
    State("table", "data"),
    prevent_initial_call="initial_duplicate",
)
def download_merged(
    n_clicks: Optional[int],
    recording_store: Dict[str, Any],
    voice_store: Dict[str, Any],
    convo_path: str,
    voice_dropdown: str,
    table_data: List[Dict[str, Any]],
) -> Optional[bytes]:
    """
    Handle the download of a merged WAV file containing recordings from the table.

    Args:
        n_clicks (Optional[int]): Number of clicks on the 'merge-btn'.
        recording_store (Dict[str, Any]): Current recording store dictionary.
        voice_store (Dict[str, Any]): Current voice store dictionary.
        convo_path (str): Selected conversation path.
        voice_dropdown (str): Selected voice dropdown value.
        table_data (List[Dict[str, Any]]): Current data in the table.

    Returns:
        Optional[bytes]: Combined WAV file data, or None if no recordings are selected.
    """
    if n_clicks > 0:
        recordings = []
        for idx, row in enumerate(table_data):
            # Get User Query
            voice_filename = row["User Recording"]
            if voice_filename != "":
                query_file = voice_store[voice_dropdown][voice_filename]
                recordings.append(base64.b64decode(query_file))

                response_file_data = recording_store[convo_path][str(idx)]
                recordings.append(base64.b64decode(response_file_data))

        # Merge recordings and get the base64 encoded combined audio
        file_data = merge_recordings(recordings)

        convo_path_name = f"convo_path_{convo_path}"
        voice_name = f"audio_{voice_dropdown}"
        output_filename = f"{convo_path_name}_{voice_name}.wav"

        # Decode base64 to bytes for downloading
        file_bytes = base64.b64decode(file_data)

        return dcc.send_bytes(file_bytes, output_filename)
    return None


@app.callback(
    Output("project-download", "data"),
    Input("export-btn", "n_clicks"),
    State("table", "data"),
    State("table", "dropdown"),
    State("convo-path-dropdown", "value"),
    State("data-store", "data"),
    State("voice-store", "data"),
)
def export_project(
    n_clicks: Optional[int],
    table_data: List[Dict[str, Any]],
    table_dropdowns: List[Dict[str, Any]],
    convo_path: str,
    data_store: Dict[str, Any],
    voice_store: Dict[str, Any],
) -> Optional[bytes]:
    """
    Export the current project configuration as a JSON file.

    Args:
        n_clicks (Optional[int]): Number of clicks on the 'export-btn'.
        table_data (List[Dict[str, Any]]): Data currently displayed in the table.
        table_dropdowns (List[Dict[str, Any]]): Dropdown options for the table.
        convo_path (str): Current selected conversation path.
        data_store (Dict[str, Any]): Data store dictionary with project data.
        voice_store (Dict[str, Any]): Voice store dictionary with available voices.

    Returns:
        Optional[bytes]: JSON file data containing the project configuration if `n_clicks` is greater than 0; otherwise, None.
    """
    if n_clicks > 0:
        project_config = {}
        data_store[convo_path] = table_data
        project_config["data_store"] = data_store
        project_config["voice_store"] = voice_store
        project_config["table_dropdown"] = table_dropdowns
        # Convert data to a JSON string and return as bytes
        return dcc.send_bytes(
            json.dumps(project_config).encode(), filename="project_config.json"
        )
    return None


@app.callback(
    Output("data-store", "data", allow_duplicate=True),
    Output("voice-store", "data", allow_duplicate=True),
    Output("convo-path-dropdown", "value", allow_duplicate=True),
    Output("convo-path-dropdown", "options", allow_duplicate=True),
    Output("voice-dropdown", "options", allow_duplicate=True),
    Output("voice-dropdown", "value", allow_duplicate=True),
    Output("table", "data", allow_duplicate=True),
    Output("table", "dropdown", allow_duplicate=True),
    Input("project-upload", "contents"),
    prevent_initial_call="initial_duplicate",
)
def import_project(
    json_contents: Optional[str],
) -> Tuple[
    Dict[str, Any],
    Dict[str, Any],
    str,
    List[Dict[str, str]],
    List[Dict[str, str]],
    str,
    List[Dict[str, Any]],
    List[Dict[str, Any]],
]:
    """
    Import a project configuration from a JSON file and update the app state.

    Args:
        json_contents (Optional[str]): Base64 encoded JSON content from the uploaded file.

    Returns:
        Tuple[
            Dict[str, Any],
            Dict[str, Any],
            str,
            List[Dict[str, str]],
            List[Dict[str, str]],
            str,
            List[Dict[str, Any]],
            List[Dict[str, Any]]
        ]:
            - Dict[str, Any]: Data store dictionary with project data.
            - Dict[str, Any]: Voice store dictionary with available voices.
            - str: Default selected conversation path.
            - List[Dict[str, str]]: Options for the conversation path dropdown.
            - List[Dict[str, str]]: Options for the voice dropdown.
            - str: Default selected voice.
            - List[Dict[str, Any]]: Data to be displayed in the table.
            - List[Dict[str, Any]]: Dropdown options for the table.
    """
    if json_contents:
        # Extract the JSON content from the uploaded file
        content_type, content_string = json_contents.split(",")
        decoded = base64.b64decode(content_string).decode("utf-8")

        json_data = json.loads(decoded)
        convo_paths = list(json_data["data_store"].keys())
        voices = list(json_data["voice_store"].keys())
        voice = voices[0]
        convo_path = convo_paths[0]
        table_data = json_data["data_store"][convo_path]
        convo_options = [{"label": convo, "value": convo} for convo in convo_paths]
        voice_options = [{"label": voice, "value": voice} for voice in voices]
        table_dropdown = json_data["table_dropdown"]

        return [
            json_data["data_store"],
            json_data["voice_store"],
            convo_path,
            convo_options,
            voice_options,
            voice,
            table_data,
            table_dropdown,
        ]
    else:
        raise PreventUpdate


server = app.server  # This is the WSGI application that Gunicorn needs to run

if __name__ == "__main__":
    app.run_server(debug=True)
