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
from trend_monitoring.dash_app.setup_dash_elements.individual_dropdowns import (
    get_projects,
)
from trend_monitoring.dash_app.setup_dash_elements.utils import (
    build_filter_text,
)
from trend_monitoring.models.metadata import Report

logger = logging.getLogger("basic")


def register_callback(app):
    @app.callback(
        Output("dropdown-project", "options"),
        Input("dropdown-assay", "value"),
    )
    def handle_assay_selection(assays):
        projects = sorted(
            {
                f"{project} - {file_id}"
                for project, file_id in Report.objects.filter(
                    report_sample__assay__in=assays
                )
                .values_list("project_name", "dnanexus_file_id")
                .distinct()
            }
        )
        return projects

    @app.callback(
        Output("dropdown-project", "data"),
        Input("dropdown-project", "options"),
    )
    def handle_assay_selection(projects):
        return get_projects(projects)

    @app.callback(
        Output("metric-over-time-graph", "figure"),
        Output("metric-over-time-graph-title", "children"),
        Input("dropdown-project", "value"),
        Input("dropdown-metric-x", "value"),
        Input("dropdown-metric-y", "value"),
        prevent_initial_call=True,
    )
    def callback_graph(project, metric_x, metric_y, *args, **kwargs):
        if not metric_x and metric_y:
            return dash.no_update, dash.no_update

        data = get_subset_queryset(
            {
                "run": project,
            }
        )
        df, projects_no_metrics, samples_no_metric = get_data_for_plotting(
            data, [metric_x, metric_y]
        )
        json_plot_data, is_grouped = format_data_for_plotly_js(df)

        fig = go.Figure()

        for json_data in json_plot_data:
            fig.add_trace(go.Scatter(**json_data))

        plot_title = build_filter_text(
            json.dumps({"metric": metric_y, "metric_x": metric_x})
        )

        return fig, plot_title
