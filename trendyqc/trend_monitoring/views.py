from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from .forms import FilterForm
from trend_monitoring.models.metadata import Report, Report_Sample
from .backend_utils.plot import (
    get_subset_queryset, get_data_for_plotting, plot_qc_data, prepare_filter_data
)


class Dashboard(View):
    template_name = "dashboard.html"
    report_data = Report.objects.all()
    report_sample_data = Report_Sample.objects.all()

    def get_context_data(self):
        """ Get the basic data that needs to be displayed in the dashboard page

        Returns:
            dict: Dict of report and assay data to be passed to the dashboard
        """

        # get all the assays and sort them
        assays = sorted({
            assay
            for assay in self.report_sample_data.values_list("assay", flat=True)
        })
        sequencer_ids = sorted({
            sequencer_id
            for sequencer_id in self.report_data.values_list("sequencer_id", flat=True)
        })
        context = {
            "report_data": self.report_data, "assays": assays,
            "sequencer_ids": sequencer_ids
        }
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
            # save the cleaned data in the session so that 
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
            subset_queryset = get_subset_queryset(filter_data["subset"])
            df_data = get_data_for_plotting(subset_queryset)
            div_plot = plot_qc_data(df_data)
            context = {"form": form, "plot": div_plot.to_html(), "data": df_data.to_html()}
            return render(request, self.template_name, context)

        return render(request, self.template_name)
