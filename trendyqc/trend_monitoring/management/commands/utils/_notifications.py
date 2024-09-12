import logging

from django.conf import settings

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger("basic")


def slack_notify(message) -> None:
    """ Notify the channel with the given message

    Args:
        message (str): Message to send
    """

    channel = settings.SLACK_CHANNEL
    logger.info(f"Sending message to {channel}")
    slack_token = settings.SLACK_TOKEN

    http = Session()
    retries = Retry(total=5, backoff_factor=10, method_whitelist=['POST'])
    http.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        response = http.post(
            'https://slack.com/api/chat.postMessage', {
                'token': slack_token,
                'channel': f"#{channel}",
                'text': message
            }).json()

        if not response['ok']:
            # error in sending slack notification
            logger.error(
                f"Error in sending slack notification: {response.get('error')}"
            )

    except Exception as err:
        logger.error(
            f"Error in sending post request for slack notification: {err}"
        )
