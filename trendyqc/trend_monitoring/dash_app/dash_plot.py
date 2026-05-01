import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trendyqc.settings")
django.setup()

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.graph_objects as go
from dash import dcc, html
from django_plotly_dash import DjangoDash
from trend_monitoring.dash_app.get_data.filtering import (
    get_data_for_plotting,
    get_subset_queryset,
    format_data_for_plotly_js,
)

from trend_monitoring.dash_app.setup_dash_elements.dropdowns import (
    get_metric_over_time_dropdowns,
)
from trend_monitoring.dash_app.setup_dash_elements.individual_dropdowns import (
    get_assay,
    get_metrics,
)
from trend_monitoring.dash_app.setup_dash_elements.tabs import (
    get_metric_over_time_tab_content,
    get_tabs,
)

app = DjangoDash("Plot", external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dmc.MantineProvider(
    html.Div(
        [
            dmc.Flex(
                get_assay() + get_metrics(),
                gap="md",
                justify="center",
                align="center",
                direction="row",
                wrap="wrap",
            ),
            dcc.Graph(id="output-graph", style={"height": "75vh"}),
        ],
        style={"padding": "10px"},
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
        return dash.no_update

    data = get_subset_queryset({"assay": assays})
    df, projects_no_metrics, samples_no_metric = get_data_for_plotting(
        data, metrics
    )
    json_plot_data, is_grouped = format_data_for_plotly_js(df)

    fig = go.Figure()

    for json_data in json_plot_data:
        fig.add_trace(go.Box(**json_data))

    return fig
