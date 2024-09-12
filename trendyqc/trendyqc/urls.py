# trend_app URL Configuration

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("trendyqc/admin/", admin.site.urls),
    path("trendyqc/", include("trend_monitoring.urls")),
    path("__debug__/", include("debug_toolbar.urls")),
]