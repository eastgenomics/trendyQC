from django.core.management.base import BaseCommand

import regex

from ._dnanexus_utils import (
    login_to_dnanexus, search_multiqc_reports, get_all_002_projects
)
from ._multiqc import MultiQC_report


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
        """ Handle options given through the CLI using the add_arguments
        function
        """

        project_ids = None

        login_to_dnanexus()

        if options["project_id"]:
            project_ids = options["project_id"]

        if options["all"]:
            project_ids = get_all_002_projects()

        assert project_ids, "Please use -a or -p_id"

        for p_id in project_ids:
            assert regex.fullmatch(r"project-[a-zA-Z0-9]{24}", p_id), (
                f"{p_id} is not a correctly formatted DNAnexus project id"
            )
            report_objects = search_multiqc_reports(p_id)

            for report_object in report_objects:
                multiqc_report = MultiQC_report(report_object)
                multiqc_report.import_in_db()
