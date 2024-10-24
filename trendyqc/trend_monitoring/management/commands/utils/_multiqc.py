from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
from typing import Dict, List

import dxpy
import regex

from django.apps import apps
from django.db import transaction
from django.db.models import Model
from django.db.utils import IntegrityError

from ._check import already_in_db
from ._parsing import load_assay_config
from ._tool import Tool
from ._utils import clean_value, clean_sample_naming

# returns the /trendyqc/trend_monitoring/management folder
BASE_DIR_MANAGEMENT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR_MANAGEMENT / "configs"


class MultiQC_report:
    def __init__(self, **kwargs) -> None:
        """Initialize MultiQC report

        Args:
            Expected kwargs are:
            - multiqc_report_id: DNAnexus multiqc report id
            - multiqc_project_id: DNAnexus project id of report
            - multiqc_job_id: DNAnexus multiqc job id
            - data: Data contained in the MultiQC json file
        """

        self.messages = []
        self.multiqc_json_id = kwargs.get("multiqc_report_id", None)
        self.project_id = kwargs.get("multiqc_project_id", None)
        self.job_id = kwargs.get("multiqc_job_id", None)
        data = kwargs.get("data", None)

        if not all([self.multiqc_json_id, self.project_id, self.job_id, data]):
            self.is_importable = False
        else:
            self.original_data = json.loads(data)
            self.assay = self.original_data.get("config_subtitle", None)
            self.is_importable = True
            # Store the Django models as a dict of model names to model objects
            self.models = {
                model.__name__.lower(): model for model in apps.get_models()
            }

            # skip projects for which we don't have a config subtitle
            if not self.assay:
                msg = (
                    "The gathered assay name in "
                    "the MultiQC JSON ('config_subtitle') is not present in "
                    "the trendyqc/trend_monitoring/management/configs/assays.json. "
                    "Skipping.."
                )
                self.is_importable = False
                self.messages.append((msg, "warning"))
            else:
                # load the report's assay tools and the fields they are
                # associated with
                try:
                    self.assay_data = load_assay_config(self.assay, CONFIG_DIR)
                except Exception:
                    msg = (
                        f"Failed to load the assay config:\n"
                        f"```{traceback.format_exc()}```"
                    )
                    self.messages.append((msg, "error"))
                    self.is_importable = False
                    return

                self.get_metadata()

                # check if the report is already in the database
                if already_in_db(
                    self.models["report"],
                    name=self.report_name,
                    dnanexus_file_id=self.multiqc_json_id,
                ):
                    self.is_importable = False
                    msg = (
                        "Has already been imported in "
                        "the database. Skipping.."
                    )
                    self.messages.append((msg, "warning"))

        if self.is_importable:
            self.setup_tools()
            self.map_models_to_tools()
            self.parse_multiqc_report()
            self.data = clean_sample_naming(self.data)
            self.create_all_instances()

    def setup_tools(self):
        """Create tools for use when parsing the MultiQC data and store them
        in self.tools"""

        self.tools = []
        multiqc_raw_data = self.original_data["report_saved_raw_data"]

        for multiqc_field_in_config, tool_metadata in self.assay_data.items():
            if multiqc_field_in_config not in multiqc_raw_data:
                self.messages.append(
                    (
                        (
                            f"`{multiqc_field_in_config}` not "
                            "present in report"
                        ),
                        "warning",
                    )
                )
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
                happy_tool.set_happy_type("PASS")
                self.tools.append(happy_tool)

                happy_tool = Tool(
                    tool, CONFIG_DIR, multiqc_field_in_config, subtool
                )
                happy_tool.set_happy_type("ALL")
                self.tools.append(happy_tool)
            else:
                tool_obj = Tool(
                    tool, CONFIG_DIR, multiqc_field_in_config, subtool
                )
                self.tools.append(tool_obj)

    def parse_multiqc_report(self):
        """Parse the multiqc report for easy import
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

                # some tools contain data at the lane and read level
                if tool_obj.divided_by_lane_read:
                    # look for the order, lane and read using regex
                    match = regex.search(
                        r"_(?P<order>S[0-9]+)_(?P<lane>L[0-9]+)_(?P<read>R[12])",
                        sample,
                    )

                    if match:
                        # use the regex matching to get the sample id
                        potential_sample_id = sample[: match.start()]
                        # find every component of the sample id
                        matches = regex.findall(
                            r"([a-zA-Z0-9]+)", potential_sample_id
                        )
                        # and join them using dashes (to fix potential errors
                        # in the sample naming)
                        sample_id = "-".join(matches)
                        lane = match.groupdict()["lane"]
                        read = match.groupdict()["read"]
                        lane_read = f"{lane}_{read}"
                    else:
                        # give up on the samples that don't have lane and read
                        sample_id = sample
                        lane = ""
                        read = ""
                        lane_read = f"{lane}_{read}"
                else:
                    # some tools provide the order in the sample name, so find
                    # that element
                    match = regex.search(r"_(?P<order>S[0-9]+)", sample)

                    if match:
                        # and get the sample id remaining
                        potential_sample_id = sample[: match.start()]
                    else:
                        # remove the happy suffixes, they were causing issues
                        # because it had a longer sample name breaking the
                        # merging of data under one sample id
                        sample = regex.sub(
                            "_INDEL_PASS|_INDEL_ALL|_SNP_PASS|_SNP_ALL",
                            "",
                            sample,
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

                # some tools need a new level to take into account the lane and
                # the read
                if tool_obj.divided_by_lane_read:
                    self.data[sample_id][tool_obj].setdefault(lane_read, {})
                    self.data[sample_id][tool_obj][lane_read] = {
                        **self.data[sample_id][tool_obj][lane_read],
                        **cleaned_data,
                    }

                elif tool_name == "happy":
                    if tool_obj.happy_type in cleaned_data.values():
                        self.data[sample_id][tool_obj] = {
                            **self.data[sample_id][tool_obj],
                            **cleaned_data,
                        }

                else:
                    self.data[sample_id][tool_obj] = {
                        **self.data[sample_id][tool_obj],
                        **cleaned_data,
                    }

    def get_metadata(self):
        """Get the metadata from the MultiQC DNAnexus object"""

        project_obj = dxpy.DXProject(self.project_id)
        self.project_name = project_obj.name
        project_date = self.project_name.split("_")[1]

        # get the sequencer id
        self.sequencer_id = self.project_name.split("_")[2]

        # get the job object
        report_job = dxpy.DXJob(self.job_id)
        # get the file id for the HTML report and save the DXFile object
        html_report = dxpy.DXFile(
            report_job.describe()["output"]["multiqc_html_report"][
                "$dnanexus_link"
            ]
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
            self.date = datetime.strptime(project_date, "%y%m%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            # if the format of the date is wrong, use the job date as the date
            # of the run
            self.date = self.datetime_job

    def map_models_to_tools(self):
        """Map Django models to tools. Store that info in the appropriate
        tool object"""

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
                self.messages.append(
                    (
                        (
                            f"`{tool.name}` matches multiple "
                            f"model names -> {matches}"
                        ),
                        "warning",
                    )
                )

    def clean_data(self, data: Dict) -> Dict:
        """Loop through the fields and values for one tool and clean the
        values

        Args:
            data (Dict): Dict containing the fields and values of a Tool

        Returns:
            Dict: Dict with cleaned data
        """

        return {field: clean_value(value) for field, value in data.items()}

    def create_all_instances(self):
        """Create instances for everything that needs to get imported

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

            for type_table in ["fastqc", "picard", "happy"]:
                link_table = self.create_link_table_instance(type_table)

                # picard and happy are not used for every assay
                if link_table:
                    self.all_instances[sample].append(link_table)

            report_sample_data = {**self.gather_instances_for("report_sample")}
            report_sample_data["assay"] = self.assay

            # get the report sample model object and instanciate using the
            # instances that were gathered previously
            report_sample_instance = self.models["report_sample"](
                **report_sample_data
            )

            self.all_instances[sample].append(report_sample_instance)

    def create_tool_data_instance(
        self, tool_obj: Tool, tool_data: dict
    ) -> List:
        """Create tool data instance. Uses the tool data structure to check
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
        # if all(isinstance(i, dict) for i in tool_data.values()):
        if tool_obj.divided_by_lane_read:
            for read, data in tool_data.items():
                sample_lane, sample_read = read.split("_")
                # this info is not available in the FastQC data so I create it
                # myself
                data["lane"] = sample_lane
                data["sample_read"] = sample_read
                model_instance = model(**data)
                # store the fastqc instances using their parent table i.e.
                # fastqc as key
                self.instances_per_sample[tool_obj.parent].append(
                    model_instance
                )
                instances_to_return.append(model_instance)
        else:
            model_instance = model(**tool_data)

            if tool_obj.parent:
                # store these tools using their parent table name as key
                self.instances_per_sample[tool_obj.parent].append(
                    model_instance
                )
            else:
                # if they have no parent that means that their parent is
                # directly the report sample table so use that as the key
                self.instances_per_sample["report_sample"].append(
                    model_instance
                )

            instances_to_return.append(model_instance)

        return instances_to_return

    def create_sample_instance(self, sample_id: str) -> Model:
        """Create the sample instance.

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
        """Create the report instance using data gathered when initialising
        the report

        Returns:
            Model: Instance object of Report Model
        """

        report = self.models["report"]
        report_instance = report(
            name=self.report_name,
            project_name=self.project_name,
            project_id=self.project_id,
            date=self.date,
            sequencer_id=self.sequencer_id,
            job_date=self.datetime_job,
            dnanexus_file_id=self.multiqc_json_id,
        )
        return report_instance

    def create_link_table_instance(self, type_table: str) -> Model:
        """Create the instances for the tables that have foreign keys i.e.
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
            # all those tables are linked to the report sample table to store
            # them accordingly
            self.instances_per_sample["report_sample"].append(
                link_table_instance
            )

            return link_table_instance
        else:
            return

    def gather_instances_for(self, type_table: str) -> Dict:
        """Gather the instances for the given type table using the
        self.instances_per_sample keys

        Args:
            type_table (str): Name of the table

        Returns:
            Dict: Dict containing the instance name and the instance itself for
            the given type table
        """

        instance_type_tables = {}
        lane_dict = {0: "1st_lane", 1: "2nd_lane"}

        # go through the instances stored for one sample
        for link_table, instances in self.instances_per_sample.items():
            lane_instances = {}

            # if the instances are the type "link_table"
            if link_table == type_table:
                for instance in instances:
                    model_name = instance._meta.model.__name__.lower()
                    # check if the tool linked to the model has a subtool i.e.
                    # a requirement for models that have data divided by lane
                    # and read
                    tool_with_subtool = [
                        tool
                        for tool in self.tools
                        if model_name == tool.subtool
                    ]

                    if tool_with_subtool:
                        tool = tool_with_subtool[0]

                        # if the data requires the data to be separated by lane
                        # and read the tool contains this information and
                        # requires the creation of 4 distinct instances
                        if tool.divided_by_lane_read:
                            lane = instance.lane
                            lane_instances.setdefault(lane, []).append(
                                [tool.subtool, instance]
                            )

                        else:
                            # i.e. picard_hs_metrics has a picard parent but is
                            # not separated by lane and read
                            instance_type_tables[model_name] = instance
                    else:
                        # i.e. somalier doesn't have a parent
                        instance_type_tables[model_name] = instance

            # check if lane and read info has been detected and added
            if lane_instances:
                if len(lane_instances) > 2:
                    self.messages.append(
                        (("Contains more than 2 lanes"), "warning")
                    )

                # order the lanes for addition
                ordered_lanes = sorted(lane_instances)

                for i, lane in enumerate(ordered_lanes):
                    # find out if the lane is the 1st or 2nd one
                    lane_in_model = lane_dict[i]

                    for subtool, instance in lane_instances[lane]:
                        read = instance.sample_read
                        instance_type_tables[
                            f"{subtool}_{lane_in_model}_{read}"
                        ] = instance

        return instance_type_tables

    @transaction.atomic
    def import_instances(self):
        """Loop through all the samples and their instances to import them"""

        for sample, instances in self.all_instances.items():
            for instance in instances:
                try:
                    instance.save()
                except IntegrityError as e:
                    instance_model_name = type(instance).__name__
                    msg = (
                        "Could not be imported because of "
                        f"{instance_model_name}:\n{e}"
                    )
                    self.messages.append((msg, "error"))

    def add_msg(self, msg, type_msg="error"):
        """Add messages usually error to the report object

        Args:
            msg (str): Message to store
            type_msg (str): Type of message for handling later.
            Defaults "error"
        """

        self.messages.append((msg, type_msg))
