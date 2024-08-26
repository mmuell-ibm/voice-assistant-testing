from typing import List, Dict, Any
from dataclasses import dataclass, field
import dash
from voice_utils import (
    transcribe_audio,
    synthesize_speech,
    create_session_id,
    query_assistant,
)


@dataclass
class AppUtils:
    # Dropdowns and options
    voice_dropdown: List[Dict[str, str]]
    convo_path_dropdown_value: str
    convo_path_dropdown_options: List[Dict[str, str]]
    response_voice_dropdown_value: str
    new_convo_path_name: str

    # Data storage
    table_data: List[Dict[str, Any]]
    table_dropdown: Dict[str, Dict[str, List[Dict[str, str]]]]
    data_store: Dict[str, List[Dict[str, Any]]]
    voice_store: Dict[str, Dict[str, str]]
    recording_store: Dict[str, Dict[int, Any]]

    # Default columns for the table
    default_columns: List[Dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "name": "User Recording",
                "id": "User Recording",
                "editable": True,
                "presentation": "dropdown",
            },
            {
                "name": "Expected User Text",
                "id": "Expected User Text",
                "editable": True,
            },
            {"name": "Transcribed Text", "id": "Transcribed Text", "editable": False},
            {
                "name": "Expected Assistant Response",
                "id": "Expected Assistant Response",
                "editable": True,
            },
            {
                "name": "Actual Assistant Response",
                "id": "Actual Assistant Response",
                "editable": False,
            },
            {"name": "Latency", "id": "Latency", "editable": True},
        ]
    )

    def run_updates(self) -> None:
        """Process updates based on the triggered event."""
        triggered = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        print(triggered)

        if triggered == "voice-dropdown":
            self.clear_table_dropdown("User Recording")
            voice_files = set(self.voice_store.get(self.voice_dropdown, {}).keys())
            for voice in voice_files:
                self.update_table_dropdown("User Recording", voice)

        elif triggered == "convo-path-dropdown":
            self.update_table()

        elif triggered == "add-row-btn":
            self.add_row()

        elif triggered == "add-convo-path-btn":
            self.add_option()

        elif triggered == "transcribe-btn":
            for idx, row in enumerate(self.table_data):
                filename = row.get("User Recording", "")
                if filename:
                    audio_file = self.voice_store.get(self.voice_dropdown, {}).get(
                        filename
                    )
                    if audio_file:
                        transcription = transcribe_audio(audio_file)
                        self.table_data[idx]["Transcribed Text"] = transcription

        elif triggered == "query-btn":
            session_id = create_session_id()
            for idx, row in enumerate(self.table_data):
                text = row.get("Transcribed Text", "") or row.get(
                    "Expected User Text", ""
                )
                response = query_assistant(text, session_id)
                self.table_data[idx]["Actual Assistant Response"] = response

        elif triggered == "gen-btn":
            self.recording_store[self.convo_path_dropdown_value] = {}
            for idx, row in enumerate(self.table_data):
                text = row.get("Actual Assistant Response")
                if text == "":
                    text = row.get("Expected Assistant Response")
                if text != "":
                    self.table_data[idx]["Assistant Response Recording"] = "recording"
                    self.recording_store[self.convo_path_dropdown_value][idx] = (
                        synthesize_speech(text, self.response_voice_dropdown_value)
                    )

    def update_table(self) -> None:
        """Update table data based on the selected conversation path."""
        self.data_store[self.convo_path_dropdown_value] = self.table_data
        self.table_data = self.data_store.get(self.convo_path_dropdown_value, [])

    def add_row(self) -> None:
        """Add a new row to the table with default column values."""
        if not self.table_data:
            columns = [col["id"] for col in self.default_columns]
            self.table_data.append({col: "" for col in columns})
        else:
            self.table_data.append({col: "" for col in self.table_data[0].keys()})
        self.data_store[self.convo_path_dropdown_value] = self.table_data

    def add_option(self) -> None:
        """Add a new option to the conversation path dropdown."""
        options = [option["value"] for option in self.convo_path_dropdown_options]
        new_option = {
            "label": self.new_convo_path_name,
            "value": self.new_convo_path_name,
        }
        if self.new_convo_path_name and new_option["value"] not in options:
            self.convo_path_dropdown_options.append(new_option)
            self.data_store[self.new_convo_path_name] = [
                {
                    "User Recording": "",
                    "Expected User Text": "",
                    "Transcribed Text": "",
                    "Expected Assistant Response": "",
                    "Latency": "",
                }
            ]

    def update_table_dropdown(self, option_type: str, new_option: str) -> None:
        """Update dropdown options in the table."""
        if option_type in self.table_dropdown:
            current_options = [
                opt["value"] for opt in self.table_dropdown[option_type]["options"]
            ]
            if new_option not in current_options:
                self.table_dropdown[option_type]["options"].append(
                    {"label": new_option, "value": new_option}
                )

    def clear_table_dropdown(self, option_type: str) -> None:
        """Clear options from a dropdown in the table."""
        if option_type in self.table_dropdown:
            self.table_dropdown[option_type]["options"] = []

    def generate_output(self) -> List:
        """Generate the output of the current state."""
        return [
            self.table_data,
            self.table_dropdown,
            self.convo_path_dropdown_options,
            self.data_store,
            self.recording_store,
        ]
