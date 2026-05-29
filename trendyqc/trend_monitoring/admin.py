from django.contrib import admin
from trend_monitoring.models.metadata import Report, Sample, Report_Sample
from trend_monitoring.models.filters import Filter


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "project_id",
        "project_name",
        "dnanexus_file_id",
        "date",
    )
    list_filter = ("date",)


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ("sample_id",)


@admin.register(Report_Sample)
class Report_SampleAdmin(admin.ModelAdmin):
    list_display = ("assay", "report", "sample")


@admin.register(Filter)
class FilterAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "content")
    list_filter = ("name", "user")
