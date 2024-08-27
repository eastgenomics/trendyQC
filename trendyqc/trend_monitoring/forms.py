import datetime

from dateutil.relativedelta import relativedelta

from django import forms
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

from trendyqc.settings import DISPLAY_DATA_JSON

username_validator = UnicodeUsernameValidator()


class FilterForm(forms.Form):
    assay_select = forms.CharField(required=False)
    run_select = forms.CharField(required=False)
    sequencer_select = forms.CharField(required=False)
    metrics_x = forms.CharField(required=False)
    date_start = forms.DateField(required=False)
    date_end = forms.DateField(required=False)
    days_back = forms.IntegerField(required=False)
    metrics_y = forms.CharField()

    @staticmethod
    def clean_form_for_user(form_data: dict):
        """ Clean the form info for the ease of comprehension for the user

        Args:
            form_data (dict): Dict containing the form data used to filter the
            data to plot

        Returns:
            dict: Dict containing the form data in a more human readable way
        """

        cleaned_form_data = {}

        for key, values in form_data.items():
            if key == "assay_select":
                new_key = "Assay(s) selected"
            elif key == "run_select":
                new_key = "Run(s) selected"
            elif key == "sequencer_select":
                new_key = "Sequencer(s) select"
            elif key == "date_start":
                new_key = "Selected date start"
            elif key == "date_end":
                new_key = "Selected date end"
            elif key == "days_back":
                new_key = "Last x days"
            elif key == "metrics_x":
                new_key = "Metric for the X-axis"
            elif key == "metrics_y":
                new_key = "Metric for the Y-axis"
            else:
                new_key = key

            for value in values:
                if key == "days_back":
                    today = datetime.date.today()
                    value = f"{value} days: {today + relativedelta(days=-int(value))} - {today}"

                cleaned_form_data.setdefault(new_key, []).append(value)

        return cleaned_form_data

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
            cleaned_data.get("date_end", None),
            cleaned_data.get("days_back", None)
        ]

        if not any(run_subset):
            self.add_error(
                None, ValidationError("No subset of runs selected")
            )

        start_date = cleaned_data.get("date_start", None)
        end_date = cleaned_data.get("date_end", None)

        # if the days_back or runs are not selected, get a default date range
        if not cleaned_data.get("days_back", None) and not cleaned_data.get("run_select", None):
            if start_date:
                # clean was converting the type automatically, i need to do it
                # manually now
                start_date = datetime.datetime.strptime(
                    start_date[0], "%Y-%m-%d"
                ).date()

            if end_date:
                end_date = datetime.datetime.strptime(
                    end_date[0], "%Y-%m-%d"
                ).date()

            if not start_date:
                start_date = datetime.date.today() + relativedelta(months=-6)

            # if start date provided but not end date, define end date as
            # today's date
            if not end_date:
                end_date = datetime.date.today()

            # basic check if the start date is later than the end date
            if end_date < start_date:
                self.add_error(
                    "date_start", ValidationError(
                        (
                            "Date end cannot be smaller than date start: "
                            f"{start_date} - {end_date}"
                        )
                    )
                )
            else:
                cleaned_data["date_start"] = [start_date]
                cleaned_data["date_end"] = [end_date]

        if not cleaned_data.get("metrics_y", None):
            self.add_error("metrics_y", ValidationError("No Y-axis metric selected"))
        else:
            metrics = []

            # for each metric passed, replace the display name by the actual
            # model name
            for ele in cleaned_data["metrics_y"]:
                metrics.extend([
                    f"{model_name}|{ele.split('|')[1]}".lower()
                    for model_name, display_name in DISPLAY_DATA_JSON.items()
                    if ele.split("|")[0] == display_name
                ])

            cleaned_data["metrics_y"] = metrics

        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(
            attrs={'class': 'form-input', 'placeholder': 'Enter username'}
        )
    )

    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={'class': 'form-input', 'placeholder': 'Enter password'}
        )
    )
