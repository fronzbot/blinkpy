"""Tests for AI video descriptions and v4 media endpoint support."""

from unittest import mock
from unittest import IsolatedAsyncioTestCase
from blinkpy import api
from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import BlinkURLHandler
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera

# Sample v4 media entry with AI description and CV detection
V4_ENTRY_WITH_AI = {
    "device_name": "Front Door",
    "media": "/api/v4/accounts/1234/media/999/video/contents",
    "created_at": "1990-01-01T00:00:00+00:00",
    "ai_vd": {
        "full_description": "A person is walking on the driveway.",
        "short_description": "Person on driveway.",
    },
    "cv_detection": ["person"],
}

# Sample v4 media entry without AI description (SVD not enabled)
V4_ENTRY_NO_AI = {
    "device_name": "Front Door",
    "media": "/api/v4/accounts/1234/media/888/video/contents",
    "created_at": "1990-01-01T00:00:00+00:00",
    "ai_vd": None,
    "cv_detection": None,
}

# Sample v4 entry with empty ai_vd object
V4_ENTRY_EMPTY_AI = {
    "device_name": "Front Door",
    "media": "/api/v4/accounts/1234/media/777/video/contents",
    "created_at": "1990-01-01T00:00:00+00:00",
    "ai_vd": {},
    "cv_detection": ["vehicle"],
}

# Full v4 response
V4_RESPONSE = {
    "media": [V4_ENTRY_WITH_AI],
    "moment_gap_time": 25,
    "page_size": 200,
    "pagination_key": None,
    "smart_video_descriptions": True,
}

# Camera config used by TestCameraAIAttributes
CAMERA_CFG = {
    "name": "foobar",
    "id": 1234,
    "network_id": 5678,
    "serial": "12345678",
    "enabled": False,
    "battery_state": "ok",
    "battery_voltage": 163,
    "wifi_strength": -38,
    "signals": {"lfr": 5, "wifi": 4, "battery": 3, "temp": 68},
    "thumbnail": "/thumb",
}


@mock.patch("blinkpy.auth.Auth.query")
class TestV4MediaEndpoint(IsolatedAsyncioTestCase):
    """Test the v4 media endpoint API function."""

    async def asyncSetUp(self):
        """Set up Blink module."""
        self.blink = Blink(session=mock.AsyncMock())
        self.blink.urls = BlinkURLHandler("test")
        self.blink.auth.account_id = 1234

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    async def test_request_videos_v4(self, mock_resp):
        """Test v4 media endpoint returns expected data."""
        mock_resp.return_value = V4_RESPONSE
        result = await api.request_videos_v4(self.blink)
        self.assertIn("media", result)
        self.assertEqual(len(result["media"]), 1)
        self.assertIn("ai_vd", result["media"][0])

    async def test_request_videos_v4_empty_response(self, mock_resp):
        """Test v4 endpoint with empty response."""
        mock_resp.return_value = None
        result = await api.request_videos_v4(self.blink)
        self.assertIsNone(result)

    async def test_request_videos_v4_no_media(self, mock_resp):
        """Test v4 endpoint with response missing media key."""
        mock_resp.return_value = {"error": "something went wrong"}
        result = await api.request_videos_v4(self.blink)
        self.assertNotIn("media", result)


@mock.patch("blinkpy.auth.Auth.query")
class TestAIDescriptionExtraction(IsolatedAsyncioTestCase):
    """Test AI description extraction in check_new_videos."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = Blink(motion_interval=0, session=mock.AsyncMock())
        self.blink.last_refresh = 1000
        self.blink.urls = BlinkURLHandler("test")
        self.blink.sync["test"] = BlinkSyncModule(self.blink, "test", "1234", [])
        self.blink.sync["test"].network_info = {"network": {"armed": True}}

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    async def test_v4_ai_description_extracted(self, mock_resp):
        """Test that ai_vd is extracted from v4 media entries."""
        mock_resp.return_value = {"media": [V4_ENTRY_WITH_AI]}
        sync_module = self.blink.sync["test"]
        sync_module.cameras = {"Front Door": None}
        self.assertTrue(await sync_module.check_new_videos())
        records = sync_module.last_records["Front Door"]
        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0]["ai_description"],
            "A person is walking on the driveway.",
        )
        self.assertEqual(records[0]["ai_description_short"], "Person on driveway.")
        self.assertEqual(records[0]["cv_detection"], ["person"])

    async def test_v4_no_ai_description(self, mock_resp):
        """Test graceful handling when ai_vd is None."""
        mock_resp.return_value = {"media": [V4_ENTRY_NO_AI]}
        sync_module = self.blink.sync["test"]
        sync_module.cameras = {"Front Door": None}
        self.assertTrue(await sync_module.check_new_videos())
        records = sync_module.last_records["Front Door"]
        self.assertEqual(len(records), 1)
        # No ai_description keys should be present
        self.assertNotIn("ai_description", records[0])
        self.assertNotIn("ai_description_short", records[0])

    async def test_v4_empty_ai_vd_object(self, mock_resp):
        """Test graceful handling when ai_vd is an empty dict."""
        mock_resp.return_value = {"media": [V4_ENTRY_EMPTY_AI]}
        sync_module = self.blink.sync["test"]
        sync_module.cameras = {"Front Door": None}
        self.assertTrue(await sync_module.check_new_videos())
        records = sync_module.last_records["Front Door"]
        self.assertEqual(len(records), 1)
        # Empty dict should not produce ai_description keys
        self.assertNotIn("ai_description", records[0])
        # But cv_detection should still be extracted
        self.assertEqual(records[0]["cv_detection"], ["vehicle"])


@mock.patch("blinkpy.auth.Auth.query", return_value={})
class TestCameraAIAttributes(IsolatedAsyncioTestCase):
    """Test AI description attributes on camera objects."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = Blink(session=mock.AsyncMock())
        self.blink.urls = BlinkURLHandler("test")
        self.blink.sync["test"] = BlinkSyncModule(self.blink, "test", 1234, [])
        self.camera = BlinkCamera(self.blink.sync["test"])
        self.camera.name = "foobar"
        self.blink.sync["test"].cameras["foobar"] = self.camera

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.camera = None

    async def test_camera_attributes_include_ai_fields(self, mock_resp):
        """Test that camera attributes include AI description fields."""
        attrs = self.camera.attributes
        self.assertIn("ai_description", attrs)
        self.assertIn("ai_description_short", attrs)
        self.assertIn("cv_detection", attrs)
        # Initially None
        self.assertIsNone(attrs["ai_description"])
        self.assertIsNone(attrs["ai_description_short"])
        self.assertIsNone(attrs["cv_detection"])

    async def test_camera_ai_description_from_records(self, mock_resp):
        """Test that camera picks up AI description from last records."""
        self.camera.sync.last_records["foobar"] = [
            {
                "clip": "/clip.mp4",
                "time": "2024-01-01T00:00:00+00:00",
                "ai_description": "A cat sitting on the porch.",
                "ai_description_short": "Cat on porch.",
                "cv_detection": ["animal"],
            }
        ]
        self.camera.sync.motion["foobar"] = True
        await self.camera.update(CAMERA_CFG, force_cache=False)
        self.assertEqual(self.camera.ai_description, "A cat sitting on the porch.")
        self.assertEqual(self.camera.ai_description_short, "Cat on porch.")
        self.assertEqual(self.camera.cv_detection, ["animal"])

    async def test_camera_no_ai_description_in_records(self, mock_resp):
        """Test camera handles records without AI description gracefully."""
        self.camera.sync.last_records["foobar"] = [
            {
                "clip": "/clip.mp4",
                "time": "2024-01-01T00:00:00+00:00",
            }
        ]
        self.camera.sync.motion["foobar"] = True
        await self.camera.update(CAMERA_CFG, force_cache=False)
        # Should be None since record didn't have these keys
        self.assertIsNone(self.camera.ai_description)
        self.assertIsNone(self.camera.ai_description_short)
        self.assertIsNone(self.camera.cv_detection)

    async def test_camera_recent_clips_include_ai_fields(self, mock_resp):
        """Test that recent_clips entries include AI description fields."""
        self.camera.sync.last_records["foobar"] = [
            {
                "clip": "/clip.mp4",
                "time": "2024-01-01T00:00:00+00:00",
                "ai_description": "A delivery person at the door.",
                "cv_detection": ["person"],
            }
        ]
        self.camera.sync.motion["foobar"] = True
        await self.camera.update_images(CAMERA_CFG, expire_clips=False)
        self.assertEqual(len(self.camera.recent_clips), 1)
        clip = self.camera.recent_clips[0]
        self.assertEqual(clip["ai_description"], "A delivery person at the door.")
        self.assertEqual(clip["cv_detection"], ["person"])

    async def test_clip_url_absolute_not_doubled(self, mock_resp):
        """Test that absolute clip URLs from v4 are not doubled with base_url."""
        absolute_url = "https://rest-u009.immedia-semi.com/api/v4/media/123/video"
        self.camera.sync.last_records["foobar"] = [
            {
                "clip": absolute_url,
                "time": "2024-01-01T00:00:00+00:00",
            }
        ]
        self.camera.sync.motion["foobar"] = False
        await self.camera.update(CAMERA_CFG, force_cache=False)
        # URL should NOT be doubled (no base_url prepended)
        self.assertEqual(self.camera.clip, absolute_url)

    async def test_clip_url_relative_gets_base_url(self, mock_resp):
        """Test that relative clip URLs still get base_url prepended."""
        self.camera.sync.last_records["foobar"] = [
            {
                "clip": "/api/v1/media/123.mp4",
                "time": "2024-01-01T00:00:00+00:00",
            }
        ]
        self.camera.sync.motion["foobar"] = False
        await self.camera.update(CAMERA_CFG, force_cache=False)
        self.assertEqual(
            self.camera.clip,
            f"{self.blink.urls.base_url}/api/v1/media/123.mp4",
        )
