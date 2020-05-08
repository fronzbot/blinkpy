"""Script to run blinkpy as an app."""
from os import environ
from datetime import datetime, timedelta
from blinkpy import blinkpy


USERNAME = environ.get("USERNAME")
PASSWORD = environ.get("PASSWORD")
TIMEDELTA = timedelta(environ.get("TIMEDELTA", 1))


def get_date():
    """Return now - timedelta for blinkpy."""
    return (datetime.now() - TIMEDELTA).isoformat()


def download_videos(blink, save_dir="/media"):
    """Make request to download videos."""
    blink.download_videos(save_dir, since=get_date())


def start():
    """Startup blink app."""
    blink = blinkpy.Blink(username=USERNAME, password=PASSWORD)
    blink.start()
    return blink


if __name__ == "__main__":
    BLINK = start()
    download_videos(BLINK)
