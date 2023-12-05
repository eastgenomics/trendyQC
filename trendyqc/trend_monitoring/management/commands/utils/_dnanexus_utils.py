import traceback
from typing import List

import dxpy

from django.conf import settings

from ._notifications import slack_notify


def login_to_dnanexus():
    """ Login to DNAnexus using a auth token present in the environment """

    DX_SECURITY_CONTEXT = {
        "auth_token_type": "Bearer",
        "auth_token": settings.DX_TOKEN,
    }

    dxpy.set_security_context(DX_SECURITY_CONTEXT)

    try:
        dxpy.whoami()
        print("DNAnexus login successful")
    except Exception:
        traceback.print_exc()
        msg = (
            "TrendyQC - Failed DNAnexus login, token may be expired.\n"

            "```"
            f"{traceback.format_exc()}"
            "```"
        )
        slack_notify(msg)
        exit()


def search_multiqc_reports(project_id: str) -> List:
    """ Look for the MultiQC reports in the given project ID

    Args:
        project_id (str): DNAnexus project ID

    Returns:
        List: List of all the MultiQC reports objects found in the DNAnexus
        project
    """

    files = dxpy.find_data_objects(
        project=project_id, name="multiqc_data.json", return_handler=True
    )

    return [file for file in files]


def get_002_projects(**kwargs) -> List:
    """ Get the 002 projects in DNAnexus

    Args:
        kwargs (dict): Dict of args that find_projects can accept

    Returns:
        List: List of 002 DNAnexus project IDs
    """

    projects = dxpy.find_projects(name="^002", name_mode="regexp", **kwargs)

    return [project["id"] for project in projects]


def is_archived(dnanexus_object: dxpy.DXFile) -> bool:
    """ Check if the given dnanexus object is archived

    Args:
        dnanexus_object (dxpy.DXFile): Generic Dnanexus DXFile

    Returns:
        bool: bool to indicate archival status
    """

    archival_state = dnanexus_object.describe()["archivalState"]

    if archival_state == "live":
        return False
    else:
        return True
