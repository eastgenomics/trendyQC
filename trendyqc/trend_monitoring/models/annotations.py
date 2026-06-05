from django.db import models
from django.contrib.auth.models import User


class PlotAnnotation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    label = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
