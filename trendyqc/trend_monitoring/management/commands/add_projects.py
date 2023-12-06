import datetime
import logging
import sys

from django.core.management.base import BaseCommand

import regex

from .utils._dnanexus_utils import login_to_dnanexus, get_002_projects
from .utils._import import import_multiqc_reports

logger = logging.getLogger("basic")
storing_logger = logging.getLogger("storing")


class Command(BaseCommand):
    help = "Update TrendyQC with new projects"

    def add_arguments(self, parser):
        type_addition = parser.add_mutually_exclusive_group()
        type_addition.add_argument(
            "-p_id", "--project_id", nargs="+",
            help=(
                "Project id(s) from which to import MultiQC reports. Mainly "
                "for testing purposes"
            )
        )
        type_addition.add_argument(
            "-t", "--time_back", required=False, help=(
                "Time back in which to look for projects, use the DNAnexus ",
                "docs for info (http://autodoc.dnanexus.com/bindings/python/current/dxpy_search.html#dxpy.bindings.search.find_data_objects) "
                "i.e. -48h looks for projects created 48h ago at the latest"
            )
        )
        type_addition.add_argument(
            "-a", "--all", action="store_true",
            help="Scan all 002 projects to import all MultiQC reports"
        )
        parser.add_argument(
            "-update", "--automated_update", action="store_true", default=False,
            help=(
                "Flag to indicate whether this was launched by an automated "
                "job"
            )
        )
        parser.add_argument(
            "-d", "--dry_run", action="store_true", default=False,
            help="Option to not import the data"
        )

    def handle(self, *args, **options):
        """ Handle options given through the CLI using the add_arguments
        function
        """

        logger.info(f"Command line: {' '.join(sys.argv)}")

        is_automated_update = options["automated_update"]
        
        if is_automated_update:
            now = datetime.datetime.now().strftime("%y%m%d|%I:%M")
            print(f"Starting update at {now}: {' '.join(sys.argv)}")

        project_ids = None

        login_to_dnanexus()

        if options["all"]:
            project_ids = get_002_projects()

        if options["time_back"]:
            project_ids = get_002_projects(created_after=options["time_back"])

        if options["project_id"]:
            project_ids = options["project_id"]

        if not project_ids:
            msg = (
                "No projects found using following command: "
                f"{' '.join(sys.argv)}"
            )
            logger.error(msg)
            raise Exception(msg)

        invalid = [
            p
            for p in project_ids
            if not regex.fullmatch(r"project-[a-zA-Z0-9]{24}", p)
        ]

        if invalid:
            msg = f"Invalid DNAnexus project id(s): {','.join(invalid)}"
            logger.error(msg)
            raise AssertionError(msg)

        imported_reports = import_multiqc_reports(
            project_ids, options["dry_run"]
        )

        if is_automated_update:
            now = datetime.datetime.now().strftime("%y%m%d|%I:%M")
            formatted_reports = "\n".join(imported_reports)
            print(
                f"Finished update at {now}, new reports:\n{formatted_reports}"
            )
