#!/usr/bin/env python3
"""Test custom filename_format parameter in download_videos()."""

import datetime
import os
from unittest import mock, IsolatedAsyncioTestCase
from blinkpy import blinkpy


class TestCustomFilenameFormat(IsolatedAsyncioTestCase):
    """Test custom filename formatting for video downloads."""

    def setUp(self):
        """Set up test fixtures."""
        self.blink = blinkpy.Blink(session=mock.AsyncMock())
        self.blink.last_refresh = 0

    def test_default_format_unchanged(self):
        """Verify default format still works (backward compatibility)."""
        created_at = "2024-01-15T14:30:22Z"
        camera_name = "Front Door"
        path = "/tmp/videos"

        result = self.blink._format_filename_default(created_at, camera_name, path)

        # Should contain path and end with .mp4
        assert result.startswith(path)
        assert result.endswith(".mp4")
        # Should be slugified (lowercase, no spaces)
        assert "front-door" in result.lower()

    def test_custom_format_simple(self):
        """Test simple custom format."""

        def simple_format(created_at, camera_name, path):
            """Create a simple format with camera name and timestamp."""
            clean_camera = camera_name.replace(" ", "_")
            filename = f"{clean_camera}_{created_at}.mp4"
            return os.path.join(path, filename)

        created_at = "2024-01-15T14:30:22Z"
        camera_name = "Front Door"
        path = "/tmp/videos"

        result = simple_format(created_at, camera_name, path)

        assert result == "/tmp/videos/Front_Door_2024-01-15T14:30:22Z.mp4"
        assert "Front_Door" in result
        assert created_at in result

    def test_custom_format_iso_style(self):
        """Test ISO-style custom format."""

        def iso_format(created_at, camera_name, path):
            """Create ISO-style format."""
            # Replace 'Z' with '+00:00' for fromisoformat compatibility
            dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            clean_camera = camera_name.replace(" ", "_")
            filename = f"{dt:%Y-%m-%d_%H-%M-%S}_{clean_camera}.mp4"
            return os.path.join(path, filename)

        created_at = "2024-01-15T14:30:22Z"
        camera_name = "Back Patio"
        path = "/videos/archive"

        result = iso_format(created_at, camera_name, path)

        assert result.startswith("/videos/archive")
        assert "2024-01-15" in result
        assert "14-30-22" in result
        assert "Back_Patio" in result

    def test_custom_format_minimal(self):
        """Test minimal format with timestamp only."""

        def minimal_format(created_at, camera_name, path):
            """Create minimal format using unix timestamp."""
            # Replace 'Z' with '+00:00' for fromisoformat compatibility
            dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            timestamp = int(dt.timestamp())
            return os.path.join(path, f"{timestamp}.mp4")

        created_at = "2024-01-15T14:30:22Z"
        camera_name = "Whatever"
        path = "/tmp"

        result = minimal_format(created_at, camera_name, path)

        assert result.startswith("/tmp")
        assert result.endswith(".mp4")
        assert any(c.isdigit() for c in result)

    @mock.patch("blinkpy.blinkpy.api.request_videos")
    async def test_download_with_custom_format(self, mock_req):
        """Test download_videos() accepts filename_format parameter."""

        def custom_format(created_at, camera_name, path):
            """Create custom format for testing."""
            return os.path.join(path, f"{camera_name}_{created_at}.mp4")

        # Mock video entry
        entry = {
            "created_at": "2024-01-15T14:30:22Z",
            "device_name": "TestCamera",
            "deleted": False,
            "media": "/some/media/url",
        }
        mock_req.return_value = {"media": [entry]}

        # Verify the download_videos signature accepts filename_format
        try:
            await self.blink.download_videos(
                "/tmp",
                stop=2,
                delay=0,
                debug=True,
                filename_format=custom_format,
            )
        except TypeError as e:
            self.fail(f"download_videos() doesn't support filename_format: {e}")


if __name__ == "__main__":
    import unittest

    unittest.main()
