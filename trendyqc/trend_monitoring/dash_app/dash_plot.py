import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trendyqc.settings")
django.setup()

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.graph_objects as go
from dash import dcc, html, Output, Input
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
)

app = DjangoDash("Plot", external_stylesheets=[dbc.themes.BOOTSTRAP])


@app.callback(
    Output("output-graph", "figure"),
    [
        Input("dropdown-assay", "value"),
        Input("dropdown-metric", "value"),
        Input("radio-date", "value"),
        Input("date-picker", "value"),
    ],
)
def callback_graph(assays, metrics, days_back, date_range):
    if not metrics:
        return dash.no_update

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

    return fig


def define_layout(**kwargs):
    request = kwargs.get("request")
    is_authenticated = request and request.user.is_authenticated

    return dmc.MantineProvider(
        html.Div(
            [
                dcc.Store(
                    id={"type": "storage", "index": "session"},
                    storage_type="session",
                ),
                dmc.Grid(
                    [
                        dmc.GridCol(get_assay(), span="auto"),
                        dmc.GridCol(get_metrics(), span="auto"),
                        dmc.GridCol(get_date_picker(), span="auto"),
                    ],
                    justify="space-between",
                    align="center",
                    grow=True,
                ),
                dcc.Graph(id="output-graph", style={"height": "75vh"}),
            ],
            style={"padding": "10px"},
        )
    )


app.layout = define_layout
