from django.db.models import Model


def already_in_db(model: Model, **kwargs) -> bool:
    """ Check in the database if the given kwargs match an instance for the
    given model

    Args:
        model (Model): Model Django object
        kwargs (dict): Dict of data used to build the filter

    Returns:
        bool: Bool to indicate if the filter managed to find an instance
    """

    if model.objects.filter(**kwargs).exists():
        return True
    else:
        return False
