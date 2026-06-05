import dash_mantine_components as dmc

from trend_monitoring.models import bam_qc, fastq_qc, vcf_qc
from trend_monitoring.models.metadata import Report, Report_Sample
from trend_monitoring.models.filters import Filter
from trend_monitoring.models.annotations import PlotAnnotation
from trend_monitoring.dash_app.setup_dash_elements.utils import (
    build_filter_text,
)

from trendyqc.settings import DISPLAY_DATA_JSON


def get_assay(dropdown_id):
    assays = sorted(
        {
            assay
            for assay in Report_Sample.objects.all()
            .values_list("assay", flat=True)
            .distinct()
        }
    )
    return [
        dmc.MultiSelect(
            data=assays,
            id=dropdown_id,
            clearable=True,
            placeholder="Select assay(s)...",
        )
    ]


def get_projects(projects=None):
    if not projects:
        projects = sorted(
            {
                f"{project} - {file_id}"
                for project, file_id in Report.objects.all()
                .values_list("project_name", "dnanexus_file_id")
                .distinct()
            }
        )

    return [
        dmc.Autocomplete(
            placeholder="Select the report to view",
            id="dropdown-project",
            data=projects,
        )
    ]


def get_metrics(dropdown_id, placeholder="Select a metric..."):
    plotable_metrics = {}
    module_content = bam_qc.__dict__ | fastq_qc.__dict__ | vcf_qc.__dict__

    module_dict = dict(
        [
            (name, cls)
            for name, cls in module_content.items()
            if isinstance(cls, type)
        ]
    )

    for model_name, model in module_dict.items():
        if model_name in DISPLAY_DATA_JSON:
            plotable_metrics[DISPLAY_DATA_JSON[model_name], model_name] = (
                sorted(
                    [
                        field.name
                        for field in model._meta.fields
                        if field.name != "id"  # skip the id field
                    ]
                )
            )

    plotable_metrics = dict(sorted(plotable_metrics.items()))

    setup_metrics = []

    for tool, fields in plotable_metrics.items():
        setup_metrics.append(
            {
                "group": tool[0],
                "items": [
                    {
                        "value": f"{tool[1]}|{field}",
                        "label": f"{tool[1]} | {field}",
                    }
                    for field in fields
                ],
            }
        )

    return [
        dmc.MultiSelect(
            placeholder=placeholder,
            id=dropdown_id,
            searchable=True,
            clearable=True,
            nothingFoundMessage="Nothing found...",
            data=setup_metrics,
        )
    ]


def get_date_picker():
    presets = {
        "Past month": "-30",
        "Last 3 months": "-90",
        "Last 6 months": "-180",
        "Past year": "-365",
    }

    return [
        dmc.Stack(
            children=[
                dmc.Group(
                    children=[
                        dmc.ChipGroup(
                            [
                                dmc.Chip(label, value=value)
                                for label, value in presets.items()
                            ],
                            multiple=False,
                            value="-180",
                            id="radio-date",
                        ),
                    ],
                    justify="center",
                ),
                dmc.DatePickerInput(
                    id="date-picker",
                    type="range",
                    label="",
                    placeholder="Select date range",
                    clearable=True,
                ),
            ],
            justify="center",
            gap="md",
        )
    ]


def get_filter_table():
    filters = Filter.objects.all()

    if not filters:
        rows = dmc.TableTr(
            [
                dmc.TableTd("No filters in the database"),
                dmc.TableTd(),
                dmc.TableTd(),
                dmc.TableTd(),
            ]
        )
    else:
        rows = [
            dmc.TableTr(
                [
                    dmc.TableTd(f.name),
                    dmc.TableTd(build_filter_text(f.content)),
                    dmc.TableTd(
                        dmc.Button(
                            "Use",
                            id={"type": "use-filter-btn", "index": f.id},
                            size="xs",
                        )
                    ),
                    dmc.TableTd(
                        dmc.Button(
                            "Delete",
                            id={"type": "delete-filter-btn", "index": f.id},
                            size="xs",
                            color="red",
                        )
                    ),
                ]
            )
            for f in filters
        ]

    return [
        dmc.TableScrollContainer(
            dmc.Table(
                [
                    dmc.TableThead(
                        dmc.TableTr(
                            [
                                dmc.TableTh("Name"),
                                dmc.TableTh("Content"),
                                dmc.TableTh(""),
                                dmc.TableTh(""),
                            ]
                        )
                    ),
                    dmc.TableTbody(rows),
                ]
            ),
            maxHeight=300,
            minWidth=600,
            id="filter-table",
        ),
    ]


def get_annotation_table():
    annotations = PlotAnnotation.objects.all()

    if not annotations:
        rows = dmc.TableTr(
            [
                dmc.TableTd("No annotations in the database"),
                dmc.TableTd(),
                dmc.TableTd(),
                dmc.TableTd(),
            ]
        )
    else:
        rows = [
            dmc.TableTr(
                [
                    dmc.TableTd(annotation.date),
                    dmc.TableTd(annotation.label),
                    dmc.TableTd(
                        dmc.Button(
                            "Delete",
                            id={
                                "type": "delete-annotation-btn",
                                "index": annotation.id,
                            },
                            size="xs",
                            color="red",
                        )
                    ),
                ]
            )
            for annotation in annotations
        ]

    return [
        dmc.TableScrollContainer(
            dmc.Table(
                [
                    dmc.TableThead(
                        dmc.TableTr(
                            [
                                dmc.TableTh("Date"),
                                dmc.TableTh("Label"),
                                dmc.TableTh(""),
                            ]
                        )
                    ),
                    dmc.TableTbody(rows),
                ]
            ),
            maxHeight=300,
            minWidth=600,
            id="annotation-table",
        ),
    ]


def get_missing_data_accordions(
    projects_no_metrics: dict, samples_no_metric: dict
):
    if not projects_no_metrics and not samples_no_metric:
        return []

    result = []

    # accordion for projects with no metrics
    if projects_no_metrics:
        items = [
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        f"{metric} ({len(projects)} projects)",
                    ),
                    dmc.AccordionPanel(
                        dmc.Table(
                            [
                                dmc.TableThead(
                                    dmc.TableTr([dmc.TableTh("Project")])
                                ),
                                dmc.TableTbody(
                                    [
                                        dmc.TableTr([dmc.TableTd(project)])
                                        for project in sorted(projects)
                                    ]
                                ),
                            ]
                        )
                    ),
                ],
                value=metric,
            )
            for metric, projects in sorted(projects_no_metrics.items())
        ]

        result.append(
            dmc.Stack(
                [
                    dmc.Text("Projects with no data", fw=500, c="red"),
                    dmc.Accordion(items),
                ]
            )
        )

    # accordion for projects with missing samples
    if samples_no_metric:
        items = [
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        f"{metric} ({len(projects)} projects)",
                    ),
                    dmc.AccordionPanel(
                        dmc.Table(
                            [
                                dmc.TableThead(
                                    dmc.TableTr(
                                        [
                                            dmc.TableTh("Project"),
                                            dmc.TableTh("Samples"),
                                        ]
                                    )
                                ),
                                dmc.TableTbody(
                                    [
                                        dmc.TableTr(
                                            [
                                                dmc.TableTd(project),
                                                dmc.TableTd(
                                                    ", ".join(sorted(samples))
                                                ),
                                            ]
                                        )
                                        for project, samples in sorted(
                                            projects.items()
                                        )
                                    ]
                                ),
                            ]
                        )
                    ),
                ],
                value=metric,
            )
            for metric, projects in sorted(samples_no_metric.items())
        ]

        result.append(
            dmc.Stack(
                [
                    dmc.Text(
                        "Projects with missing samples", fw=500, c="orange"
                    ),
                    dmc.Accordion(items),
                ]
            )
        )

    return result
