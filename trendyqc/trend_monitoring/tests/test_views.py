import json

from django.test import TestCase
from unittest.mock import patch

from trend_monitoring.models.filters import Filter


class TestViews(TestCase):
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

    # def tearDown(self):
    #     for filter_obj in Filter.objects.all():
    #         filter_obj.delete()

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
        self.assertRedirects(response, "/trendyqc/plot/", status_code=302)

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
        self.assertRedirects(response, "/trendyqc/plot/", status_code=302)

    def test_dashboard_post_save_filter(self):
        """ Test dashboard post request for saving filter.
        Check if a save filter request using a filter redirects to the
        dashboard and correctly saves the filter.
        """

        post_data = {
            'assay_select': ['Cancer Endocrine Neurology'],
            'date_start': [''],
            'date_end': [''],
            'metrics_y': ['avg_length'],
            # filter use returns the id of the filter to use
            'save_filter': "Name of filter"
        }
        response = self.client.post("/trendyqc/", post_data)

        created_filter_id = Filter.objects.all()[1]

        # assert the redirection
        with self.subTest("Failed redirection"):
            self.assertRedirects(response, "/trendyqc/", status_code=302)

        # assert the saving of the filter
        with self.subTest("Failed saving of filter"):
            self.assertEqual(created_filter_id.name, "Name of filter")
            self.assertEqual(created_filter_id.user, "")
            self.assertEqual(created_filter_id.content, json.dumps(
                {
                    'assay_select': ['Cancer Endocrine Neurology'],
                    'metrics_y': ['avg_length']
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
            self.assertRedirects(response, "/trendyqc/", status_code=302)

        # assert the deletion of the filter worked
        with self.subTest("Failed deletion of filter"):
            with self.assertRaises(Filter.DoesNotExist):
                Filter.objects.get(id=filter_id_to_delete)

    def test_plot_get_with_empty_form(self):
        self.client.session["form"] = None
        response = self.client.get("/trendyqc/plot/")
        self.assertRedirects(response, "/trendyqc/plot/", status_code=200)
