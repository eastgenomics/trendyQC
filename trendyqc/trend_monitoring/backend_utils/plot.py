from typing import Dict

import pandas as pd
import plotly.graph_objs as go
from plotly.graph_objs import Scatter

from django.apps import apps
from django.core.exceptions import FieldError
from django.db.models.query import QuerySet
from trend_monitoring.models.metadata import Report_Sample


def prepare_filter_data(filter_recap: Dict) -> Dict:
    """ Order the data received in the filter form into a dict with the keys
    being categories to help getting the data needed and the appropriate
    metrics i.e.
    {
        "subset": {
            "sequencer_id": A01303
            "date_start": 2023-06-13
        },
        "y_axis": {
            "gc_perc": 48
        }
    }

    Args:
        filter_recap (dict): Dict containing the field and values inputted in
        the form

    Returns:
        dict: Dict as described above. Primary keys pointing to the category of
        data and secondary keys and values being the data passed through the
        form
    """

    data = {}
    data.setdefault("subset", {})
    data.setdefault("x_axis", {})
    data.setdefault("y_axis", {})

    for field, value in filter_recap.items():
        # skip if a field was not given any data
        if not value:
            continue

        # I'm setting a list by default because I want the user to be able to
        # select multiple runs for example
        if field in [
            "assay_select", "run_select", "sequencer_select"
        ]:
            data["subset"].setdefault(field, [])
            data["subset"][field].append(value)

        # this is kept separated from the above because you can input only one
        # date range
        if field in ["date_start", "date_end"]:
            data["subset"].setdefault(field, "")
            data["subset"][field] = value

        if field == "metrics_x":
            data["x_axis"].setdefault(field, "")
            data["x_axis"][field] = value

        if field == "metrics_y":
            data["y_axis"].setdefault(field, "")
            data["y_axis"][field] = value

    return data


def get_subset_queryset(data: Dict) -> QuerySet:
    """ Get all the Report_sample objects that belong to the subset that the
    user inputted

    Args:
        data (dict): Dict of data from the subset part of the form

    Returns:
        Django Queryset: Queryset containing all the Report sample objects
        after filtering using the data inputted by the user
    """

    assays = data.get("assay_select", [])
    runs = data.get("run_select", [])
    sequencer_ids = data.get("sequencer_select", [])
    date_start = data.get("date_start")
    date_end = data.get("date_end")

    # combine all the data passed through the form to build the final queryset
    return (
        Report_Sample.objects.filter(report__project_name__in=runs) |
        Report_Sample.objects.filter(assay__in=assays) |
        Report_Sample.objects.filter(report__sequencer_id__in=sequencer_ids) |
        Report_Sample.objects.filter(
            report__date__range=(date_start, date_end)
        )
    ).prefetch_related()


def get_data_for_plotting(
    report_sample_queryset: QuerySet, metric: str = "total_sequences"
) -> pd.DataFrame:
    """ Get the data from the queryset in a Pandas dataframe.

    Args:
        report_sample_queryset (QuerySet): Report sample queryset
        metric (str, optional): Metric that we want to plot on the Y-axis.
        Defaults to "total_sequences" for testing purposes.

    Returns:
        pd.DataFrame: Dataframe that looks like this:
                sample1 sample2 sample3
            date1 	value1 	value2 	value3
    """

    # get the filter string needed to get the metric data from the queryset
    metric_filter = get_metric_filter(metric)

    data = {}

    # loop through the queryset and extract sample id, date of report and
    # metric
    for row in report_sample_queryset.values(
        "sample__sample_id", "report__date", metric_filter
    ):
        data.setdefault(row["sample__sample_id"], {})
        data[row["sample__sample_id"]][row["report__date"]] = row[metric_filter]

    # convert dict into a dataframe
    data_df = pd.DataFrame(data)

    return data_df


def get_metric_filter(metric: str) -> str:
    """ Get the metric filter needed to extract the metric data from the
    queryset

    Args:
        metric (str): Metric name

    Returns:
        str: String containing the metric in a Django format for querying the
        queryset
    """

    metric_filter = None

    # loop through the models and their fields to find in which model the
    # metric comes from
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if field.name == metric:
                metric_filter = f"{model.__name__.lower()}__{metric}"
                break

    assert metric_filter, f"{metric} does not exist in any model"

    # handle cases where there is an intermediary table between Report sample
    # and the table containing the metric field
    for ele in ["", "fastqc", "picard", "happy"]:
        if ele == "":
            metric_filter = metric_filter
        else:
            # add the intermediary table in the filter string
            metric_filter = f"{ele}__{metric_filter}"

        try:
            Report_Sample.objects.all().values(metric_filter)
        # the filter failed i.e. couldn't access the metric field using the
        # built filter from Report_sample
        except FieldError:
            continue
        else:
            return metric_filter

    return None


def plot_qc_data(plot_data: pd.DataFrame) -> go.Figure:
    """ Create plot given the form data

    Args:
        plot_data (pd.DataFrame): Pandas Dataframe containing the data to plot

    Returns:
        go.Figure: Figure to be displayed in the view
    """

    # initiate the figure
    fig = go.Figure()

    # for each column i.e. sample in our dataframe
    for col in plot_data.columns:
        # add a scatter plot with the date on the x-axis and the metric values
        # on the y-axis
        # hide the legend and name each point using the sample id
        fig.add_trace(
            Scatter(
                x=plot_data[col].index.values.tolist(), y=plot_data[col],
                text=col, showlegend=False
            )
        )

    return fig
