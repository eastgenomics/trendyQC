import datetime
import json
import logging

from django.contrib.auth.models import User
import dash
from dash import Output, Input, ALL, State
from trend_monitoring.models.annotations import PlotAnnotation

from trend_monitoring.dash_app.setup_dash_elements.individual_components import (
    get_annotation_table,
)
from trend_monitoring.dash_app.get_data.annotations import import_annotation

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
        Input("annotation-store", "data"),
    )
    def refresh_annotation_table(*args, **kwargs):
        return get_annotation_table()

    @app.callback(
        Output("annotation-store", "data"),
        Output("message-store", "data"),
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
        Output("message-store", "data"),
        Input("submit-annotation-info", "n_clicks"),
        State("annotation-date", "value"),
        State("annotation-label", "value"),
        State("annotation-store", "data"),
        prevent_initial_call=True,
    )
    def save_annotation(n_clicks, date, label, current, *args, **kwargs):
        triggered = (
            kwargs.get("callback_context")
            .triggered[0]["prop_id"]
            .split(".")[0]
        )

        msg_data = {}

        if triggered == "submit-annotation-info":
            request = kwargs["request"]

            msg, msg_status = import_annotation(
                date=date,
                label=label,
                user=User.objects.get(pk=request.user.pk),
                created_at=datetime.datetime.now(),
            )

            msg_data = {
                "attributes": {
                    "label": "Annotation saved",
                    "message": f"Created annotation for {date} with {label} as the label",
                },
                "color": "green" if msg_status else "red",
                "hide": False,
            }

            return (current + 1, msg_data)

        return current, msg_data
