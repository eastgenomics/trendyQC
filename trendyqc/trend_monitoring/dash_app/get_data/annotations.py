import datetime
import json

from django.conf import settings
import pandas as pd
import plotly.graph_objects as go


def load_annotations():
    annotation_file = (
        settings.CONFIG_PATH / "plotting_configs" / "annotations.json"
    )

    if not annotation_file.exists():
        return None

    with open(annotation_file) as f:
        return json.load(f)


def add_annotations(fig: go.Figure, plot_data: pd.DataFrame) -> go.Figure:
    """Add vertical lines between projects based on annotation dates.

    Args:
        fig (go.Figure): Plotly figure
        plot_data (pd.DataFrame): DataFrame with project_name and date columns

    Returns:
        go.Figure: Figure with annotations
    """
    annotations = load_annotations()

    if annotations is None:
        return fig

    # get the sorted list of (date, project_name) pairs
    project_dates = (
        plot_data[["project_name", "date"]]
        .drop_duplicates()
        .sort_values("date")
        .reset_index(drop=True)
    )

    project_order = project_dates["project_name"].tolist()
    n_projects = len(project_order)

    for annotation in annotations:
        annotation_date = annotation["date"]

        # find the index of the first project after the annotation date
        later_projects = project_dates[
            project_dates["date"]
            > datetime.date.fromisoformat(annotation_date)
        ]

        if later_projects.empty:
            continue

        first_later = later_projects.iloc[0]["project_name"]
        insert_index = project_order.index(first_later)

        if insert_index == 0:
            continue

        # position is between insert_index - 1 and insert_index
        # on a categorical axis, each category is at 0, 1, 2...
        # so the midpoint between two adjacent categories is at index - 0.5
        x_position = insert_index - 0.5

        fig.add_shape(
            type="line",
            xref="x",
            yref="paper",
            x0=x_position,
            x1=x_position,
            y0=0,
            y1=1,
            line=dict(color="red", width=2, dash="dash"),
        )
        fig.add_annotation(
            xref="x",
            yref="paper",
            x=x_position,
            y=1,
            text=annotation["label"],
            showarrow=False,
            font=dict(size=12, color="red"),
            textangle=-90,
            xanchor="left",
        )

    return fig
