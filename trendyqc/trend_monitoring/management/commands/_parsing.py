import json
from typing import Dict


def load_assay_config(assay_name: str, config_dir) -> Dict:
    """ Read and load the assays.json

    Args:
        assay_name (str): Assay name to return the appropriate data in the
        assays.json

    Returns:
        dict: Dict with the MultiQC fields and tool names to load the
        appropriate subsequent JSON
    """

    assay_config = config_dir / "assays.json"
    data = json.loads(assay_config.read_text())
    assert assay_name in data, (
        f"{assay_name} is not present in the assay config file"
    )
    return data[assay_name]
