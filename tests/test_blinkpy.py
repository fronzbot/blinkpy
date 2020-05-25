"""
Test full system.

Tests the system initialization and attributes of
the main Blink system.  Tests if we properly catch
any communication related errors at startup.
"""

import unittest
from unittest import mock
from blinkpy.blinkpy import Blink, BlinkSetupError
from blinkpy.helpers.constants import __version__


class TestBlinkSetup(unittest.TestCase):
    """Test the Blink class in blinkpy."""

    def setUp(self):
        """Initialize blink test object."""
        self.blink = Blink()
        self.blink.available = True

    def tearDown(self):
        """Cleanup blink test object."""
        self.blink = None

    def test_initialization(self):
        """Verify we can initialize blink."""
        blink = Blink()
        self.assertEqual(blink.version, __version__)

    def test_network_id_failure(self):
        """Check that with bad network data a setup error is raised."""
        self.blink.networks = None
        with self.assertRaises(BlinkSetupError):
            self.blink.setup_network_ids()

    def test_multiple_networks(self):
        """Check that we handle multiple networks appropriately."""
        self.blink.networks = {
            "0000": {"onboarded": False, "name": "foo"},
            "5678": {"onboarded": True, "name": "bar"},
            "1234": {"onboarded": False, "name": "test"},
        }
        self.blink.setup_network_ids()
        self.assertTrue("5678" in self.blink.network_ids)

    def test_multiple_onboarded_networks(self):
        """Check that we handle multiple networks appropriately."""
        self.blink.networks = {
            "0000": {"onboarded": False, "name": "foo"},
            "5678": {"onboarded": True, "name": "bar"},
            "1234": {"onboarded": True, "name": "test"},
        }
        self.blink.setup_network_ids()
        self.assertTrue("0000" not in self.blink.network_ids)
        self.assertTrue("5678" in self.blink.network_ids)
        self.assertTrue("1234" in self.blink.network_ids)

    @mock.patch("blinkpy.blinkpy.time.time")
    def test_throttle(self, mock_time):
        """Check throttling functionality."""
        now = self.blink.refresh_rate + 1
        mock_time.return_value = now
        self.assertEqual(self.blink.last_refresh, None)
        self.assertEqual(self.blink.check_if_ok_to_update(), True)
        self.assertEqual(self.blink.last_refresh, None)
        with mock.patch(
            "blinkpy.sync_module.BlinkSyncModule.refresh", return_value=True
        ):
            self.blink.refresh()

        self.assertEqual(self.blink.last_refresh, now)
        self.assertEqual(self.blink.check_if_ok_to_update(), False)
        self.assertEqual(self.blink.last_refresh, now)

    def test_sync_case_insensitive_dict(self):
        """Check that we can access sync modules ignoring case."""
        self.blink.sync["test"] = 1234
        self.assertEqual(self.blink.sync["test"], 1234)
        self.assertEqual(self.blink.sync["TEST"], 1234)
        self.assertEqual(self.blink.sync["tEsT"], 1234)

    @mock.patch("blinkpy.api.request_homescreen")
    def test_setup_cameras(self, mock_home):
        """Check retrieval of camera information."""
        mock_home.return_value = {
            "cameras": [
                {"name": "foo", "network_id": 1234, "id": 5678},
                {"name": "bar", "network_id": 1234, "id": 5679},
                {"name": "test", "network_id": 4321, "id": 0000},
            ]
        }
        result = self.blink.setup_camera_list()
        self.assertEqual(
            result,
            {
                "1234": [{"name": "foo", "id": 5678}, {"name": "bar", "id": 5679}],
                "4321": [{"name": "test", "id": 0000}],
            },
        )

    @mock.patch("blinkpy.api.request_homescreen")
    def test_setup_cameras_failure(self, mock_home):
        """Check that on failure we raise a setup error."""
        mock_home.return_value = {}
        with self.assertRaises(BlinkSetupError):
            self.blink.setup_camera_list()

    def test_setup_urls(self):
        """Check setup of URLS."""
        self.blink.auth.region_id = "test"
        self.blink.setup_urls()
        self.assertEqual(self.blink.urls.subdomain, "rest-test")

    def test_setup_urls_failure(self):
        """Check that on failure we raise a setup error."""
        self.blink.auth.region_id = None
        with self.assertRaises(BlinkSetupError):
            self.blink.setup_urls()

    @mock.patch("blinkpy.api.request_networks")
    def test_setup_networks(self, mock_networks):
        """Check setup of networks."""
        mock_networks.return_value = {"summary": "foobar"}
        self.blink.setup_networks()
        self.assertEqual(self.blink.networks, "foobar")

    @mock.patch("blinkpy.api.request_networks")
    def test_setup_networks_failure(self, mock_networks):
        """Check that on failure we raise a setup error."""
        mock_networks.return_value = {}
        with self.assertRaises(BlinkSetupError):
            self.blink.setup_networks()

    @mock.patch("blinkpy.blinkpy.Auth.send_auth_key")
    def test_setup_prompt_2fa(self, mock_key):
        """Test setup with 2fa prompt."""
        self.blink.auth.data["username"] = "foobar"
        self.blink.key_required = True
        mock_key.return_value = True
        with mock.patch("builtins.input", return_value="foo"):
            self.blink.setup_prompt_2fa()
        self.assertFalse(self.blink.key_required)
        mock_key.return_value = False
        with mock.patch("builtins.input", return_value="foo"):
            self.blink.setup_prompt_2fa()
        self.assertTrue(self.blink.key_required)

    @mock.patch("blinkpy.blinkpy.Blink.setup_camera_list")
    @mock.patch("blinkpy.api.request_networks")
    def test_setup_post_verify(self, mock_networks, mock_camera):
        """Test setup after verification."""
        self.blink.available = False
        self.blink.key_required = True
        mock_networks.return_value = {
            "summary": {"foo": {"onboarded": False, "name": "bar"}}
        }
        mock_camera.return_value = []
        self.assertTrue(self.blink.setup_post_verify())
        self.assertTrue(self.blink.available)
        self.assertFalse(self.blink.key_required)

    @mock.patch("blinkpy.api.request_networks")
    def test_setup_post_verify_failure(self, mock_networks):
        """Test failed setup after verification."""
        self.blink.available = False
        mock_networks.return_value = {}
        self.assertFalse(self.blink.setup_post_verify())
        self.assertFalse(self.blink.available)

    def test_merge_cameras(self):
        """Test merging of cameras."""
        self.blink.sync = {
            "foo": MockSync({"test": 123, "foo": "bar"}),
            "bar": MockSync({"fizz": "buzz", "bar": "foo"}),
        }
        combined = self.blink.merge_cameras()
        self.assertEqual(combined["test"], 123)
        self.assertEqual(combined["foo"], "bar")
        self.assertEqual(combined["fizz"], "buzz")
        self.assertEqual(combined["bar"], "foo")


class MockSync:
    """Mock sync module class."""

    def __init__(self, cameras):
        """Initialize fake class."""
        self.cameras = cameras
