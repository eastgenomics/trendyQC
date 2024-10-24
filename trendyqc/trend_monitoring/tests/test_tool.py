import json
import unittest

from trend_monitoring.management.commands.utils._tool import Tool
from trendyqc.settings import BASE_DIR


class TestTool(unittest.TestCase):
    """Test class for the tools.

    Setup:
    - get the configuration directory for use when setting up the tool
    - read in the test tool data for matching the inputs to the Tool object to
    the expected MultiQC fields

    Tests:
    - Check that the fields for a given Tool object match the ones gathered in
    the configuration files
    """

    def setUp(self):
        # config directory path
        self.config_dir = (
            BASE_DIR / "trend_monitoring" / "management" / "configs"
        )

        test_tool_data_file = (
            BASE_DIR
            / "trend_monitoring"
            / "tests"
            / "test_data"
            / "tools.json"
        )

        with open(test_tool_data_file) as f:
            # tools dict containing the arguments necessary to setup the tool
            # objects and the expected fields from the JSON files
            self.tools = json.loads(f.read())

    def test_tools(self):
        """Check the fields that the tools objects extract from the config
        JSON files. This will catch changes in the configuration files that
        might occur in the future
        """

        for tool in self.tools:
            test_tool_dict, expected_fields = self.tools[tool]
            test_tool = Tool(config_dir=self.config_dir, **test_tool_dict)

            with self.subTest(f"Testing {tool} fields"):
                self.assertEqual(test_tool.fields, expected_fields)
