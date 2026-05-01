import dash_mantine_components as dmc
from dash import dcc
from trend_monitoring.models import bam_qc, fastq_qc, vcf_qc
from trend_monitoring.models.metadata import Report_Sample

from trendyqc.settings import DISPLAY_DATA_JSON


def get_assay():
    assays = sorted(
        {
            assay
            for assay in Report_Sample.objects.all()
            .values_list("assay", flat=True)
            .distinct()
        }
    )
    return dmc.MultiSelect(
        data=assays,
        id="dropdown-assay",
        clearable=True,
        placeholder="Select assay(s)...",
    )


def get_metrics():
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
                    {"value": f"{tool[1]}|{field}", "label": field}
                    for field in fields
                ],
            }
        )

    return dmc.MultiSelect(
        placeholder="Select a metric...",
        id="dropdown-metric",
        searchable=True,
        clearable=True,
        nothingFoundMessage="Nothing found...",
        data=setup_metrics,
    )
