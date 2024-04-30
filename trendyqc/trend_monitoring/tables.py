from collections import OrderedDict
import json

from django.utils.html import format_html
from django.utils.safestring import mark_safe

import django_tables2 as tables

from .models import Report, Filter


class FilterContentColumn(tables.Column):
    def __init__(self, classname=None, *args, **kwargs):
        self.classname=classname
        super(FilterContentColumn, self).__init__(*args, **kwargs)

    def render(self, value):
        """ Render the cell content using a multilevel list i.e.
        - filter key
            - filter value
            - filter value
        - filter key
            - filter value

        Args:
            value (str): Cell value (content column in Filter model)

        Returns:
            str: HTML-ised string
        """

        order_key = [
            "assay", "run", "sequencer",
            "metrixs_x", "metrics_y",
            "date_start", "date_end",
        ]

        # load data (json dumped data) 
        filter_data = json.loads(value)
        # remove the select from the keys
        filter_data = {
            k.replace("_select", ""): v
            for k, v in filter_data.items()
        }
        # order the dict for displaying in the filter table
        filter_data = OrderedDict(
            (k, filter_data[k]) for k in order_key if k in filter_data
        )

        formatted_data = []

        for key, values in filter_data.items():
            data = f"<ul><li><b>{key}</b>: <ul>"

            if isinstance(values, list):
                for value in values:
                    data += f"<li>{value}</li>"
            else:
                data += f"<li>{values}</li>"

            data += "</ul></li></ul>"

            formatted_data.append(data)

        return format_html("".join(formatted_data))


# custom column to display a button in the filter table
class FilterButton(tables.Column):
    empty_values = list()

    def render(self, value, record):
        return mark_safe(
            f'<button value="{record.id}" name="filter_use" class="btn btn-primary" onclick="submitFilterUse()">Use filter</button>'
        )


class DeleteFilterButton(tables.Column):
    empty_values = list()

    def render(self, value, record): 
        return mark_safe(
            f'<button value="{record.id}" name="delete_filter" class="btn btn-danger" onclick="confirmDelete(event)">Delete filter</button>'
        )


class ReportTable(tables.Table):
    name = tables.Column()
    project_id = tables.Column(orderable=False)
    sequencer_id = tables.Column()
    date = tables.Column()

    class Meta:
        model = Report
        order_by = "-date"
        fields = ("name", "project_id", "sequencer_id", "date")


class FilterTable(tables.Table):
    name = tables.Column()
    content = FilterContentColumn(classname="custom_column")
    apply_filter = FilterButton()
    delete_filter = DeleteFilterButton()

    class Meta:
        model = Filter
        order_by = "name"
