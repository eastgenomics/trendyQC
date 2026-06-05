import json
import logging

import dash
import plotly.graph_objects as go
from dash import Output, Input

from trend_monitoring.dash_app.get_data.filtering import (
    get_data_for_plotting,
    get_subset_queryset,
    format_data_for_scatterplot,
)
from trend_monitoring.dash_app.setup_dash_elements.individual_components import (
    get_missing_data_accordions,
)
from trend_monitoring.dash_app.setup_dash_elements.utils import (
    build_filter_text,
)
from trend_monitoring.models.metadata import Report

logger = logging.getLogger("basic")


def register_callback(app):
    @app.callback(
        Output("dropdown-project", "data"),
        Input("dropdown-assay-metric-v-metric", "value"),
        prevent_initial_call=True,
    )
    def update_projects(assays):
        if not assays:
            return []

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
        return [{"value": p, "label": p} for p in projects]

    @app.callback(
        Output("metric-vs-metric-output-graph", "figure"),
        Output("metric-vs-metric-graph-title", "children"),
        Output("metric-vs-metric-missing-data-accordion", "children"),
        Input("dropdown-project", "value"),
        Input("dropdown-metric-x", "value"),
        Input("dropdown-metric-y", "value"),
        prevent_initial_call=True,
    )
    def callback_graph_metric_vs_metric(
        project, metric_x, metric_y, *args, **kwargs
    ):
        if not metric_x or not metric_y:
            return dash.no_update, dash.no_update

        data = get_subset_queryset(
            {"run": [project.split(" - ")[0]] if project else []}
        )
        df, projects_no_metrics, samples_no_metric = get_data_for_plotting(
            data, metric_x + metric_y
        )
        json_plot_data, _ = format_data_for_scatterplot(df)

        fig = go.Figure()

        for json_data in json_plot_data:
            fig.add_trace(go.Scatter(**json_data))

        plot_title = build_filter_text(
            json.dumps(
                {"run": [project], "metric_x": metric_x, "metric": metric_y}
            )
        )
        accordion = get_missing_data_accordions(
            projects_no_metrics, samples_no_metric
        )

        return fig, plot_title, accordion
