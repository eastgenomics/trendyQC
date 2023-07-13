import dxpy

from django.conf import settings


def login_to_dnanexus():
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


def search_multiqc_reports(project_id):
    data = []

    files = dxpy.find_data_objects(
        project=project_id, name="multiqc_data.json"
    )

    for file in files:
        data.append(dxpy.DXFile(file["id"], file["project"]))

    return data


def get_all_002_projects():
    prod_projects = []
    projects = dxpy.find_projects(name="^002", name_mode="regexp")

    for project in projects:
        prod_projects.append(project["id"])

    return prod_projects
