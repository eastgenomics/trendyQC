# trend monitoring URL Configuration

from django.urls import include, path

from . import views
from .dash_app import dash_plot

urlpatterns = [
    path("", views.Dashboard.as_view(), name="Dashboard"),
    path("logs/", include("log_viewer.urls")),
    path("login/", views.Login.as_view(), name="Login"),
    path("logout/", views.Logout.as_view(), name="Logout"),
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
    path("auth-status/", views.auth_status, name="auth_status"),
]
