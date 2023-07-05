from django.core.management.base import BaseCommand
from ._dnanexus_utils import search_multiqc_data, get_all_002_projects


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

    def handle(self, *args, **options):
        project_ids = None

        if options["project_id"]:
            project_ids = options["project_id"]

        if options["all"]:
            project_ids = get_all_002_projects()

        assert project_ids is not None, "Please use -a or -p_id"

        for p_id in project_ids:
            report_ids = search_multiqc_data(p_id)
