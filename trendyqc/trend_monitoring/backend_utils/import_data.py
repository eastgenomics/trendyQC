import json

from django.core.exceptions import ObjectDoesNotExist

from trend_monitoring.models.filters import Filter

from .plot import prepare_filter_data


def import_filter(filter_name: str, data: dict) -> str:
    """ Import filter data 

    Args:
        filter_name (str): Name of the filter
        data (dict): Dict containing the filtering info

    Returns:
        str: Message to indicate whether the import was successful
    """

    filter_data = prepare_filter_data(data)

    # attempt to find an existing filter with the same name
    try:
        Filter.objects.get(name=filter_name)
    except ObjectDoesNotExist:
        # no filter with that name was found
        pass
    else:
        return f"Filter {filter_name} already exists"

    filter_obj = Filter(name=filter_name, content=json.dumps(filter_data))
    filter_obj.save()

    return f"Filter {filter_name} has been created"
