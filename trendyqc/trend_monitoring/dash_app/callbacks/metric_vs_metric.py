import json
import logging

import dash
import plotly.graph_objects as go
from dash import Output, Input

from trend_monitoring.dash_app.get_data.filtering import (
    get_data_for_plotting,
    get_subset_queryset,
    format_data_for_plotly_js,
)
from trend_monitoring.dash_app.setup_dash_elements.utils import (
    build_filter_text,
)

logger = logging.getLogger("basic")


def register_callback(app):
    @app.callback(
        Output("metric-over-time-graph", "figure"),
        Output("metric-over-time-graph-title", "children"),
        Input("dropdown-assay-metric-v-metric", "value"),
        Input("dropdown-metric-x", "value"),
        Input("dropdown-metric-y", "value"),
        prevent_initial_call=True,
    )
    def callback_graph(assays, metric_x, metric_y, *args, **kwargs):
        if not metric_x and metric_y:
            return dash.no_update, dash.no_update

        data = get_subset_queryset(
            {
                "assay": assays,
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
                }
            )
        )

        return fig, plot_title
