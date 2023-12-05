import logging
import sys

from django.core.management.base import BaseCommand

from .utils._dnanexus_utils import login_to_dnanexus, get_002_projects
from .utils._import import import_multiqc_reports

logger = logging.getLogger("basic")
storing_logger = logging.getLogger("storing")


class Command(BaseCommand):
    help = "Update TrendyQC with new projects"

    def add_arguments(self, parser):
        parser.add_argument(
            "-t", "--time_back", help=(
                "Time frame in which to look for projects, use the DNAnexus ",
                "docs for info (http://autodoc.dnanexus.com/bindings/python/current/dxpy_search.html#dxpy.bindings.search.find_data_objects)"
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

        project_ids = None

        login_to_dnanexus()

        if options["time_back"]:
            project_ids = get_002_projects(created_after=options["time_back"])
        else:
            project_ids = get_002_projects()

        import_multiqc_reports(project_ids, options["dry_run"])
