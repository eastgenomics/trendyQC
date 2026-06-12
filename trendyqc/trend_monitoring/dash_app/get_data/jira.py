import json
import logging

import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

from trend_monitoring.dash_app.setup_dash_elements.utils import (
    remove_prefix_suffix_from_run_name,
)

logger = logging.getLogger("basic")


def get_failed_statuses():
    annotation_file = (
        settings.CONFIG_PATH / "plotting_configs" / "failed_run_statuses.json"
    )
    with open(annotation_file) as f:
        return json.load(f)


def get_failed_runs(run_names: list) -> set:
    """Query JIRA for tickets matching run names and return those with
    failed statuses.

    Args:
        run_names (list): List of run names to check

    Returns:
        set: Set of run names that have a failed status in JIRA
    """

    failed_statuses = get_failed_statuses()

    if not run_names:
        return set()

    jira_url = settings.JIRA_URL
    jira_token = settings.JIRA_TOKEN
    jira_email = settings.JIRA_EMAIL
    project_key = settings.JIRA_PROJECT_KEY

    if not all([jira_url, jira_token, jira_email, project_key]):
        logger.warning(
            "JIRA settings are not fully configured, skipping JIRA check"
        )
        return set()

    auth = HTTPBasicAuth(jira_email, jira_token)

    # build JQL with ~ for each run name
    run_name_conditions = " OR ".join(
        f'summary ~ "{remove_prefix_suffix_from_run_name(name)}*"'
        for name in run_names
    )
    jql = (
        f"project = {project_key} AND "
        f"({run_name_conditions}) AND "
        'type = "Sequencing Run"'
    )

    all_issues = []
    next_page_token = None

    while True:
        params = {
            "jql": jql,
            "fields": "summary,status",
        }

        if next_page_token:
            params["nextPageToken"] = next_page_token

        try:
            response = requests.get(
                f"{jira_url}/rest/api/3/search/jql",
                headers={"Accept": "application/json"},
                auth=auth,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch JIRA tickets: {e}")
            return set()

        data = response.json()
        all_issues.extend(data.get("issues", []))

        if data.get("isLast", True):
            break

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    failed_runs = set()

    for issue in response.json().get("issues", []):
        summary = issue["fields"]["summary"]
        status = issue["fields"]["status"]["name"]

        if status in failed_statuses:
            for run_name in run_names:
                cleaned = remove_prefix_suffix_from_run_name(run_name)
                # check if cleaned run name matches or is contained in summary
                if cleaned in summary or summary in cleaned:
                    failed_runs.add(run_name)

    return failed_runs
