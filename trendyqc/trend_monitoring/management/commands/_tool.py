import json
from pathlib import Path


class Tool:
    def __init__(
        self, tool_name: str, config_dir: Path, multiqc_field: str,
        subtool: str = None
    ):
        """ Initialize Tool object with the tool name, its subtool
        (if it exists) and the config directory

        Args:
            tool_name (str): Tool name
            config_dir (Path): Pathlib Path pointing to the config folder where
            the tool object will find its config file
            multiqc_field (str): Name of the multiqc field containing data for
            that tool
            subtool (str, optional): Subtool name if it has one. Defaults to None.
        """

        self.name = tool_name
        self.multiqc_field_name = multiqc_field
        self.subtool = subtool
        self.parent = None
        self.children = []
        self.happy_type = ""
        self.model = None

        if subtool:
            self.parent = tool_name

        self.config_path = config_dir / "tool_configs" / f"{tool_name}.json"
        self.read_config_data()

    def read_config_data(self):
        """ Read in the data in the tool config file """

        fields = json.loads(self.config_path.read_text())

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
            multiqc_data (dict): Dict containing the MultiQC data for a
                specific tool

        Returns:
            dict: Same dict as the tool data but with the appropriate field
            names
        """

        converted_data = {}

        # loop through the data fields in MultiQC
        for field, data in multiqc_data.items():
            # check if the multiqc field exists in our config mapping file
            if field in self.fields:
                # use the name in the mapping i.e. how the fields are named in
                # the models to build a new dict
                converted_data[self.fields[field]] = data

        # list of bool to know if all expected fields are present
        check_fields = [
            True if field in converted_data else False
            for field in self.fields.values()
        ]

        # bool to know if all fields are present
        fields_all_present = all(check_fields)
        # bool to know if we have at least one field
        some_fields_present = any(check_fields)

        # check if we have some fields but not all
        if not fields_all_present and some_fields_present:
            # some tools don't provide all the fields they are supposed to
            # provide so check if we have all the fields that we want and add
            # them if we are missing them
            for field in self.fields.values():
                if field not in converted_data:
                    converted_data[field] = "NA"

        return converted_data

    def set_happy_type(self, happy_type):
        self.happy_type = happy_type

    def set_model(self, model):
        self.model = model
