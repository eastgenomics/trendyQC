import json
import tarfile
import random

from django.test import TestCase
import regex

from trend_monitoring.models.metadata import (
    Report, Patient, Report_Sample, Sample
)
from trend_monitoring.models.fastq_qc import (
    Fastqc_read_data, Fastqc, Bcl2fastq_data
)
from trend_monitoring.models.bam_qc import (
    VerifyBAMid_data,
    Samtools_data,
    Custom_coverage,
    Picard,
    Picard_alignment_summary_metrics,
    Picard_base_distribution_by_cycle_metrics,
    Picard_duplication_metrics,
    Picard_gc_bias_metrics,
    Picard_hs_metrics,
    Picard_insert_size_metrics,
    Picard_pcr_metrics,
    Picard_quality_yield_metrics,
)
from trend_monitoring.models.vcf_qc import (
    Somalier_data,
    Sompy_data,
    Happy,
    Happy_indel_all,
    Happy_indel_pass,
    Happy_snp_all,
    Happy_snp_pass
)

from trend_monitoring.management.commands.utils._multiqc import MultiQC_report
from trend_monitoring.management.commands.utils._dnanexus_utils import login_to_dnanexus
from trendyqc.settings import BASE_DIR


class TestMultiqc(TestCase):
    """
    To setup this battery of tests, the setUpClass will import reports from
    TWE, CEN, TSO500, MYE assays.
    """

    def shortDescription(self):
        if self._testMethodDoc:
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
    def import_tool_info(cls):
        test_tool_file = BASE_DIR / "trend_monitoring" / "tests" / "test_data" / "tools.json"

        with open(test_tool_file) as f:
            tool_data = json.loads(f.read())

        return tool_data

    @classmethod
    def setUpClass(cls):
        """ Set up the data for the battery of tests by:
        - Logging into dnanexus
        - Getting the test tar and performing some checks
        - Untar-ing the reports
        - Importing said reports
        """

        super(TestMultiqc, cls).setUpClass()
        login_to_dnanexus()
        cls.tool_data = cls.import_tool_info()
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

        assay, subkey = random.choice(list(self.reports.items()))
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

    def test_import_not_in_db(self):
        """ Test to check if the report will be imported """

        # find the test CEN report to get its data for creating new fake report
        for report in self.multiqc_objects:
            if report.assay == "Cancer Endocrine Neurology":
                data = json.dumps(report.original_data)

        # MultiQC json from 002_211222_A01295_0042_AHV5W2DRXY_CEN
        # + data from test CEN report
        test_dict = {
            "multiqc_report_id": "file-G72y9vQ4fJb1y7v8F51qXg3v",
            "multiqc_project_id": "project-G72pFZ04p90bVB6FP1fYBGBg",
            "multiqc_job_id": "job-G72y2BQ4p90gF31v23KJ57qQ",
            "data": data,
        }

        test_report = MultiQC_report(**test_dict)
        test_msg = (
            f"Testing if {test_report.multiqc_json_id} is importable "
            "because it is not in the db"
        )
        self.assertTrue(test_report.is_importable, test_msg)

    def test_assay_key_missing(self):
        """
        Test that a report is not importable because the assay key doesn't
        exist in the JSON file
        """

        assay, subkey = random.choice(list(self.reports.items()))
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

    def test_assay_not_in_config(self):
        """ Test that a report is not importable because the assay value in the
        MultiQC data doesn't exist in the assays.json file
        """

        assay, subkey = random.choice(list(self.reports.items()))
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

    def test_parse_fastqc_data(self):
        """ Test that the fastqc data has been imported and imported correctly
        """
        field_in_json = self.tool_data["fastqc"][0]["multiqc_field"]

        for report in self.multiqc_objects:
            for sample, data in report.original_data["report_saved_raw_data"][field_in_json].items():
                match = regex.search(
                    r"_(?P<order>S[0-9]+)_(?P<lane>L[0-9]+)_(?P<read>R[12])",
                    sample
                )

                if match:
                    # use the regex matching to get the sample id
                    potential_sample_id = sample[:match.start()]
                    # find every component of the sample id
                    matches = regex.findall(
                        r"([a-zA-Z0-9]+)", potential_sample_id
                    )
                    # and join them using dashes (to fix potential errors
                    # in the sample naming)
                    sample_id = "-".join(matches)
                    lane = match.groupdict()["lane"]
                    read = match.groupdict()["read"]
                else:
                    exit()

                filter_dict = {
                    "sample_read": read,
                    "lane": lane,
                    f"fastqc_{lane}_{read}__report_sample__sample__sample_id": sample_id
                }

                db_data = Fastqc_read_data.objects.get(**filter_dict)
                json_fields = self.tool_data["fastqc"][1]

                msg = f"Couldn't find data for {sample_id} using {filter_dict}"
                self.assertTrue(db_data, msg)

                if db_data:
                    for json_field, db_field in json_fields.items():
                        msg = f"Testing for {sample_id}: {json_field}"

                        with self.subTest(msg):
                            self.assertEqual(
                                data[json_field], db_data.__dict__[db_field]
                            )
