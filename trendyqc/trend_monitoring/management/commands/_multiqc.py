from datetime import datetime
import json
from typing import Dict

import dxpy

from ._parsing import load_assay_config, load_tool_config


class MultiQC_report():
    def __init__(self, multiqc_report: dxpy.DXFile) -> None:
        self.dnanexus_report = multiqc_report
        self.original_data = json.loads(multiqc_report.read())
        self.assay = self.original_data["config_subtitle"]
        # load the suite of tools that is used for the report's assay
        self.suite_of_tools = load_assay_config(self.assay)
        self.data = self.parse_multiqc_report()
        self.get_metadata()

    def parse_multiqc_report(self) -> Dict:
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

        Returns:
            dict: Dict containing the relevant data from MultiQC
        """

        data = {}
        raw_data = self.original_data["report_saved_raw_data"]

        for multiqc_field, tool_metadata in self.suite_of_tools.items():
            tool, subtool = tool_metadata
            assert multiqc_field in raw_data, (
                f"{multiqc_field} doesn't exist in the multiqc report"
            )
            data_all_samples = raw_data[multiqc_field]
            # load multiqc fields and the models fields that they will be
            # replaced with
            tool_config = load_tool_config(tool, subtool)

            for sample, tool_data in data_all_samples.items():
                if sample == "undetermined":
                    continue

                # convert the multiqc fields name for ease the import in the db
                converted_fields = self.convert_tool_fields(
                    tool_data, tool_config
                )

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

                data.setdefault(sample_id, {})
                data[sample_id].setdefault(tool, {})

                if subtool:
                    tool_key = f"{tool}-{subtool}"
                else:
                    tool_key = tool

                # fastqc needs a new level to take into account the lane and
                # the read
                if tool == "fastqc":
                    data[sample_id][tool_key][f"{lane}_{read}"] = converted_fields
                else:
                    data[sample_id][tool_key] = converted_fields

        return data

    def convert_tool_fields(self, tool_data: Dict, tool_config: Dict) -> Dict:
        """ Convert the field names from MultiQC to ones that are written in
        the Django models
        i.e.
        {
            "Filter_indel": data,
            "TRUTH.TOTAL_indel": data_also
        }

        to

        {
            "filter_indel": data,
            "truth_total_indel": data_also
        }

        Args:
            tool_data (dict): Dict containing the MultiQC data for a specific
            tool
            tool_config (dict): Dict containing the field names from MultiQC
            and what they need to be replaced with for that specific tool

        Returns:
            dict: Same dict as the tool data but with the appropriate field
            names
        """

        converted_data = {}

        for field, data in tool_data.items():
            if field in tool_config:
                converted_data[tool_config[field]] = data

        return converted_data

    def get_metadata(self) -> Dict:
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
