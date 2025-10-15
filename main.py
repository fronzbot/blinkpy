import asyncio
from aiohttp import ClientSession
from blinkpy.blinkpy import Blink

async def start():
    blink = Blink(session=ClientSession())
    await blink.start()
    return blink

blink = asyncio.run(start())