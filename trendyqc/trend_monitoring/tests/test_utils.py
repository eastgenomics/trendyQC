from math import nan
import unittest

from trend_monitoring.management.commands.utils._multiqc import MultiQC_report

class TestUtils(unittest.TestCase):
    """ This class will test the utils type functions """

    def shortDescription(self):
        doc = [ele.strip() for ele in self._testMethodDoc.strip().split("\n")]
        return "\n".join(doc) or None

    @classmethod
    def setUpClass(cls):
        """ Set up data for use in the only test present right now (will 
        probably evolve in the future to account for other tests)
        """

        cls.test_and_expected_values = (
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

    def test_cleaning_multiqc_data_correct_values(self):
        """ Test to assess the various outcomes of the clean value function in 
        the MultiQC_report class
        """

        for test_parameter, expected_value in self.test_and_expected_values:
            with self.subTest(f"Testing {test_parameter}"):
                test_value = MultiQC_report.clean_value(test_parameter)
                self.assertEqual(test_value, expected_value)