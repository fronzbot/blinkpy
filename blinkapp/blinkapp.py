"""Script to run blinkpy as an blinkapp."""
import logging
from os import environ
from datetime import datetime, timedelta
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG,
)

CREDFILE = environ.get("CREDFILE")
TIMEDELTA = timedelta(int(environ.get("TIMEDELTA", "1")))


def get_date():
    """Return now - timedelta for blinkpy."""
    return (datetime.now() - TIMEDELTA).isoformat()


def download_videos(blink, save_dir="/media"):
    """Make request to download videos."""
    since = get_date()
    print("Downloading all videos since " + since)
    blink.download_videos(save_dir, since=since)


def start():
    """Startup blink app."""
    blink = Blink()
    blink.auth = Auth(json_load(CREDFILE))
    blink.start()
    return blink


def main():
    """Run the blink app."""
    print("Starting blink app")
    blink = start()
    download_videos(blink)
    blink.save(CREDFILE)


if __name__ == "__main__":
    main()
