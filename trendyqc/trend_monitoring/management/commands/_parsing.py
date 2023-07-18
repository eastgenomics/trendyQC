import json
from pathlib import Path
from typing import Dict

# returns the /trendyqc/trend_monitoring/management folder
BASE_DIR_MANAGEMENT = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR_MANAGEMENT / "configs"


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
    assert assay_name in data, (
        f"{assay_name} is not present in the assay config file"
    )
    return data[assay_name]
