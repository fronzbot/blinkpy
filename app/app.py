"""Script to run blinkpy as an app."""
from os import environ
from datetime import datetime, timedelta
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load


CREDFILE = environ.get("CREDFILE")
TIMEDELTA = timedelta(environ.get("TIMEDELTA", 1))


def get_date():
    """Return now - timedelta for blinkpy."""
    return (datetime.now() - TIMEDELTA).isoformat()


def download_videos(blink, save_dir="/media"):
    """Make request to download videos."""
    blink.download_videos(save_dir, since=get_date())


def start():
    """Startup blink app."""
    blink = Blink()
    blink.auth = Auth(json_load(CREDFILE))
    blink.start()
    return blink


def main():
    """Run the app."""
    blink = start()
    download_videos(blink)
    blink.save(CREDFILE)


if __name__ == "__main__":
    main()
