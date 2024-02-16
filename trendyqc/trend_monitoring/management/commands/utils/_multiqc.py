from collections import defaultdict
from datetime import datetime
import logging
import json
from pathlib import Path
from typing import Dict, List

import dxpy
import regex

from django.apps import apps
from django.db import transaction
from django.db.models import Model
from django.utils import timezone

from ._check import already_in_db
from ._parsing import load_assay_config
from ._tool import Tool
from ._utils import clean_value, clean_sample_naming

# returns the /trendyqc/trend_monitoring/management folder
BASE_DIR_MANAGEMENT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR_MANAGEMENT / "configs"

logger = logging.getLogger("basic")


class MultiQC_report():
    def __init__(
        self,
        multiqc_report_id: str,
        multiqc_project_id: str,
        multiqc_job_id: str,
        data: str
    ) -> None:
        """ Initialize MultiQC report

        Args:
            multiqc_report_id (str): DNAnexus file id for MultiQC report data
            multiqc_project_id (str): DNAnexus project id for MultiQC report
            data
            multiqc_job_id (str): DNAnexus job id for MultiQC report data
            data (str): Content of MultiQC report data 
        """

        self.project_id = multiqc_project_id
        self.multiqc_json_id = multiqc_report_id
        self.job_id = multiqc_job_id

        self.original_data = json.loads(data)
        self.assay = self.original_data.get("config_subtitle", None)
        self.is_importable = True
        # Store the Django models as a dict of model names to model objects
        self.models = {
            model.__name__.lower(): model for model in apps.get_models()
        }

        # skip projects for which we don't have a config subtitle
        if self.assay:
            # load the report's assay tools and the fields they are associated
            # with
            self.assay_data = load_assay_config(self.assay, CONFIG_DIR)
            self.get_metadata()

            if already_in_db(
                self.models["report"], dnanexus_file_id=self.multiqc_json_id,
                name=self.report_name
            ):
                self.is_importable = False
                logger.warning((
                    f"{self.multiqc_json_id} has already been imported in the "
                    "database. Skipping.."
                ))
            else:
                self.setup_tools()
                self.parse_multiqc_report()
                self.data = clean_sample_naming(self.data)
                self.map_models_to_tools()
                self.create_all_instances()
        else:
            self.is_importable = False
            logger.warning((
                f"{self.multiqc_json_id}: the gathered assay name in "
                "the MultiQC JSON ('config_subtitle') is not present in the "
                "trendyqc/trend_monitoring/management/configs/assays.json. "
                "Skipping.."
            ))

    def setup_tools(self):
        """ Create tools for use when parsing the MultiQC data and store them
        in self.tools"""

        self.tools = []
        multiqc_raw_data = self.original_data["report_saved_raw_data"]

        for multiqc_field_in_config, tool_metadata in self.assay_data.items():
            if multiqc_field_in_config not in multiqc_raw_data:
                logger.debug((
                    f"{self.multiqc_json_id}: {multiqc_field_in_config} not "
                    "present in report"
                ))
                continue

            # subtool is used to specify for example, HSMetrics or insertSize
            # for Picard. It will equal None if the main tool doesn't have a
            # subtool
            tool, subtool = tool_metadata

            if tool == "happy":
                # setup the happy tools and distinguish that happy has ALL and
                # PASS statuses
                happy_tool = Tool(
                    tool, CONFIG_DIR, multiqc_field_in_config, subtool
                )
                happy_tool.set_happy_type("pass")
                self.tools.append(happy_tool)

                happy_tool = Tool(
                    tool, CONFIG_DIR, multiqc_field_in_config, subtool
                )
                happy_tool.set_happy_type("all")
                self.tools.append(happy_tool)
            else:
                tool_obj = Tool(
                    tool, CONFIG_DIR, multiqc_field_in_config, subtool
                )
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

        for tool_obj in self.tools:
            # subtool is used to specify for example, HSMetrics or insertSize
            # for Picard. It will equal None if the main tool doesn't have a
            # subtool
            tool_name = tool_obj.name
            data_all_samples = multiqc_raw_data[tool_obj.multiqc_field_name]

            for sample, tool_data in data_all_samples.items():
                if sample == "undetermined":
                    continue

                # convert the multiqc fields name for ease the import in the db
                converted_fields = tool_obj.convert_tool_fields(tool_data)

                # SNP genotyping adds a "sorted" in the sample name
                sample = sample.replace("_sorted", "")

                # fastqc contains data at the lane and read level
                if tool_name == "fastqc":
                    # look for the order, lane and read using regex
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
                        # give up on the samples that don't have lane and read
                        sample_id = sample
                        lane = ""
                        read = ""
                else:
                    # some tools provide the order in the sample name, so find
                    # that element
                    match = regex.search(r"_(?P<order>S[0-9]+)", sample)

                    if match:
                        # and get the sample id remaining
                        potential_sample_id = sample[:match.start()]
                    else:
                        # remove the happy suffixes, they were causing issues
                        # because it had a longer sample name breaking the
                        # merging of data under one sample id
                        sample = regex.sub(
                            "_INDEL_PASS|_INDEL_ALL|_SNP_PASS|_SNP_ALL", "",
                            sample
                        )

                        potential_sample_id = sample

                    # same as before, find every element in the sample id
                    matches = regex.findall(
                        r"([a-zA-Z0-9]+)", potential_sample_id
                    )
                    # and join using dashes
                    sample_id = "-".join(matches)

                self.data.setdefault(sample_id, {})
                self.data[sample_id].setdefault(tool_obj, {})

                # convert data in appropriate types for future import
                cleaned_data = self.clean_data(converted_fields)

                # fastqc needs a new level to take into account the lane and
                # the read
                if tool_name == "fastqc":
                    self.data[sample_id][tool_obj][f"{lane}_{read}"] = cleaned_data
                else:
                    self.data[sample_id][tool_obj] = cleaned_data

    def get_metadata(self):
        """ Get the metadata from the MultiQC DNAnexus object """

        project_obj = dxpy.DXProject(self.project_id)
        self.project_name = project_obj.name
        project_date = self.project_name.split("_")[1]

        # get the sequencer id
        self.sequencer_id = self.project_name.split("_")[2]

        # get the job object
        report_job = dxpy.DXJob(self.job_id)
        # get the file id for the HTML report and save the DXFile object
        html_report = dxpy.DXFile(
            report_job.describe()["output"]["multiqc_html_report"]["$dnanexus_link"]
        )
        # get the name of the HTML report
        self.report_name = html_report.describe()["name"]

        # DNAnexus returns a timestamp that includes milliseconds which Python
        # does not handle. So striping the last 3 characters
        creation_timestamp = int(str(report_job.describe()["created"])[:-3])
        self.datetime_job = datetime.fromtimestamp(
            creation_timestamp, tz=timezone.utc
        )

        try:
            self.date = datetime.strptime(
                project_date, "%y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            # if the format of the date is wrong, use the job date as the date
            # of the run
            self.date = self.datetime_job

    def map_models_to_tools(self):
        """ Map Django models to tools. Store that info in the appropriate
        tool object """

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
                logger.warning((
                    f"{self.multiqc_json_id}: {tool.name} matches multiple "
                    f"model names -> {matches}"
                ))

    def clean_data(self, data: Dict) -> Dict:
        """ Loop through the fields and values for one tool and clean the
        values

        Args:
            data (Dict): Dict containing the fields and values of a Tool

        Returns:
            Dict: Dict with cleaned data
        """

        return {
            field: clean_value(value) for field, value in data.items()
        }

    def create_all_instances(self):
        """ Create instances for everything that needs to get imported

        Creates:
            - self.all_instances: Dict containing the sample as keys and the
            values are lists of the instances to import in the correct order
        """

        self.all_instances = {}
        report_instance = self.create_report_instance()

        for sample in self.data:
            # reset the self.instances_per_sample variable to keep
            # instances per sample
            self.instances_per_sample = defaultdict(list)
            self.instances_per_sample["report_sample"].append(report_instance)
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

            fastqc_link_table = self.create_link_table_instance("fastqc")
            picard_instance = self.create_link_table_instance("picard")
            happy_instance = self.create_link_table_instance("happy")

            # check if a fastqc link table was created
            if fastqc_link_table:
                self.all_instances[sample].append(fastqc_link_table)

            # picard and happy are not used for every assay
            if picard_instance:
                self.all_instances[sample].append(picard_instance)

            if happy_instance:
                self.all_instances[sample].append(happy_instance)

            report_sample_data = {**self.gather_instances_for("report_sample")}
            report_sample_data["assay"] = self.assay

            # get the report sample model object and instanciate using the
            # instances that were gathered previously
            report_sample_instance = self.models["report_sample"](
                **report_sample_data
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
                self.instances_per_sample["fastqc"].append(model_instance)
                instances_to_return.append(model_instance)
        else:
            model_instance = model(**tool_data)

            if tool_obj.parent:
                # store these tools using their parent table name as key
                self.instances_per_sample[tool_obj.parent].append(model_instance)
            else:
                # if they have no parent that means that their parent is
                # directly the report sample table so use that as the key
                self.instances_per_sample["report_sample"].append(model_instance)

            instances_to_return.append(model_instance)

        return instances_to_return

    def create_sample_instance(self, sample_id: str) -> Model:
        """ Create the sample instance.

        Args:
            sample (str): Sample id

        Returns:
            Model: Instance object of Sample Model
        """

        sample = self.models["sample"]
        sample_instance = sample(sample_id=sample_id)
        self.instances_per_sample["report_sample"].append(sample_instance)
        return sample_instance

    def create_report_instance(self) -> Model:
        """ Create the report instance using data gathered when initialising
        the report

        Returns:
            Model: Instance object of Report Model
        """

        report = self.models["report"]
        report_instance = report(
            name=self.report_name, project_name=self.project_name,
            project_id=self.project_id, date=self.date,
            sequencer_id=self.sequencer_id, job_date=self.datetime_job,
            dnanexus_file_id=self.multiqc_json_id
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
            # self.instances_per_sample dict
            link_table_instance = model(**instances)
            # all those tables are linked to the report sample table to store them
            # accordingly
            self.instances_per_sample["report_sample"].append(link_table_instance)

            return link_table_instance
        else:
            return

    def gather_instances_for(self, type_table: str) -> Dict:
        """ Gather the instances for the given type table using the
        self.instances_per_sample keys

        Args:
            type_table (str): Name of the table

        Returns:
            Dict: Dict containing the instance name and the instance itself for
            the given type table
        """

        return {
            instance._meta.model.__name__.lower(): instance
            for link_table, instances in self.instances_per_sample.items()
            for instance in instances
            if link_table == type_table
        }

    @transaction.atomic
    def import_instances(self):
        """ Loop through all the samples and their instances to import them """

        for sample, instances in self.all_instances.items():
            for instance in instances:
                instance.save()
