# trend monitoring URL Configuration

from django.urls import path, include
from . import views

urlpatterns = [
    path("dashboard/", views.Dashboard.as_view(), name="Dashboard"),
    path("accounts/", include("django.contrib.auth.urls")),
]
