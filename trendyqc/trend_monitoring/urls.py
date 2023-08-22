# trend monitoring URL Configuration

from django.urls import path, include
from . import views

urlpatterns = [
    path("dashboard/", views.Dashboard.as_view(), name="Dashboard"),
    path("plot/", views.Plot.as_view(), name="Plot"),
    path("logs/", views.Logs.as_view(), name="Logs"),
    path("accounts/", include("django.contrib.auth.urls")),
]
