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
        # i can't use super().clean() because QueryDict are dumb:
        # https://docs.djangoproject.com/en/4.2/ref/request-response/#django.http.QueryDict.__getitem__
        # converting the querydict into a normal dict, this means a lot of the
        # automatic cleaning that clean() was doing is going to be done
        # manually by yours truly
        data = dict(self.data.lists())
        cleaned_data = {}

        for key, value in data.items():
            # clean also removed the crsf token, removing it manually
            if key == "csrfmiddlewaretoken":
                continue
            # when submitting the form using the Plot button, remove it from
            # the plotting filter recap
            elif key == "plot":
                continue

            for v in value:
                if v:
                    cleaned_data.setdefault(key, []).append(v)

        run_subset = [
            cleaned_data.get("assay_select", None),
            cleaned_data.get("run_select", None),
            cleaned_data.get("sequencer_select", None),
            cleaned_data.get("date_start", None),
            cleaned_data.get("date_end", None)
        ]

        start_date = cleaned_data.get("date_start", None)
        end_date = cleaned_data.get("date_end", None)

        if start_date:
            # clean was converting the type automatically, i need to do it
            # manually now
            start_date = datetime.datetime.strptime(
                start_date[0], "%Y-%m-%d"
            ).date()
            cleaned_data["date_start"] = start_date

        if end_date:
            end_date = datetime.datetime.strptime(
                end_date[0], "%Y-%m-%d"
            ).date()
            cleaned_data["date_end"] = end_date

        if not start_date and end_date:
            self.add_error(
                "date_start", ValidationError("No start date selected")
            )

        # if start date provided but not end date, define end date as today's
        # date
        if not end_date and start_date:
            now = datetime.date.today()
            cleaned_data["date_end"] = now
            end_date = now

        if not any(run_subset):
            self.add_error(None, ValidationError("No subset of runs selected"))

        # basic check if the start date is later than the end date
        if end_date and start_date:
            if end_date < start_date:
                self.add_error(
                    None, ValidationError(
                        (
                            "Date end cannot be smaller than date start: "
                            f"{start_date} - {end_date}"
                        )
                    )
                )

        if not cleaned_data.get("metrics_y", None):
            self.add_error(None, ValidationError("No Y-axis metric selected"))
        else:
            cleaned_data["metrics_y"] = [
                ele.lower() for ele in cleaned_data["metrics_y"]
            ]

        return cleaned_data
