import dash_bootstrap_components as dbc
from trend_monitoring.dash_app.setup_dash_elements.individual_dropdowns import (
    get_assay, get_metrics)


def get_metric_over_time_dropdowns():
    return [get_assay(), get_metrics()]
