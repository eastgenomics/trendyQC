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
            request.session["temp_data"] = form.cleaned_data
            return redirect("Plot")

        return render(request, self.template_name, context)


class Plot(View):
    template_name = "plot.html"

    def get(self, request, *args, **kwargs):
        form_data = request.session.get("temp_data")
        return render(request, self.template_name)
