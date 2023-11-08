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
