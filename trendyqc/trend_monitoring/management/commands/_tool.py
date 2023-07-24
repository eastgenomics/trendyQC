import json
from pathlib import Path


class Tool:
    def __init__(self, tool_name: str, config_dir: Path, subtool: str = None):
        self.name = tool_name
        self.subtool = subtool

        if subtool:
            self.parent = tool_name

        self.config = config_dir / "tool_configs" / f"{tool_name}.json"
        self.read_config_data()

    def read_config_data(self):
        fields = json.loads(self.config.read_text())

        if self.subtool:
            self.fields = fields[self.subtool]
        else:
            self.fields = fields

    def convert_tool_fields(self, multiqc_data):
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

        Returns:
            dict: Same dict as the tool data but with the appropriate field
            names
        """

        converted_data = {}

        for field, data in multiqc_data.items():
            if field in self.fields:
                converted_data[self.fields[field]] = data

        return converted_data
