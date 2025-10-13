"""Test api functions."""

from unittest import mock
from unittest import IsolatedAsyncioTestCase
from blinkpy import api
from blinkpy.blinkpy import Blink, util
from blinkpy.auth import Auth
import tests.mock_responses as mresp

COMMAND_RESPONSE = {"network_id": "12345", "id": "54321"}
COMMAND_COMPLETE = {"complete": True, "status_code": 908}
COMMAND_COMPLETE_BAD = {"complete": True, "status_code": 999}
COMMAND_NOT_COMPLETE = {"complete": False, "status_code": 908}


@mock.patch("blinkpy.auth.Auth.query")
class TestAPI(IsolatedAsyncioTestCase):
    """Test the API class in blinkpy."""

    async def asyncSetUp(self):
        """Set up Login Handler."""
        self.blink = Blink(session=mock.AsyncMock())
        self.auth = Auth()
        self.blink.available = True
        self.blink.urls = util.BlinkURLHandler("region_id")
        self.blink.account_id = 1234
        self.blink.client_id = 5678

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.auth = None

    async def test_request_verify(self, mock_resp):
        """Test api request verify."""
        mock_resp.return_value = mresp.MockResponse({}, 200)
        response = await api.request_verify(self.auth, self.blink, "test key")
        self.assertEqual(response.status, 200)

    async def test_request_logout(self, mock_resp):
        """Test request_logout."""
        mock_resp.return_value = mresp.MockResponse({}, 200)
        response = await api.request_logout(self.blink)
        self.assertEqual(response.status, 200)

    async def test_request_networks(self, mock_resp):
        """Test request networks."""
        mock_resp.return_value = {"networks": "1234"}
        self.assertEqual(await api.request_networks(self.blink), {"networks": "1234"})

    async def test_request_user(self, mock_resp):
        """Test request_user."""
        mock_resp.return_value = {"user": "userid"}
        self.assertEqual(await api.request_user(self.blink), {"user": "userid"})

    async def test_request_network_status(self, mock_resp):
        """Test request network status."""
        mock_resp.return_value = {"user": "userid"}
        self.assertEqual(
            await api.request_network_status(self.blink, "network"), {"user": "userid"}
        )

    async def test_request_command_status(self, mock_resp):
        """Test command_status."""
        mock_resp.side_effect = ({"command": "done"}, COMMAND_COMPLETE)
        self.assertEqual(
            await api.request_command_status(self.blink, "network", "command"),
            {"command": "done"},
        )

    async def test_request_new_image(self, mock_resp):
        """Test api request new image."""
        mock_resp.side_effect = (
            mresp.MockResponse(COMMAND_RESPONSE, 200),
            COMMAND_COMPLETE,
        )
        response = await api.request_new_image(self.blink, "network", "camera")
        self.assertEqual(response.status, 200)

    async def test_request_new_video(self, mock_resp):
        """Test api request new Video."""
        mock_resp.side_effect = (
            mresp.MockResponse(COMMAND_RESPONSE, 200),
            COMMAND_COMPLETE,
        )
        response = await api.request_new_video(self.blink, "network", "camera")
        self.assertEqual(response.status, 200)

    async def test_request_video_count(self, mock_resp):
        """Test api request video count."""
        mock_resp.return_value = {"count": "10"}
        self.assertEqual(await api.request_video_count(self.blink), {"count": "10"})

    async def test_request_cameras(self, mock_resp):
        """Test api request cameras."""
        mock_resp.return_value = {"cameras": {"camera_id": 1}}
        self.assertEqual(
            await api.request_cameras(self.blink, "network"),
            {"cameras": {"camera_id": 1}},
        )

    async def test_request_camera_usage(self, mock_resp):
        """Test api request cameras."""
        mock_resp.return_value = {"cameras": "1111"}
        self.assertEqual(
            await api.request_camera_usage(self.blink), {"cameras": "1111"}
        )

    async def test_request_notification_flags(self, mock_resp):
        """Test notification flag request."""
        mock_resp.return_value = {"notifications": {"some_key": False}}
        self.assertEqual(
            await api.request_notification_flags(self.blink),
            {"notifications": {"some_key": False}},
        )

    async def test_request_set_notification_flag(self, mock_resp):
        """Test set of notifiaction flags."""
        mock_resp.side_effect = (
            mresp.MockResponse(COMMAND_RESPONSE, 200),
            COMMAND_COMPLETE,
        )
        response = await api.request_set_notification_flag(self.blink, {})
        self.assertEqual(response.status, 200)

    async def test_request_motion_detection_enable(self, mock_resp):
        """Test  Motion detect enable."""
        mock_resp.side_effect = (
            mresp.MockResponse(COMMAND_RESPONSE, 200),
            COMMAND_COMPLETE,
        )
        response = await api.request_motion_detection_enable(
            self.blink, "network", "camera"
        )
        self.assertEqual(response.status, 200)

    async def test_request_motion_detection_disable(self, mock_resp):
        """Test  Motion detect enable."""
        mock_resp.side_effect = (
            mresp.MockResponse(COMMAND_RESPONSE, 200),
            COMMAND_COMPLETE,
        )
        response = await api.request_motion_detection_disable(
            self.blink, "network", "camera"
        )
        self.assertEqual(response.status, 200)

    async def test_request_local_storage_clip(self, mock_resp):
        """Test Motion detect enable."""
        mock_resp.side_effect = (
            mresp.MockResponse(COMMAND_RESPONSE, 200),
            COMMAND_COMPLETE,
        )
        response = await api.request_local_storage_clip(
            self.blink, "network", "sync_id", "manifest_id", "clip_id"
        )
        self.assertEqual(response.status, 200)

    async def test_request_get_config(self, mock_resp):
        """Test request get config."""
        mock_resp.return_value = {"config": "values"}
        self.assertEqual(
            await api.request_get_config(self.blink, "network", "camera_id", "owl"),
            {"config": "values"},
        )
        self.assertEqual(
            await api.request_get_config(
                self.blink, "network", "camera_id", "catalina"
            ),
            {"config": "values"},
        )

    async def test_request_update_config(self, mock_resp):
        """Test Motion detect enable."""
        mock_resp.return_value = mresp.MockResponse(COMMAND_RESPONSE, 200)
        response = await api.request_update_config(
            self.blink, "network", "camera_id", "owl"
        )
        self.assertEqual(response.status, 200)
        response = await api.request_update_config(
            self.blink, "network", "camera_id", "catalina"
        )
        self.assertEqual(response.status, 200)
        self.assertIsNone(
            await api.request_update_config(
                self.blink, "network", "camera_id", "other_camera"
            )
        )

    async def test_wait_for_command(self, mock_resp):
        """Test Motion detect enable."""
        mock_resp.side_effect = (COMMAND_NOT_COMPLETE, COMMAND_COMPLETE)
        response = await api.wait_for_command(self.blink, COMMAND_RESPONSE)
        assert response

        # mock_resp.side_effect = (COMMAND_NOT_COMPLETE, COMMAND_NOT_COMPLETE, None)
        # response = await api.wait_for_command(self.blink, COMMAND_RESPONSE)
        # self.assertFalse(response)

        mock_resp.side_effect = (COMMAND_COMPLETE_BAD, {})
        response = await api.wait_for_command(self.blink, COMMAND_RESPONSE)
        self.assertFalse(response)

        response = await api.wait_for_command(self.blink, None)
        self.assertFalse(response)

    async def test_request_camera_snooze(self, mock_resp):
        """Test request_camera_snooze."""
        mock_resp.return_value = mresp.MockResponse({}, 200)
        response = await api.request_camera_snooze(
            self.blink, "network", "camera_id", "owl", {}
        )
        self.assertEqual(response.status, 200)
        response = await api.request_camera_snooze(
            self.blink, "network", "camera_id", "catalina", {}
        )
        self.assertEqual(response.status, 200)
        response = await api.request_camera_snooze(
            self.blink, "network", "camera_id", "doorbell", {}
        )
        self.assertEqual(response.status, 200)

    async def test_request_sync_snooze(self, mock_resp):
        """Test sync snooze update."""
        mock_resp.return_value = mresp.MockResponse({}, 200)
        response = await api.request_sync_snooze(self.blink, "network", {})
        self.assertEqual(response.status, 200)
