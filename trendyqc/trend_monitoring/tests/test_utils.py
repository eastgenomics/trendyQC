from math import nan
import unittest

from trend_monitoring.management.commands.utils._utils import (
    clean_value, clean_sample_naming
)

class TestUtils(unittest.TestCase):
    """ This class will test the utils type functions """

    def shortDescription(self):
        doc = [ele.strip() for ele in self._testMethodDoc.strip().split("\n")]
        return "\n".join(doc) or None

    def test_cleaning_multiqc_data_correct_values(self):
        """ Test to assess the various outcomes of the clean value function in 
        the MultiQC_report class
        """

        test_and_expected_values = (
            [None, None],
            ["?", None],
            ["NA", None],
            ["str", "str"],
            [nan, None],
            [1.0, 1.0],
            ["1.0", 1.0],
            [1, 1],
            ["1", 1]
        )

        for test_parameter, expected_value in test_and_expected_values:
            with self.subTest(f"Testing {test_parameter}"):
                test_value = clean_value(test_parameter)
                self.assertEqual(test_value, expected_value)

    def test_cleaning_sample_names(self):
        """ Test to check if the merging of sample names works properly """

        test_data = {
            "NA12878-NA12878": {"tool1": "dummy_data"},
            "NA12878": {"tool2": "dummy_data"},
            "NA12878-NA12878-TWE-F": {"tool3": "dummy_data"}
        }

        expected_data = {
            "NA12878": {
                "tool1": "dummy_data",
                "tool2": "dummy_data",
                "tool3": "dummy_data"
            }
        }

        test_return = clean_sample_naming(test_data)
        self.assertEqual(test_return, expected_data)
