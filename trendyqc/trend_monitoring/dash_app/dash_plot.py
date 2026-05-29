import logging
import json
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trendyqc.settings")
django.setup()

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.graph_objects as go
from dash import dcc, html, Output, Input, State, ALL
from django_plotly_dash import DjangoDash

from trend_monitoring.dash_app.get_data.filtering import (
    get_data_for_plotting,
    get_subset_queryset,
    format_data_for_plotly_js,
)
from trend_monitoring.dash_app.setup_dash_elements.individual_dropdowns import (
    get_assay,
    get_metrics,
    get_date_picker,
    get_filter_table,
)
from trend_monitoring.dash_app.setup_dash_elements.utils import (
    build_filter_text,
)
from trend_monitoring.dash_app.handle_filters import import_filter

from trend_monitoring.models.filters import Filter

logger = logging.getLogger("basic")

app = DjangoDash("Plot", external_stylesheets=[dbc.themes.BOOTSTRAP])


def define_layout(**kwargs):
    return dmc.MantineProvider(
        dcc.Store(id="message-store"),
        dmc.Alert(id="alert-message", duration=5000, hide=True),
        dmc.Stack(
            [
                dmc.Modal(
                    id="filter-name-modal",
                    children=[
                        dmc.TextInput(id="filter-name", label="Your filter:"),
                        dmc.Group(
                            mt="lg",
                            justify="flex-end",
                            children=[
                                dmc.Button("Submit", id="submit-filter_name"),
                            ],
                        ),
                    ],
                ),
                dcc.Store(id="auth-store"),
                dcc.Store(id="filter-store", data=0),
                dcc.Store(id="applied-filter-store", data=None),
                dcc.Interval(
                    id="auth-interval",
                    interval=500,
                    n_intervals=0,
                    max_intervals=1,
                ),
                dmc.Stack(
                    [
                        dmc.Group(
                            get_assay() + get_metrics() + get_date_picker(),
                            justify="center",
                            gap="md",
                            grow=True,
                        ),
                        dmc.Button(
                            "Save filter",
                            id="save-filter-btn",
                            justify="center",
                        ),
                    ]
                    + [
                        html.Div(
                            get_filter_table(), id="filter-table-container"
                        )
                    ],
                    align="stretch",
                    justify="center",
                    gap="sm",
                ),
                html.Div(
                    [
                        html.H3("", id="graph-title"),
                        dcc.Graph(id="output-graph", style={"height": "75vh"}),
                    ]
                ),
            ],
            align="stretch",
            justify="center",
            gap="sm",
            style={"padding": "10px"},
        ),
    )


app.layout = define_layout

# handle authentification status with dash
app.clientside_callback(
    """
    function(n) {
        return fetch("/trendyqc/auth-status/")
            .then(r => r.json())
            .then(data => data.is_authenticated);
    }
    """,
    Output("auth-store", "data"),
    Input("auth-interval", "n_intervals"),
)


@app.callback(
    Output("save-filter-btn", "style"),
    Output("filter-table", "style"),
    Input("auth-store", "data"),
)
def toggle_save_button(is_authenticated):
    if is_authenticated:
        return {"display": "flex"}, {"display": "flex"}

    return {"display": "none"}, {"display": "none"}


@app.callback(Output("alert-message", "style"), Input("message-store", "data"))
def update_message(data):
    return data


@app.callback(
    Output("filter-table-container", "children"),
    Input("submit-filter_name", "n_clicks"),
    Input("auth-interval", "n_intervals"),
    Input("filter-store", "data"),  # triggers refresh after delete
)
def refresh_filter_table(*args, **kwargs):
    return get_filter_table()


@app.callback(
    Output("applied-filter-store", "data"),
    Input("dropdown-assay", "value"),
    Input("dropdown-metric", "value"),
    Input("radio-date", "value"),
    Input("date-picker", "value"),
    Input({"type": "use-filter-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def update_filter_store(
    assays, metrics, days_back, date_range, n_clicks, *args, **kwargs
):
    triggered = kwargs.get("callback_context").triggered[0]["prop_id"]

    if "use-filter-btn" in triggered:
        if not any(n_clicks):
            raise dash.exceptions.PreventUpdate
        filter_id = json.loads(triggered.split(".")[0])["index"]
        filter_obj = Filter.objects.get(id=filter_id)
        return json.loads(filter_obj.content)

    # store dropdown values directly
    return {
        "assay": assays,
        "metric": metrics,
        "days_back": [days_back],
        "date_start": date_range[0] if date_range else None,
        "date_end": date_range[1] if date_range else None,
    }


@app.callback(
    Output("filter-store", "data"),
    Output("message-store", "data"),
    Input({"type": "delete-filter-btn", "index": ALL}, "n_clicks"),
    State("filter-store", "data"),
    prevent_initial_call=True,
)
def delete_filter(n_clicks, current, *args, **kwargs):
    if not any(n_clicks):
        raise dash.exceptions.PreventUpdate

    triggered = kwargs.get("callback_context").triggered[0]["prop_id"]
    filter_id = json.loads(triggered.split(".")[0])["index"]

    filter_to_delete = Filter.objects.filter(id=filter_id)
    filter_name = filter_to_delete.name
    delete_msg = Filter.objects.filter(id=filter_id).delete()

    msg = f"Filter '{filter_name}' has been successfully deleted"
    msg_data = {
        "attributes": {
            "label": "Filter deleted",
            "message": msg,
        },
        "color": "green",
        "hide": False,
    }
    logger.info(f"{msg}: {delete_msg}")

    return (current + 1, msg_data)  # increment to trigger refresh


@app.callback(
    Output("filter-name-modal", "opened"),
    Output("message-store", "data"),
    Input("save-filter-btn", "n_clicks"),
    Input("submit-filter_name", "n_clicks"),
    State("filter-name", "value"),
    State("filter-name-modal", "opened"),
    State("dropdown-assay", "value"),
    State("dropdown-metric", "value"),
    State("radio-date", "value"),
    State("date-picker", "value"),
    prevent_initial_call=True,
)
def save_filter(
    save_button,
    submit_name,
    filter_name,
    opened,
    assays,
    metrics,
    days_back,
    date_range,
    *args,
    **kwargs,
):
    triggered = (
        kwargs.get("callback_context").triggered[0]["prop_id"].split(".")[0]
    )

    msg_data = {}

    if triggered == "save-filter-btn":
        return True, msg_data

    if triggered == "submit-filter_name":
        form_data = {
            "assay": assays,
            "metric": metrics,
            "days_back": [days_back],
            "date_start": date_range[0] if date_range else None,
            "date_end": date_range[1] if date_range else None,
        }

        if kwargs.get("request"):
            request = kwargs["request"]
            msg, msg_status = import_filter(
                filter_name, request.user.username, form_data
            )
            msg_data = {
                "attributes": {
                    "label": "Filter saved",
                    "message": msg,
                },
                "color": "green",
                "hide": False,
            }
            logger.info(msg)

        return False, msg_data

    return opened, msg_data


@app.callback(
    Output("output-graph", "figure"),
    Output("graph-title", "children"),
    Input("applied-filter-store", "data"),
    prevent_initial_call=True,
)
def callback_graph(applied_filter):
    if not applied_filter:
        return dash.no_update, dash.no_update

    assays = applied_filter.get("assay")
    metrics = applied_filter.get("metric")
    days_back = applied_filter.get("days_back", [None])[0]
    date_range = [
        applied_filter.get("date_start"),
        applied_filter.get("date_end"),
    ]

    if not metrics:
        return dash.no_update, dash.no_update

    data = get_subset_queryset(
        {
            "assay": assays,
            "date_start": date_range[0] if date_range else None,
            "date_end": date_range[1] if date_range else None,
            "days_back": int(days_back) if days_back else None,
        }
    )
    df, projects_no_metrics, samples_no_metric = get_data_for_plotting(
        data, metrics
    )
    json_plot_data, is_grouped = format_data_for_plotly_js(df)

    fig = go.Figure()

    for json_data in json_plot_data:
        fig.add_trace(go.Box(**json_data))

    plot_title = build_filter_text(
        json.dumps(
            {
                "assay": assays,
                "metric": metrics,
                "date_start": date_range[0] if date_range else None,
                "date_end": date_range[1] if date_range else None,
                "days_back": [int(days_back)] if days_back else None,
            }
        )
    )

    return fig, plot_title
