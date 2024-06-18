import json

from django.test import TestCase
from unittest.mock import patch

from trend_monitoring.models.filters import Filter


class TestDashboard(TestCase):
    """ Suite of tests to test the backend functionality """

    def setUp(self):
        """ Create a test filter to be used in the tests """
        json_dict = {
            "assay_select": "Cancer Endocrine Neurology",
            "metrics_y": "avg_length"
        }

        filter_obj = Filter.objects.create(
            name="Filter1",
            user="User1",
            content=json.dumps(json_dict)
        )
        filter_obj.save()

    @patch("trend_monitoring.views.Dashboard._get_context_data")
    def test_dashboard_get(self, mock_context_data):
        """ Test dashboard get request.
        Check whether the scrolling menus contain the appropriate data.

        Args:
            mock_context_data (patch): Mock the context data
        """

        mock_context_data.return_value = {
            "assays": ["CEN", "TSO500"],
            "tables": [],
            "project_names": ["Project1", "Project2"],
            "sequencer_ids": ["Sequencer1", "Sequencer2"],
            "metrics": ["Metric1", "Metric2"]
        }
        response = self.client.get("/trendyqc/")
        self.assertEqual(response.status_code, 200)

        context = response.context

        # Test for the assay scrolling menu
        with self.subTest():
            self.assertEqual(context["assays"], ["CEN", "TSO500"])

        # Test for the project names scrolling menu
        with self.subTest():
            self.assertEqual(
                context["project_names"], ["Project1", "Project2"]
            )

        # Test for the sequencer ids scrolling menu
        with self.subTest():
            self.assertEqual(
                context["sequencer_ids"], ["Sequencer1", "Sequencer2"]
            )

        # Test for the metrics scrolling menu
        with self.subTest():
            self.assertEqual(context["metrics"], ["Metric1", "Metric2"])

    def test_dashboard_post_plot(self):
        """ Test dashboard post request for plotting.
        Check if a plotting request redirects to the plot URL.
        """

        post_data = {
            'assay_select': ['Cancer Endocrine Neurology'],
            'date_start': [''],
            'date_end': [''],
            'metrics_y': ['avg_length'],
            # post plot response
            'plot': ['Plot']
        }
        response = self.client.post("/trendyqc/", post_data)
        self.assertRedirects(response, "/trendyqc/plot/")

    def test_dashboard_post_plot_filter(self):
        """ Test dashboard post request for plotting using filter.
        Check if a plotting request using a filter redirects to the plot URL.
        """

        post_data = {
            'assay_select': ['Cancer Endocrine Neurology'],
            'date_start': [''],
            'date_end': [''],
            'metrics_y': ['avg_length'],
            # filter use returns the id of the filter to use
            'filter_use': Filter.objects.all()[0].id
        }
        response = self.client.post("/trendyqc/", post_data)
        self.assertRedirects(response, "/trendyqc/plot/")

    def test_dashboard_post_save_filter(self):
        """ Test dashboard post request for saving filter.
        Check if a save filter request using a filter redirects to the
        dashboard and correctly saves the filter.
        """

        post_data = {
            'assay_select': ['Cancer Endocrine Neurology'],
            'date_start': [''],
            'date_end': [''],
            'metrics_y': ['FastQC|avg_length'],
            # filter use returns the id of the filter to use
            'save_filter': "Name of filter"
        }
        response = self.client.post("/trendyqc/", post_data)

        created_filter_id = Filter.objects.all()[1]

        # assert the redirection
        with self.subTest("Failed redirection"):
            self.assertRedirects(response, "/trendyqc/")

        # assert the saving of the filter
        with self.subTest("Failed saving of filter"):
            self.assertEqual(created_filter_id.name, "Name of filter")
            self.assertEqual(created_filter_id.user, "")
            self.assertEqual(created_filter_id.content, json.dumps(
                {
                    'assay_select': ['Cancer Endocrine Neurology'],
                    'metrics_y': ['read_data|avg_length']
                }
            ))

    def test_dashboard_post_delete_filter(self):
        """ Test dashboard post request for deleting filter """

        filter_id_to_delete = Filter.objects.all()[0].id

        post_data = {
            'assay_select': [''],
            'date_start': [''],
            'date_end': [''],
            'metrics_y': [''],
            # filter use returns the id of the filter to delete
            'delete_filter': filter_id_to_delete
        }
        response = self.client.post("/trendyqc/", post_data)

        # assert the redirection
        with self.subTest("Failed redirection"):
            self.assertRedirects(response, "/trendyqc/")

        # assert the deletion of the filter worked
        with self.subTest("Failed deletion of filter"):
            with self.assertRaises(Filter.DoesNotExist):
                Filter.objects.get(id=filter_id_to_delete)


class TestPlot(TestCase):
    """ Suite of tests for the Plot view """

    def setUp(self):
        self.expected_keys = [
            "form",
            "plot",
            "is_grouped",
            "y_axis",
            "skipped_projects",
            "skipped_samples"
        ]

    @patch("trend_monitoring.views.format_data_for_plotly_js")
    @patch("trend_monitoring.views.get_data_for_plotting")
    @patch("trend_monitoring.views.get_subset_queryset")
    @patch("trend_monitoring.views.prepare_filter_data")
    def test_plot_get_with_filled_form_end_to_end(
        self,
        mock_filter_data,
        mock_queryset,
        mock_plotting_data,
        mock_plotly_js
    ):
        """ Test for GET request in Plot class view.
        This test contains a correct filled form to reach the final render
        return.
        The context data contains 2 identical elements for some reason and
        inside those elements the context data I'm interested in is a
        dictionary with the expected keys.

        Args:
            mock_filter_data (Mock): Mock for the prepare_filter_data
            mock_queryset (Mock): Mock for the get_subset_queryset
            mock_plotting_data (Mock): Mock for the get_data_for_plotting
            mock_plotly_js (Mock): Mock for the format_data_for_plotly_js
        """

        # I use the session to send data to the Plot view, as posting using the
        # normal URL dispatcher with the amount of parameters i have, sounds
        # like a nightmare
        session = self.client.session
        session["form"] = {"k1": "v1", "k2": "v2"}
        session.save()

        mock_filter_data.return_value = {"subset": "", "y_axis": ""}
        mock_queryset.return_value = "not None"
        mock_plotting_data.return_value = (
            ["mock dataframe"],
            {},
            {}
        )
        mock_plotly_js.return_value = (
            [
                {
                    "x0": "project1",
                    "y": ["value1", "value2"],
                    "name": "230523",
                    "type": "box",
                    "text": ["sample1", "sample2"],
                    "boxpoints": "suspectedoutliers",
                    "marker": {
                        "color": "ff1c4d",
                    }
                },
                {
                    "x0": "project2",
                    "y": ["value1", "value2"],
                    "name": "220523",
                    "type": "box",
                    "text": ["sample3", "sample4"],
                    "boxpoints": "suspectedoutliers",
                    "marker": {
                        "color": "ff1c4d",
                    }
                }
            ],
            False
        )

        expected_context = {
            'form': {'k1': ['v1'], 'k2': ['v2']},
            'plot': [
                {
                    'x0': 'project1',
                    'y': ['value1', 'value2'],
                    'name': '230523',
                    'type': 'box',
                    'text': ['sample1', 'sample2'],
                    'boxpoints': 'suspectedoutliers',
                    'marker': {'color': 'ff1c4d'}
                },
                {
                    'x0': 'project2',
                    'y': ['value1', 'value2'],
                    'name': '220523',
                    'type': 'box',
                    'text': ['sample3', 'sample4'],
                    'boxpoints': 'suspectedoutliers',
                    'marker': {'color': 'ff1c4d'}
                }
            ],
            'is_grouped': False,
            'y_axis': '',
            'skipped_projects': {},
            'skipped_samples': {}
        }

        response = self.client.get("/trendyqc/plot/", follow=True)

        with self.subTest("Status code test"):
            self.assertEqual(response.status_code, 200)

        found_expected_dict = False

        with self.subTest("Context data content test"):
            # for some reason i get 2 identical elements in the context data so
            # I need to loop to check one if the context data content
            for context_data in response.context:
                for info in context_data:
                    if isinstance(info, dict):
                        # check if all the expected keys are present in the
                        # element
                        if all([
                            True if info.get(key, None) is not None else False
                            for key in self.expected_keys
                        ]):
                            found_expected_dict = True

                            for key in self.expected_keys:
                                self.assertEqual(
                                    info[key], expected_context[key]
                                )
                self.assertEqual(
                    found_expected_dict,
                    True,
                    "Didn't find the dict containing all the expected keys"
                )
                break

    def test_plot_get_with_empty_form(self):
        """ Test for GET request in Plot class view.
        This test contains a empty form to reach the render return without
        context data.
        """

        session = self.client.session
        self.client.session["form"] = None
        session.save()

        response = self.client.get("/trendyqc/plot/")

        with self.subTest("Status code test"):
            self.assertEqual(response.status_code, 200)

        with self.subTest("Context data content test"):
            flag_to_test_presence = False

            # for some reason i get 2 identical elements in the context data so
            # I need to loop to check one if the context data content
            for context_data in response.context:
                for info in context_data:
                    if isinstance(info, dict):
                        # check if all the expected keys are present in the
                        # element
                        if all([
                            True if info.get(key, None) is not None else False
                            for key in self.expected_keys
                        ]):
                            flag_to_test_presence = True

            self.assertEqual(flag_to_test_presence, False)
