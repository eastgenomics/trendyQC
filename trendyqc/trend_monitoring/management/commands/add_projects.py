import datetime
import json
import logging
import sys

from django.core.management.base import BaseCommand

import regex

from .utils._notifications import slack_notify, build_report
from .utils._dnanexus_utils import login_to_dnanexus, get_002_projects
from .utils._report import setup_report_object, import_multiqc_report

logger = logging.getLogger("basic")
storing_logger = logging.getLogger("storing")


class Command(BaseCommand):
    help = "Add projects in TrendyQC"

    def add_arguments(self, parser):
        type_addition = parser.add_mutually_exclusive_group()
        type_addition.add_argument(
            "-p_id",
            "--project_id",
            nargs="+",
            help=(
                "Project id(s) from which to import MultiQC reports. Mainly "
                "for testing purposes"
            ),
        )
        type_addition.add_argument(
            "-t",
            "--time_back",
            help=(
                "Time back in which to look for projects, use the DNAnexus ",
                "docs for info (http://autodoc.dnanexus.com/bindings/python/current/dxpy_search.html#dxpy.bindings.search.find_data_objects) "
                "i.e. -48h looks for projects created 48h ago at the latest",
            ),
        )
        type_addition.add_argument(
            "-a",
            "--all",
            action="store_true",
            help="Scan all 002 projects to import all MultiQC reports",
        )
        parser.add_argument(
            "-update",
            "--automated_update",
            action="store_true",
            default=False,
            help=(
                "Flag to indicate whether this was launched by an automated "
                "job"
            ),
        )
        parser.add_argument(
            "-d",
            "--dry_run",
            action="store_true",
            default=False,
            help="Option to not import the data",
        )

    def handle(self, *args, **options):
        """Handle options given through the CLI using the add_arguments
        function
        """

        now = datetime.datetime.now().strftime("%y%m%d|%I:%M")
        header_msg = (
            f"[{now}] - TrendyQC - Command line: `{' '.join(sys.argv)}`"
        )

        is_automated_update = options["automated_update"]

        if is_automated_update:
            header_msg = (
                f"Starting update to add projects from the last 48h at {now}: "
                f"{' '.join(sys.argv)}"
            )

        project_ids = None

        login_to_dnanexus()

        if options["all"]:
            project_ids = get_002_projects()

        if options["time_back"]:
            project_ids = get_002_projects(created_after=options["time_back"])

        if options["project_id"]:
            project_ids = options["project_id"]

        if not project_ids:
            final_msg = (
                "No projects found using following command: "
                f"{' '.join(sys.argv)}"
            )

            if is_automated_update:
                now = datetime.datetime.now().strftime("%y%m%d|%I:%M")
                final_msg = (
                    f"Finished update at {now}, no new projects detected"
                )

            report_msg = build_report(header_msg, final_msg)
            logger.info(report_msg)
            slack_notify(report_msg)

        else:
            invalid = [
                p
                for p in project_ids
                if not regex.fullmatch(r"project-[a-zA-Z0-9]{24}", p)
            ]

            if invalid:
                msg = f"Invalid DNAnexus project id(s): {','.join(invalid)}"
                logger.error(msg)
                raise AssertionError(msg)

            imported_reports = []
            project2reports = {}
            all_reports = []

            for project_id in project_ids:
                for report in setup_report_object(project_id):
                    project2reports.setdefault(project_id, []).append(
                        report.multiqc_json_id
                    )
                    all_reports.append(report)

                    if not options["dry_run"]:
                        has_been_imported = import_multiqc_report(report)

                        if has_been_imported:
                            imported_reports.append(report.multiqc_json_id)

            header_msg += (
                f"\n\nDetected {len(project_ids)} projects with "
                f"{len(all_reports)} reports for potential import"
            )

            logger.info(header_msg)
            logger.debug(json.dumps(project2reports, indent=2))

            errors = {}
            warnings = {}

            for report in all_reports:
                for msg, type_msg in report.messages:
                    if type_msg == "error":
                        errors.setdefault(report.multiqc_json_id, []).append(
                            msg
                        )

                    elif type_msg == "warning":
                        warnings.setdefault(report.multiqc_json_id, []).append(
                            msg
                        )

            if is_automated_update:
                now = datetime.datetime.now().strftime("%y%m%d|%I:%M")

                if imported_reports:
                    formatted_reports = "\n".join(imported_reports)
                    final_msg = (
                        f"Finished update at {now}, new reports:\n"
                        f"{formatted_reports}"
                    )
                else:
                    final_msg = (
                        f"Finished update at {now}, no new projects added"
                    )

            else:
                final_msg = (
                    f"Finished importing {len(imported_reports)} reports"
                )

            logger.info(final_msg)

            all_issues = {}

            for k, v in list(errors.items()) + list(warnings.items()):
                all_issues.setdefault(k, []).extend(v)

            summary_report = build_report(header_msg, final_msg, all_issues)

            if errors:
                error_report = build_report(header_msg, final_msg, errors)
                logger.error(error_report)

            if warnings:
                warning_report = build_report(header_msg, final_msg, warnings)
                logger.warning(warning_report)

            slack_notify(summary_report)
