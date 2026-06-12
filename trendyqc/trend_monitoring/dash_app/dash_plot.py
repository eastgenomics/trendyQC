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
    annotations,
)
from trend_monitoring.dash_app.setup_dash_elements.tabs import get_tabs

app = DjangoDash("Plot", external_stylesheets=[dbc.themes.BOOTSTRAP])


def define_layout(**kwargs):
    return dmc.MantineProvider(
        [
            dcc.Store(id="auth-store"),
            dcc.Store(id="message-store"),
            dcc.Store(id="annotation-store", data=0),
            dcc.Store(id="filter-store", data=0),
            dcc.Store(id="applied-filter-store", data=None),
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
annotations.register_callback(app)


@app.callback(
    Output("alert-message", "hide"),
    Output("alert-message", "children"),
    Output("alert-message", "color"),
    Input("message-store", "data"),
)
def show_alert(msg):
    if not msg:
        raise dash.exceptions.PreventUpdate

    return (
        msg.get("hide", True),
        msg.get("attributes", {}).get("message", ""),
        msg.get("color", "blue"),
    )
