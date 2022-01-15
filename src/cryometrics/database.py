import sys
import requests

from loguru import logger

def send_http_data(endpoint: str, line: str, username: str = None, password: str = None, timeout: int = 10):
    try:
        r = requests.post(
            endpoint,
            params=dict(db='telegraf'),
            data=line.encode('utf-8'),
            auth=username and password and (username, password),
            timeout=timeout
        )
    except requests.exceptions.Timeout:
        logger.error(f'Timeout after {timeout} seconds.')
        return False
    except requests.exceptions.TooManyRedirects as e:
        logger.error(f'Too many redirects with url: {endpoint}')
        raise e
    except requests.exceptions.RequestException as e:
        logger.error(f'Unexpected exception: {e}')
        raise e

    if r.status_code != 204:
        logger.error(f'Received {r.status_code}: {r.reason}.')

    return r.status_code == 204