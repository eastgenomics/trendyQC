import dash_mantine_components as dmc
from dash import dcc, html

from trend_monitoring.dash_app.setup_dash_elements.individual_dropdowns import (
    get_assay,
    get_projects,
    get_metrics,
    get_date_picker,
    get_filter_table,
)


def get_tabs():
    return dmc.Tabs(
        [
            dmc.TabsList(
                [
                    dmc.TabsTab("Metrics over time", value="metric-over-time"),
                    dmc.TabsTab("Metric vs metric", value="metric-vs-metric"),
                ],
            ),
            dmc.TabsPanel(
                get_metric_over_time_tab_content(),
                value="metric-over-time",
            ),
            dmc.TabsPanel(
                get_metric_vs_metric_tab_content(),
                value="metric-vs-metric",
            ),
        ],
        id="tabs",
        value="metric-over-time",
        style={"padding": "10px"},
    )


def get_metric_over_time_tab_content():
    return (
        dmc.Stack(
            [
                dmc.Modal(
                    id="filter-name-modal",
                    children=[
                        dmc.TextInput(id="filter-name", label="Your filter:"),
                        dmc.Group(
                            mt="lg",
                            justify="flex-end",
                            children=[
                                dmc.Button("Submit", id="submit-filter_name"),
                            ],
                        ),
                    ],
                ),
                dcc.Store(id="auth-store"),
                dcc.Store(id="filter-store", data=0),
                dcc.Store(id="filter-saved-store", data=0),
                dcc.Store(id="applied-filter-store", data=None),
                dcc.Interval(
                    id="auth-interval",
                    interval=500,
                    n_intervals=0,
                    max_intervals=1,
                ),
                dmc.Stack(
                    [
                        dmc.Group(
                            get_assay("dropdown-assay")
                            + get_metrics("dropdown-metric")
                            + get_date_picker()
                            + [
                                dmc.Checkbox(
                                    id="annotation-checkbox",
                                    label="Show annotations",
                                    checked=True,
                                ),
                            ],
                            justify="center",
                            gap="md",
                            grow=True,
                        ),
                        dmc.Button(
                            "Save filter",
                            id="save-filter-btn",
                            justify="center",
                        ),
                        html.Div(
                            get_filter_table(), id="filter-table-container"
                        ),
                    ],
                    align="stretch",
                    justify="center",
                    gap="sm",
                ),
                html.Div(
                    [
                        html.H5(
                            "",
                            id="metric-over-time-graph-title",
                            style={
                                "padding": "10px",
                                "text-align": "center",
                            },
                        ),
                        dcc.Graph(
                            id="metric-over-time-graph",
                            style={"height": "75vh"},
                        ),
                    ]
                ),
            ],
            align="stretch",
            justify="center",
            gap="sm",
            style={"padding": "10px"},
        ),
    )


def get_metric_vs_metric_tab_content():
    return (
        dmc.Stack(
            [
                dmc.Stack(
                    [
                        dmc.Group(
                            [
                                dmc.Stack(
                                    get_assay("dropdown-assay-metric-v-metric")
                                    + get_projects()
                                ),
                                dmc.Stack(
                                    get_metrics(
                                        "dropdown-metric-x",
                                        "Select the metric for X",
                                    )
                                    + get_metrics(
                                        "dropdown-metric-y",
                                        "Select the metric for Y",
                                    )
                                ),
                            ],
                            justify="center",
                            gap="md",
                            grow=True,
                        ),
                    ],
                    align="stretch",
                    justify="center",
                    gap="sm",
                ),
                html.Div(
                    [
                        html.H5(
                            "",
                            id="metric-vs-metric-graph-title",
                            style={
                                "padding": "10px",
                                "text-align": "center",
                            },
                        ),
                        dcc.Graph(
                            id="metric-vs-metric-output-graph",
                            style={"height": "75vh"},
                        ),
                    ]
                ),
            ],
            align="stretch",
            justify="center",
            gap="sm",
            style={"padding": "10px"},
        ),
    )
