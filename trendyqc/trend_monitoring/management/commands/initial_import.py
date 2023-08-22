import logging
import sys

import regex

from django.core.management.base import BaseCommand

from ._dnanexus_utils import (
    login_to_dnanexus, search_multiqc_reports, get_all_002_projects,
    is_archived
)
from ._multiqc import MultiQC_report

logger = logging.getLogger()
storing_logger = logging.getLogger("storing")


class Command(BaseCommand):
    help = "Initial import of the MultiQC reports"

    def add_arguments(self, parser):
        parser.add_argument(
            "-p_id", "--project_id", nargs="+",
            help=(
                "Project id(s) from which to import MultiQC reports. Mainly "
                "for testing purposes"
            )
        )
        parser.add_argument(
            "-a", "--all", action="store_true",
            help="Scan all 002 projects to import all MultiQC reports"
        )
        parser.add_argument(
            "-d", "--dry_run", action="store_true", default=False,
            help="Option to not import the data"
        )

    def handle(self, *args, **options):
        """ Handle options given through the CLI using the add_arguments
        function
        """

        logger.debug(f"Command line: {' '.join(sys.argv)}")

        project_ids = None

        login_to_dnanexus()

        if options["project_id"]:
            project_ids = options["project_id"]

        if options["all"]:
            project_ids = get_all_002_projects()

        if not project_ids:
            msg = "Please use -a or -p_id"
            logger.error(msg)
            raise Exception(msg)

        archived_reports = []

        for p_id in project_ids:
            if not regex.fullmatch(r"project-[a-zA-Z0-9]{24}", p_id):
                msg = f"{p_id} is not a correctly formatted DNAnexus project id"
                logger.error(msg)
                raise Exception(msg)

            report_objects = search_multiqc_reports(p_id)

            for report_object in report_objects:
                if is_archived(report_object):
                    archived_reports.append(report_object.id)
                    continue

                multiqc_report = MultiQC_report(report_object)

                if multiqc_report.is_importable:
                    if not options["dry_run"]:
                        multiqc_report.import_instances()
                        logger.info((
                            f"Successfully imported: "
                            f"{multiqc_report.multiqc_json_id}"
                        ))
                else:
                    logger.warning((
                        f"{report_object.id} doesn't have an "
                        "assay name  present in the trendyqc/trend_monitoring/"
                        "management/configs/assays.json"
                    ))

        if archived_reports:
            storing_logger.warning(
                f"{len(archived_reports)} archived report(s): "
                f"{','.join(archived_reports)}"
            )
