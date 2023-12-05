import logging

from ._dnanexus_utils import (
    search_multiqc_reports, is_archived
)
from ._multiqc import MultiQC_report

logger = logging.getLogger("basic")
storing_logger = logging.getLogger("storing")


def import_multiqc_reports(project_ids, dry_run=False):
    archived_reports = []

    for p_id in project_ids:
        report_objects = search_multiqc_reports(p_id)

        for report_object in report_objects:
            if is_archived(report_object):
                archived_reports.append(report_object.id)
                continue

            multiqc_report = MultiQC_report(report_object)

            if multiqc_report.is_importable:
                if not dry_run:
                    multiqc_report.import_instances()
                    logger.info((
                        f"Successfully imported: "
                        f"{multiqc_report.multiqc_json_id}"
                    ))

    if archived_reports:
        storing_logger.warning(
            f"{len(archived_reports)} archived report(s): "
            f"{','.join(archived_reports)}"
        )
