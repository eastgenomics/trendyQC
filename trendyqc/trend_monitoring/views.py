from django.views import View
from django.shortcuts import render, redirect
from .forms import FilterForm
from trend_monitoring.models.metadata import Report, Report_Sample


class Dashboard(View):
    template_name = "dashboard.html"
    report_data = Report.objects.all()
    report_sample_data = Report_Sample.objects.all()

    def get_context_data(self):
        assays = sorted({
            "".join(assay)
            for assay in self.report_sample_data.values_list("assay")
        })
        context = {"report_data": self.report_data, "assays": assays}
        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        form = FilterForm(request.POST)

        if form.is_valid():
            request.session["form"] = form.cleaned_data
            return redirect("Plot")

        return render(request, self.template_name, context)


class Plot(View):
    template_name = "plot.html"

    def get(self, request):
        if request.session.get("form"):
            filter_recap = self.filter_recap(request)
            print(self.get_data_for_plotting(filter_recap))
            context = {"data": filter_recap}
            return render(request, self.template_name, context)

        return render(request, self.template_name)

    def filter_recap(self, request):
        form_data = request.session.get("form")
        cleaned_plot_data = {
            key: value
            for key, value in form_data.items() if value
        }
        return cleaned_plot_data

    def get_data_for_plotting(self, filter_recap):
        data = {}
        data.setdefault("subset", {})
        data.setdefault("x_axis", "")
        data.setdefault("y_axis", "")

        for field, value in filter_recap.items():
            if not value:
                continue

            if field in ["assay_select", "run_select", "sequencer_select"]:
                data["subset"][field] = value

            if field in ["metrics_x", "date_start", "date_end"]:
                data["x_axis"][field] = value

            if field == "metrics_y":
                data["y_axis"][field] = value

        return self.get_subset_queryset(data["subset"])

    def get_subset_queryset(self, subset_data):
        return Report_Sample.objects.filter(
            report__name=subset_data["assay_select"],
            assay=subset_data["run_select"]
        )

    def plot(self, plot_data):
        pass
