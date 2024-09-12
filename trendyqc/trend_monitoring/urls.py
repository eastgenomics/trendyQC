# trend monitoring URL Configuration

from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.Dashboard.as_view(), name="Dashboard"),
    path("plot/", views.Plot.as_view(), name="Plot"),
    path("logs/", include("log_viewer.urls")),
    path("login/", views.Login.as_view(), name="Login"),
    path("logout/", views.Logout.as_view(), name="Logout"),
]