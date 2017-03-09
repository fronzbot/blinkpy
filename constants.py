'''
constants.py
Generates constants for use in blinkpy
'''

'''
URLS
'''
BLINK_URL = 'immedia-semi.com'
LOGIN_URL = 'https://prod.' + BLINK_URL + '/login'
BASE_URL = 'https://prod.' + BLINK_URL
DEFAULT_URL = 'prod.' + BLINK_URL
HOME_URL = BASE_URL + '/homescreen'
EVENT_URL = BASE_URL + '/events/network/'
NETWORK_URL = BASE_URL + '/network/'

'''
Dictionaries
'''
ONLINE = {'online': True, 'offline': False}