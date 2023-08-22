from trend_monitoring.models import Report


def report_already_in_db(**kwargs):
    if Report.objects.filter(**kwargs).exists():
        return True
    else:
        return False
