from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View

from django_tables2 import SingleTableView

from trend_monitoring.models.metadata import Report, Report_Sample

from .tables import ReportTable
from .forms import FilterForm
from .backend_utils.plot import (
    get_subset_queryset, get_data_for_plotting, prepare_filter_data,
    format_data_for_plotly_js
)


class Dashboard(SingleTableView):
    template_name = "dashboard.html"
    table_class = ReportTable
    model = Report
    report_sample_data = Report_Sample.objects.all()

    def get_context_data(self):
        """ Get the basic data that needs to be displayed in the dashboard page

        Returns:
            dict: Dict of report and assay data to be passed to the dashboard
        """

        # object list needs to be defined for SingleTableViews but i have no
        # need for it
        # get the default context data (the one i need is one called table)
        context = super().get_context_data(object_list="")

        # get all the assays and sort them
        assays = sorted({
            assay
            for assay in self.report_sample_data.values_list(
                "assay", flat=True)
        })
        sequencer_ids = sorted({
            sequencer_id
            for sequencer_id in self.model.objects.all().values_list(
                "sequencer_id", flat=True)
        })
        project_names = sorted(
            project_name
            for project_name in self.model.objects.all().values_list(
                "project_name", flat=True)
        )

        context["project_names"] = project_names
        context["assays"] = assays
        context["sequencer_ids"] = sequencer_ids
        return context

    def get(self, request):
        """ Handle GET request

        Args:
            request (?): HTML request coming in

        Returns:
            ?: Render Django thingy?
        """

        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ Handle POST request

        Args:
            request (?): HTML request coming in

        Returns:
            ?: Render Django thingy? | Redirect thingy towards the Plot view
        """

        context = self.get_context_data()
        form = FilterForm(request.POST)

        # call the clean function and see if the form data is valid
        if form.is_valid():
            # save the cleaned data in the session so that it gets passed to
            # the Plot view
            request.session["form"] = form.cleaned_data
            return redirect("Plot")
        else:
            # add the errors for displaying in the dashboard template
            for error_field in form.errors:
                if isinstance(form.errors[error_field], list):
                    for error in form.errors[error_field]:
                        messages.add_message(
                            request, messages.ERROR,
                            f"{error_field}: {error}"
                        )
                else:
                    messages.add_message(
                            request, messages.ERROR,
                            f"{error_field}: {''.join(form.errors[error])}"
                        )

        return render(request, self.template_name, context)


class Plot(View):
    template_name = "plot.html"

    def get(self, request):
        """ Handle GET request. This should only happen after the form has been
        submitted.

        Args:
            request (?): HTML request

        Returns:
            ?: Render Django thingy
        """

        form = request.session.get("form")

        # check if we have the form data in the session request
        if form:
            # clean the form data
            filter_data = prepare_filter_data(form)
            # get queryset of report_sample filtered using the "subset" options
            # selected by the user and passed through the form
            subset_queryset = get_subset_queryset(filter_data["subset"])
            df_data = get_data_for_plotting(subset_queryset)
            (
                json_plot_data, json_trend_data
            ) = format_data_for_plotly_js(df_data)
            context = {
                "form": form, "plot": json_plot_data, "trend": json_trend_data
            }
            return render(request, self.template_name, context)

        return render(request, self.template_name)
