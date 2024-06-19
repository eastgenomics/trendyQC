import datetime

from django.test import TestCase

from trend_monitoring.backend_utils.plot import get_subset_queryset
from trend_monitoring.models.metadata import Report, Report_Sample, Patient, Sample


class TestPlotting(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestPlotting, cls).setUpClass()

        Report_Sample.objects.create(
            assay="CEN",
            report=Report.objects.create(
                name="Report1",
                project_id="Project1",
                project_name="ProjectName1",
                dnanexus_file_id="File1",
                sequencer_id="Sequencer1",
                date=datetime.date(2020, 1, 1),
                job_date=datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
            ),
            sample=Sample.objects.create(
                patient=Patient.objects.create(
                    gm_number="GM#",
                    sex="U"
                ),
                sample_id="Sample1"
            ),
            bcl2fastq_data=None,
            fastqc=None,
            custom_coverage=None,
            verifybamid_data=None,
            samtools_data=None,
            picard=None,
            somalier_data=None,
            sompy_data=None,
            vcfqc_data=None,
            happy=None
        )

        Report_Sample.objects.create(
            assay="MYE",
            report=Report.objects.create(
                name="Report2",
                project_id="Project2",
                project_name="ProjectName2",
                dnanexus_file_id="File2",
                sequencer_id="Sequencer2",
                date=datetime.date(2024, 1, 1),
                job_date=datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
            ),
            sample=Sample.objects.create(
                patient=Patient.objects.create(
                    gm_number="GM#",
                    sex="U"
                ),
                sample_id="Sample2"
            ),
            bcl2fastq_data=None,
            fastqc=None,
            custom_coverage=None,
            verifybamid_data=None,
            samtools_data=None,
            picard=None,
            somalier_data=None,
            sompy_data=None,
            vcfqc_data=None,
            happy=None
        )

    def test_get_subset_queryset_assay_query(self):
        """ Test the get_subset_queryset function which gets a queryset based
        on filtering options, case:
        - Assay filter
        """

        test_input = {"assay_select": ["CEN", "MYE"]}
        test_output = get_subset_queryset(test_input)
        expected_output = Report_Sample.objects.filter(
            assay__in=["CEN", "MYE"]
        )
        self.assertQuerysetEqual(test_output, expected_output, ordered=False)

    def test_get_subset_queryset_run_query(self):
        """ Test the get_subset_queryset function which gets a queryset based
        on filtering options, case:
        - Run filter
        """
        test_input = {"run_select": ["ProjectName1", "ProjectName2"]}
        test_output = get_subset_queryset(test_input)
        expected_output = Report_Sample.objects.filter(
            report__project_name__in=["ProjectName1", "ProjectName2"]
        )
        self.assertQuerysetEqual(test_output, expected_output, ordered=False)

    def test_get_subset_queryset_sequencer_query(self):
        """ Test the get_subset_queryset function which gets a queryset based
        on filtering options, case:
        - Sequencer filter
        """
        test_input = {"sequencer_select": ["Sequencer1", "Sequencer2"]}
        test_output = get_subset_queryset(test_input)
        expected_output = Report_Sample.objects.filter(
            report__sequencer_id__in=["Sequencer1", "Sequencer2"]
        )
        self.assertQuerysetEqual(test_output, expected_output, ordered=False)

    def test_get_subset_queryset_date_query(self):
        """ Test the get_subset_queryset function which gets a queryset based
        on filtering options, case:
        - Date filter
        """
        test_input = {"date_start": datetime.date(2022, 1, 1), "date_end": datetime.date.today()}
        test_output = get_subset_queryset(test_input)
        expected_output = Report_Sample.objects.filter(
            report__date__range=[datetime.date(2022, 1, 1), datetime.date.today()]
        )
        self.assertQuerysetEqual(test_output, expected_output, ordered=False)

    def test_get_subset_queryset_multiple_query(self):
        """ Test the get_subset_queryset function which gets a queryset based
        on filtering options, case:
        - Assay filter
        - Sequencer filter
        """
        test_input = {"assay_select": "CEN", "sequencer_select": "Sequencer2"}
        test_output = get_subset_queryset(test_input)
        expected_output = Report_Sample.objects.filter(
            assay__in=["CEN"],
            report__sequencer_id__in=["Sequencer2"]
        )
        self.assertQuerysetEqual(test_output, expected_output, ordered=False)
