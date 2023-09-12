import json
from statistics import median
from typing import Dict

import numpy as np
import pandas as pd

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
    data.setdefault("x_axis", [])
    data.setdefault("y_axis", [])

    for field, value in filter_recap.items():
        # I'm setting a list by default because I want the user to be able to
        # select multiple runs for example
        if field in [
            "assay_select", "run_select", "sequencer_select"
        ]:
            data["subset"].setdefault(field, [])

            if isinstance(value, list):
                data["subset"][field].extend(value)
            else:
                data["subset"][field].append(value)

        # this is kept separated from the above because you can input only one
        # date range
        if field in ["date_start", "date_end"]:
            data["subset"].setdefault(field, "")
            data["subset"][field] = value

        if field == "metrics_x":
            data["x_axis"].extend(value)

        if field == "metrics_y":
            data["y_axis"].extend(value)

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
    report_sample_queryset: QuerySet, metrics: list
) -> list:
    """ Get the data from the queryset in a Pandas dataframe. Find projects and
    samples for which the metric is not present or empty

    Args:
        report_sample_queryset (QuerySet): Report sample queryset
        metrics (list): Metrics that we want to plot on the Y-axis.

    Returns:
        list: List of Dataframes for every metric. Each dataframe has the
        following format:
            +-----------+-------+--------------+--------------+
            | sample_id | date  | project_name | metric_field |
            +-----------+-------+--------------+--------------+
            | sample1   | date1 | name1        | value1       |
            | sample2   | date1 | name1        | value2       |
            | sample3   | date1 | name2        | value3       |
            | sample4   | date2 | name3        | value4       |
            +-----------+-------+--------------+--------------+

        dict: Dict containing the projects for which no metric values were
        found.
        Example format:
        {
            metric1: [project1, project2, project3],
            metric2: [project1, project4]
        }
        dict: Dict containing the samples for which no metric values were
        found.
        Example format:
        {
            metric1: {
                project1: list_sample1,
                project2: list_sample2,
                project3: list_sample3
            },
            metric2: {
                project1: list_sample1,
                project4: list_sample4
            }
        }
    """

    list_df = []
    projects_no_metrics = {}
    samples_no_metric = {}

    for metric in metrics:
        # get the filter string needed to get the metric data from the queryset
        metric_filter = get_metric_filter(metric)
        metric_field = metric_filter.split("__")[-1]

        df = pd.DataFrame(
            report_sample_queryset.values(
                "sample__sample_id", "report__date",
                "report__project_name", metric_filter
            )
        )

        df.columns = ["sample_id", "date", "project_name", metric_field]

        for project_name in df["project_name"].unique():
            # get subdataframe for a single run
            data_one_run = df[df["project_name"] == project_name]

            # get the metric series and look for None and NaN
            none_in_metric_column = data_one_run[metric_field].apply(
                lambda x: x is None or np.isnan(x)
            )

            # if all values are None/NaN
            if all(none_in_metric_column):
                projects_no_metrics.setdefault(metric, []).append(project_name)

            # if one value is None/NaN
            elif any(none_in_metric_column):
                samples_no_metric.setdefault(metric, {})
                samples_no_metric[metric][project_name] = data_one_run.loc[
                    none_in_metric_column, "sample_id"
                ].values

        # filter out the None/NaN values in the metric column
        pd_data_no_none = df[
            ~df[metric_field].apply(lambda x: x is None or np.isnan(x))
        ]

        # convert dict into a dataframe
        list_df.append(pd_data_no_none)

    return list_df, projects_no_metrics, samples_no_metric


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


def format_data_for_plotly_js(plot_data: pd.DataFrame) -> tuple:
    """ Format the dataframe data for Plotly JS.

    Args:
        plot_data (pd.DataFrame): Pandas Dataframe containing the data to plot

    Example format:
        +-----------+-------+--------------+--------------+
        | sample_id | date  | project_name | metric_field |
        +-----------+-------+--------------+--------------+
        | sample1   | date1 | name1        | value1       |
        | sample2   | date1 | name1        | value2       |
        | sample3   | date1 | name2        | value3       |
        | sample4   | date2 | name3        | value4       |
        +-----------+-------+--------------+--------------+

    Returns:
        str: Serialized string of the boxplot data that needs to be plotted
        str: Serialized string of the trend data that needs to be plotted
    """

    date_coloring = {
        1: "FF7800",
        2: "000000",
        3: "969696",
        4: "c7962c",
        5: "ff1c4d",
        6: "ff65ff",
        7: "6600cc",
        8: "1c6dff",
        9: "6ddfff",
        10: "ffdf3c",
        11: "00cc99",
        12: "00a600",
    }

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

    metric_name = plot_data.columns[-1]

    for project_name in plot_data.sort_values("date")["project_name"].unique():
        data_one_run = plot_data[plot_data["project_name"] == project_name]

        report_date = data_one_run["date"].unique()[0]
        boxplot_color = date_coloring[report_date.month]

        sub_df = data_one_run.sort_values(
            metric_name
        )[["sample_id", metric_name]]

        # convert values to native python types for JSON serialisation
        data_values = [value.item() for value in sub_df[metric_name].values]

        # setup each boxplot with the appropriate annotation and data points
        trace = {
            "x0": project_name,
            "y": data_values,
            "name": str(report_date),
            "type": "box",
            "text": list(sub_df["sample_id"].values),
            "boxpoints": "suspectedoutliers",
            "marker": {
                "color": boxplot_color,
            }
        }
        traces.append(trace)

        # add median of current boxplot for trend line
        data_median = median(data_values)
        median_trace["x"].append(project_name)
        median_trace["y"].append(data_median)

    return json.dumps(traces), json.dumps(median_trace)
