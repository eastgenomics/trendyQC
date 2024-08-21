import calendar
import datetime
import json
import re
import random
from typing import Dict

from dateutil.relativedelta import relativedelta
import pandas as pd

from django.apps import apps
from django.core.exceptions import FieldError
from django.db.models.query import QuerySet
from trend_monitoring.models.metadata import Report_Sample


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
        filter_dict["report__date__range"] = ((
            today + relativedelta(days=-int(days_back[0])),
            today
        ))
    else:
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
                "sample__sample_id", "report__date", "report__project_name",
                "assay", "report__sequencer_id", *metric_filter
            )
        )

        df.columns = [
            "sample_id", "date", "project_name", "assay", "sequencer_id",
            *metric_filter
        ]

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

        if model_name == form_model:
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
        +-----------+-------+--------------+--------+--------------+------------+-------------+--------------------+--------------------+--------------------+--------------------+
        | sample_id | date  | project_name | assay  | sequencer_id | first lane | second lane | metric_field_L1_R1 | metric_field_L1_R2 | metric_field_L2_R1 | metric_field_L2_R2 |
        +-----------+-------+--------------+--------+--------------+------------+-------------+--------------------+--------------------+--------------------+--------------------+
        | sample1   | date1 | name1        | assay1 | sequencer1   | value1     | value1      | value1             | value1             | value1             | value1             |
        | sample2   | date1 | name1        | assay2 | sequencer2   | value2     | value2      | value2             | value2             | value2             | value2             |
        | sample3   | date1 | name2        | assay3 | sequencer3   | value3     | value3      | value3             | value3             | value3             | value3             |
        | sample4   | date2 | name3        | assay4 | sequencer4   | value4     | value4      | value4             | value4             | value4             | value4             |
        +-----------+-------+--------------+--------+--------------+------------+-------------+--------------------+--------------------+--------------------+--------------------+

    Returns:
        list: List of lists of the traces that need to be plotted
    """

    colors = [
        "#FF0000",   # red
        "#FFBABA",   # pinkish
        "#A04D4D",   # brown
        "#B30000",   # maroon
        "#FF7800",   # orange
        "#B69300",   # ugly yellow
        "#7D8040",   # olive
        "#00FF00",   # bright green
        "#000000",   # black
        "#969696",   # grey
        "#c7962c",   # goldish
        "#ff65ff",   # fushia
        "#6600cc",   # purple
        "#1c6dff",   # blue
        "#6ddfff",   # light blue
        "#ffdf3c",  # yellow
        "#00cc99",  # turquoise
        "#00a600",  # green
    ]

    # args dict for configuring the traces for combined, first, second lane
    args = {
        "Combined": {
            "lane": None,
            "visible": True,
            "boxplot_color": None,
            "boxplot_line_color": None,
        },
        "First lane": {
            "lane": None,
            "visible": "legendonly",
            "boxplot_color": "AED6F1",
            "boxplot_line_color": "000000",
            "name": "First lane",
            "offsetgroup": "First lane",
            "legendgroup": "First lane",
        },
        "Second lane": {
            "lane": None,
            "visible": "legendonly",
            "boxplot_color": "F1948A",
            "boxplot_line_color": "000000",
            "name": "Second lane",
            "offsetgroup": "Second lane",
            "legendgroup": "Second lane",
        }
    }

    # Bool to indicate whether legend needs to be displayed
    shown_legend = True

    # get the column names for the metrics: either 6 columns when there is data
    # for lanes or 1 column if the data is not separated by lane
    metrics = plot_data.columns[5:]

    traces = []

    # get groups of assay and sequencer id
    groups = build_groups(plot_data)
    seen_groups = []

    group_colors = {}

    # too many groups are possible
    if len(colors) < len(groups):
        return f"Not enough colors are possible for the groups: {groups}"

    # assign colors to groups
    for i, group in enumerate(groups):
        random_color = random.choice(colors)
        group_colors[group] = random_color
        colors.remove(random_color)

    # first second lane flag to fix duplication in the legend
    seen_first_lane = False
    seen_second_lane = False

    # for each project name, gather the necessary data to create the individual
    # boxplots
    for project_name in plot_data.sort_values("date")["project_name"].unique():
        # get sub df with for the project name
        data_one_run = plot_data[
            plot_data["project_name"] == project_name
        ].copy()

        assay_name = data_one_run['assay'].unique()[0]
        sequencer_id = data_one_run['sequencer_id'].unique()[0]
        legend_name = f"{assay_name} - {sequencer_id}"

        if legend_name not in seen_groups:
            seen_groups.append(legend_name)
            shown_legend = True
        else:
            shown_legend = False

        if len(metrics) > 1:
            # get the lane columns
            first_lane_column = data_one_run.columns[5]
            second_lane_column = data_one_run.columns[6]
            # get the lane names
            first_lane = list(set(data_one_run[first_lane_column].values))[0]
            second_lane = list(set(data_one_run[second_lane_column].values))[0]

            args["Combined"]["columns"] = plot_data.columns[7:]
            args["First lane"]["columns"] = plot_data.columns[7:9]
            args["Second lane"]["columns"] = plot_data.columns[9:11]

            args["Combined"]["boxplot_color"] = group_colors[legend_name]
            args["Combined"]["boxplot_line_color"] = group_colors[legend_name]
            args["Combined"]["name"] = legend_name
            args["Combined"]["offsetgroup"] = legend_name
            args["Combined"]["legendgroup"] = legend_name

            args["First lane"]["lane"] = first_lane
            args["Second lane"]["lane"] = second_lane

            for name, sub_dict in args.items():
                # calculate mean across appropriate columns
                data_one_run[name] = data_one_run.loc[:, sub_dict["columns"]].mean(axis=1)

                if name == "First lane" and seen_first_lane:
                    shown_legend = False

                if name == "Second lane" and seen_second_lane:
                    shown_legend = False

                trace_args = {
                    "data": data_one_run,
                    "data_column": name,
                    "project_name": project_name,
                    "name": sub_dict["name"],
                    "visible": sub_dict["visible"],
                    "lane": sub_dict["lane"],
                    "boxplot_color": sub_dict["boxplot_color"],
                    "boxplot_line_color": sub_dict["boxplot_line_color"],
                    "offsetgroup": sub_dict["offsetgroup"],
                    "legendgroup": sub_dict["legendgroup"],
                    "showlegend": shown_legend
                }

                if name == "First lane":
                    seen_first_lane = True

                if name == "Second lane":
                    seen_second_lane = True

                traces.append(create_trace(**trace_args))

            is_grouped = True

        else:
            metric_name = data_one_run.columns[-1]

            legend_args = {
                "legendgroup": legend_name,
                "name": legend_name,
            }

            trace_args = {
                **{
                    "data": data_one_run,
                    "data_column": metric_name,
                    "project_name": project_name,
                    "lane": None,
                    "offsetgroup": "",
                    "boxplot_color": group_colors[legend_name],
                    "boxplot_line_color": group_colors[legend_name],
                    "showlegend": shown_legend
                },
                **legend_args
            }

            traces.append(create_trace(**trace_args))
            is_grouped = False

    return json.dumps(traces), json.dumps(is_grouped)


def create_trace(**kwargs):
    """ Setup the trace according to given data

    Args:
        data (pd.DataFrame): Dataframe containing the data for that boxplot
        data_column (str): Column name in which values are stored

    Returns:
        dict: Dict containing the data needed for Plotly
    """

    sub_df = kwargs["data"].sort_values(
        kwargs["data_column"]
    )[["sample_id", kwargs["data_column"]]]

    # convert values to native python types for JSON serialisation
    data_values = [
        float(value) for value in sub_df[kwargs["data_column"]].values
    ]

    date = get_date_from_project_name(kwargs["project_name"])

    text_data = []

    # set text displayed when hovering outliers
    for ele in list(sub_df["sample_id"].values):
        if kwargs["lane"]:
            text_data.append(f"{ele} - {kwargs['lane']}")
        else:
            text_data.append(ele)

    # setup each boxplot with the appropriate annotation and data points
    trace = {
        "x": [
            [date]*len(data_values), [kwargs["project_name"]]*len(data_values)
        ],
        "y": data_values,
        "name": kwargs["name"],
        "type": "box",
        # text associated with every sample value
        "text": text_data,
        # type of box to display
        "boxpoints": "suspectedoutliers",
        # coloring of outliers
        "marker": {
            "color": kwargs["boxplot_color"],
        },
        # coloring of edges of box
        "line": {
            "color": kwargs.get("boxplot_line_color", "#444")
        },
        # +80 adds transparency
        "fillcolor": kwargs["boxplot_color"]+"80",
        # grouping of boxes
        "offsetgroup": kwargs["offsetgroup"],
        # name of group in the legend
        "legendgroup": kwargs.get("legendgroup", ""),
        "legend": kwargs.get("legendgroup", ""),
        "visible": kwargs.get("visible", True),
        "showlegend": kwargs["showlegend"]
    }

    return trace


def get_date_from_project_name(project_name):
    """ Get a date formatted for reading i.e. 2405 -> May 2024

    Args:
        project_name (str): Project name in which to look for the date in

    Returns:
        str: String containing the abbreviated name of the month and the year
    """

    # regex to match most dates in the following format YYMMDD
    matches = re.findall(r"[0-9]{2}[0-1][0-9][0-3][0-9]", project_name)

    assert matches, f"Couldn't find a date in {project_name}"

    # if multiple date matches are found, additional filtering is required
    if len(matches) > 1:
        check = []

        # extract individual elements and see if it's actually a date before
        # throwing an error
        for match in matches:
            try:
                datetime.datetime.strptime(match, "%y%m%d")
            except ValueError:
                check.append(False)
            else:
                check.append(True)

        assert not all(check), (
            f"Multiple date looking objects have been found in {project_name}"
        )

    month_abbr = calendar.month_abbr[int(matches[0][2:4])]

    return f"{month_abbr}. 20{matches[0][0:2]}"


def build_groups(df):
    """ Get the groups of assay and sequencer id combinaisons for the grouping
    of traces

    Args:
        df (pd.DataFrame): Dataframe in which to extract the groups

    Returns:
        list: List of assay and sequencer id present in the dataframe
    """

    # group the rows by the assay and sequencer id columns
    # count number of occurences of these combos
    # add the first column back
    # name the count column
    df = df \
        .groupby(['assay', 'sequencer_id']) \
        .size() \
        .reset_index() \
        .rename(columns={0: 'count'})

    # get the list of combos and format it for displaying in legend
    return list(
        df[df["count"] != 0].agg(
            lambda x: f"{x['assay']} - {x['sequencer_id']}", axis=1
        ).values
    )
