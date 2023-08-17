"""Tests camera and system functions."""
import datetime
from unittest import IsolatedAsyncioTestCase
from unittest import mock
import aiofiles
from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import BlinkURLHandler, to_alphanumeric
from blinkpy.sync_module import (
    BlinkSyncModule,
    BlinkOwl,
    BlinkLotus,
    LocalStorageMediaItem,
)
from blinkpy.camera import BlinkCamera
from tests.test_blink_functions import MockCamera
import tests.mock_responses as mresp


@mock.patch("blinkpy.auth.Auth.query")
class TestBlinkSyncModule(IsolatedAsyncioTestCase):
    """Test BlinkSyncModule functions in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink: Blink = Blink(motion_interval=0, session=mock.AsyncMock())
        self.blink.last_refresh = 0
        self.blink.urls = BlinkURLHandler("test")
        self.blink.sync["test"]: (BlinkSyncModule) = BlinkSyncModule(
            self.blink, "test", "1234", []
        )
        self.blink.sync["test"].network_info = {"network": {"armed": True}}
        self.camera: BlinkCamera = BlinkCamera(self.blink.sync)
        self.mock_start = [
            {
                "syncmodule": {
                    "id": 1234,
                    "network_id": 5678,
                    "serial": "12345678",
                    "status": "foobar",
                }
            },
            {"event": True},
            {},
            {},
            None,
            {"devicestatus": {}},
        ]

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.camera = None
        self.mock_start = None

    def test_bad_status(self, mock_resp) -> None:
        """Check that we mark module unavaiable on bad status."""
        self.blink.sync["test"].status = None
        self.blink.sync["test"].available = True
        self.assertFalse(self.blink.sync["test"].online)
        self.assertFalse(self.blink.sync["test"].available)

    async def test_arm(self, mock_resp) -> None:
        """Check that we arm and disarm a module."""
        self.assertTrue(await self.blink.sync["test"].async_arm(True))
        self.assertTrue(await self.blink.sync["test"].async_arm(False))

    def test_bad_arm(self, mock_resp) -> None:
        """Check that we mark module unavaiable if bad arm status."""
        self.blink.sync["test"].network_info = None
        self.blink.sync["test"].available = True
        self.assertEqual(self.blink.sync["test"].arm, None)
        self.assertFalse(self.blink.sync["test"].available)
        self.blink.sync["test"].network_info = {}
        self.blink.sync["test"].available = True
        self.assertEqual(self.blink.sync["test"].arm, None)
        self.assertFalse(self.blink.sync["test"].available)

    async def test_get_events(self, mock_resp) -> None:
        """Test get events function."""
        mock_resp.return_value = {"event": True}
        self.assertEqual(await self.blink.sync["test"].get_events(), True)

    @mock.patch(
        "blinkpy.api.request_sync_events",
        mock.AsyncMock(return_value={"BAD_event": True}),
    )
    async def test_get_events_malformed(self, mock_resp) -> None:
        """Test malformed event message."""
        self.assertFalse(await self.blink.sync["test"].get_events())

    @mock.patch("blinkpy.sync_module.BlinkSyncModule.get_events")
    async def test_get_events_fail(self, mock_get, mock_resp) -> None:
        """Test handling of failed get events function."""
        mock_resp.return_value = None
        mock_get.return_value = None
        self.assertFalse(await self.blink.sync["test"].get_events())
        mock_resp.return_value = {}
        mock_get.return_value = {}
        self.assertFalse(await self.blink.sync["test"].get_events())

    async def test_get_camera_info(self, mock_resp) -> None:
        """Test get camera info function."""
        mock_resp.return_value = {"camera": ["foobar"]}
        self.assertEqual(
            await self.blink.sync["test"].get_camera_info("1234"), "foobar"
        )

    async def test_get_camera_info_fail(self, mock_resp) -> None:
        """Test handling of failed get camera info function."""
        mock_resp.return_value = None
        self.assertEqual(await self.blink.sync["test"].get_camera_info("1"), {})
        mock_resp.return_value = {}
        self.assertEqual(await self.blink.sync["test"].get_camera_info("1"), {})
        mock_resp.return_value = {"camera": None}
        self.assertEqual(await self.blink.sync["test"].get_camera_info("1"), {})

    async def test_get_network_info(self, mock_resp) -> None:
        """Test network retrieval."""
        mock_resp.return_value = {"network": {"sync_module_error": False}}
        self.assertTrue(await self.blink.sync["test"].get_network_info())
        mock_resp.return_value = {"network": {"sync_module_error": True}}
        self.assertFalse(await self.blink.sync["test"].get_network_info())

    async def test_get_network_info_failure(self, mock_resp) -> None:
        """Test failed network retrieval."""
        mock_resp.return_value = {}
        self.blink.sync["test"].available = True
        self.assertFalse(await self.blink.sync["test"].get_network_info())
        self.assertFalse(self.blink.sync["test"].available)
        self.blink.sync["test"].available = True
        mock_resp.return_value = None
        self.assertFalse(await self.blink.sync["test"].get_network_info())
        self.assertFalse(self.blink.sync["test"].available)

    async def test_check_new_videos_startup(self, mock_resp) -> None:
        """Test that check_new_videos does not block startup."""
        sync_module = self.blink.sync["test"]
        self.blink.last_refresh = None
        self.assertFalse(await sync_module.check_new_videos())

    async def test_check_new_videos_failed(self, mock_resp) -> None:
        """Test method when response is unexpected."""
        generic_entry = {
            "device_name": "foo",
            "deleted": True,
            "media": "/bar.mp4",
        }
        result = [generic_entry]
        mock_resp.return_value = {"media": result}
        sync_module = self.blink.sync["test"]
        # I think this should be false - should the exception return False?
        self.assertTrue(await sync_module.check_new_videos())

        mock_resp.side_effect = [None, "just a string", {}]
        sync_module.cameras = {"foo": None}

        sync_module.motion["foo"] = True
        self.assertFalse(await sync_module.check_new_videos())
        self.assertFalse(sync_module.motion["foo"])

        sync_module.motion["foo"] = True
        self.assertFalse(await sync_module.check_new_videos())
        self.assertFalse(sync_module.motion["foo"])

        sync_module.motion["foo"] = True
        self.assertFalse(await sync_module.check_new_videos())
        self.assertFalse(sync_module.motion["foo"])

    async def test_unexpected_summary(self, mock_resp) -> None:
        """Test unexpected summary response."""
        self.mock_start[0] = None
        mock_resp.side_effect = self.mock_start
        self.assertFalse(await self.blink.sync["test"].start())

    async def test_summary_with_no_network_id(self, mock_resp) -> None:
        """Test handling of bad summary."""
        self.mock_start[0]["syncmodule"] = None
        mock_resp.side_effect = self.mock_start
        self.assertFalse(await self.blink.sync["test"].start())

    async def test_missing_key_startup(self, mock_resp) -> None:
        """Test for missing key at sync module startup."""
        del self.mock_start[0]["syncmodule"]["serial"]
        mock_resp.side_effect = self.mock_start
        self.assertFalse(await self.blink.sync["test"].start())

    async def test_summary_with_only_network_id(self, mock_resp) -> None:
        """Test handling of sparse summary."""
        self.mock_start[0]["syncmodule"] = {"network_id": 8675309}
        mock_resp.side_effect = self.mock_start
        await self.blink.sync["test"].start()
        self.assertEqual(self.blink.sync["test"].network_id, 8675309)

    async def test_unexpected_camera_info(self, mock_resp) -> None:
        """Test unexpected camera info response."""
        self.blink.sync["test"].cameras["foo"] = None
        self.mock_start[5] = None
        mock_resp.side_effect = self.mock_start
        await self.blink.sync["test"].start()
        self.assertEqual(self.blink.sync["test"].cameras, {"foo": None})

    async def test_missing_camera_info(self, mock_resp) -> None:
        """Test missing key from camera info response."""
        self.blink.sync["test"].cameras["foo"] = None
        self.mock_start[5] = {}
        await self.blink.sync["test"].start()
        self.assertEqual(self.blink.sync["test"].cameras, {"foo": None})

    def test_sync_attributes(self, mock_resp) -> None:
        """Test sync attributes."""
        self.assertEqual(self.blink.sync["test"].attributes["name"], "test")
        self.assertEqual(self.blink.sync["test"].attributes["network_id"], "1234")

    async def test_name_not_in_config(self, mock_resp) -> None:
        """Check that function exits when name not in camera_config."""
        test_sync = self.blink.sync["test"]
        test_sync.camera_list = [{"foo": "bar"}]
        self.assertTrue(await test_sync.update_cameras())

    async def test_camera_config_key_error(self, mock_resp) -> None:
        """Check that update returns False on KeyError."""
        test_sync = self.blink.sync["test"]
        test_sync.camera_list = [{"name": "foobar"}]
        self.assertFalse(await test_sync.update_cameras())

    @mock.patch(
        "blinkpy.sync_module.BlinkSyncModule.get_network_info",
        mock.AsyncMock(return_value=False),
    )
    async def test_refresh_network_info(self, mock_resp) -> None:
        """Test no network info on refresh."""
        self.assertFalse(await self.blink.sync["test"].refresh())

    async def test_update_local_storage_manifest(self, mock_resp) -> None:
        """Test getting the manifest from the sync module."""
        self.blink.account_id = 10111213
        test_sync = self.blink.sync["test"]
        test_sync._local_storage["status"] = True
        test_sync.sync_id = 1234
        mock_resp.side_effect = [
            {"id": 387372591, "network_id": 123456},
            {
                "version": "1.0",
                "manifest_id": "4321",
                "clips": [
                    {
                        "id": "866333964",
                        "size": "234",
                        "camera_name": "BackDoor",
                        "created_at": "2022-12-01T21:11:50+00:00",
                    },
                    {
                        "id": "1568781420",
                        "size": "430",
                        "camera_name": "FrontDoor",
                        "created_at": "2022-12-01T21:11:22+00:00",
                    },
                    {
                        "id": "1289590916",
                        "size": "425",
                        "camera_name": "BackDoor",
                        "created_at": "2022-12-01T18:12:26+00:00",
                    },
                    {
                        "id": "1893118325",
                        "size": "186",
                        "camera_name": "FrontDoor",
                        "created_at": "2022-12-01T11:35:52+00:00",
                    },
                    {
                        "id": "2358747807",
                        "size": "452",
                        "camera_name": "Yard",
                        "created_at": "2022-12-01T11:34:55+00:00",
                    },
                ],
            },
        ]
        test_sync._names_table[to_alphanumeric("Front Door")] = "Front Door"
        test_sync._names_table[to_alphanumeric("Back Door")] = "Back Door"
        test_sync._names_table[to_alphanumeric("Yard")] = "Yard"
        await test_sync.update_local_storage_manifest()
        self.assertEqual(len(test_sync._local_storage["manifest"]), 5)
        self.assertEqual(
            test_sync._local_storage["manifest"][0].url(),
            "/api/v1/accounts/10111213/networks/1234/sync_modules/1234/local_storage/"
            + "manifest/4321/clip/request/2358747807",
        )
        self.assertEqual(
            test_sync._local_storage["manifest"][4].url(),
            "/api/v1/accounts/10111213/networks/1234/sync_modules/1234/local_storage/"
            + "manifest/4321/clip/request/866333964",
        )

    async def test_check_new_videos_with_local_storage(self, mock_resp) -> None:
        """Test checking new videos in local storage."""
        self.blink.account_id = 10111213
        test_sync = self.blink.sync["test"]
        test_sync._local_storage["status"] = True
        test_sync.sync_id = 1234

        test_sync.cameras["Back Door"] = MockCamera(self.blink.sync)
        test_sync.cameras["Front_Door"] = MockCamera(self.blink.sync)
        created_at = (
            datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
        ).isoformat()
        mock_resp.side_effect = [
            {"id": 387372591, "network_id": 123456},
            {
                "version": "1.0",
                "manifest_id": "4321",
                "clips": [
                    {
                        "id": "866333964",
                        "size": "234",
                        "camera_name": "BackDoor",
                        "created_at": f"{created_at}",
                    },
                    {
                        "id": "1568781420",
                        "size": "430",
                        "camera_name": "Front_Door",
                        "created_at": f"{created_at}",
                    },
                ],
            },
            {"media": []},
            {"id": 489371591, "network_id": 123456},
            {"id": 489371592, "network_id": 123456},
            {"media": []},
            {"id": 489371592, "network_id": 123456},
            {"id": 489371592, "network_id": 123456},
        ]

        test_sync._names_table[to_alphanumeric("Front_Door")] = "Front_Door"
        test_sync._names_table[to_alphanumeric("Back Door")] = "Back Door"
        await test_sync.update_local_storage_manifest()
        self.assertTrue(await test_sync.check_new_videos())
        self.assertTrue(await test_sync.check_new_videos())
        self.assertEqual(
            test_sync.last_records["Back Door"][0]["clip"],
            "/api/v1/accounts/10111213/networks/1234/sync_modules/1234/local_storage/"
            + "manifest/4321/clip/request/866333964",
        )
        self.assertEqual(
            test_sync.last_records["Front_Door"][0]["clip"],
            "/api/v1/accounts/10111213/networks/1234/sync_modules/1234/local_storage/"
            + "manifest/4321/clip/request/1568781420",
        )

    @mock.patch("blinkpy.sync_module.BlinkSyncModule.poll_local_storage_manifest")
    # Need to mock out poll_local_storage_manifest due to retries timing out test
    async def test_check_no_missing_id_with_update_local_storage_manifest(
        self, mock_poll, mock_resp
    ) -> None:
        """Test checking missing ID in local storage update."""
        self.blink.account_id = 10111213
        test_sync = self.blink.sync["test"]
        test_sync._local_storage["status"] = True
        test_sync.sync_id = 1234

        test_sync.cameras["Back Door"] = MockCamera(self.blink.sync)
        test_sync.cameras["Front_Door"] = MockCamera(self.blink.sync)
        mock_poll.return_value = [
            {"network_id": 123456},
        ]
        test_sync._names_table[to_alphanumeric("Front_Door")] = "Front_Door"
        test_sync._names_table[to_alphanumeric("Back Door")] = "Back Door"

        self.assertIsNone(await test_sync.update_local_storage_manifest())

    async def test_check_missing_manifest_id_with_update_local_storage_manifest(
        self, mock_resp
    ) -> None:
        """Test checking missing manifest in update."""
        self.blink.account_id = 10111213
        test_sync = self.blink.sync["test"]
        test_sync._local_storage["status"] = True
        test_sync.sync_id = 1234

        test_sync.cameras["Back Door"] = MockCamera(self.blink.sync)
        test_sync.cameras["Front_Door"] = MockCamera(self.blink.sync)
        created_at = (
            datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
        ).isoformat()

        mock_resp.side_effect = [
            {"id": 387372591, "network_id": 123456},
            {
                "version": "1.0",
                "clips": [
                    {
                        "id": "866333964",
                        "size": "234",
                        "camera_name": "BackDoor",
                        "created_at": f"{created_at}",
                    },
                    {
                        "id": "1568781420",
                        "size": "430",
                        "camera_name": "Front_Door",
                        "created_at": f"{created_at}",
                    },
                ],
            },
        ]

        test_sync._names_table[to_alphanumeric("Front_Door")] = "Front_Door"
        test_sync._names_table[to_alphanumeric("Back Door")] = "Back Door"

        self.assertIsNone(await test_sync.update_local_storage_manifest())

    async def test_check_malformed_clips_with_update_local_storage_manifest(
        self, mock_resp
    ) -> None:
        """Test checking malformed clips in update."""
        self.blink.account_id = 10111213
        test_sync = self.blink.sync["test"]
        test_sync._local_storage["status"] = True
        test_sync.sync_id = 1234

        test_sync.cameras["Back Door"] = MockCamera(self.blink.sync)
        test_sync.cameras["Front_Door"] = MockCamera(self.blink.sync)
        created_at = (
            datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
        ).isoformat()

        mock_resp.side_effect = [
            {"id": 489371591, "network_id": 123456},
            {
                "version": "1.0",
                "manifest_id": "4321",
                "clips": [
                    {
                        "id": "866333964",
                        "camera_name": "BackDoor",
                        "created_at": f"{created_at}",
                    },
                    {
                        "id": "1568781420",
                        "size": "430",
                        "camera_name": "Front_Door",
                        "created_at": f"{created_at}",
                    },
                ],
            },
        ]
        test_sync._names_table[to_alphanumeric("Front_Door")] = "Front_Door"
        test_sync._names_table[to_alphanumeric("Back Door")] = "Back Door"

        self.assertIsNone(await test_sync.update_local_storage_manifest())

    async def test_check_poll_local_storage_manifest_retry(self, mock_resp) -> None:
        """Test checking poll local storage manifest retry."""
        self.blink.account_id = 10111213
        test_sync = self.blink.sync["test"]
        test_sync._local_storage["status"] = True
        test_sync.sync_id = 1234

        test_sync.cameras["Back Door"] = MockCamera(self.blink.sync)
        test_sync.cameras["Front_Door"] = MockCamera(self.blink.sync)

        mock_resp.side_effect = [
            {"network_id": 123456},
        ]
        test_sync._names_table[to_alphanumeric("Front_Door")] = "Front_Door"
        test_sync._names_table[to_alphanumeric("Back Door")] = "Back Door"

        response = await test_sync.poll_local_storage_manifest(max_retries=1)
        self.assertEqual(
            response,
            {"network_id": 123456},
        )

    async def test_sync_owl_init(self, mock_resp):
        """Test sync owl setup with no serial in response."""
        self.blink: Blink = Blink(motion_interval=0, session=mock.AsyncMock())
        self.blink.last_refresh = 0
        self.blink.urls = BlinkURLHandler("test")
        response_value = {"id": 489371591, "enabled": 123456, "serial": None}
        test = BlinkOwl(self.blink, "test", "1234", response=response_value)

        self.assertIsNotNone(test.serial)

        self.blink.homescreen = {"owls": {"enabled": True}}
        self.assertIsNone(await test.get_camera_info("test"))

    async def test_sync_lotus_init(self, mock_resp):
        """Test sync lotus setup with no serial in response."""
        self.blink: Blink = Blink(motion_interval=0, session=mock.AsyncMock())
        self.blink.last_refresh = 0
        self.blink.urls = BlinkURLHandler("test")
        response_value = {"id": 489371591, "enabled": 123456, "serial": None}
        test = BlinkLotus(self.blink, "test", "1234", response=response_value)

        self.assertIsNotNone(test.serial)

        self.blink.homescreen = {"doorbells": {"enabled": True}}
        self.assertIsNone(await test.get_camera_info("test"))

    async def test_local_storage_media_item(self, mock_resp):
        """Test local storage media properties."""
        blink: Blink = Blink(motion_interval=0, session=mock.AsyncMock())
        blink.last_refresh = 0
        blink.urls = BlinkURLHandler("test")
        item = LocalStorageMediaItem(
            "1234",
            "Backdoor",
            datetime.datetime.utcnow().isoformat(),
            "432",
            " manifest_id",
            "url",
        )
        item2 = LocalStorageMediaItem(
            "1235",
            "Backdoor",
            datetime.datetime.utcnow().isoformat(),
            "432",
            " manifest_id",
            "url",
        )
        self.assertEqual(item.id, 1234)
        self.assertEqual(item.size, "432")
        self.assertFalse(item == item2)

        mock_resp.side_effect = [
            {"network_id": 123456},
        ]

        self.assertEquals(
            await item.prepare_download(blink, max_retries=1), {"network_id": 123456}
        )

        with mock.patch("blinkpy.api.http_post", return_value=""):
            self.assertIsNone(await item2.prepare_download(blink, max_retries=0))

    async def test_poll_local_storage_manifest(self, mock_resp):
        """Test incorrect response."""
        with mock.patch("blinkpy.api.request_local_storage_manifest", return_value=""):
            self.assertIsNone(
                await self.blink.sync["test"].poll_local_storage_manifest(max_retries=0)
            )

    async def test_delete_video(self, mock_resp):
        """Test item delete."""
        blink: Blink = Blink(motion_interval=0, session=mock.AsyncMock())
        blink.last_refresh = 0
        blink.urls = BlinkURLHandler("test")
        item = LocalStorageMediaItem(
            "1234",
            "Backdoor",
            datetime.datetime.utcnow().isoformat(),
            "432",
            " manifest_id",
            "url",
        )
        mock_resp.return_value = mresp.MockResponse({"status": 200}, 200)
        self.assertTrue(await item.delete_video(blink))

        mock_resp.return_value = mresp.MockResponse({"status": 400}, 400)
        self.assertFalse(await item.delete_video(blink, 1))

    async def test_download_video(self, mock_resp):
        """Test item download."""
        blink: Blink = Blink(motion_interval=0, session=mock.AsyncMock())
        blink.last_refresh = 0
        blink.urls = BlinkURLHandler("test")
        item = LocalStorageMediaItem(
            "1234",
            "Backdoor",
            datetime.datetime.utcnow().isoformat(),
            "432",
            " manifest_id",
            "url",
        )
        mock_file = mock.MagicMock()
        aiofiles.threadpool.wrap.register(mock.MagicMock)(
            lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(
                *args, **kwargs
            )
        )
        with mock.patch("aiofiles.threadpool.sync_open", return_value=mock_file):
            mock_resp.return_value = mresp.MockResponse({"status": 200}, 200)
            self.assertTrue(await item.download_video(blink, "filename.mp4"))

            mock_resp.return_value = mresp.MockResponse({"status": 400}, 400)
            self.assertFalse(await item.download_video(blink, "filename.mp4", 1))

    @mock.patch("blinkpy.sync_module.LocalStorageMediaItem.download_video")
    @mock.patch("blinkpy.sync_module.LocalStorageMediaItem.delete_video")
    @mock.patch("blinkpy.sync_module.LocalStorageMediaItem.prepare_download")
    async def test_download_delete(self, mock_prepdl, mock_del, mock_dl, mock_resp):
        """Test download and delete."""
        blink: Blink = Blink(motion_interval=0, session=mock.AsyncMock())
        blink.last_refresh = 0
        blink.urls = BlinkURLHandler("test")
        item = LocalStorageMediaItem(
            "1234",
            "Backdoor",
            datetime.datetime.utcnow().isoformat(),
            "432",
            " manifest_id",
            "url",
        )

        self.assertTrue(await item.download_video_delete(self.blink, "filename.mp4"))

        mock_prepdl.return_value = False
        self.assertFalse(await item.download_video_delete(self.blink, "filename.mp4"))

        mock_prepdl.return_value = mock.AsyncMock()
        mock_del.return_value = False
        self.assertFalse(await item.download_video_delete(self.blink, "filename.mp4"))

        mock_del.return_value = mock.AsyncMock()
        mock_dl.return_value = False
        self.assertFalse(await item.download_video_delete(self.blink, "filename.mp4"))
