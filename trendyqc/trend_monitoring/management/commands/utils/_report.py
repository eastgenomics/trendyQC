import logging
import traceback

from django.apps import apps

from ._check import already_in_db
from ._dnanexus_utils import search_multiqc_reports, is_archived
from ._multiqc import MultiQC_report
from ._notifications import slack_notify

logger = logging.getLogger("basic")
storing_logger = logging.getLogger("storing")


def setup_report_objects(project_ids: list):
    """ Import all the multiqc reports contained in the list of projects ids
    given

    Args:
        project_ids (list): List of project ids to look for MultiQC reports in
    """

    archived_reports = []
    reports = []

    # get the report model object from all models
    report_model = {
        model.__name__.lower(): model for model in apps.get_models()
    }["report"]

    for p_id in project_ids:
        report_objects = search_multiqc_reports(p_id)

        for report_object in report_objects:
            report_id = report_object.id
            report_kwargs = {
                "dnanexus_file_id": report_id, "project_id": p_id
            }

            # check if the report is already in the database
            if already_in_db(report_model, **report_kwargs):
                continue

            # check if the report is archived
            if is_archived(report_object):
                archived_reports.append(report_id)
                continue

            job_id = report_object.describe()["createdBy"]["job"]
            report_data = report_object.read()

            try:
                # this will fully setup the multiqc report to be ready for import
                multiqc_report = MultiQC_report(
                    report_id, p_id, job_id, report_data
                )
            except Exception:
                msg = (
                    f"TrendyQC - Failed to setup {report_id}\n"

                    "```"
                    f"{traceback.format_exc()}"
                    "```"
                )
                slack_notify(msg)

            reports.append(multiqc_report)

    if archived_reports:
        storing_logger.warning(
            f"{len(archived_reports)} archived report(s): "
            f"{','.join(archived_reports)}"
        )

    return reports


def import_multiqc_reports(reports: list):
    """ Import the MultiQC report objects in the database

    Args:
        reports (list): List of MultiQC report objects

    Returns:
        list: List of imported reports
    """

    imported_reports = []

    for report in reports:
        if report.is_importable:
            try:
                report.import_instances()
            except Exception:
                msg = (
                    "TrendyQC - Failed to import "
                    f"{report.multiqc_json_id}\n"

                    "```"
                    f"{traceback.format_exc()}"
                    "```"
                )
                slack_notify(msg)

            imported_reports.append(report)
            logger.info((
                f"Successfully imported: "
                f"{report.multiqc_json_id}"
            ))

    return imported_reports
