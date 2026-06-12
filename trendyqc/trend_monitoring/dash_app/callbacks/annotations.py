import json
import logging

import dash
from dash import Output, Input, ALL, State
from trend_monitoring.models.annotations import PlotAnnotation

from trend_monitoring.dash_app.setup_dash_elements.individual_components import (
    get_annotation_table,
)

logger = logging.getLogger("basic")


def register_callback(app):
    @app.callback(
        Output("add-annotation", "style"),
        Input("auth-store", "data"),
    )
    def toggle_add_annotation(is_authenticated):
        if is_authenticated:
            return {}
        return {"display": "none"}

    @app.callback(
        Output("annotation-table-container", "children"),
        Input("auth-interval", "n_intervals"),
        Input("annotation-store", "data"),
        Input(
            "annotation-saved-store", "data"
        ),  # triggers refresh after delete
    )
    def refresh_annotation_table(*args, **kwargs):
        return get_annotation_table()

    @app.callback(
        Output("annotation-store", "data"),
        Output("message-store", "data", allow_duplicate=True),
        Input({"type": "delete-annotation-btn", "index": ALL}, "n_clicks"),
        State("annotation-store", "data"),
        prevent_initial_call=True,
    )
    def delete_annotation(n_clicks, current, *args, **kwargs):
        if not any(n_clicks):
            raise dash.exceptions.PreventUpdate

        triggered = kwargs.get("callback_context").triggered[0]["prop_id"]
        annotation_id = json.loads(triggered.split(".")[0])["index"]

        annotation_to_delete = PlotAnnotation.objects.get(id=annotation_id)
        annotation_label = annotation_to_delete.label
        delete_msg = annotation_to_delete.delete()

        msg = f"Annotation '{annotation_label}' has been successfully deleted"
        msg_data = {
            "attributes": {
                "label": "Annotation deleted",
                "message": msg,
            },
            "color": "green",
            "hide": False,
        }
        logger.info(f"{msg}: {delete_msg}")

        return (current + 1, msg_data)  # increment to trigger refresh

    @app.callback(
        Output("annotation-store", "data"),
        Output("message-store", "data", allow_duplicate=True),
        Input("submit-annotation-info", "n_clicks"),
        State("annotation-date", "value"),
        State("annotation-label", "value"),
        State("annotation-store", "data"),
        prevent_initial_call=True,
    )
    def save_annotation(n_clicks, date, label, current):
        print(n_clicks)
        if not any(n_clicks):
            raise dash.exceptions.PreventUpdate

        print(date, label)

        msg_data = ""

        return (current + 1, msg_data)
