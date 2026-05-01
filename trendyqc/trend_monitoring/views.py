import json
import logging
from itertools import count

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django_tables2 import MultiTableMixin
from django_tables2.config import RequestConfig
from trend_monitoring.forms import FilterForm
from trend_monitoring.models.filters import Filter
from trend_monitoring.models.metadata import Report, Report_Sample

from trendyqc.settings import VERSION

from .backend_utils.filtering import import_filter
from .backend_utils.plot import (format_data_for_plotly_js,
                                 get_data_for_plotting, get_subset_queryset)
from .dash_app import dash_plot
from .forms import FilterForm, LoginForm
from .tables import FilterTable, ReportTable

logger = logging.getLogger("basic")


class Dashboard(MultiTableMixin, TemplateView):
    template_name = "dashboard.html"
    report_sample_data = Report_Sample.objects.all()
    tables = [ReportTable(Report.objects.all())]
    model = Report

    table_pagination = {"per_page": 10}

    def _get_context_data(self):
        """Get the basic data that needs to be displayed in the dashboard page

        Returns:
            dict: Dict of report and assay data to be passed to the dashboard
        """

        # get the default context data (the one key i need is one called tables)
        context = super().get_context_data()

        # setup the filter table
        filter_table = FilterTable(Filter.objects.all())

        # so moving the FilterTable away from the class init "breaks" the
        # default pagination for the filter table. I reused the code in the
        # django-tables2 code (https://github.com/jieter/django-tables2/blob/master/django_tables2/views.py#L235)
        # to resetup the pagination
        # i have no idea what this code does tbh
        table_counter = count()
        filter_table.prefix = filter_table.prefix or self.table_prefix.format(
            next(table_counter)
        )
        RequestConfig(
            self.request, paginate=self.get_table_pagination(filter_table)
        ).configure(filter_table)

        context["tables"].append(filter_table)
        context["version"] = VERSION
        return context

    def get(self, request):
        """Handle GET request

        Args:
            request (?): HTML request coming in

        Returns:
            ?: Render Django thingy?
        """

        context = self._get_context_data()
        request.session.pop("form", None)
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request

        Args:
            request (?): HTML request coming in

        Returns:
            ?: Render Django thingy? | Redirect thingy towards the Plot view
        """

        context = self._get_context_data()
        form = FilterForm(request.POST)
        request.session.pop("form", None)

        # Use filter button in the filter table has been clicked
        if "filter_use" in request.POST:
            # get the filter id from the button value
            filter_id = request.POST["filter_use"]
            # get the filter obj in the database
            filter_obj = Filter.objects.get(id=filter_id)
            # deserialize the filter content for use in the Plot page
            request.session["form"] = json.loads(filter_obj.content)
            return redirect("Plot")

        # Delete filter button in the filter table has been clicked
        if "delete_filter" in request.POST:
            # get the filter id from the button value
            filter_id = request.POST["delete_filter"]
            # get the filter obj in the database
            filter_obj = Filter.objects.get(id=filter_id)
            filter_name = filter_obj.name

            try:
                # delete the filter
                filter_obj.delete()
            except Exception as e:
                messages.add_message(
                    request,
                    messages.ERROR,
                    (
                        f"Couldn't delete {filter_name}. "
                        "Please contact the bioinformatics team"
                    ),
                )
                logger.error(f"Issue with trying to delete {filter_name}: {e}")
            else:
                msg = f"Filter {filter_name} has been deleted."
                messages.add_message(request, messages.SUCCESS, msg)
                logger.info(msg)

            return redirect("Dashboard")

        return render(request, self.template_name, context)


class Login(FormView):
    template_name = "login.html"
    form_class = LoginForm

    def get(self, request):
        context = super().get_context_data()
        context["version"] = VERSION
        return render(request, self.template_name, context)

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )

            if user:
                auth_login(request, user)
                msg = "Successfully logged in!"
                messages.add_message(request, messages.SUCCESS, msg)
                return redirect("Dashboard")

        msg = "Login failed!"
        messages.add_message(request, messages.ERROR, msg)

        context = super().get_context_data()
        context["version"] = VERSION

        return render(request, self.template_name, context)


class Logout(View):
    template_name = "dashboard.html"

    def get(self, request):
        auth_logout(request)
        msg = "Successfully logged out!"
        messages.add_message(request, messages.SUCCESS, msg)
        return redirect("Dashboard")
