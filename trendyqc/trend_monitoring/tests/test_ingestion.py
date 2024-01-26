import json
import tarfile

from django.test import TestCase
import pandas as pd

from trend_monitoring.backend_utils.plot import get_metric_filter
from trend_monitoring.management.commands.utils._multiqc import MultiQC_report
from trend_monitoring.management.commands.utils._dnanexus_utils import login_to_dnanexus
from trend_monitoring.models.metadata import Report, Report_Sample
from trendyqc.settings import BASE_DIR


class TestIngestion(TestCase):
    """
    To setup this battery of tests, the setUpClass will import reports from
    TWE, CEN, TSO500, MYE assays.
    """

    def shortDescription(self):
        doc = [ele.strip() for ele in self._testMethodDoc.strip().split("\n")]
        return "\n".join(doc) or None

    @classmethod
    def get_reports_tar(cls):
        """ Get the report tar file

        Returns:
            str: Name of the test report tar
        """

        test_reports_dir = BASE_DIR / "trend_monitoring" / "tests" / "test_reports"
        test_reports_tar = list(test_reports_dir.iterdir())

        assert len(test_reports_tar) == 1, "Multiple files in test_reports dir"

        test_reports_tar = test_reports_tar[0]

        assert test_reports_tar.name == "test_reports.tar.gz", (
            "Name of report tar is not as expected"
        )

        return test_reports_tar

    @classmethod
    def untar_stream_reports(cls, tar):
        """ Untar and uncompress the tar file to extract the JSON Multiqc file
        and the metadata file associated with every report file

        Args:
            tar (str): Name and path to the tar file

        Returns:
            dict: Dict containing the file id, project id and job id as well as
            the JSON content
        """

        reports = {}

        with tarfile.open(tar) as tf:
            tar_dict = {}

            # go through the files in the tar
            for member in tf.getmembers():
                # folders are present in the tar, skip them
                if member.isfile():
                    folder_name, file_name = member.name.split("/")
                    tar_dict.setdefault(folder_name, []).append(member)

            # should probably be another function
            # looping through the assays and the files
            for assay, files in tar_dict.items():
                metadata_file = [
                    file for file in files if "metadata" in file.name
                ][0]

                data_file = [
                    file for file in files if "metadata" not in file.name
                ][0]

                # get the data from the metadata file
                metadata_file_content = tf.extractfile(metadata_file).read()
                metadata_json = json.loads(metadata_file_content)
                # get the JSON data from the report
                file_content = tf.extractfile(data_file).read()

                reports.setdefault(assay, {})
                reports[assay] = metadata_json
                reports[assay]["data"] = file_content

        return reports

    @classmethod
    def import_test_reports(cls, reports):
        """ Import the test reports

        Returns:
            list: List of MultiQC reports objects
        """

        multiqc_report_objects = []

        for assay, subkey in reports.items():
            test_dict = {
                "multiqc_report_id": subkey["file_id"],
                "multiqc_project_id": subkey["project_id"],
                "multiqc_job_id": subkey["job_id"],
                "data": subkey["data"] 
            }

            multiqc_report = MultiQC_report(**test_dict)
            multiqc_report.import_instances()
            multiqc_report_objects.append(multiqc_report)

        return multiqc_report_objects

    @classmethod
    def setUpClass(cls):
        """ Set up the data for the battery of tests by:
        - Logging into dnanexus
        - Getting the test tar and performing some checks
        - Untar-ing the reports
        - Importing said reports
        """

        super(TestIngestion, cls).setUpClass()
        login_to_dnanexus()
        reports_tar = cls.get_reports_tar()
        cls.reports = cls.untar_stream_reports(reports_tar)
        cls.multiqc_objects = cls.import_test_reports(cls.reports)

    def test_multiqc_assay(self):
        """ Test if the assay data i.e. the multiqc fields + tool/subtool name
        associated match the appropriate content of the assay file
        """

        assay_file = BASE_DIR / "trend_monitoring" / "management" / "configs" / "assays.json"

        with open(assay_file) as f:
            assay_file_content = json.loads(f.read())

        for multiqc_object in self.multiqc_objects:
            test_data = multiqc_object.assay_data
            test_msg = (
                f"Testing the assay data for {multiqc_object.multiqc_json_id}"
            )

            expected_values = assay_file_content[multiqc_object.assay]

            with self.subTest(test_msg):
                self.assertEqual(test_data, expected_values)

    def test_import_already_in_db(self):
        """ Test that the report is defined as being not importable """

        for assay, subkey in self.reports.items():
            test_dict = {
                "multiqc_report_id": subkey["file_id"],
                "multiqc_project_id": subkey["project_id"],
                "multiqc_job_id": subkey["job_id"],
                "data": subkey["data"] 
            }

            test_report = MultiQC_report(**test_dict)
            test_msg = (
                f"Testing if {test_report.multiqc_json_id} is not importable "
                "because it is already in the db"
            )
            self.assertFalse(test_report.is_importable, test_msg)
            break

    def test_assay_key_missing(self):
        """
        Test that a report is not importable because the assay key doesn't
        exist in the JSON file
        """

        for assay, subkey in self.reports.items():
            # remove the config_subtitle key from the data to trigger the
            # "not importable" status
            data = json.loads(subkey["data"])
            del data["config_subtitle"]
            test_data = json.dumps(data)

            test_dict = {
                "multiqc_report_id": subkey["file_id"],
                "multiqc_project_id": subkey["project_id"],
                "multiqc_job_id": subkey["job_id"],
                "data": test_data
            }

            test_report = MultiQC_report(**test_dict)
            test_msg = (
                f"Testing if {test_report.multiqc_json_id} is not importable "
                "because of the missing key in the JSON file"
            )
            self.assertFalse(test_report.is_importable, test_msg)
            break

    def test_assay_not_in_config(self):
        """ Test that a report is not importable because the assay value in the
        MultiQC data doesn't exist in the assays.json file
        """

        for assay, subkey in self.reports.items():
            # replace the value for the assay in the MultiQC data
            data = json.loads(subkey["data"])
            data["config_subtitle"] = "Unknown assay"
            test_data = json.dumps(data)

            test_dict = {
                "multiqc_report_id": subkey["file_id"],
                "multiqc_project_id": subkey["project_id"],
                "multiqc_job_id": subkey["job_id"],
                "data": test_data
            }

            test_msg = (
                f"Testing if {subkey['file_id']} is not importable "
                "because the assay in the MultiQC data doesn't exist in the "
                "assays.json file"
            )

            with self.assertRaises(AssertionError, msg=test_msg):
                MultiQC_report(**test_dict)

            break

    # def test_data_integrity(self):
    #     """ Actual test to check if the data has been imported correctly """

    #     reports_db = Report.objects.all()

    #     # go through the reports in the database
    #     for report in reports_db:
    #         # get the MultiQC report object matching the report in the database
    #         report_obj = [
    #             report_obj for report_obj in self.report_objects
    #             if report.dnanexus_file_id == report_obj.multiqc_json_id
    #         ][0]

    #         # go through the tools of the MultiQC report
    #         for tool in report_obj.tools:
    #             # get the data in the JSON file for that tool
    #             df = pd.DataFrame(
    #                 report_obj.original_data["report_saved_raw_data"][tool.multiqc_field_name]
    #             ).T

    #             # get the report_sample links in preparation
    #             report_samples = Report_Sample.objects.filter(report=report)
    #             # get list of samples for current report
    #             samples = list(
    #                 report_samples.values_list("sample__sample_id", flat=True)
    #             )

    #             # go through the samples of that MultiQC report
    #             for sample in samples:
    #                 # get the row(s) with that sample name
    #                 filtered_df = df[
    #                     [sample in index for index in df.index]
    #                 ]

    #                 # only one match which is the expected outcome for most
    #                 # cases
    #                 if filtered_df.shape[0] == 1:
    #                     # go through the fields for the tool
    #                     for multiqc_field, db_field in tool.fields.items():
    #                         # get and clean the value in the dataframe
    #                         value_from_file = MultiQC_report.clean_value(
    #                             filtered_df[multiqc_field].to_numpy()[0]
    #                         )

    #                         # build a metric field
    #                         metric_filter = get_metric_filter(
    #                             tool.model.__name__.lower(), db_field
    #                         )
    #                         # get the value from the database using the metric
    #                         # filter
    #                         value_imported = list(
    #                             report_samples.filter(
    #                                 sample__sample_id=sample
    #                             ).values_list(metric_filter, flat=True)
    #                         )[0]

    #                         self.assertEqual(value_from_file, value_imported)

    #                 elif filtered_df.shape[0] >= 2:
    #                     pass
