from bs4 import BeautifulSoup

from django.test import TestCase


class TestIntegration(TestCase):
    """Main integration test for the plotting i.e. query database using POST
    request until the actual Plotly plot"""

    # fixtures to import in the test database
    fixtures = [
        "trendyqc/trend_monitoring/tests/test_data/integration_test_data.json",
    ]

    def test_plot_data(self):
        """Test for the plot data from the database to the HTML output.
        This test requires manual check in order to insure that the right
        values are calculated. The trendyqc/trend_monitoring/tests/test_data/test_integration_output.html file
        should be extracted from the Docker container and open in a browser in
        order to check the values. More info: https://cuhbioinformatics.atlassian.net/wiki/spaces/DV/pages/3071475867/TrendyQC+-+v1.0.0#%F0%9F%90%A7--Unittesting-result
        """

        post_data = {
            "assay_select": ["Cancer Endocrine Neurology"],
            "date_start": [""],
            "date_end": [""],
            "metrics_y": ["Custom coverage|cov_200x"],
            "plot": ["Plot"],
        }

        response = self.client.post("/trendyqc/", post_data, follow=True)

        # read the response HTML page
        html = BeautifulSoup(response.content.decode(), features="html.parser")

        # in order to get a standalone HTML page that can be opened without
        # issues, the JS files used for created for the plot are embedded in
        # HTML output
        with open(
            "trendyqc/trend_monitoring/tests/test_data/test_integration_output.html",
            "w",
        ) as f:
            # look for "script" tags in the head portion of the HTML page
            for ele in html.head.find_all("script"):
                # open the src files present in those script tags
                with open(f'/app/{ele["src"]}') as g:
                    # get the js file content
                    js_file_content = g.read()

                # remove the src attribute
                del ele["src"]
                # add the content of the js file to the tag
                ele.string = js_file_content

            f.write(str(html))
