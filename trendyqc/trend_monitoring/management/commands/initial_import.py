import logging
import sys

import regex

from django.core.management.base import BaseCommand

from .utils._dnanexus_utils import login_to_dnanexus, get_002_projects
from .utils._import import import_multiqc_reports

logger = logging.getLogger("basic")
storing_logger = logging.getLogger("storing")


class Command(BaseCommand):
    help = "Initial import of the MultiQC reports"

    def add_arguments(self, parser):
        projects = parser.add_mutually_exclusive_group()
        projects.add_argument(
            "-p_id", "--project_id", nargs="+",
            help=(
                "Project id(s) from which to import MultiQC reports. Mainly "
                "for testing purposes"
            )
        )
        projects.add_argument(
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

        logger.info(f"Command line: {' '.join(sys.argv)}")

        project_ids = None

        login_to_dnanexus()

        if options["project_id"]:
            project_ids = options["project_id"]

        if options["all"]:
            project_ids = get_002_projects()

        if not project_ids:
            msg = "Please use -a or -p_id"
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

        import_multiqc_reports(project_ids, options["dry_run"])
