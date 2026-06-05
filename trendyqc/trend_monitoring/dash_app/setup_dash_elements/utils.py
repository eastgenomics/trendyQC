import datetime
import json

from dateutil.relativedelta import relativedelta


def build_filter_text(filter_content):
    text = ""

    if not filter_content:
        return text
    else:
        cleaned_filter_content = clean_filter_content(filter_content)

    for k, v in cleaned_filter_content.items():
        if isinstance(v, list):
            v = ", ".join([str(i) for i in v])

        elif isinstance(v, (int, float)):
            v = str(v)

        text += f"{k}: {v} | "

    return text.strip(" | ")


def clean_filter_content(filter_content):
    cleaning_keys = {
        "assay": "Assay(s) selected",
        "date_start": "Selected date start",
        "date_end": "Selected date end",
        "days_back": "Last x days",
        "metric": "Metric for the Y-axis",
        "metric_x": "Metric for X-axis",
        "run": "Run selected",
    }

    cleaned_form_data = {}

    for key, values in json.loads(filter_content).items():
        new_key = cleaning_keys.get(key, key)

        if values:
            for value in values:
                if key == "days_back":
                    today = datetime.date.today()
                    value = f"{value} days: {today + relativedelta(days=int(value))} - {today}"

                cleaned_form_data.setdefault(new_key, []).append(value)

    return cleaned_form_data


def remove_prefix_suffix_from_run_name(run_name):
    return "_".join(run_name.replace("002_", "").split("_")[:4])
