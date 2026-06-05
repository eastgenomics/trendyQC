import logging

from dash import Output, Input

logger = logging.getLogger("basic")


def register_callback(app):
    @app.callback(
        Output("add-annotation", "style"),
        Input("auth-store", "data"),
    )
    def toggle_add_annotation(is_authenticated):
        if is_authenticated:
            return {"display": "flex"}

        return {"display": "none"}
