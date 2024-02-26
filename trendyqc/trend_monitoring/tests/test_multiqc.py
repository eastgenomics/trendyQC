import json
import tarfile
import random
import re
from string import Formatter

from django.test import TestCase
from django.db.models import Model

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

def get_reports_tar():
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


def untar_stream_reports(tar):
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
        # go through the files in the tar
        for member in tf.getmembers():
            # folders are present in the tar, skip them
            if member.isfile():
                folder_name, file_name = member.name.split("/")
                metadata_file = member if "metadata" in file_name else None
                data_file = member if "metadata" not in file_name else None

                reports.setdefault(folder_name, {})

                if metadata_file:
                    # get the data from the metadata file
                    metadata_file_content = tf.extractfile(metadata_file).read()
                    metadata_json = json.loads(metadata_file_content)

                    for key, value in metadata_json.items():
                        reports[folder_name][key] = value

                if data_file:
                    # get the JSON data from the report
                    file_content = tf.extractfile(data_file).read()
                    reports[folder_name]["data"] = file_content

    return reports


def import_tool_info():
    """ Read the JSON containing tool information like the mapping between
    the field names in the report and the field names in the models

    Returns:
        dict: Dict containing the JSON file content
    """        

    test_tool_file = BASE_DIR / "trend_monitoring" / "tests" / "test_data" / "tools.json"

    with open(test_tool_file) as f:
        tool_data = json.loads(f.read())
    
    return tool_data


def import_test_reports(reports):
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


def setUpModule():
    """ Set up the data for the battery of tests by:
    - Logging into dnanexus
    - Getting the test tar and performing some checks
    - Untar-ing the reports
    - Importing said reports
    """

    global reports
    global tool_data
    global multiqc_objects

    login_to_dnanexus()
    reports_tar = get_reports_tar()
    reports = untar_stream_reports(reports_tar)
    tool_data = import_tool_info()
    multiqc_objects = import_test_reports(reports)


class TestMultiqc(TestCase):
    """
    To setup this battery of tests, the setUpClass will import reports from
    TWE, CEN, TSO500, MYE assays.
    """

    def shortDescription(self):
        if self._testMethodDoc:
            doc = [ele.strip() for ele in self._testMethodDoc.strip().split("\n")]
            return "\n".join(doc) or None


    def test_multiqc_assay(self):
        """ Test if the assay data i.e. the multiqc fields + tool/subtool name
        associated match the appropriate content of the assay file
        """

        assay_file = BASE_DIR / "trend_monitoring" / "management" / "configs" / "assays.json"

        with open(assay_file) as f:
            assay_file_content = json.loads(f.read())

        for multiqc_object in multiqc_objects:
            test_data = multiqc_object.assay_data
            test_msg = (
                f"Testing the assay data for {multiqc_object.multiqc_json_id}"
            )

            expected_values = assay_file_content[multiqc_object.assay]

            with self.subTest(test_msg):
                self.assertEqual(test_data, expected_values)

    def test_import_already_in_db(self):
        """ Test that the report is defined as being not importable """

        assay, subkey = random.choice(list(reports.items()))
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
        for report in multiqc_objects:
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

        assay, subkey = random.choice(list(reports.items()))
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

        assay, subkey = random.choice(list(reports.items()))
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


class TestParsingAndImport(TestCase):
    """ Organise the code so that it is structured.
    Contains all the tests for parsing and import the data
    """

    def _parsing_like_multiqc_report(self, tool_name: str, sample: str) -> list:
        """ Parse the sample name

        Args:
            tool_name (str): Tool name
            sample (str): Sample name to parse

        Returns:
            list: List containing the sample id, lane and read
        """

        lane = ""
        read = ""

        # SNP genotyping adds a "sorted" in the sample name
        sample = sample.replace("_sorted", "")

        # fastqc contains data at the lane and read level
        if tool_name == "fastqc":
            # look for the order, lane and read using regex
            match = re.search(
                r"_(?P<order>S[0-9]+)_(?P<lane>L[0-9]+)_(?P<read>R[12])",
                sample
            )

            if match:
                # use the regex matching to get the sample id
                potential_sample_id = sample[:match.start()]
                # find every component of the sample id
                matches = re.findall(
                    r"([a-zA-Z0-9]+)", potential_sample_id
                )
                # and join them using dashes (to fix potential errors
                # in the sample naming)
                sample_id = "-".join(matches)
                lane = match.groupdict()["lane"]
                read = match.groupdict()["read"]
            else:
                # give up on the samples that don't have lane and read
                sample_id = sample
        else:
            # some tools provide the order in the sample name, so find
            # that element
            match = re.search(r"_(?P<order>S[0-9]+)", sample)

            if match:
                # and get the sample id remaining
                potential_sample_id = sample[:match.start()]
            else:
                # remove the happy suffixes, they were causing issues
                # because it had a longer sample name breaking the
                # merging of data under one sample id
                sample = re.sub(
                    "_INDEL_PASS|_INDEL_ALL|_SNP_PASS|_SNP_ALL", "",
                    sample
                )

                potential_sample_id = sample

            # same as before, find every element in the sample id
            matches = re.findall(
                r"([a-zA-Z0-9]+)", potential_sample_id
            )
            # and join using dashes
            sample_id = "-".join(matches)

        return sample_id, lane, read

    def _build_filter_dict(self, filter_dict: dict, template_dict: dict) -> dict:
        """ Build a filter dictionary to replpace the string formatting keys
        with the actual values

        Args:
            filter_dict (dict): Dictionary containing the keys and values that
            need formatting
            template_dict (dict): Dictionary containing the values to associate
            to in the filter dictionary

        Returns:
            dict: Dictionary containing the keys and values formatted using the
            values in the template dict
        """

        dynamic_filter_dict = {}

        for key, value in filter_dict.items():
            # get the keys of the keys that are in need of formatting
            # replacement
            keys_to_replace_in_key = [
                ele[1]
                for ele in Formatter().parse(key)
                if ele[1] is not None and ele[1] in template_dict
            ]

            # get the keys of the values that are in need of formatting
            # replacement
            keys_to_replace_in_value = [
                ele[1]
                for ele in Formatter().parse(value)
                if ele[1] is not None and ele[1] in template_dict
            ]

            # if keys were found to possess elements that need formatting
            if keys_to_replace_in_key:
                filtering_key = key.format(**template_dict)
            else:
                filtering_key = key

            # if values were found to possess elements that need formatting
            if keys_to_replace_in_value:
                filtering_value = value.format(**template_dict)
            else:
                filtering_value = value

            # build final filtering dict
            dynamic_filter_dict[filtering_key] = filtering_value

        return dynamic_filter_dict

    def _get_data_for(self, tool_name: str, filter_dict: dict, model: Model):
        """ Generator function that yields the subtest info message and the
        values to compare for a given tool

        Args:
            tool_name (str): Tool name
            filter_dict (dict): Filter dictionary containing the keys/values to filter the model instances with
            model (Model): Model object to use for finding model instances

        Yields:
            tuple: Tuple containing the subtest info message and for a given
            tool: the value from the json and the value from the database
        """

        # name of the data field in the multiqc json i.e.
        # multiqc_picard_AlignmentSummaryMetrics for
        # picard alignmentsummarymetrics
        field_in_json = tool_data[tool_name][0]["multiqc_field"]

        # go over the imported multiqc objects
        for report in multiqc_objects:
            # not all reports have picard data
            if field_in_json not in report.original_data["report_saved_raw_data"]:
                continue
            # go through the raw data stored in the json that is saved in the
            # multiqc object
            for sample, data in report.original_data["report_saved_raw_data"][field_in_json].items():
                if sample == "undetermined":
                    continue

                sample_id, lane, read = self._parsing_like_multiqc_report(
                    tool_name, sample
                )

                template_dict = {
                    "read": read,
                    "lane": lane,
                    "sample_id": sample_id
                }

                dynamic_filter_dict = self._build_filter_dict(
                    filter_dict, template_dict
                )

                # look for the fastqc read data object (should be unique)
                db_data = model.objects.filter(**dynamic_filter_dict)
                # in this dict, key = field name in json / value = field name
                # in db model
                json_fields = tool_data[tool_name][1]

                msg = (
                    f"Couldn't find data or unique data for {sample_id} "
                    f"using {dynamic_filter_dict}"
                )
                self.assertEqual(len(db_data), 1, msg)

                for json_field, db_field in json_fields.items():
                    msg = (
                        f"Testing for {report.report_name}|"
                        f"{report.multiqc_json_id} - {sample_id}: {json_field}"
                    )

                    yield msg, data[json_field], db_data[0].__dict__[db_field]

    def test_parse_fastqc_data(self):
        """ Test that the fastqc data has been imported and imported correctly
        """

        # name of the tool in the config
        tool_name = "fastqc"

        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            "sample_read": "{read}",
            "lane": "{lane}",
            "fastqc_{lane}_{read}__report_sample__sample__sample_id": "{sample_id}"
        }

        model = Fastqc_read_data

        for msg, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            with self.subTest(msg):
                self.assertEqual(json_data, db_data)

    def test_parse_picard_alignment_summary_metrics_data(self):
        """ Test that the picard data has been imported and imported correctly
        """

        tool_name = "picard_alignment_summary_metrics"

        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            (
                "picard__report_sample__sample__sample_id"
            ): "{sample_id}"
        }

        model = Picard_alignment_summary_metrics

        for msg, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            with self.subTest(msg):
                self.assertEqual(json_data, db_data)
