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

        run_subset = [
            data.get("assay_select", None),
            data.get("run_select", None),
            data.get("sequencer_select", None),
            data.get("date_start", None),
            data.get("date_end", None)
        ]

        # clean was converting the type automatically, i need to do it manually
        # now
        start_date = datetime.datetime.strptime(
            data.get("date_start", None)[0], "%Y-%m-%d"
        ).date()
        end_date = data.get("date_end", None)[0]

        # add the date data in the dict
        data["date_start"] = start_date
        data["date_end"] = end_date

        if not any(run_subset):
            self.add_error(None, ValidationError("No subset of runs selected"))

        if not start_date and end_date:
            self.add_error(
                "date_start", ValidationError("No start date selected")
            )

        if not end_date and start_date:
            now = datetime.date.today()
            data["date_end"] = now
            end_date = now

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

        if not data.get("metrics_y", None):
            self.add_error(None, ValidationError("No Y-axis metric selected"))

        cleaned_data = {}

        for key, value in data.items():
            # clean also removed the crsf token, removing it manually
            if key == "csrfmiddlewaretoken":
                continue

            if value:
                if isinstance(value, str):
                    cleaned_data[key] = value.strip()

                elif isinstance(value, list):
                    # clean flattened the data (since it was returning the last
                    # value). Handling those [""] occurences
                    if "" in value and len(value) == 1:
                        continue

                    cleaned_data[key] = value

                elif isinstance(value, datetime.date):
                    cleaned_data[key] = value

                else:
                    # error message just in case of any other weird stuff
                    self.add_error(None, ValidationError((
                        "Unexpected type in the form data. Please contact the "
                        "bioinformatics team"
                    )))

        return cleaned_data
