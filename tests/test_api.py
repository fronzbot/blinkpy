"""Test API calls with correct info."""

import unittest
from unittest import mock
from blinkpy import api
from blinkpy.helpers.util import BlinkURLHandler


def mock_post(blink, url, is_retry=False):
    """Mock the http_post function."""
    split_url = url.split("/")
    uri = split_url[0]
    subdomain = split_url[2]
    new_list = [uri, subdomain]
    base_url = "//".join(new_list)
    return base_url == blink.urls.base_url


def mock_get(blink, url, stream=False, json=True, is_retry=False):
    """Mock the http_get function."""
    return mock_post(blink, url)


class TestAPI(unittest.TestCase):
    """Test API calls."""

    def setUp(self):
        """Set up Login Handler."""
        self.account_id = 123456
        self.client_id = 987654
        self.region_id = "mock"
        self.blink = MockBlink(self.region_id, self.account_id, self.client_id)

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    @mock.patch("__main__.api.http_get", side_effect=mock_get)
    @mock.patch("__main__.api.http_post", side_effect=mock_post)
    def test_malformed_urls(self, mockpost, mockget):
        """Check request_networks function."""
        self.assertTrue(api.request_networks(self.blink))
        self.assertTrue(api.request_network_status(self.blink, 1))
        self.assertTrue(api.request_syncmodule(self.blink, 1))
        self.assertTrue(api.request_system_arm(self.blink, 1))
        self.assertTrue(api.request_system_disarm(self.blink, 1))
        self.assertTrue(api.request_command_status(self.blink, 1, 2))
        self.assertTrue(api.request_homescreen(self.blink))
        self.assertTrue(api.request_sync_events(self.blink, 1))
        self.assertTrue(api.request_new_image(self.blink, 1, 2))
        self.assertTrue(api.request_new_video(self.blink, 1, 2))
        self.assertTrue(api.request_video_count(self.blink))
        self.assertTrue(api.request_videos(self.blink))
        self.assertTrue(api.request_cameras(self.blink, 1))
        self.assertTrue(api.request_camera_info(self.blink, 1, 2))
        self.assertTrue(api.request_camera_sensors(self.blink, 1, 2))
        self.assertTrue(api.request_motion_detection_enable(self.blink, 1, 2))
        self.assertTrue(api.request_motion_detection_disable(self.blink, 1, 2))


class MockBlink:
    """Object to mock basic blink class."""

    def __init__(self, region_id, account_id, client_id):
        """Initialize mock blink class."""
        self.urls = BlinkURLHandler(region_id)
        self.account_id = account_id
        self.client_id = client_id
