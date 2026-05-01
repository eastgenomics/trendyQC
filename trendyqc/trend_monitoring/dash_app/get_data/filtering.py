import calendar
import datetime
import json
import re
from copy import deepcopy
from typing import Dict

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.conf import settings
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db.models.query import QuerySet
from trend_monitoring.models.metadata import Report_Sample


def get_subset_queryset(data: Dict) -> QuerySet:
    """Get all the Report_sample objects that belong to the subset that the
    user inputted

    Args:
        data (dict): Dict of data from the subset part of the form

    Returns:
        Django Queryset: Queryset containing all the Report sample objects
        after filtering using the data inputted by the user
    """

    filter_dict = {}

    assays = data.get("assay", [])
    runs = data.get("run", [])
    sequencer_ids = data.get("sequencer", [])
    date_start = data.get("date_start")
    date_end = data.get("date_end")
    days_back = data.get("days_back")

    if assays:
        filter_dict["assay__in"] = assays

    if runs:
        filter_dict["report__project_name__in"] = runs

    if sequencer_ids:
        filter_dict["report__sequencer_id__in"] = sequencer_ids

    if days_back:
        # calculate the date range at the filtering level in order to keep the
        # days back option dynamic i.e. if a filter is saved with 30 days back
        # and is used at the beginning of the month or at the end of the month,
        # the results will be different
        today = datetime.date.today()
        filter_dict["report__date__range"] = (
            today + relativedelta(days=-int(days_back[0])),
            today,
        )
    else:
        if date_start and date_end:
            if isinstance(date_start, list):
                date_start = date_start[0]

            if isinstance(date_end, list):
                date_end = date_end[0]

            date_start = datetime.datetime.strptime(date_start, "%Y-%m-%d")
            date_end = datetime.datetime.strptime(date_end, "%Y-%m-%d")

            filter_dict["report__date__range"] = (date_start, date_end)

    # combine all the data passed through the form to build the final queryset
    return Report_Sample.objects.filter(**filter_dict).prefetch_related()


def get_data_for_plotting(
    report_sample_queryset: QuerySet, metrics: list
) -> tuple:
    """Get the data from the queryset in a Pandas dataframe. Find projects and
    samples for which the metric is not present or empty

    Args:
        report_sample_queryset (QuerySet): Report sample queryset
        metrics (list): Metrics that we want to plot on the Y-axis.

    Returns:
        tuple: Tuple of Dataframes for every metric. Each dataframe has the
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

    projects_no_metrics = {}
    samples_no_metric = {}

    metric_filters = [
        metric_filter
        for metric in metrics
        for metric_filter in get_metric_filter(*metric.split("|"))
    ]

    df = pd.DataFrame(
        report_sample_queryset.values(
            "sample__sample_id",
            "report__date",
            "report__project_name",
            "assay",
            "report__sequencer_id",
            *metric_filters,
        )
    )

    df.columns = [
        "sample_id",
        "date",
        "project_name",
        "assay",
        "sequencer_id",
        *metric_filters,
    ]

    for metric in metrics:
        for project_name in df["project_name"].unique():
            # get subdataframe for a single run
            data_one_run = df[df["project_name"] == project_name]

            # get the metric df
            metric_df = data_one_run[metric_filters]

            for series_name, series in metric_df.items():
                # if all values are None/NaN
                if series.isnull().all():
                    projects_no_metrics.setdefault(metric, set()).add(
                        project_name
                    )

                # if one value is None/NaN
                elif series.isnull().any():
                    samples_no_metric.setdefault(metric, {})

                    for values in data_one_run.loc[series.isna()].values:
                        samples_no_metric[metric].setdefault(
                            project_name, set()
                        )
                        # extract sample name
                        data = [value for value in values][0]
                        samples_no_metric[metric][project_name].add(data)

    # filter out the None/NaN values in the metric column(s)
    pd_data_no_none = df[df[metric_filters].notna().any(axis=1)]

    return (
        pd_data_no_none.sort_values(by=["project_name"]),
        projects_no_metrics,
        samples_no_metric,
    )


def get_metric_filter(form_model: str, form_metric: str) -> str:
    """Get the metric filter needed to extract the metric data from the
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

        if model_name == form_model.lower():
            for field in model._meta.get_fields():
                if field.name.lower() == form_metric:
                    metric_filter_dict[model_name] = (
                        f"{model_name}__{field.name}"
                    )

    assert metric_filter_dict, f"{form_metric} does not exist in any model"

    original_metric_filter = list(metric_filter_dict.values())[0]

    # for fastqc and picard base distribution, build the metric filter directly
    # to take into account the lanes
    if "read_data" in original_metric_filter:
        metric_filter = [
            f"fastqc__{lane_read}__{original_metric_filter.split('__')[-1]}"
            for lane_read in [
                "read_data_1st_lane_R1",
                "read_data_1st_lane_R2",
                "read_data_2nd_lane_R1",
                "read_data_2nd_lane_R2",
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
                "base_distribution_by_cycle_metrics_2nd_lane_R2",
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
