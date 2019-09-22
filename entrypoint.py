''' Download videos from Blink '''
from os import environ
from datetime import datetime, timedelta
from blinkpy import blinkpy

USERNAME = environ.get('USERNAME')
PASSWORD = environ.get('PASSWORD')
TIMEDELTA = int(environ.get('TIMEDELTA', 1))

blink = blinkpy.Blink(username=USERNAME, password=PASSWORD)
blink.start()
blink.download_videos('/media/blinkpy', since=(datetime.now() -
                                               timedelta(days=TIMEDELTA)
                                              ).isoformat()
                     )
