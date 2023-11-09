import json
import logging

from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.base import TemplateView

from django_tables2 import MultiTableMixin

from trend_monitoring.models.metadata import Report, Report_Sample
from trend_monitoring.models.filters import Filter
from trend_monitoring.models import bam_qc, fastq_qc, vcf_qc

from .tables import ReportTable, FilterTable
from .forms import FilterForm
from .backend_utils.plot import (
    get_subset_queryset, get_data_for_plotting, prepare_filter_data,
    format_data_for_plotly_js
)
from .backend_utils.filtering import import_filter

logger = logging.getLogger("basic")


class Dashboard(MultiTableMixin, TemplateView):
    template_name = "dashboard.html"
    report_sample_data = Report_Sample.objects.all()
    tables = [
        ReportTable(Report.objects.all()),
        FilterTable(Filter.objects.all())
    ]
    model = Report

    table_pagination = {
        "per_page": 10
    }

    def _get_context_data(self):
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
        plotable_metrics = {
            **self._get_plotable_metrics(bam_qc),
            **self._get_plotable_metrics(fastq_qc),
            **self._get_plotable_metrics(vcf_qc)
        }
        context["metrics"] = dict(sorted(plotable_metrics.items()))
        return context

    def _get_plotable_metrics(self, module) -> dict:
        """ Gather all the plotable metrics by model in a dict

        Args:
            module (module): Module containing the definition of models

        Returns:
            dict: Dict with the name of the model as key and the name of the
            field as value
        """

        plotable_metrics = {}

        # loop through the modules' classes and get their name and object into
        # a dict
        module_dict = dict(
            [
                (name, cls)
                for name, cls in module.__dict__.items()
                if isinstance(cls, type)
            ]
        )

        for model_name, model in module_dict.items():
            plotable_metrics.setdefault(model_name, [])

            for field in model._meta.fields:
                # get the type of the field
                field_type = field.get_internal_type()

                # only get fields with those type for plotability
                if field_type in ["FloatField", "IntegerField"]:
                    plotable_metrics[model_name].append(field.name)

            plotable_metrics[model_name].sort()

        return plotable_metrics

    def get(self, request):
        """ Handle GET request

        Args:
            request (?): HTML request coming in

        Returns:
            ?: Render Django thingy?
        """

        context = self._get_context_data()
        request.session.pop("form", None)
        return render(request, self.template_name, context)

    def post(self, request):
        """ Handle POST request

        Args:
            request (?): HTML request coming in

        Returns:
            ?: Render Django thingy? | Redirect thingy towards the Plot view
        """

        context = self._get_context_data()
        form = FilterForm(request.POST)
        request.session.pop("form", None)

        # button in the filter table has been clicked
        if "filter_use" in request.POST:
            # get the filter id from the button value
            filter_id = request.POST["filter_use"]
            # get the filter obj in the database
            filter_obj = Filter.objects.get(id=filter_id)
            # deserialize the filter content for use in the Plot page
            request.session["form"] = json.loads(filter_obj.content)
            return redirect("Plot")

        # call the clean function and see if the form data is valid
        if form.is_valid():
            if "plot" in request.POST:
                # save the cleaned data in the session so that it gets passed to
                # the Plot view
                request.session["form"] = form.cleaned_data
                return redirect("Plot")

            elif "save_filter" in request.POST:
                filter_name = request.POST["save_filter"]

                # the default value that the prompt return is Save filter i.e.
                # if nothing was inputted the value is Save filter
                if filter_name != "Save filter":
                    msg, msg_status = import_filter(
                        filter_name, form.cleaned_data
                    )
                    messages.add_message(request, msg_status, f"{msg}")

                return redirect("Dashboard")

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

            if not subset_queryset:
                msg = f"No data found for {filter_data['subset']}"
                messages.error(request, msg)
                return render(request, self.template_name, {})

            (
                data_dfs, projects_no_metric, samples_no_metric
            ) = get_data_for_plotting(
                subset_queryset, filter_data["y_axis"]
            )

            if len(data_dfs) != 1:
                msg = (
                    "An issue has occurred. Please contact the bioinformatics "
                    "team."
                )
                messages.warning(request, msg)
                logger.debug(
                    "An error occurred using the following filtering data: "
                    f"{filter_data}"
                )

            (
                json_plot_data, json_trend_data
            ) = format_data_for_plotly_js(data_dfs[0])

            context = {
                "form": dict(sorted(form.items())), "plot": json_plot_data,
                "trend": json_trend_data,
                "skipped_projects": projects_no_metric,
                "skipped_samples": samples_no_metric
            }
            return render(request, self.template_name, context)

        return render(request, self.template_name)

    def post(self, request):
        # back to dashboard button is clicked
        if "dashboard" in request.POST:
            # clear the session of the form info
            request.session.pop("form", None)
            return redirect("Dashboard")

        # same save filter logic as in the dashboard view
        elif "save_filter" in request.POST:
            filter_name = request.POST["save_filter"]

            if filter_name != "Save filter":
                msg, msg_status = import_filter(
                    filter_name, request.session.get("form")
                )
                messages.add_message(request, msg_status, f"Filter: {msg}")

            return redirect("Plot")
