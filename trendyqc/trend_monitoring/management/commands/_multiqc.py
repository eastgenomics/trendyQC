from datetime import datetime
import json
from pathlib import Path
from typing import Dict

import dxpy
import regex

from django.apps import apps

from ._parsing import load_assay_config
from ._tool import Tool

# returns the /trendyqc/trend_monitoring/management folder
BASE_DIR_MANAGEMENT = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR_MANAGEMENT / "configs"


class MultiQC_report():
    def __init__(self, multiqc_report: dxpy.DXFile) -> None:
        """ Initialize MultiQC report

        Args:
            multiqc_report (dxpy.DXFile): DXFile object
        """

        self.dnanexus_report = multiqc_report
        self.original_data = json.loads(multiqc_report.read())
        self.assay = self.original_data["config_subtitle"]
        # load the suite of tools that is used for the report's assay
        self.suite_of_tools = load_assay_config(self.assay, CONFIG_DIR)
        self.setup_tools()
        self.parse_multiqc_report()
        self.get_metadata()
        self.map_models_to_tools()
        self.create_all_instances()

    def setup_tools(self):
        """ Setup tools for use when parsing the MultiQC data """

        self.tools = []
        multiqc_raw_data = self.original_data["report_saved_raw_data"]

        for multiqc_field_in_config, tool_metadata in self.suite_of_tools.items():
            # subtool is used to specify for example, HSMetrics or insertSize
            # for Picard. It will equal None if the main tool doesn't have a
            # subtool
            tool, subtool = tool_metadata
            assert multiqc_field_in_config in multiqc_raw_data, (
                f"{multiqc_field_in_config} doesn't exist in the multiqc "
                "report"
            )

            if tool == "happy":
                # setup the happy tools and distinguish that happy has ALL and
                # PASS statuses
                happy_tool = Tool(tool, CONFIG_DIR, subtool)
                happy_tool.set_happy_type("pass")
                self.tools.append(happy_tool)

                happy_tool = Tool(tool, CONFIG_DIR, subtool)
                happy_tool.set_happy_type("all")
                self.tools.append(happy_tool)
            else:
                tool_obj = Tool(tool, CONFIG_DIR, subtool)
                self.tools.append(tool_obj)

    def parse_multiqc_report(self):
        """ Parse the multiqc report for easy import
        Output should look like:
        {
            "sample_id": {
                "tool_name": {
                    "field_name": data
                },
                "other_tool_name": {
                    "lane_read": {
                        "field_name": data
                    }
                }
            }
        }
        """

        self.data = {}
        multiqc_raw_data = self.original_data["report_saved_raw_data"]

        for multiqc_field_in_config, tool_metadata in self.assay_data.items():
            # subtool is used to specify for example, HSMetrics or insertSize
            # for Picard. It will equal None if the main tool doesn't have a
            # subtool
            tool, subtool = tool_metadata
            data_all_samples = multiqc_raw_data[multiqc_field_in_config]

            for sample, tool_data in data_all_samples.items():
                if sample == "undetermined":
                    continue

                # get the tool for the sample
                tool_obj = [
                    tool_obj
                    for tool_obj in self.tools
                    if tool == tool_obj.name and subtool == tool_obj.subtool
                    and tool_obj.happy_type in sample.lower()
                ]

                # quick check for the testing, might need to be improved
                assert len(tool_obj) == 1, "Multiple tools found"

                tool_obj = tool_obj[0]

                # convert the multiqc fields name for ease the import in the db
                converted_fields = tool_obj.convert_tool_fields(tool_data)

                # SNP genotyping adds a "sorted" in the sample name
                sample = sample.replace("_sorted", "")

                sample_data = sample.split("_")
                assert len(sample_data) <= 4, (
                    "Unexpected number of fields when splitting using _: "
                    f"{sample.split('_')}"
                )

                # fastqc contains data at the lane and read level
                if tool == "fastqc":
                    sample_id, order, lane, read = sample_data
                else:
                    sample_id = sample_data[0]

                self.data.setdefault(sample_id, {})
                self.data[sample_id].setdefault(tool_obj, {})

                # fastqc needs a new level to take into account the lane and
                # the read
                if tool == "fastqc":
                    self.data[sample_id][tool_obj][f"{lane}_{read}"] = converted_fields
                else:
                    self.data[sample_id][tool_obj] = converted_fields

    def get_metadata(self):
        """ Get the metadata from the MultiQC DNAnexus object """

        self.report_name = self.dnanexus_report.describe()["name"],
        self.project_name = self.dnanexus_report.describe()["project"],
        self.report_id = self.dnanexus_report.describe()["id"]

        # Get the job ID from the multiqc report
        self.job_id = self.dnanexus_report.describe()["createdBy"]["job"]
        # DNAnexus returns a timestamp that includes milliseconds which Python
        # does not handle. So striping the last 3 characters
        creation_timestamp = int(
            str(
                dxpy.DXJob(self.job_id).describe()["created"]
            )[:-3]
        )
        self.datetime_job = datetime.fromtimestamp(
            creation_timestamp
        )

    def map_models_to_tools(self):
        self.models = {
            model.__name__: model for model in apps.get_models()
        }

        self.mapping_models_tools = {}

        for tool, subtool in self.set_of_tools:
            if subtool:
                tool_name = subtool
                tool_key = f"{tool}-{subtool}"
            else:
                tool_name = tool
                tool_key = tool

            tool_regex = regex.compile(f"{tool_name}", regex.IGNORECASE)
            matches = list(filter(tool_regex.search, self.models.keys()))

            if len(matches) == 1:
                self.mapping_models_tools[tool_key] = self.models[matches[0]]
            # TO-DO: log if there are multiple matches, probably warning or
            # something

    def create_all_instances(self):
        # this dict will contain the data for all the instances created
        # the key will be the name of the table from which they depend upon
        self.instances = {}
        self.create_report_instance()

        for sample in self.data:
            sample_data = self.data[sample]
            self.create_sample_instance(sample)

            for tool in sample_data:
                self.create_tool_data_instance(tool, sample_data[tool])

            self.create_link_table_instance("qc")
            self.create_link_table_instance("picard")

    def create_tool_data_instance(self, tool_name, tool_data):
        model = self.mapping_models_tools[tool_name]

        # check if the tool data has a level for the reads i.e.
        # {read: {field: data, field: data}} vs {field: data, field: data}
        if any(isinstance(i, dict) for i in tool_data.values()):
            for read, data in tool_data.items():
                model_instance = model(**data)
                self.instances["report_sample"].append(model_instance)
        else:
            model_instance = model(**tool_data)
            self.instances["standalone"].append(model_instance)

    def create_sample_instance(self, sample):
        sample = self.models["Sample"]
        sample_instance = sample(sample_id=sample)

    def create_report_instance(self):
        report = self.models["Report"]
        self.instances["standalone"].append(
            report(
                name=self.report_name, run=self.project_name,
                dnanexus_file_id=self.report_id, job_date=self.datetime_job
            )
        )

    def create_link_table_instance(self, type_table):
        if type_table == "qc":
            report_sample = self.models["Report_sample"]
            report_sample_instance = ""
        elif type_table == "picard":
            pass
