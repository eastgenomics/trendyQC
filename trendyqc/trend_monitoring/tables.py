from collections import OrderedDict
import json

from django.utils.html import format_html
from django.utils.safestring import mark_safe

import django_tables2 as tables

from .models import Report, Filter


# custom column to display a button in the filter table
class FilterButton(tables.Column): 
    empty_values = list()

    def render(self, value, record): 
        return mark_safe(
            f'<button value="{record.id}" name="filter_use" class="btn btn-info">Use filter</button>'
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
    content = tables.Column()
    apply_filter = FilterButton()

    class Meta:
        model = Filter
        order_by = "name"

    def render_content(self, value):
        order_key = [
            "assay", "run", "sequencer",
            "metrixs_x", "metrics_y",
            "date_start", "date_end",
        ]

        value = json.loads(value)
        # remove the select from the keys, and join the value if necessary
        value = {
            k.replace("_select", ""): (";".join(v) if isinstance(v, list) else v)
            for k, v in value.items()
        }
        # order the dict for displaying in the filter table
        value = OrderedDict((k, value[k]) for k in order_key if k in value)
        # add bold for the key
        value = [f"<b>{k}</b>: {v}" for k, v in value.items()]
        return format_html(" | ".join(value))
