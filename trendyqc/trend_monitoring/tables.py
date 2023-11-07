import django_tables2 as tables

from .models import Report, Filter


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


    class Meta:
        model = Filter
        order_by = "name"
