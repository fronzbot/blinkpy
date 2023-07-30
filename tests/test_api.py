"""Test api functions."""

from unittest import mock
from unittest import IsolatedAsyncioTestCase
from blinkpy import api
from blinkpy.blinkpy import Blink, util
from blinkpy.auth import Auth
import tests.mock_responses as mresp


@mock.patch("blinkpy.auth.Auth.query")
class TestAPI(IsolatedAsyncioTestCase):
    """Test the API class in blinkpy."""

    def setUp(self):
        """Set up Login Handler."""
        self.blink = Blink(session=mock.AsyncMock())
        self.auth = Auth(session=mock.AsyncMock())
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
        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        response = await api.request_verify(self.auth, self.blink, "test key")
        self.assertEqual(response.status, 200)
        
        mock_resp.return_value = mresp.MockResponseDict({}, 200)
        self.assertIsNone(await api.request_verify(self.auth, self.blink, "test key"))

    async def test_request_logout(self, mock_resp):
        """Test request_logout."""
        mock_resp.return_value = mresp.MockResponseDict({}, 200)
        response = await api.request_logout(self.blink)
        self.assertEqual(response.status, 200)

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_logout(self.blink))

    async def test_request_networks(self, mock_resp):
        """Test request networks."""
        mock_resp.return_value = {"networks": "1234"}
        self.assertEqual(await api.request_networks(self.blink), {"networks": "1234"})

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_networks(self.blink))

    async def test_request_user(self, mock_resp):
        """Test request_user."""
        mock_resp.return_value = {"user": "userid"}
        self.assertEqual(await api.request_user(self.blink), {"user": "userid"})

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_user(self.blink))

    async def test_request_network_status(self, mock_resp):
        """Test request network status."""
        mock_resp.return_value = {"user": "userid"}
        self.assertEqual(
            await api.request_network_status(self.blink, "network"), {"user": "userid"}
        )

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_network_status(self.blink, "network"))

    async def test_request_command_status(self, mock_resp):
        """Test command_status."""
        mock_resp.return_value = {"command": "done"}
        self.assertEqual(
            await api.request_command_status(self.blink, "network", "command"),
            {"command": "done"},
        )
        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_command_status(self.blink, "network", "command"))

    async def test_request_new_image(self, mock_resp):
        """Test api request new image."""
        mock_resp.return_value = mresp.MockResponseDict({}, 200)
        response = await api.request_new_image(self.blink, "network", "camera")
        self.assertEqual(response.status, 200)

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_new_image(self.blink,"Network","Camera",force=True))

    async def test_request_new_video(self, mock_resp):
        """Test api request new Video."""
        mock_resp.return_value = mresp.MockResponseDict({}, 200)
        response = await api.request_new_video(self.blink, "network", "camera")
        self.assertEqual(response.status, 200)

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_new_video(self.blink, "network", "camera",force=True))


    async def test_request_video_count(self, mock_resp):
        """Test api request video count."""
        mock_resp.return_value = {"count": "10"}
        self.assertEqual(await api.request_video_count(self.blink), {"count": "10"})

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_video_count(self.blink,force=True))


    async def test_request_cameras(self, mock_resp):
        """Test api request cameras."""
        mock_resp.return_value = {"cameras": {"camera_id": 1}}
        self.assertEqual(
            await api.request_cameras(self.blink, "network"),
            {"cameras": {"camera_id": 1}},
        )

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_cameras(self.blink, "network"))

    async def test_request_camera_usage(self, mock_resp):
        """Test api request cameras."""
        mock_resp.return_value = {"cameras": "1111"}
        self.assertEqual(
            await api.request_camera_usage(self.blink), {"cameras": "1111"}
        )
        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_camera_usage(self.blink))

    async def test_request_motion_detection_enable(self, mock_resp):
        """Test  Motion detect enable."""
        mock_resp.return_value = mresp.MockResponseDict({}, 200)
        response = await api.request_motion_detection_enable(
            self.blink, "network", "camera"
        )
        self.assertEqual(response.status,200)

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_motion_detection_enable(
            self.blink, "network", "camera",force=True
        ))

    async def test_request_motion_detection_disable(self, mock_resp):
        """Test  Motion detect enable."""
        mock_resp.return_value = mresp.MockResponseDict({}, 200)
        response = await api.request_motion_detection_disable(
            self.blink, "network", "camera"
        )
        self.assertEqual(response.status, 200)

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_motion_detection_disable(
            self.blink, "network", "camera",force=True
        ))

    async def test_request_local_storage_clip(self, mock_resp):
        """Test Motion detect enable."""
        mock_resp.return_value = mresp.MockResponseDict({}, 200)
        response = await api.request_local_storage_clip(
            self.blink, "network", "sync_id", "manifest_id", "clip_id"
        )
        self.assertEqual(response.status, 200)

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_local_storage_clip(
            self.blink, "network", "sync_id", "manifest_id", "clip_id"
        ))

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

        mock_resp.return_value = mresp.MockResponseClient({}, 200)
        self.assertIsNone(await api.request_get_config(
                self.blink, "network", "camera_id", "catalina"
            ))


    async def test_request_update_config(self, mock_resp):
        """Test Motion detect enable."""
        mock_resp.return_value = mresp.MockResponseClient({}, 200)
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

        self.assertIsNone(await api.request_update_config(
                self.blink, "network", "camera_id", "other_camera"
            ))
        
        mock_resp.return_value = mresp.MockResponseDict({}, 200)
        self.assertIsNone(await api.request_update_config(
                self.blink, "network", "camera_id", "catalina"
            ))
    async def test_request_system_arm_disarm(self,mock_resp):
        """Test system arm/disarm functions fail with bad response."""
        with mock.patch("blinkpy.api.http_post", return_value = {"1":"2"}):
            self.assertEqual(await api.request_system_arm(self.blink,"network"),{"1":"2"})
            self.assertEqual(await api.request_system_disarm(self.blink,"network"),{"1":"2"})
        with mock.patch("blinkpy.api.http_post", return_value = ""):
            self.assertIsNone(await api.request_system_arm(self.blink,"network"))
            self.assertIsNone(await api.request_system_disarm(self.blink,"network"))
            
    async def test_request_homescreen(self,mock_resp):
        """Test system homescreen functions fail with bad response."""
        with mock.patch("blinkpy.api.http_get", return_value = {"1":"2"}):
            self.assertEqual(await api.request_homescreen(self.blink),{"1":"2"})
        with mock.patch("blinkpy.api.http_get", return_value = ""):
            self.assertIsNone(await api.request_homescreen(self.blink,force=True))
    
    async def test_request_sync_events(self,mock_resp):
        """Test request sync events api."""
        with mock.patch("blinkpy.api.http_get", return_value = {"1":"2"}):
            self.assertEqual(await api.request_sync_events(self.blink,"Network"),{"1":"2"})
        with mock.patch("blinkpy.api.http_get", return_value = ""):
            self.assertIsNone(await api.request_sync_events(self.blink,"Network",force=True))

    async def test_request_camera_liveview(self,mock_resp):
        """Test request camera liveview api."""
        with mock.patch("blinkpy.api.http_post",return_value = {"1":"2"}):
            self.assertEqual(await api.request_camera_liveview(self.blink,"Network","Camera"),{"1":"2"})
        with mock.patch("blinkpy.api.http_post", return_value = ""):
            self.assertIsNone(await api.request_camera_liveview(self.blink,"Network","Camera"))

    async def test_request_local_manifest(self,mock_resp):
        """Test request camera liveview api."""
        with mock.patch("blinkpy.api.http_post",return_value = {"1":"2"}):
            self.assertEqual(await api.request_local_storage_manifest(self.blink,"Network","Camera"),{"1":"2"})
        with mock.patch("blinkpy.api.http_post", return_value = ""):
            self.assertIsNone(await api.request_local_storage_manifest(self.blink,"Network","Camera"))

    async def test_get_local_storage_manifest(self,mock_resp):
        """Test request camera liveview api."""
        with mock.patch("blinkpy.api.http_get",return_value = {"1":"2"}):
            self.assertEqual(await api.get_local_storage_manifest(self.blink,"Network","sync","manifest"),{"1":"2"})
        with mock.patch("blinkpy.api.http_get", return_value = ""):
            self.assertIsNone(await api.get_local_storage_manifest(self.blink,"Network","sync","manifest"))
