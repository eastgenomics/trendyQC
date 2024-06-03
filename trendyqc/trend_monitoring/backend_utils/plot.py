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
        if field in [
            "assay_select", "run_select", "sequencer_select"
        ]:
            # I'm setting a list by default because I want the user to be able
            # to select multiple runs for example
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
        model, form_metric = metric.split("|")

        # get the filter string needed to get the metric data from the queryset
        metric_filter = get_metric_filter(model, form_metric)

        df = pd.DataFrame(
            report_sample_queryset.values(
                "sample__sample_id", "report__date",
                "report__project_name", *metric_filter
            )
        )

        df.columns = ["sample_id", "date", "project_name", *metric_filter]

        for project_name in df["project_name"].unique():
            # get subdataframe for a single run
            data_one_run = df[df["project_name"] == project_name]

            # get the metric df
            metric_df = data_one_run[metric_filter]

            for series_name, series in metric_df.items():
                # if all values are None/NaN
                if series.isnull().all():
                    projects_no_metrics.setdefault(metric, set()).add(project_name)

                # if one value is None/NaN
                elif series.isnull().any():
                    samples_no_metric.setdefault(metric, {})

                    for values in data_one_run.loc[series.isna()].values:
                        samples_no_metric[metric].setdefault(project_name, set())
                        # extract sample name
                        data = [value for value in values][0]
                        samples_no_metric[metric][project_name].add(data)

        # filter out the None/NaN values in the metric column(s)
        pd_data_no_none = df[df[metric_filter].notna().any(axis=1)]

        list_df.append(pd_data_no_none)

    return list_df, projects_no_metrics, samples_no_metric


def get_metric_filter(form_model: str, form_metric: str) -> str:
    """ Get the metric filter needed to extract the metric data from the
    queryset

    Args:
        form_model (str): Model name from the form
        form_metric (str): Metric name from the form

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
            if (field.name == form_metric) and (model_name == form_model):
                metric_filter_dict[model_name] = f"{model_name}__{field.name}"

    assert metric_filter_dict, f"{form_metric} does not exist in any model"

    original_metric_filter = list(metric_filter_dict.values())[0]

    # for fastqc and picard base distribution, build the metric filter directly
    # to take into account the lanes
    if "read_data" in original_metric_filter:
        metric_filter = [
            f"fastqc__{lane_read}__{original_metric_filter.split('__')[-1]}"
            for lane_read in [
                "read_data_1st_lane_R1", "read_data_1st_lane_R2",
                "read_data_2nd_lane_R1", "read_data_2nd_lane_R2"
            ]
        ]
        metric_filter.insert(0, "fastqc__read_data_2nd_lane_R1__lane")
        metric_filter.insert(0, "fastqc__read_data_1st_lane_R1__lane")
        return metric_filter

    elif "base_distribution" in original_metric_filter:
        metric_filter = [
            f"picard__{lane_read}__{original_metric_filter.split('__')[-1]}"
            for lane_read in [
                "base_distribution_by_cycle_metrics_1st_lane_R1",
                "base_distribution_by_cycle_metrics_1st_lane_R2",
                "base_distribution_by_cycle_metrics_2nd_lane_R1",
                "base_distribution_by_cycle_metrics_2nd_lane_R2"
            ]
        ]
        metric_filter.insert(
            0, "picard__base_distribution_by_cycle_metrics_2nd_lane_R1__lane"
        )
        metric_filter.insert(
            0, "picard__base_distribution_by_cycle_metrics_1st_lane_R1__lane"
        )
        return metric_filter

    # handle cases where there is an intermediary table between Report sample
    # and the table containing the metric field:
    # The list represent the cases we want to test. "" is testing if the field
    # is in a table directly linked to report_sample. Fastqc, picard and happy
    # are the intermediate tables that could separate the field to
    # report_sample
    for intermediate_table in ["", "picard", "happy"]:
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
            return [metric_filter]

    return None


def format_data_for_plotly_js(plot_data: pd.DataFrame) -> tuple:
    """ Format the dataframe data for Plotly JS.

    Args:
        plot_data (pd.DataFrame): Pandas Dataframe containing the data to plot

    Example format:
    For tools with no lane data, the dataframe should only be 4 columns:
        +-----------+-------+--------------+--------------+
        | sample_id | date  | project_name | metric_field |
        +-----------+-------+--------------+--------------+
        | sample1   | date1 | name1        | value1       |
        | sample2   | date1 | name1        | value2       |
        | sample3   | date1 | name2        | value3       |
        | sample4   | date2 | name3        | value4       |
        +-----------+-------+--------------+--------------+

    For tools with lane data, the dataframe should be 8 columns:
        +-----------+-------+--------------+------------+-------------+--------------------+--------------------+--------------------+--------------------+
        | sample_id | date  | project_name | first lane | second lane | metric_field_L1_R1 | metric_field_L1_R2 | metric_field_L2_R1 | metric_field_L2_R2 |
        +-----------+-------+--------------+------------+-------------+--------------------+--------------------+--------------------+--------------------+
        | sample1   | date1 | name1        | value1     | value1      | value1             | value1             | value1             | value1             |
        | sample2   | date1 | name1        | value2     | value2      | value2             | value2             | value2             | value2             |
        | sample3   | date1 | name2        | value3     | value3      | value3             | value3             | value3             | value3             |
        | sample4   | date2 | name3        | value4     | value4      | value4             | value4             | value4             | value4             |
        +-----------+-------+--------------+------------+-------------+--------------------+--------------------+--------------------+--------------------+

    Returns:
        list: List of lists of the traces that need to be plotted
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

    # Bool to indicate whether legend needs to be displayed
    shown_legend = True

    # get the column names for the metrics: either 6 columns when there is data
    # for lanes or 1 column if the data is not separated by lane
    metrics = plot_data.columns[3:]

    combined_traces = []
    first_lane_traces = []
    second_lane_traces = []
    default_traces = []

    # for each project name, gather the necessary data to create the individual
    # boxplots
    for project_name in plot_data.sort_values("date")["project_name"].unique():
        # get sub df with for the project name
        data_one_run = plot_data[plot_data["project_name"] == project_name]
        report_date = data_one_run["date"].unique()[0]
        boxplot_color = date_coloring[report_date.month]

        if len(metrics) > 1:
            first_lane_column = data_one_run.columns[3]
            second_lane_column = data_one_run.columns[4]

            first_lane = list(set(data_one_run[first_lane_column].values))[0]
            second_lane = list(set(data_one_run[second_lane_column].values))[0]

            data_one_run["Default data"] = data_one_run.apply(
                calculate_mean_across_columns, axis=1, args=(range(5, 9))
            )
            data_one_run[first_lane] = data_one_run.apply(
                calculate_mean_across_columns, axis=1, args=([5, 6])
            )
            data_one_run[second_lane] = data_one_run.apply(
                calculate_mean_across_columns, axis=1, args=([7, 8])
            )

            default_data_trace = create_trace(
                data_one_run, "Default data",
                project_name=project_name,
                name="Combined",
                boxplot_color=boxplot_color,
                showlegend=shown_legend
            )

            if first_lane:
                first_lane_trace = create_trace(
                    data_one_run, first_lane,
                    project_name=project_name,
                    name="First lane",
                    visible="legendonly",
                    hovertext=first_lane,
                    lane=first_lane,
                    boxplot_color=boxplot_color,
                    showlegend=shown_legend
                )
                first_lane_traces.append(first_lane_trace)

            if second_lane:
                second_data_trace = create_trace(
                    data_one_run, second_lane,
                    project_name=project_name,
                    name="Second lane",
                    visible="legendonly",
                    lane=second_lane,
                    hovertext=second_lane,
                    boxplot_color=boxplot_color,
                    showlegend=shown_legend
                )
                second_lane_traces.append(second_data_trace)

            shown_legend = False
            combined_traces.append(default_data_trace)

        else:
            metric_name = data_one_run.columns[-1]

            default_data_trace = create_trace(
                data_one_run, metric_name,
                project_name=project_name,
                name=str(report_date),
                boxplot_color=boxplot_color,
                showlegend=False
            )

            default_traces.append(default_data_trace)

    if default_traces:
        plot_data = {"plot": json.dumps(default_traces)}
    else:
        plot_data = {"plot": json.dumps(combined_traces)}

    return {
        **plot_data,
        **{
            "first_lane": json.dumps(first_lane_traces),
            "second_lane": json.dumps(second_lane_traces)
        }
    }


def create_trace(data, data_column, **kwargs):
    """ Setup the trace according to given data

    Args:
        data (pd.DataFrame): Dataframe containing the data for that boxplot
        data_column (str): Column name in which values are stored

    Returns:
        dict: Dict containing the data needed for Plotly
    """

    sub_df = data.sort_values(data_column)[["sample_id", data_column]]

    # convert values to native python types for JSON serialisation
    data_values = [
        value.item() if isinstance(value, np.float64) else value
        for value in sub_df[data_column].values
    ]

    if kwargs.get("lane", None):
        legend_group = f"{kwargs['name']} | {kwargs.get('lane')}"
    else:
        legend_group = kwargs['name']

    # setup each boxplot with the appropriate annotation and data points
    trace = {
        "x0": kwargs["project_name"],
        "y": data_values,
        "name": kwargs["name"],
        "type": "box",
        "text": list(sub_df["sample_id"].values),
        "boxpoints": "suspectedoutliers",
        "marker": {
            "color": kwargs["boxplot_color"],
        },
        "legendgroup": legend_group,
        "visible": kwargs.get("visible", True),
        "showlegend": kwargs["showlegend"]
    }

    return trace


def calculate_mean_across_columns(row, *columns):
    """ Calculate the mean for a selection of columns

    Args:
        row (pd.Series): Series containing the data to manipulate

    Returns:
        float: Mean of the values for the select columns
    """

    denominator = 0
    value = 0

    for column in columns:
        if row.iloc[column]:
            value += row[column]
            denominator += 1

    if denominator:
        return value / denominator
    else:
        return None
