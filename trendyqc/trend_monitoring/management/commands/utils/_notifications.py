import logging

from django.conf import settings

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger("basic")


def slack_notify(message) -> None:
    """Notify the channel with the given message

    Args:
        message (str): Message to send
    """

    channel = settings.SLACK_CHANNEL
    logger.info(f"Sending message to {channel}")
    slack_token = settings.SLACK_TOKEN

    http = Session()
    retries = Retry(total=5, backoff_factor=10, allowed_methods=["POST"])
    http.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        response = http.post(
            "https://slack.com/api/chat.postMessage",
            {"token": slack_token, "channel": f"#{channel}", "text": message},
        ).json()

        if not response["ok"]:
            # error in sending slack notification
            logger.error(
                f"Error in sending slack notification: {response.get('error')}"
            )

    except Exception as err:
        logger.error(
            f"Error in sending post request for slack notification: {err}"
        )


def build_report(header: str, final_msg: str, dict_info: dict = {}):
    """Given all the messages that a MultiQC report object possesses, create a
    summary report of all the messages

    Args:
        header (str): Message to use as header of the summary report

        dict_info (dict): Dict containing the report file-id and the messages
        to report

    Returns:
        msg_report: Summary report string to send to loggers and to Slack
    """

    msg_report = f"{header}\n\n"

    for report_id, msgs in dict_info.items():
        msg_report += f" - {report_id}\n"

        for msg in msgs:
            msg_report += f"   - {msg}\n"

    msg_report += f"\n{final_msg}"

    return msg_report
