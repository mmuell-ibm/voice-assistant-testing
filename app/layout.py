from dash import dcc, html, dash_table
from typing import Dict, List
from voice_utils import get_voices


def create_layout(
    initial_data: Dict[str, List[Dict[str, str]]] = {
        "base": [
            {
                "User Recording": "",
                "Expected User Text": "",
                "Transcribed Text": "",
                "Expected Assistant Response": "",
                "Actual Assistant Response": "",
                "Latency": "",
            }
            for _ in range(10)  # Generate 10 identical dictionaries
        ],
    },
) -> html.Div:
    """
    Create the layout for the Dash app.

    Args:
        initial_data (Dict[str, List[Dict[str, str]]]): A dictionary containing the initial data to populate the table.

    Returns:
        html.Div: The main layout of the Dash app.
    """
    layout = html.Div(
        id="main-container",
        children=[
            html.Div(
                id="header",
                children=[
                    html.H1(
                        id="main-header",
                        children="Watsonx.Assistant Voice Testing Tool",
                    ),
                    html.H2(id="sub-header", children="Client Engineering"),
                ],
            ),
            html.Div(
                id="row-container",
                children=[
                    html.Div(
                        id="convo-path-section",
                        className="section",
                        children=[
                            html.Div(
                                className="section-title", children="Conversation Path"
                            ),
                            html.Div(
                                className="input-controls",
                                children=[
                                    dcc.Input(
                                        id="new-convo-path-name",
                                        type="text",
                                        placeholder="Enter new conversation path name",
                                    ),
                                    html.Button(
                                        "Add Conversation Path",
                                        id="add-convo-path-btn",
                                        n_clicks=0,
                                    ),
                                ],
                            ),
                            dcc.Dropdown(
                                id="convo-path-dropdown",
                                placeholder="Conversation Path",
                                options=[
                                    {"label": option, "value": option}
                                    for option in initial_data.keys()
                                ],
                                value=list(initial_data.keys())[
                                    0
                                ],  # Default to the first key
                            ),
                        ],
                    ),
                    html.Div(
                        id="voice-controls",
                        className="section",
                        children=[
                            html.Div(
                                className="section-title", children="Voice Controls"
                            ),
                            dcc.Upload(
                                id="voice-upload",
                                children=html.Div(
                                    ["Drag and Drop or ", html.A("Select Files")]
                                ),
                            ),
                            dcc.Dropdown(
                                id="voice-dropdown",
                                placeholder="User Voice",
                                options=[],
                            ),
                            dcc.Dropdown(
                                id="response-voice-dropdown",
                                placeholder="Response Voice",
                                options=[
                                    {"label": voice, "value": voice}
                                    for voice in get_voices()
                                ],
                                value="en-US_EmmaExpressive",
                                clearable=False,
                            ),
                            dcc.ConfirmDialog(
                                id="upload-popup",
                                message="Your ZIP file has been successfully uploaded and processed.",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="table-container",
                children=[
                    dash_table.DataTable(
                        id="table",
                        columns=[
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
                            {
                                "name": "Transcribed Text",
                                "id": "Transcribed Text",
                                "editable": False,
                            },
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
                            {
                                "name": "Assistant Response Recording",
                                "id": "Assistant Response Recording",
                                "editable": False,
                            },
                            {"name": "Latency", "id": "Latency", "editable": False},
                        ],
                        data=initial_data[
                            list(initial_data.keys())[0]
                        ],  # Default to the first key
                        editable=True,
                        dropdown={"User Recording": {"options": []}},
                        style_data_conditional=[
                            {
                                "if": {"column_id": "Assistant Response Recording"},
                                "textDecoration": "underline",
                                "color": "blue",
                            },
                            {
                                "if": {
                                    "filter_query": "{Expected User Text} = {Transcribed Text}",
                                    "column_id": "Transcribed Text",
                                },
                                "backgroundColor": "green",
                                "color": "white",
                            },
                            {
                                "if": {
                                    "filter_query": "{Expected User Text} != {Transcribed Text}",
                                    "column_id": "Transcribed Text",
                                },
                                "backgroundColor": "red",
                                "color": "white",
                            },
                            {
                                "if": {
                                    "filter_query": "{Expected Assistant Response} = {Actual Assistant Response}",
                                    "column_id": "Actual Assistant Response",
                                },
                                "backgroundColor": "green",
                                "color": "white",
                            },
                            {
                                "if": {
                                    "filter_query": "{Expected Assistant Response} != {Actual Assistant Response}",
                                    "column_id": "Actual Assistant Response",
                                },
                                "backgroundColor": "red",
                                "color": "white",
                            },
                        ],
                        row_deletable=True,
                        style_table={
                            "overflowY": "auto",  # Enables vertical scrolling
                            "overflowX": "auto",  # Enables horizontal scrolling
                            "height": "100%",  # Allow the table to take full height of its container
                            "width": "100%",  # Allow the table to take full width of its container
                            "minHeight": "750px",  # Set a minimum height for the table
                            "minWidth": "1200px",  # Set a minimum width for the table
                        },
                        style_cell={
                            "minWidth": "150px",
                            "width": "150px",
                            "maxWidth": "200px",
                            "whiteSpace": "normal",  # Enable text wrapping
                            "textOverflow": "ellipsis",
                        },
                        page_size=10,  # Enable pagination after 10 rows
                    ),
                ],
            ),
            html.Div(
                id="table-buttons-section",
                className="section",
                children=[
                    html.Button("Add Row", id="add-row-btn", n_clicks=0),
                    html.Button("Transcribe Text", id="transcribe-btn", n_clicks=0),
                    html.Button("Query Assistant", id="query-btn", n_clicks=0),
                    html.Button("Generate Recordings", id="gen-btn", n_clicks=0),
                    html.Button(
                        "Download Merged Recording", id="merge-btn", n_clicks=0
                    ),
                    dcc.Download(id="response-download"),
                    dcc.Download(id="merged-download"),
                ],
            ),
            html.Div(
                id="export-section",
                className="section",
                children=[
                    html.Button("Export Data", id="export-btn", n_clicks=0),
                    dcc.Download(id="project-download"),
                    dcc.Upload(
                        id="project-upload",
                        children=html.Button(
                            "Import Data", id="import-btn", n_clicks=0
                        ),
                    ),
                ],
            ),
            dcc.Store(id="data-store", data=initial_data),
            dcc.Store(id="voice-store", data={}),
            dcc.Store(id="recording-store", data={}),
        ],
    )
    return layout
