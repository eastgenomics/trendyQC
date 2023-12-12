from django.db import models


class Filter(models.Model):
    name = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    content = models.TextField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "filter"
