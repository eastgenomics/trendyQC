import json
from statistics import median
from typing import Dict

import pandas as pd
import plotly.graph_objs as go

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

    filter_dict = {}

    assays = data.get("assay_select", [])
    runs = data.get("run_select", [])
    sequencer_ids = data.get("sequencer_select", [])
    date_start = data.get("date_start")
    date_end = data.get("date_end")

    if assays:
        filter_dict["assay__in"] = assays

    if runs:
        filter_dict["report__project_name__in"] = runs

    if sequencer_ids:
        filter_dict["report__sequencer_id__in"] = sequencer_ids

    if date_start and date_end:
        filter_dict["report__date__range"] = (date_start, date_end)

    # combine all the data passed through the form to build the final queryset
    return Report_Sample.objects.filter(**filter_dict).prefetch_related()


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
        "sample__sample_id", "report__date", "report__project_name", metric_filter
    ):
        sample_id = row["sample__sample_id"]
        report_date = row["report__date"]
        report_project_name = row["report__project_name"]
        data.setdefault(sample_id, {})
        data[sample_id][f"{report_date}|{report_project_name}"] = row[metric_filter]

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

    metric_filter_dict = {}

    # loop through the models and their fields to find in which model the
    # metric comes from
    for model in apps.get_models():
        model_name = model.__name__.lower()

        for field in model._meta.get_fields():
            if field.name == metric:
                metric_filter_dict[model_name] = f"{model_name}__{metric}"

    assert metric_filter_dict, f"{metric} does not exist in any model"
    assert len(metric_filter_dict) == 1, (
        f"{metric} is present in '{', '.join(metric_filter_dict.keys())}'"
    )

    original_metric_filter = list(metric_filter_dict.values())[0]

    # handle cases where there is an intermediary table between Report sample
    # and the table containing the metric field:
    # The list represent the cases we want to test. "" is testing if the field
    # is in a table directly linked to report_sample. Fastqc, picard and happy
    # are the intermediate tables that could separate the field to
    # report_sample
    for intermediate_table in ["", "fastqc", "picard", "happy"]:
        if intermediate_table != "":
            # add the intermediary table in the filter string
            metric_filter = f"{intermediate_table}__{original_metric_filter}"
        else:
            metric_filter = original_metric_filter

        try:
            Report_Sample.objects.all().values(metric_filter)
        # the filter failed i.e. couldn't access the metric field using the
        # built filter from Report_sample
        except FieldError:
            continue
        else:
            return metric_filter

    return None


def format_data_for_plotly_js(plot_data: pd.DataFrame) -> go.Figure:
    """ Format the dataframe data for Plotly JS.

    Args:
        plot_data (pd.DataFrame): Pandas Dataframe containing the data to plot

    Returns:
        str: Serialized string of the boxplot data that needs to be plotted
        str: Serialized string of the trend data that needs to be plotted
    """

    # create the list of boxplots that will be displayed in the plot
    traces = []

    # formatting median trace
    median_trace = {
        "mode": "lines",
        "name": "trend",
        "line": {
            "dash": "dashdot",
            "width": 2
        }
    }
    median_trace.setdefault("x", [])
    median_trace.setdefault("y", [])

    plot_data = plot_data.sort_index()

    for index in plot_data.index:
        report_date, project_name = index.split("|")
        data_for_one_run = plot_data.loc[[index]].transpose().dropna().to_dict()
        # sort the data using the values for use in the Plotly computation
        sorted_data = {
            k: v for k, v in sorted(
                data_for_one_run[index].items(), key=lambda item: item[1]
            )
        }

        # setup each boxplot with the appropriate annotation and data points
        trace = {
            "x0": project_name,
            "y": list(sorted_data.values()),
            "name": report_date,
            "type": "box",
            "text": list(sorted_data.keys())
        }
        traces.append(trace)

        # add median of current boxplot for trend line
        data_median = median(list(sorted_data.values()))
        median_trace["x"].append(project_name)
        median_trace["y"].append(data_median)

    return json.dumps(traces), json.dumps(median_trace)
