import dxpy
from typing import List

from django.conf import settings


def login_to_dnanexus():
    """ Login to DNAnexus using a auth token present in the environment """

    DX_SECURITY_CONTEXT = {
        "auth_token_type": "Bearer",
        "auth_token": settings.DX_TOKEN,
    }

    dxpy.set_security_context(DX_SECURITY_CONTEXT)

    try:
        dxpy.api.system_whoami()
        print("DNAnexus login successful")
    except Exception as err:
        print(err)
        exit()


def search_multiqc_reports(project_id: str) -> List:
    """ Look for the MultiQC reports in the given project ID

    Args:
        project_id (str): DNAnexus project ID

    Returns:
        List: List of all the project IDs found in the DNAnexus project
    """

    data = []

    files = dxpy.find_data_objects(
        project=project_id, name="multiqc_data.json"
    )

    for file in files:
        data.append(dxpy.DXFile(file["id"], file["project"]))

    return data


def get_all_002_projects() -> List:
    """ Get all the 002 projects in DNAnexus

    Returns:
        List: List of all the 002 DNAnexus project IDs
    """

    prod_projects = []
    projects = dxpy.find_projects(name="^002", name_mode="regexp")

    for project in projects:
        prod_projects.append(project["id"])

    return prod_projects
