import datetime

from django import forms
from django.core.exceptions import ValidationError


class FilterForm(forms.Form):
    assay_select = forms.CharField(required=False)
    run_select = forms.CharField(required=False)
    sequencer_select = forms.CharField(required=False)
    metrics_x = forms.CharField(required=False)
    date_start = forms.DateField(required=False)
    date_end = forms.DateField(required=False)
    metrics_y = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()

        run_subset = [
            cleaned_data.get("assay_select", None),
            cleaned_data.get("run_select", None),
            cleaned_data.get("sequencer_select", None)
        ]

        start_date = cleaned_data.get("date_start", None)
        end_date = cleaned_data.get("date_end", None)

        if not any(run_subset):
            raise ValidationError("No subset of runs selected")

        x_metric = [
            cleaned_data.get("metrics_x", None),
            cleaned_data.get("date_start", None)
        ]

        if not x_metric:
            raise ValidationError("No X-axis values selected")
        else:
            if not end_date and start_date:
                now = datetime.date.today()
                cleaned_data["date_end"] = now
                end_date = now

            if end_date and start_date:
                if end_date < start_date:
                    raise ValidationError((
                        "Date end cannot be smaller than date start: "
                        f"{start_date} - {end_date}"
                    ))

        if not cleaned_data.get("metrics_y", None):
            raise ValidationError("No Y-axis metric selected")

        return cleaned_data
