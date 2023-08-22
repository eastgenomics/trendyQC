from django.apps import apps


def already_in_db(model, **kwargs):
    if model.objects.filter(**kwargs).exists():
        return True
    else:
        return False
