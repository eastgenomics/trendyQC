import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trendyqc.settings")
django.setup()

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, Output, Input
from django_plotly_dash import DjangoDash

from trend_monitoring.dash_app.callbacks import (
    metric_vs_metric,
    metric_over_time,
    add_annotation,
)
from trend_monitoring.dash_app.setup_dash_elements.tabs import get_tabs

app = DjangoDash("Plot", external_stylesheets=[dbc.themes.BOOTSTRAP])


def define_layout(**kwargs):
    return dmc.MantineProvider(
        [
            dcc.Store(id="save-message-store"),
            dcc.Store(id="delete-message-store"),
            dcc.Store(id="message-store"),
            dmc.Alert(
                id="alert-message",
                duration=5000,
                hide=True,
                style={"padding": "10px"},
            ),
            get_tabs(),
        ]
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

metric_over_time.register_callback(app)
metric_vs_metric.register_callback(app)
add_annotation.register_callback(app)


@app.callback(
    Output("message-store", "data"),
    Input("save-message-store", "data"),
    Input("delete-message-store", "data"),
)
def update_message_store(save_msg, delete_msg):
    if save_msg:
        return save_msg
    if delete_msg:
        return delete_msg
    return {}


@app.callback(
    Output("alert-message", "hide"),
    Output("alert-message", "children"),
    Output("alert-message", "color"),
    Input("save-message-store", "data"),
    Input("delete-message-store", "data"),
)
def show_alert(save_msg, delete_msg, *args, **kwargs):
    triggered_list = kwargs.get("callback_context").triggered

    if not triggered_list:
        raise dash.exceptions.PreventUpdate

    triggered = triggered_list[0]["prop_id"]
    msg_data = save_msg if "save" in triggered else delete_msg

    if not msg_data:
        raise dash.exceptions.PreventUpdate

    return (
        False,
        msg_data.get("attributes", {}).get("message", ""),
        msg_data.get("color", "green"),
    )
