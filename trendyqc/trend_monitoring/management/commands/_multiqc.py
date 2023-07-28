from collections import defaultdict
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any, Dict, List

import dxpy
import regex

from django.apps import apps
from django.db.models import Model

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
        # load the report's assay tools and the fields they are associated with
        self.assay_data = load_assay_config(self.assay, CONFIG_DIR)
        self.setup_tools()
        self.parse_multiqc_report()
        self.get_metadata()
        self.map_models_to_tools()
        self.create_all_instances()

    def setup_tools(self):
        """ Create tools for use when parsing the MultiQC data and store them
        in self.tools"""

        self.tools = []
        multiqc_raw_data = self.original_data["report_saved_raw_data"]

        for multiqc_field_in_config, tool_metadata in self.assay_data.items():
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

                # convert data in appropriate types for future import
                cleaned_data = self.clean_data(converted_fields)

                # fastqc needs a new level to take into account the lane and
                # the read
                if tool == "fastqc":
                    self.data[sample_id][tool_obj][f"{lane}_{read}"] = cleaned_data
                else:
                    self.data[sample_id][tool_obj] = cleaned_data

    def get_metadata(self):
        """ Get the metadata from the MultiQC DNAnexus object """

        # TO-DO this returns the name of the json that i pull data from.
        # Need to extract the HTML from the job id
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
        """ Map Django models to tools. Store that info in the appropriate
        tool object """

        # Store the Django models as a dict of model names to model objects
        self.models = {
            model.__name__.lower(): model for model in apps.get_models()
        }

        # loop through the tools that we have for this MultiQC report
        for tool in self.tools:
            if tool.happy_type:
                tool_regex = f"{tool.subtool}_{tool.happy_type}"
            elif tool.subtool:
                tool_regex = tool.subtool
            else:
                tool_regex = tool.name

            compiled_regex = regex.compile(tool_regex, regex.IGNORECASE)
            # look for the tool in the self.models, get a list of the matches
            matches = list(filter(compiled_regex.search, self.models.keys()))

            if len(matches) == 1:
                # store the model in the tool object
                tool.set_model(self.models[matches[0]])
            else:
                # TO-DO: log if there are multiple matches, probably warning or
                # something
                print("no")

    def create_all_instances(self):
        """ Create instances for everything that needs to get imported

        Creates:
            - self.all_instances: Dict containing the sample as keys and the
            values are lists of the instances to import in the correct order
        """

        self.all_instances = {}
        report_instance = self.create_report_instance()

        for sample in self.data:
            # reset the self.instances_one_sample variable to keep instances
            # per sample
            self.instances_one_sample = defaultdict(list)
            self.instances_one_sample["report_sample"].append(report_instance)
            # setup the all instances per sample so that they are appended in
            # order of future import
            self.all_instances.setdefault(sample, [])
            self.all_instances[sample].append(report_instance)

            sample_data = self.data[sample]
            self.all_instances[sample].append(
                self.create_sample_instance(sample)
            )

            for tool in sample_data:
                # create instance for every tool
                self.all_instances[sample].extend(
                    self.create_tool_data_instance(tool, sample_data[tool])
                )

            self.all_instances[sample].append(
                self.create_link_table_instance("fastqc")
            )

            picard_instance = self.create_link_table_instance("picard")
            happy_instance = self.create_link_table_instance("happy")

            # picard and happy are not used for every assay
            if picard_instance:
                self.all_instances[sample].append(picard_instance)

            if happy_instance:
                self.all_instances[sample].append(happy_instance)

            # get the report sample model object and instanciate using the
            # instances that were gathered previously
            report_sample_instance = self.models["report_sample"](
                **self.gather_instances_for("report_sample")
            )

            self.all_instances[sample].append(report_sample_instance)

    def create_tool_data_instance(self, tool_obj: Tool, tool_data: dict) -> List:
        """ Create tool data instance. Uses the tool data structure to check
        how to create model instances.

        Args:
            tool_obj (Tool): Tool object
            tool_data (dict): Data that is stored for that tool

        Returns:
            List: List of the model instances created
        """

        instances_to_return = []
        model = tool_obj.model

        # check if the tool data has a level for the reads i.e.
        # {read: {field: data, field: data}} vs {field: data, field: data}
        if all(isinstance(i, dict) for i in tool_data.values()):
            for read, data in tool_data.items():
                # this info is not available in the FastQC data so I create it
                # myself
                data["lane"] = read.split("_")[0]
                data["sample_read"] = read.split("_")[1]
                model_instance = model(**data)
                # store the fastqc instances using their parent table i.e.
                # fastqc as key
                self.instances_one_sample["fastqc"].append(model_instance)
                instances_to_return.append(model_instance)
        else:
            model_instance = model(**tool_data)

            if tool_obj.parent:
                # store these tools using their parent table name as key
                self.instances_one_sample[tool_obj.parent].append(model_instance)
            else:
                # if they have no parent that means that their parent is
                # directly the report sample table so use that as the key
                self.instances_one_sample["report_sample"].append(model_instance)

            instances_to_return.append(model_instance)

        return instances_to_return

    def clean_data(self, data: Dict) -> Dict:
        """ Loop through the fields and values for one tool and clean the
        values

        Args:
            data (Dict): Dict containing the fields and values of a Tool

        Returns:
            Dict: Dict with cleaned data
        """

        return {
            field: self.clean_value(value) for field, value in data.items()
        }

    @staticmethod
    def clean_value(value: str) -> Any:
        """ Clean given value

        Args:
            value (str): Value stored for a field

        Returns:
            Any: Value that has correct type if it passed tests or cleaned
            value
        """

        # check if value is an empty string + check if value is not 0
        # otherwise it returns None
        if not value and value != 0:
            return None

        try:
            float(value)
        except ValueError:
            # Probably str
            return value

        # nan doesn't trigger the exception, so handle them separately
        if math.isnan(float(value)):
            return None

        # it can float, check if it's an int or float
        if '.' in str(value):
            return float(value)
        else:
            return int(value)

    def create_sample_instance(self, sample_id: str) -> Model:
        """ Create the sample instance.

        Args:
            sample (str): Sample id

        Returns:
            Model: Instance object of Sample Model
        """

        sample = self.models["sample"]
        sample_instance = sample(sample_id=sample_id)
        self.instances_one_sample["report_sample"].append(sample_instance)
        return sample_instance

    def create_report_instance(self) -> Model:
        """ Create the report instance using data gathered when initialising
        the report

        Returns:
            Model: Instance object of Report Model
        """

        report = self.models["report"]
        report_instance = report(
            name=self.report_name, run=self.project_name,
            dnanexus_file_id=self.report_id, job_date=self.datetime_job
        )
        return report_instance

    def create_link_table_instance(self, type_table: str) -> Model:
        """ Create the instances for the tables that have foreign keys i.e.
        picard, happy, fastqc

        Args:
            type_table (str): Name of the link table

        Returns:
            Model: Instance object of link table Model (Picard, FastQC, Happy)
        """

        # get the model object using the type table variable
        model = self.models[type_table]
        instances = self.gather_instances_for(type_table)

        if instances:
            # instantiate the link table by gathering the data from the
            # self.instances_one_sample dict
            link_table_instance = model(
                **self.gather_instances_for(type_table)
            )
            # all those tables are linked to the report sample table to store them
            # accordingly
            self.instances_one_sample["report_sample"].append(link_table_instance)
            return link_table_instance
        else:
            return

    def gather_instances_for(self, type_table: str) -> Dict:
        """ Gather the instances for the given type table using the
        self.instances_one_sample keys

        Args:
            type_table (str): Name of the table

        Returns:
            Dict: Dict containing the instance name and the instance itself for
            the given type table
        """

        return {
            instance._meta.model.__name__.lower(): instance
            for link_table, instances in self.instances_one_sample.items()
            for instance in instances
            if link_table == type_table
        }

    def import_instances(self):
        """ Loop through all the samples and their instances to import them """

        for sample, instances in self.all_instances.items():
            for instance in instances:
                instance.save()
