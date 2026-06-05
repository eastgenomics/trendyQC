import json
import logging

import dash
import plotly.graph_objects as go
from dash import Output, Input, State, ALL

from trend_monitoring.dash_app.get_data.filtering import (
    get_data_for_plotting,
    get_subset_queryset,
    format_data_for_boxplot,
)
from trend_monitoring.dash_app.get_data.jira import get_failed_runs
from trend_monitoring.dash_app.get_data.annotations import add_annotations
from trend_monitoring.dash_app.setup_dash_elements.individual_dropdowns import (
    get_filter_table,
)
from trend_monitoring.dash_app.setup_dash_elements.utils import (
    build_filter_text,
)
from trend_monitoring.dash_app.handle_filters import import_filter

from trend_monitoring.models.filters import Filter

logger = logging.getLogger("basic")


def register_callback(app):
    @app.callback(
        Output("save-filter-btn", "style"),
        Output("filter-table", "style"),
        Input("auth-store", "data"),
    )
    def toggle_filter_components(is_authenticated):
        if is_authenticated:
            return {"display": "flex"}, {"display": "flex"}

        return {"display": "none"}, {"display": "none"}

    @app.callback(
        Output("filter-table-container", "children"),
        Input("auth-interval", "n_intervals"),
        Input("filter-store", "data"),
        Input("filter-saved-store", "data"),  # triggers refresh after delete
    )
    def refresh_filter_table(*args, **kwargs):
        return get_filter_table()

    @app.callback(
        Output("filter-name-modal", "opened"),
        Output("save-message-store", "data"),
        Output("filter-saved-store", "data"),
        Input("save-filter-btn", "n_clicks"),
        Input("submit-filter_name", "n_clicks"),
        State("filter-name", "value"),
        State("filter-name-modal", "opened"),
        State("dropdown-assay", "value"),
        State("dropdown-metric", "value"),
        State("radio-date", "value"),
        State("date-picker", "value"),
        State("filter-saved-store", "data"),
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
        filter_saved,
        *args,
        **kwargs,
    ):
        triggered = (
            kwargs.get("callback_context")
            .triggered[0]["prop_id"]
            .split(".")[0]
        )

        msg_data = {}

        if triggered == "save-filter-btn":
            return True, msg_data, filter_saved

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
                    "color": "green" if msg_status else "red",
                    "hide": False,
                }
                logger.info(msg)

            return False, msg_data, filter_saved + 1

        return opened, msg_data, filter_saved

    @app.callback(
        Output("filter-store", "data"),
        Output("delete-message-store", "data"),
        Input({"type": "delete-filter-btn", "index": ALL}, "n_clicks"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def delete_filter(n_clicks, current, *args, **kwargs):
        if not any(n_clicks):
            raise dash.exceptions.PreventUpdate

        triggered = kwargs.get("callback_context").triggered[0]["prop_id"]
        filter_id = json.loads(triggered.split(".")[0])["index"]

        filter_to_delete = Filter.objects.get(id=filter_id)
        filter_name = filter_to_delete.name
        delete_msg = filter_to_delete.delete()

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
        Output("metric-over-time-graph", "figure"),
        Output("metric-over-time-graph-title", "children"),
        Input("applied-filter-store", "data"),
        Input("annotation-checkbox", "checked"),
        prevent_initial_call=True,
    )
    def callback_graph(applied_filter, show_annotations):
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

        # fetch failed runs from JIRA
        run_names = df["project_name"].unique().tolist()
        failed_runs = get_failed_runs(run_names)

        json_plot_data, is_grouped = format_data_for_boxplot(df)

        fig = go.Figure()
        for json_data in json_plot_data:
            fig.add_trace(go.Box(**json_data))

        # add failed run annotations above the plot
        for project_name in df.sort_values("date")["project_name"].unique():
            if project_name in failed_runs:
                fig.add_annotation(
                    x=project_name,
                    y=1,
                    yref="paper",
                    text="⚠ Failed",
                    showarrow=False,
                    font=dict(size=12, color="red"),
                    yanchor="bottom",
                )

        if show_annotations and not df.empty:
            fig = add_annotations(fig, df)

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
