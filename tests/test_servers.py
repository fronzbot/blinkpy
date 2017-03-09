import requests
import unittest
from constants import BASE_URL

class TestRemoteServerResponse(unittest.TestCase):
    def test_request_response(self):
        response = requests.get(BASE_URL)
        self.assertEqual(response.ok, True)