from datetime import date, datetime
import json

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from trend_monitoring.models.filters import Filter


def import_filter(filter_name: str, username: str, data: dict) -> str:
    """ Import filter data 

    Args:
        filter_name (str): Name of the filter
        username (str): Name of the user submitting the filter data
        data (dict): Dict containing the filtering info

    Returns:
        str: Message to indicate whether the import was successful
    """

    if data.get("save_filter", None):
        del data["save_filter"]

    # attempt to find an existing filter with the same name
    try:
        Filter.objects.get(name=filter_name)
    except ObjectDoesNotExist:
        # no filter with that name was found
        pass
    else:
        return f"Filter {filter_name} already exists", messages.ERROR

    filter_obj = Filter(
        name=filter_name, user=username,
        content=json.dumps(data, default=serialize_date)
    )
    filter_obj.save()

    return f"Filter {filter_name} has been created", messages.SUCCESS


def serialize_date(obj):
    """ Serialize the given obj for import in the database

    Args:
        obj (dict): Dict containing the data that needs to be imported in the
        database

    Raises:
        TypeError: Object is not serializable

    Returns:
        str: String date in isoformat
    """

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    raise TypeError (f"Type {type(obj)} not serializable")
