import datetime
import json

from django.contrib import messages
from django.test import TestCase

from trend_monitoring.backend_utils.filtering import (
    import_filter,
    serialize_date,
)
from trend_monitoring.models.filters import Filter


class TestImportFilter(TestCase):
    def test_import_filter_create(self):
        """Test a filter is created correctly"""

        form_data = {
            "save_filter": "info",
            "metric1": "metric_value1",
            "metric2": "metric_value2",
            "metric3": "metric_value3",
        }
        test_output = import_filter("Name_filter1", "User1", form_data)

        expected_output = (
            "Filter Name_filter1 has been created",
            messages.SUCCESS,
        )

        with self.subTest("Test output of function"):
            self.assertEqual(test_output, expected_output)

        with self.subTest("Test filter was saved"):
            Filter.objects.filter(
                name="Name_filter1",
                user="User1",
                content=json.dumps(form_data, default=serialize_date),
            )

    def test_import_filter_already_exists(self):
        """Test if a filter is not created if its name already exists"""

        form_data = {
            "save_filter": "info",
            "metric1": "metric_value1",
            "metric2": "metric_value2",
            "metric3": "metric_value3",
        }
        filter_obj = Filter(
            name="Name_filter2",
            user="User2",
            content=json.dumps(form_data, default=serialize_date),
        )
        filter_obj.save()
        test_output = import_filter("Name_filter2", "User3", form_data)

        expected_output = (
            "Filter Name_filter2 already exists",
            messages.ERROR,
        )

        with self.subTest("Test output of function"):
            self.assertEqual(test_output, expected_output)


class TestSerializeDate(TestCase):
    def test_serialize_date_successful(self):
        """Test successful serialisation of date object"""

        time = datetime.datetime.today()
        test_output = serialize_date(time)
        expected_output = time.isoformat()
        self.assertEqual(test_output, expected_output)

    def test_serialize_date_failed(self):
        """Test failed serialisation of str object"""

        time = "Not a date"

        with self.assertRaisesRegex(
            TypeError, r"^Type <class 'str'> is not a date$"
        ):
            serialize_date(time)
