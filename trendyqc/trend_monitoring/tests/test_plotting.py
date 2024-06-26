import datetime
from unittest.mock import Mock, patch

from django.test import TestCase
import pandas as pd

from trend_monitoring.backend_utils.plot import (
    get_subset_queryset,
    get_data_for_plotting,
    get_metric_filter,
    get_date_from_project_name,
    build_groups
)
from trend_monitoring.models.metadata import (
    Report, Report_Sample, Patient, Sample
)


class TestPlotting(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestPlotting, cls).setUpClass()

        Report_Sample.objects.create(
            assay="Assay1",
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
            assay="Assay2",
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

        test_input = {"assay_select": ["Assay1", "Assay2"]}
        test_output = get_subset_queryset(test_input)
        expected_output = Report_Sample.objects.filter(
            assay__in=["Assay1", "Assay2"]
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

    @patch("trend_monitoring.backend_utils.plot.get_metric_filter")
    def test_get_data_for_plotting_no_missing_values(self, mock_metric_filter):
        """ Test the get_data_for_plotting function while providing no empty
        values

        Args:
            mock_metric_filter (Mock thing?): Mock thing for the
            get_metric_filter function used in get_data_for_plotting
        """

        mock_metric_filter.return_value = [
            "picard__hs_metrics__fold_enrichment"
        ]
        test_queryset = Mock()
        # configure the mock object to return the following values when the
        # ".values" method is called on the mock
        test_queryset.configure_mock(**{
            "values.return_value": [{
                "sample__sample_id": "Sample1",
                "report__date": "2000-01-01",
                "report__project_name": "Project1",
                "assay": "Assay1",
                "report__sequencer_id": "Sequencer1",
                "picard__hs_metrics__fold_enrichment": 80.0
            }]
        })

        test_output = get_data_for_plotting(
            test_queryset, ["fake_metric|fake_metric"]
        )

        expected_output = (
            [
                pd.DataFrame(
                    {
                        "sample_id": ["Sample1"],
                        "date": ["2000-01-01"],
                        "project_name": ["Project1"],
                        "assay": ["Assay1"],
                        "sequencer_id": ["Sequencer1"],
                        "picard__hs_metrics__fold_enrichment": [80.0]
                    }
                )
            ],
            {},
            {}
        )

        with self.subTest():
            for test, expected in zip(test_output, expected_output):
                if isinstance(test, list):
                    for test_pd, expected_pd in zip(test, expected):
                        pd.testing.assert_frame_equal(test_pd, expected_pd)
                else:
                    self.assertEqual(test, expected)

    @patch("trend_monitoring.backend_utils.plot.get_metric_filter")
    def test_get_data_for_plotting_missing_samples(self, mock_metric_filter):
        """ Test the get_data_for_plotting function while providing a sample
        without a value

        Args:
            mock_metric_filter (Mock thing?): Mock thing for the
            get_metric_filter function used in get_data_for_plotting
        """

        mock_metric_filter.return_value = [
            "picard__hs_metrics__fold_enrichment"
        ]
        test_queryset = Mock()
        # configure the mock object to return the following values when the
        # ".values" method is called on the mock
        test_queryset.configure_mock(**{
            "values.return_value": [
                {
                    "sample__sample_id": "Sample1",
                    "report__date": "2000-01-01",
                    "report__project_name": "Project1",
                    "assay": "Assay1",
                    "report__sequencer_id": "Sequencer1",
                    "picard__hs_metrics__fold_enrichment": 80.0
                },
                {
                    "sample__sample_id": "Sample2",
                    "report__date": "2000-01-01",
                    "report__project_name": "Project1",
                    "assay": "Assay1",
                    "report__sequencer_id": "Sequencer1",
                    "picard__hs_metrics__fold_enrichment": 75.0
                },
                {
                    "sample__sample_id": "Sample3",
                    "report__date": "2000-01-01",
                    "report__project_name": "Project1",
                    "assay": "Assay1",
                    "report__sequencer_id": "Sequencer1",
                    "picard__hs_metrics__fold_enrichment": None
                }
            ]
        })

        test_output = get_data_for_plotting(
            test_queryset, ["fake_metric|fake_metric"]
        )

        expected_output = (
            [
                pd.DataFrame(
                    {
                        "sample_id": ["Sample1", "Sample2"],
                        "date": ["2000-01-01", "2000-01-01"],
                        "project_name": ["Project1", "Project1"],
                        "assay": ["Assay1", "Assay1"],
                        "sequencer_id": ["Sequencer1", "Sequencer1"],
                        "picard__hs_metrics__fold_enrichment": [80.0, 75.0]
                    },
                )
            ],
            {},
            {
                "fake_metric|fake_metric": {
                    "Project1": set(["Sample3"])
                }
            }
        )

        with self.subTest():
            for test, expected in zip(test_output, expected_output):
                if isinstance(test, list):
                    for test_pd, expected_pd in zip(test, expected):
                        pd.testing.assert_frame_equal(test_pd, expected_pd)
                else:
                    self.assertEqual(test, expected)

    @patch("trend_monitoring.backend_utils.plot.get_metric_filter")
    def test_get_data_for_plotting_missing_project(self, mock_metric_filter):
        """ Test the get_data_for_plotting function while providing one project
        with missing values

        Args:
            mock_metric_filter (Mock thing?): Mock thing for the
            get_metric_filter function used in get_data_for_plotting
        """

        mock_metric_filter.return_value = [
            "picard__hs_metrics__fold_enrichment"
        ]
        test_queryset = Mock()
        # configure the mock object to return the following values when the
        # ".values" method is called on the mock
        test_queryset.configure_mock(**{
            "values.return_value": [
                {
                    "sample__sample_id": "Sample1",
                    "report__date": "2000-01-01",
                    "report__project_name": "Project1",
                    "assay": "Assay1",
                    "report__sequencer_id": "Sequencer1",
                    "picard__hs_metrics__fold_enrichment": 80.0
                },
                {
                    "sample__sample_id": "Sample2",
                    "report__date": "2000-01-01",
                    "report__project_name": "Project2",
                    "assay": "Assay1",
                    "report__sequencer_id": "Sequencer1",
                    "picard__hs_metrics__fold_enrichment": None
                }
            ]
        })

        test_output = get_data_for_plotting(
            test_queryset, ["fake_metric|fake_metric"]
        )

        expected_output = (
            [
                pd.DataFrame(
                    {
                        "sample_id": ["Sample1"],
                        "date": ["2000-01-01"],
                        "project_name": ["Project1"],
                        "assay": ["Assay1"],
                        "sequencer_id": ["Sequencer1"],
                        "picard__hs_metrics__fold_enrichment": [80.0]
                    },
                )
            ],
            {
                "fake_metric|fake_metric": set(["Project2"])
            },
            {}
        )

        with self.subTest():
            for test, expected in zip(test_output, expected_output):
                if isinstance(test, list):
                    for test_pd, expected_pd in zip(test, expected):
                        pd.testing.assert_frame_equal(test_pd, expected_pd)
                else:
                    self.assertEqual(test, expected)

    @patch("trend_monitoring.backend_utils.plot.get_metric_filter")
    def test_get_data_for_plotting_missing_project_samples(
        self, mock_metric_filter
    ):
        """ Test the get_data_for_plotting function while providing one sample
        with missing values and a project with missing values

        Args:
            mock_metric_filter (Mock thing?): Mock thing for the
            get_metric_filter function used in get_data_for_plotting
        """

        mock_metric_filter.return_value = [
            "picard__hs_metrics__fold_enrichment"
        ]
        test_queryset = Mock()
        # configure the mock object to return the following values when the
        # ".values" method is called on the mock
        test_queryset.configure_mock(**{
            "values.return_value": [
                {
                    "sample__sample_id": "Sample1",
                    "report__date": "2000-01-01",
                    "report__project_name": "Project1",
                    "assay": "Assay1",
                    "report__sequencer_id": "Sequencer1",
                    "picard__hs_metrics__fold_enrichment": 80.0
                },
                {
                    "sample__sample_id": "Sample2",
                    "report__date": "2000-01-01",
                    "report__project_name": "Project1",
                    "assay": "Assay1",
                    "report__sequencer_id": "Sequencer1",
                    "picard__hs_metrics__fold_enrichment": 75.0
                },
                {
                    "sample__sample_id": "Sample3",
                    "report__date": "2000-01-01",
                    "report__project_name": "Project1",
                    "assay": "Assay1",
                    "report__sequencer_id": "Sequencer1",
                    "picard__hs_metrics__fold_enrichment": None
                },
                {
                    "sample__sample_id": "Sample4",
                    "report__date": "2000-01-01",
                    "report__project_name": "Project2",
                    "assay": "Assay1",
                    "report__sequencer_id": "Sequencer1",
                    "picard__hs_metrics__fold_enrichment": None
                }
            ]
        })

        test_output = get_data_for_plotting(
            test_queryset, ["fake_metric|fake_metric"]
        )

        expected_output = (
            [
                pd.DataFrame(
                    {
                        "sample_id": ["Sample1", "Sample2"],
                        "date": ["2000-01-01", "2000-01-01"],
                        "project_name": ["Project1", "Project1"],
                        "assay": ["Assay1", "Assay1"],
                        "sequencer_id": ["Sequencer1", "Sequencer1"],
                        "picard__hs_metrics__fold_enrichment": [80.0, 75.0]
                    },
                )
            ],
            {
                "fake_metric|fake_metric": set(["Project2"])
            },
            {
                "fake_metric|fake_metric": {
                    "Project1": set(["Sample3"])
                }
            }
        )

        with self.subTest():
            for test, expected in zip(test_output, expected_output):
                if isinstance(test, list):
                    for test_pd, expected_pd in zip(test, expected):
                        pd.testing.assert_frame_equal(test_pd, expected_pd)
                else:
                    self.assertEqual(test, expected)

    def test_get_metric_filter_normal_filter(self):
        """ Test the get_metric_filter using VerifyBAMid """

        model, metric = "verifybamid_data", "freemix"
        test_output = get_metric_filter(model, metric)
        expected_output = ["verifybamid_data__freemix"]
        self.assertEqual(test_output, expected_output)

    def test_get_metric_filter_intermediate_picard_filter(self):
        """ Test the get_metric_filter using Picard """

        model, metric = "hs_metrics", "fold_enrichment"
        test_output = get_metric_filter(model, metric)
        expected_output = ["picard__hs_metrics__fold_enrichment"]
        self.assertEqual(test_output, expected_output)

    def test_get_metric_filter_intermediate_happy_filter(self):
        """ Test the get_metric_filter using Happy """

        model, metric = "happy_snp_all", "truth_total_het_hom_ratio_snp"
        test_output = get_metric_filter(model, metric)
        expected_output = [
            "happy__happy_snp_all__truth_total_het_hom_ratio_snp"
        ]
        self.assertEqual(test_output, expected_output)

    def test_get_metric_filter_fastqc_filter(self):
        """ Test the get_metric_filter using FastQC (special case) """

        model, metric = "read_data", "total_sequences"
        test_output = get_metric_filter(model, metric)
        expected_output = [
            "fastqc__read_data_1st_lane_R1__lane",
            "fastqc__read_data_2nd_lane_R1__lane",
            "fastqc__read_data_1st_lane_R1__total_sequences",
            "fastqc__read_data_1st_lane_R2__total_sequences",
            "fastqc__read_data_2nd_lane_R1__total_sequences",
            "fastqc__read_data_2nd_lane_R2__total_sequences"
        ]
        self.assertEqual(test_output, expected_output)

    def test_get_metric_filter_base_distribution_filter(self):
        """ Test the get_metric_filter using Picard Base distribution by cycle
        (special case)
        """

        model, metric = "base_distribution_by_cycle_metrics", "sum_pct_t"
        test_output = get_metric_filter(model, metric)
        expected_output = [
            "picard__base_distribution_by_cycle_metrics_1st_lane_R1__lane",
            "picard__base_distribution_by_cycle_metrics_2nd_lane_R1__lane",
            "picard__base_distribution_by_cycle_metrics_1st_lane_R1__sum_pct_t",
            "picard__base_distribution_by_cycle_metrics_1st_lane_R2__sum_pct_t",
            "picard__base_distribution_by_cycle_metrics_2nd_lane_R1__sum_pct_t",
            "picard__base_distribution_by_cycle_metrics_2nd_lane_R2__sum_pct_t"
        ]
        self.assertEqual(test_output, expected_output)

    def test_get_date_from_project_name_date_present(self):
        """ Test get_date_from_project_name function using a mock project name
        that contains a correct date
        """

        test_project_name = "240101"
        test_output = get_date_from_project_name(test_project_name)
        expected_output = "Jan. 2024"
        self.assertEqual(test_output, expected_output)

    def test_get_date_from_project_name_date_absent(self):
        """ Test get_date_from_project_name function using a mock project name
        that doesn't contain a correct date
        """

        test_project_name = "243101"
        with self.assertRaisesRegex(
            AssertionError,
            r"^Couldn't find a date in 243101$",
        ):
            get_date_from_project_name(test_project_name)

    def test_get_date_from_project_name_multiple_dates(self):
        """ Test get_date_from_project_name function using a mock project name
        that contains multiple valid dates
        """

        test_project_name = "240101_240102"
        with self.assertRaisesRegex(
            AssertionError,
            r"^Multiple date looking objects have been found in 240101_240102$"
        ):
            get_date_from_project_name(test_project_name)

    def test_get_date_from_project_name_check_a_lot_of_dates(self):
        """ Test get_date_from_project_name function using 1000 dates to check
        """

        today = datetime.datetime.today()
        dates_to_check = [
            (today - datetime.timedelta(days=x)).strftime('%y%m%d')
            for x in range(1000)
        ]

        for date in dates_to_check:
            with self.subTest():
                try:
                    get_date_from_project_name(date)
                except AssertionError:
                    raise AssertionError(f"{date} is not a valid date")

    def test_build_groups(self):
        """ Test build_groups function """

        test_df = pd.DataFrame(
            {
                "assay": ["Assay1", "Assay1", "Assay1", "Assay2", "Assay3"],
                "sequencer_id": [
                    "Sequencer1",
                    "Sequencer2",
                    "Sequencer1",
                    "Sequencer1",
                    "Sequencer2"
                ],
                "values": [1, 2, 3, 4, 5]
            }
        )

        test_output = build_groups(test_df)
        expected_output = [
            "Assay1 - Sequencer1",
            "Assay1 - Sequencer2",
            "Assay2 - Sequencer1",
            "Assay3 - Sequencer2"
        ]

        self.assertEqual(test_output, expected_output)
