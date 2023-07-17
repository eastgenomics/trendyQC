import json
from pathlib import Path
from typing import Dict

import dxpy

# returns the /trendyqc/trend_monitoring/management folder
BASE_DIR_MANAGEMENT = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR_MANAGEMENT / "configs"


def parse_multiqc_report(multiqc_report: dxpy.DXFile) -> Dict:
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

    Args:
        multiqc_report (dxpy.DXFile): DXFile object pointing to a MultiQC
        report

    Returns:
        dict: Dict containing the relevant data from MultiQC
    """

    data = {}

    # read in the data in the DXFile and build a dict using the json package
    multiqc_data = json.loads(multiqc_report.read())

    raw_data = multiqc_data["report_saved_raw_data"]
    # load the suite of tools that is used for the report's assay
    suite_of_tools = load_assay_config(multiqc_data["config_subtitle"])

    for multiqc_field, tool_metadata in suite_of_tools.items():
        tool, subtool = tool_metadata
        data_all_samples = raw_data[multiqc_field]
        # load multiqc fields and the models fields that they will be replaced
        # with
        tool_config = load_tool_config(tool, subtool)

        for sample, tool_data in data_all_samples.items():
            # convert the multiqc fields name for ease the import in the db
            converted_fields = convert_tool_fields(tool_data, tool_config)

            # fastqc contains data at the lane and read level
            if tool == "fastqc":
                sample_id, order, lane, read = sample.split("_")
            else:
                sample_id = sample

            data.setdefault(sample_id, {})
            data[sample_id].setdefault(tool, {})

            # fastqc needs a new level to take into account the lane and the
            # read
            if tool == "fastqc":
                data[sample_id][tool][f"{lane}_{read}"] = converted_fields
            else:
                data[sample_id][tool] = converted_fields

    return data


def convert_tool_fields(tool_data: Dict, tool_config: Dict) -> Dict:
    """ Convert the field names from MultiQC to ones that are written in the
    Django models
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
        tool_data (dict): Dict containing the MultiQC data for a specific tool
        tool_config (dict): Dict containing the field names from MultiQC and
        what they need to be replaced with for that specific tool

    Returns:
        dict: Same dict as the tool data but with the appropriate field names
    """

    converted_data = {}

    for field, data in tool_data.items():
        if field in tool_config:
            converted_data[tool_config[field]] = data

    return converted_data


def load_tool_config(tool_name: str, subtool: str = None) -> Dict:
    """ Read in the tool config and store it as a json

    Args:
        tool_name (str): Tool name i.e. Picard
        subtool (str, optional): Subtool name i.e. hs_metrics
        Defaults to None.

    Returns:
        dict: Dict containing the MultiQC fields and the fields from the models
    """

    tool_config = CONFIG_DIR / "tool_configs" / f"{tool_name}.json"
    data = json.loads(tool_config.read_text())

    if subtool:
        return data[subtool]

    return data


def load_assay_config(assay_name: str) -> Dict:
    """ Read and load the assays.json

    Args:
        assay_name (str): Assay name to return the appropriate data in the
        assays.json

    Returns:
        dict: Dict with the MultiQC fields and tool names to load the
        appropriate subsequent JSON
    """

    assay_config = CONFIG_DIR / "assays.json"
    data = json.loads(assay_config.read_text())
    return data[assay_name]
