"""Script to run blinkpy as an blinkapp."""
from os import environ
import asyncio
from datetime import datetime, timedelta
from aiohttp import ClientSession
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load

CREDFILE = environ.get("CREDFILE")
TIMEDELTA = timedelta(environ.get("TIMEDELTA", 1))


def get_date():
    """Return now - timedelta for blinkpy."""
    return (datetime.now() - TIMEDELTA).isoformat()


async def download_videos(blink, save_dir="/media"):
    """Make request to download videos."""
    await blink.download_videos(save_dir, since=get_date())


async def start(session: ClientSession):
    """Startup blink app."""
    blink = Blink(session=session)
    blink.auth = Auth(await json_load(CREDFILE))
    await blink.start()
    return blink


async def main():
    """Run the blink app."""
    session = ClientSession()
    blink = await start(session)
    await download_videos(blink)
    blink.save(CREDFILE)
    await session.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
