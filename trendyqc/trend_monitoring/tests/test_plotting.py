from django.test import TestCase
from django.utils import timezone

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
                date=timezone.now(),
                job_date=timezone.now()
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
                date=timezone.now(),
                job_date=timezone.now()
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
        test_input = {"assay_select": ["CEN", "MYE"]}
        test_output = get_subset_queryset(test_input)
        expected_output = Report_Sample.objects.filter(
            assay__in=["CEN", "MYE"]
        )
        self.assertQuerysetEqual(test_output, expected_output, ordered=False)

    def test_get_subset_queryset_run_query(self):
        test_input = {"run_select": ["ProjectName1", "ProjectName2"]}
        test_output = get_subset_queryset(test_input)
        expected_output = Report_Sample.objects.filter(
            report__project_name__in=["ProjectName1", "ProjectName2"]
        )
        self.assertQuerysetEqual(test_output, expected_output, ordered=False)
