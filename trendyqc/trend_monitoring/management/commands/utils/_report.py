import logging
import traceback

from ._dnanexus_utils import search_multiqc_reports, is_archived
from ._multiqc import MultiQC_report
from ._notifications import slack_notify

logger = logging.getLogger("basic")
storing_logger = logging.getLogger("storing")


def setup_report_object(project_id: list):
    """ Import all the multiqc reports contained in the list of projects ids
    given

    Args:
        project_id (str): Project id to look for MultiQC reports in
    """

    report_objects = search_multiqc_reports(project_id)

    if not report_objects:
        logger.warning(f"Couldn't find reports in {project_id}")

    for report_object in report_objects:
        report_id = report_object.id
        job_id = report_object.describe()["createdBy"]["job"]

        # check if the report is archived
        if is_archived(report_object):
            logger.warning(
                f"{project_id}:{report_id} is archived"
            )
            multiqc_report = MultiQC_report(
                multiqc_report_id=report_id,
                multiqc_project_id=project_id,
                multiqc_job_id=job_id
            )
        else:
            report_data = report_object.read()

            try:
                # this will fully setup the multiqc report to be ready for
                # import
                multiqc_report = MultiQC_report(
                    multiqc_report_id=report_id,
                    multiqc_project_id=project_id,
                    multiqc_job_id=job_id,
                    data=report_data
                )
            except Exception:
                msg = (
                    f"TrendyQC - Failed to setup {report_id}\n"

                    "```"
                    f"{traceback.format_exc()}"
                    "```"
                )
                slack_notify(msg)

        yield multiqc_report


def import_multiqc_report(report: MultiQC_report):
    """ Import the MultiQC report objects in the database

    Args:
        report (MultiQC_report): MultiQC report object

    Returns:
        MultiQC_report: Imported MultiQC_report object
    """

    if report.is_importable:
        try:
            report.import_instances()
        except Exception:
            msg = (
                f"TrendyQC - Failed to import {report.multiqc_json_id}\n"

                "```"
                f"{traceback.format_exc()}"
                "```"
            )
            slack_notify(msg)
            return False

        logger.info((
            f"Successfully imported: "
            f"{report.multiqc_json_id}"
        ))
        return True
    else:
        logger.debug(f"{report.multiqc_json_id} is not importable")
        return False
