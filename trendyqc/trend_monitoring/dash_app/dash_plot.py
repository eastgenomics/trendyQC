import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trendyqc.settings")
django.setup()

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.express as px
from dash import dcc, html
from django_plotly_dash import DjangoDash
from trend_monitoring.dash_app.get_data.filtering import (
    get_data_for_plotting, get_subset_queryset)
from trend_monitoring.dash_app.setup_dash_elements.dropdowns import \
    get_metric_over_time_dropdowns
from trend_monitoring.dash_app.setup_dash_elements.individual_dropdowns import (
    get_assay, get_metrics)
from trend_monitoring.dash_app.setup_dash_elements.tabs import (
    get_metric_over_time_tab_content, get_tabs)

app = DjangoDash("Plot", external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dmc.MantineProvider(
    html.Div(
        [
            get_assay(),
            get_metrics(),
            dcc.Graph(id="output-graph"),
        ],
    )
)


@app.callback(
    dash.dependencies.Output("output-graph", "figure"),
    [
        dash.dependencies.Input("dropdown-assay", "value"),
        dash.dependencies.Input("dropdown-metric", "value"),
    ],
)
def callback_graph(assays, metrics):
    if not assays or not metrics:
        return px.box()

    data = get_subset_queryset({"assay": assays})
    df, projects_no_metrics, samples_no_metric = get_data_for_plotting(
        data, metrics
    )
    metric_col = df.columns[5]
    fig = px.box(
        df,
        x="date",
        y=metric_col,
    )
    return fig
