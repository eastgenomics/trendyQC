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
        pass

    def plot(self, plot_data):
        pass
