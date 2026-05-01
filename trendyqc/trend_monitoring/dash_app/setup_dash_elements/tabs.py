from dash import dcc


def get_tabs():
    return (
        dcc.Tabs(
            id="tabs",
            value="metric-over-time",
            children=[
                dcc.Tab(label="Metrics over time", value="metric-over-time"),
                dcc.Tab(label="Metric vs metric", value="metric-vs-metric"),
            ],
        ),
    )


def get_metric_over_time_tab_content():
    pass
