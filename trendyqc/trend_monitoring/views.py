from django.views import View
from django.shortcuts import render


class Dashboard(View):
    template_name = "dashboard.html"

    def get(self, request):
        return render(request, self.template_name)
