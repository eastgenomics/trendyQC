from django.db import models


class Filter(models.Model):
    name = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    subset = models.TextField(null=True)
    date = models.TextField(null=True)
    metric = models.TextField(null=True)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "filter"
