from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from .forms import FilterForm
from trend_monitoring.models.metadata import Report, Report_Sample


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
            "".join(assay)
            for assay in self.report_sample_data.values_list("assay")
        })
        context = {"report_data": self.report_data, "assays": assays}
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
            filter_recap = self.clean_form_data(form)
            context = {"data": filter_recap}
            return render(request, self.template_name, context)

        return render(request, self.template_name)

    def clean_form_data(self, form_data):
        """ Clean form data by removing empty values

        Args:
            form_data (dict): Dict containing data from the Dashboard form

        Returns:
            dict: Dict of cleaned form data
        """

        cleaned_plot_data = {
            key: value
            for key, value in form_data.items() if value
        }
        return cleaned_plot_data

    def get_data_for_plotting(self, filter_recap):
        data = {}
        data.setdefault("subset", {})
        # data.setdefault("x_axis", "")
        # data.setdefault("y_axis", "")

        for field, value in filter_recap.items():
            if not value:
                continue

            if field in ["assay_select", "run_select", "sequencer_select"]:
                data["subset"].setdefault(field, []).append(value)

            # if field in ["metrics_x", "date_start", "date_end"]:
            #     data["x_axis"][field] = value

            # if field == "metrics_y":
            #     data["y_axis"][field] = value

        return self.get_subset_queryset(data["subset"])

    def get_subset_queryset(self, subset_data):
        assays = subset_data.get("assay_select", [])
        runs = subset_data.get("run_select", [])
        return Report_Sample.objects.filter(report__project_name__in=runs) | Report_Sample.objects.filter(assay__in=assays)

    def plot(self, plot_data):
        pass
