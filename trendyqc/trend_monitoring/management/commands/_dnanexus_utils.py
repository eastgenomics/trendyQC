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


def search_multiqc_data(project_id):
    pass


def get_all_002_projects():
    pass
