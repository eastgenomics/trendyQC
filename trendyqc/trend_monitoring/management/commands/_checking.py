import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trendyqc.settings")

import django.apps


def check_multiqc_report_integrity(fields, tool_name, subtool=None):
    pass


def check_tools():
    pass


def check_model_names():
    models = django.apps.apps.get_models()

    model_names = {str(model.__name__).lower(): model for model in models}

    if tool_name in model_names:
        model = model_names[tool_name]
        models_fields = [field.name for field in model._meta.get_fields()]
        print(tool_name)
        print(model)
        print(fields)
        print(models_fields)
