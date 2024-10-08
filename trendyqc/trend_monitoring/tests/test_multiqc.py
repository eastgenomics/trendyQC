import json
import tarfile
import random
import re
from string import Formatter

from django.core.exceptions import FieldError as Django_FieldError
from django.test import TestCase
from django.db import models

from trend_monitoring.models.metadata import (
    Report, Sample
)
from trend_monitoring.models.fastq_qc import (
    Read_data, Bcl2fastq_data, Fastqc
)
from trend_monitoring.models.bam_qc import (
    VerifyBAMid_data,
    Samtools_data,
    Custom_coverage,
    Picard,
    Alignment_summary_metrics,
    Base_distribution_by_cycle_metrics,
    Duplication_metrics,
    GC_bias_metrics,
    HS_metrics,
    Insert_size_metrics,
    PCR_metrics,
    Quality_yield_metrics,
)
from trend_monitoring.models.vcf_qc import (
    Somalier_data,
    Sompy_data,
    Vcfqc_data,
    Happy_indel_all,
    Happy_indel_pass,
    Happy_snp_all,
    Happy_snp_pass
)

from trend_monitoring.management.commands.utils._multiqc import MultiQC_report
from trend_monitoring.management.commands.utils._dnanexus_utils import (
    login_to_dnanexus
)
from trendyqc.settings import BASE_DIR
from .custom_tests import CustomTests


def get_reports_tar():
    """ Get the report tar file

    Returns:
        str: Name of the test report tar
    """

    test_reports_dir = BASE_DIR / "trend_monitoring" / "tests" / "test_reports"
    test_reports_tar = list(test_reports_dir.iterdir())

    assert len(test_reports_tar) == 1, "Expected only one file"

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
        metadata_file_contents = [
            json.loads(tf.extractfile(member).read())
            for member in tf.getmembers()
            if member.isfile() and "metadata" in member.name
        ]

        # go through the files in the tar
        for member in tf.getmembers():
            if member.isfile():
                data_file = member.name.split("/")[-1]

                for metadata in metadata_file_contents:
                    if data_file in metadata.keys():
                        reports[data_file] = metadata[data_file]
                        reports[data_file].update(
                            {"data": tf.extractfile(member.name).read()}
                        )

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
            doc = [
                ele.strip() for ele in self._testMethodDoc.strip().split("\n")
            ]
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

        report = MultiQC_report(**test_dict)
        assert len(report.messages) == 1
        assert (
            "Unknown assay is not present in the assay config file" in report.messages[0][0] and report.messages[0][1] == "error"
        ), test_msg


class TestParsingAndImport(TestCase, CustomTests):
    """ Organise the code so that it is structured.
    Contains all the tests for parsing and import the data
    """

    def _parsing_like_multiqc_report(
        self, tool_name: str, sample: str
    ) -> list:
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

        # some tools contains data at the lane and read level
        if tool_name in ["fastqc", "picard_base_content"]:
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

    def _build_filter_dict(
        self, filter_dict: dict, template_dict: dict
    ) -> dict:
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
            # get the keys of the dict keys that are in need of formatting
            # replacement
            keys_to_replace_in_key = [
                ele[1]
                for ele in Formatter().parse(key)
                if ele[1] is not None and ele[1] in template_dict
            ]

            # get the keys of the dict values that are in need of formatting
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

    def _get_data_for(
        self, tool_name: str, filter_dict: dict, model: models.Model
    ):
        """ Generator function that yields the subtest info message and the
        values to compare for a given tool

        Args:
            tool_name (str): Tool name
            filter_dict (dict): Filter dictionary containing the keys/values
            to filter the model instances with
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
            original_data = report.original_data["report_saved_raw_data"]

            # not all reports have picard data
            if field_in_json not in original_data:
                continue

            continue_flag = False
            # go through the raw data stored in the json that is saved in the
            # multiqc object
            for sample, data in original_data[field_in_json].items():
                if sample == "undetermined":
                    continue

                json_fields = tool_data[tool_name][1]

                # in the case of custom coverage, its data is contained in the
                # multiqc-general-stats and multiqc-general-stats is present in
                # other assays so skipping cases where we don't find all the
                # expected fields
                for json_field in json_fields:
                    if json_field not in data:
                        continue_flag = True

                if continue_flag:
                    continue

                # remove some elements that are added in the sample name by
                # tools (these are handled by the clean_sample_naming function
                # in the _utils.py script)
                sample = re.sub(r"_FR|_sorted", "", sample)

                sample_id, lane, read = self._parsing_like_multiqc_report(
                    tool_name, sample
                )

                # loop to generate a filter dict depending on the lane number
                for nb_lane in ["1st_lane", "2nd_lane"]:
                    template_dict = {
                        "read": read,
                        "lane": lane,
                        "nb_lane": nb_lane,
                        "sample_id": sample_id
                    }

                    dynamic_filter_dict = self._build_filter_dict(
                        filter_dict, template_dict
                    )

                    try:
                        db_data = model.objects.filter(**dynamic_filter_dict)
                    except Django_FieldError:
                        # presumably a model without lane and read requirement
                        # i.e. not fastqc or picard base content
                        continue
                    else:
                        # presumably wrong lane filter i.e. fastqc or picard
                        # base content but not the right lane
                        if not db_data:
                            continue
                        # found the right data, break the loop
                        else:
                            break

                msg = (
                    f"Couldn't find data or unique data for {sample_id} "
                    f"using {dynamic_filter_dict}"
                )
                self.assertEqual(len(db_data), 1, msg)

                if "happy" in tool_name:
                    model_name = model._meta.model_name

                    if "indel" in tool_name:
                        if data["Filter_indel"].lower() not in model_name:
                            continue

                    elif "snp" in tool_name:
                        if data["Filter_snp"].lower() not in model_name:
                            continue

                for json_field, db_field in json_fields.items():
                    msg = (
                        f"Testing for {report.report_name}|"
                        f"{report.multiqc_json_id} - {model._meta.model_name} "
                        f"- {sample_id}: {json_field}"
                    )

                    yield (
                        msg, db_field,
                        data[json_field], db_data[0].__dict__[db_field]
                    )

    def test_import_reports(self):
        """ Test whether the reports have been imported correctly.
        Setup the Multiqc object as before and use its metadata to find the
        database row for that report.
        """

        for assay, subkey in reports.items():
            setup_dict = {
                "multiqc_report_id": subkey["file_id"],
                "multiqc_project_id": subkey["project_id"],
                "multiqc_job_id": subkey["job_id"],
                "data": subkey["data"]
            }

            multiqc_obj = MultiQC_report(**setup_dict)

            filter_dict = {
                "name": multiqc_obj.report_name,
                "project_name": multiqc_obj.project_name,
                "project_id": multiqc_obj.project_id,
                "date": multiqc_obj.date,
                "sequencer_id": multiqc_obj.sequencer_id,
                "job_date": multiqc_obj.datetime_job,
                "dnanexus_file_id": multiqc_obj.multiqc_json_id
            }

            report_obj = Report.objects.filter(**filter_dict)

            with self.subTest(
                f"Test found Report object given: {filter_dict}"
            ):
                self.assertEqual(len(report_obj), 1)

    def test_import_sample_ids(self):
        """ Test whether the sample ids from the multiqc reports have been
        imported correctly.

        The test goes through the test multiqc reports, parse the sample ids
        encountered like the production code would and find it in the database.
        """

        for report in multiqc_objects:
            original_data = report.original_data["report_saved_raw_data"]
            # go through the raw data stored in the json that is saved in the
            # multiqc object
            for multiqc_tool in original_data:
                tool_name = None

                # get the tool name in order to be able to reuse the
                # _parsing_like_multiqc_report function
                for tool, data in tool_data.items():
                    if multiqc_tool == data[0]["multiqc_field"]:
                        tool_name = tool

                # this will skip tools that we do not handle, example =
                # bcl2fastq_bylane
                if not tool_name:
                    continue

                for sample in original_data[multiqc_tool]:
                    if sample == "undetermined":
                        continue

                    # remove some elements that are added in the sample name by
                    # tools (these are handled by the clean_sample_naming
                    # function in the _utils.py script)
                    sample_replaced = re.sub(
                        r"_FR|_sorted|_TANDEM", "", sample
                    )

                    sample_id, lane, read = self._parsing_like_multiqc_report(
                        tool_name, sample_replaced
                    )

                    db_data = Sample.objects.filter(sample_id=sample_id)

                    # additional testing required to see if the instances
                    # for each lane/read combo as been created
                    if tool_name == "fastqc":
                        fastqc_obj = Fastqc.objects.filter(
                            report_sample__sample__sample_id=sample_id
                        )

                        try:
                            value_for_sample = fastqc_obj.values_list(
                                f"read_data_1st_lane_{read}"
                            )
                        except Django_FieldError:
                            value_for_sample = fastqc_obj.values_list(
                                f"read_data_2nd_lane_{read}"
                            )

                        with self.subTest(
                            "Assert we can find an instance of Fastqc with "
                            f"{sample_id}"
                        ):
                            self.assertEqual(len(value_for_sample), 1)

                        with self.subTest(
                            "Assert that an instance for that lane/read combo "
                            f"has been created: read_data_{lane}_{read}"
                        ):
                            self.assertNotEqual(value_for_sample[0][0], None)

                    if tool_name == "picard_base_content":
                        picard_obj = Picard.objects.filter(
                            report_sample__sample__sample_id=sample_id
                        )

                        try:
                            value_for_sample = picard_obj.values_list(
                                f"base_distribution_by_cycle_metrics_1st_lane_{read}"
                            )
                        except Django_FieldError:
                            value_for_sample = picard_obj.values_list(
                                f"base_distribution_by_cycle_metrics_2nd_lane_{read}"
                            )

                        with self.subTest(
                            "Assert we can find an instance of Picard with "
                            f"{sample_id}"
                        ):
                            self.assertEqual(len(value_for_sample), 1)

                        with self.subTest(
                            "Assert that an instance for that lane/read combo "
                            "has been created: "
                            f"base_distribution_by_cycle_metrics_{lane}_{read}"
                        ):
                            self.assertNotEqual(value_for_sample[0][0], None)

                    msg = (
                        f"{tool_name} - Couldn't find {sample} in database. "
                        f"Parsed sample id: {sample_id}"
                    )

                    with self.subTest(msg):
                        self.assertEqual(len(db_data), 1)

    def test_parse_bcl2fastq(self):
        """ Test that the bcl2fastq data has been imported and imported
        correctly
        """

        # name of the tool in the config
        tool_name = "bcl2fastq"
        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            "report_sample__sample__sample_id": "{sample_id}"
        }
        model = Bcl2fastq_data

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field_type = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field_type, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_fastqc_data(self):
        """ Test that the fastqc data has been imported and imported correctly
        """

        # name of the tool in the config
        tool_name = "fastqc"
        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            "sample_read": "{read}",
            "lane": "{lane}",
            "read_data_{nb_lane}_{read}__report_sample__sample__sample_id": "{sample_id}"
        }
        model = Read_data

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field_type = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field_type, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_picard_alignment_summary_metrics_data(self):
        """ Test that the picard_alignment_summary_metrics_data has been
        imported and imported correctly
        """

        tool_name = "picard_alignment_summary_metrics"
        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            "picard__report_sample__sample__sample_id": "{sample_id}"
        }
        model = Alignment_summary_metrics

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                # because of a quirk with some tools, empty strings are
                # imported as None
                # these cannot be compared directly, so I wrote a custom
                # assertion test to account for those cases --> more
                # information in the docstring of the assertKindaEqual test
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_picard_hs_metrics(self):
        """ Test that the picard_hs_metrics data has been imported and
        imported correctly
        """

        tool_name = "picard_hsmetrics"
        filter_dict = {
            "picard__report_sample__sample__sample_id": "{sample_id}"
        }
        model = HS_metrics

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_picard_insertsize(self):
        """ Test that the picard_insertsize data has been imported and
        imported correctly
        """

        tool_name = "picard_insertsize"
        filter_dict = {
            "picard__report_sample__sample__sample_id": "{sample_id}"
        }
        model = Insert_size_metrics

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_picard_base_content(self):
        """ Test that the picard_base_content data has been imported and
        imported correctly
        """

        # name of the tool in the config
        tool_name = "picard_base_content"
        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            "sample_read": "{read}",
            "lane": "{lane}",
            "base_distribution_by_cycle_metrics_{nb_lane}_{read}__report_sample__sample__sample_id": "{sample_id}"
        }
        model = Base_distribution_by_cycle_metrics

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field_type = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field_type, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_picard_duplication(self):
        """ Test that the picard_duplication data has been imported and
        imported correctly
        """

        tool_name = "picard_dups"
        filter_dict = {
            "picard__report_sample__sample__sample_id": "{sample_id}"
        }
        model = Duplication_metrics

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_picard_gcbias(self):
        """ Test that the picard_gcbias data has been imported and
        imported correctly
        """

        tool_name = "picard_gcbias"
        filter_dict = {
            "picard__report_sample__sample__sample_id": "{sample_id}"
        }
        model = GC_bias_metrics

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_picard_pcrmetrics(self):
        """ Test that the picard_pcrmetrics data has been imported and
        imported correctly
        """

        tool_name = "picard_pcrmetrics"
        filter_dict = {
            "picard__report_sample__sample__sample_id": "{sample_id}"
        }
        model = PCR_metrics

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_picard_quality_yield(self):
        """ Test that the picard_quality_yield data has been imported and
        imported correctly
        """

        tool_name = "picard_quality_yield"
        filter_dict = {
            "picard__report_sample__sample__sample_id": "{sample_id}"
        }
        model = Quality_yield_metrics

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_custom_coverage(self):
        """ Test that the custom coverage data has been imported and imported
        correctly
        """

        tool_name = "custom_coverage"
        filter_dict = {
            "report_sample__sample__sample_id": "{sample_id}"
        }
        model = Custom_coverage

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_vcfqc(self):
        """ Test that the vcfqc data has been imported and imported correctly
        """

        # name of the tool in the config
        tool_name = "vcfqc"
        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            "report_sample__sample__sample_id": "{sample_id}"
        }
        model = Vcfqc_data

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field_type = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field_type, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_flagstat(self):
        """ Test that the samtools flagstat data has been imported and imported
        correctly
        """

        # name of the tool in the config
        tool_name = "flagstat"
        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            "report_sample__sample__sample_id": "{sample_id}"
        }
        model = Samtools_data

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field_type = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field_type, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_somalier(self):
        """ Test that the somalier data has been imported and imported
        correctly
        """

        # name of the tool in the config
        tool_name = "somalier"
        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            "report_sample__sample__sample_id": "{sample_id}"
        }
        model = Somalier_data

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field_type = model._meta.get_field(db_field)

            with self.subTest(msg):
                # need to check the paternal and maternal ids using the kinda
                # equal as I expect a sample id type value but if not provided
                # the field is equal to 0.0
                if (
                    isinstance(model_field_type, models.FloatField)
                ) or (
                    isinstance(model_field_type, models.CharField)
                ):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_sompy(self):
        """ Test that the sompy data has been imported and imported
        correctly
        """

        # name of the tool in the config
        tool_name = "sompy"
        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            "report_sample__sample__sample_id": "{sample_id}"
        }
        model = Sompy_data

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field_type = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field_type, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_verifybamid(self):
        """ Test that the verifybamid data has been imported and imported
        correctly
        """

        # name of the tool in the config
        tool_name = "verifybamid"
        # build a filter dict to have dynamic search of the sample id
        filter_dict = {
            "report_sample__sample__sample_id": "{sample_id}"
        }
        model = VerifyBAMid_data

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field_type = model._meta.get_field(db_field)

            with self.subTest(msg):
                # NA values are present which get converted in None if the
                # model field is CharField. Using the kindaEqual function to
                # assert their value
                if (
                    isinstance(model_field_type, models.FloatField)
                ) or (
                    isinstance(model_field_type, models.CharField)
                ):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_happy_indel_all(self):
        """ Test that the Happy indel all data has been imported and imported
        correctly
        """

        tool_name = "happy_indel"
        filter_dict = {
            "happy__report_sample__sample__sample_id": "{sample_id}",
            "filter_indel": "ALL"
        }
        model = Happy_indel_all

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    # happy stores data as strings, need to convert them into
                    # integers before comparing
                    try:
                        int(json_data)
                        int(db_data)
                    except ValueError:
                        self.assertEqual(json_data, db_data)
                    else:
                        self.assertEqual(int(json_data), int(db_data))

    def test_parse_happy_indel_pass(self):
        """ Test that the Happy indel pass data has been imported and imported
        correctly
        """

        tool_name = "happy_indel"
        filter_dict = {
            "happy__report_sample__sample__sample_id": "{sample_id}",
            "filter_indel": "PASS"
        }
        model = Happy_indel_pass

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    # happy stores data as strings, need to convert them into
                    # integers before comparing
                    try:
                        int(json_data)
                        int(db_data)
                    except ValueError:
                        self.assertEqual(json_data, db_data)
                    else:
                        self.assertEqual(int(json_data), int(db_data))

    def test_parse_happy_snp_all(self):
        """ Test that the Happy snp all data has been imported and imported
        correctly
        """

        tool_name = "happy_snp"
        filter_dict = {
            "happy__report_sample__sample__sample_id": "{sample_id}",
            "filter_snp": "ALL"
        }
        model = Happy_snp_all

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    # happy stores data as strings, need to convert them into
                    # integers before comparing
                    try:
                        int(json_data)
                        int(db_data)
                    except ValueError:
                        self.assertEqual(json_data, db_data)
                    else:
                        self.assertEqual(int(json_data), int(db_data))

    def test_parse_happy_snp_pass(self):
        """ Test that the Happy snp pass data has been imported and imported
        correctly
        """

        tool_name = "happy_snp"
        filter_dict = {
            "happy__report_sample__sample__sample_id": "{sample_id}",
            "filter_snp": "PASS"
        }
        model = Happy_snp_pass

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    # happy stores data as strings, need to convert them into
                    # integers before comparing
                    try:
                        int(json_data)
                        int(db_data)
                    except ValueError:
                        self.assertEqual(json_data, db_data)
                    else:
                        self.assertEqual(int(json_data), int(db_data))

    def test_parse_sentieon_alignment_summary_metrics_data(self):
        """ Test that the Sentieon alignment summary metrics data has been
        imported and imported correctly
        """

        tool_name = "sentieon_alignment_summary_metrics"
        filter_dict = {
            "picard__report_sample__sample__sample_id": "{sample_id}",
        }
        model = Alignment_summary_metrics

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)

    def test_parse_sentieon_insertsize(self):
        """ Test that the Sentieon insert size data has been imported and
        imported correctly
        """

        tool_name = "sentieon_insertsize"
        filter_dict = {
            "picard__report_sample__sample__sample_id": "{sample_id}",
        }
        model = Insert_size_metrics

        for msg, db_field, json_data, db_data in self._get_data_for(
            tool_name, filter_dict, model
        ):
            model_field = model._meta.get_field(db_field)

            with self.subTest(msg):
                if isinstance(model_field, models.FloatField):
                    self.assertKindaEqual(json_data, db_data)
                else:
                    self.assertEqual(json_data, db_data)
