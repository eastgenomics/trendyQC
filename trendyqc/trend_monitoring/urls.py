# trend monitoring URL Configuration

from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.Dashboard.as_view(), name="Dashboard"),
    path("plot/", views.Plot.as_view(), name="Plot"),
    path("logs/", include("log_viewer.urls")),
    path("accounts/", admin.site.urls),
]