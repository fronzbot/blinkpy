from blinkpy import blinkpy
from os import environ
from datetime import datetime, timedelta

username = environ.get('USERNAME')
password = environ.get('PASSWORD')

blink = blinkpy.Blink(username=username, password=password)
blink.start()
blink.download_videos('/media/blinkpy', since=(datetime.now() - timedelta(days=1)).isoformat())
