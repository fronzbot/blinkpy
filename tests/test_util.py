"""Test various api functions."""

from unittest import mock, IsolatedAsyncioTestCase
import time
import aiofiles
from io import BufferedIOBase
from blinkpy.helpers.util import (
    json_load,
    json_save,
    Throttle,
    time_to_seconds,
    gen_uid,
    get_time,
    merge_dicts,
    backoff_seconds,
    BlinkException,
)
from blinkpy.helpers import constants as const


class TestUtil(IsolatedAsyncioTestCase):
    """Test the helpers/util module."""

    def setUp(self):
        """Initialize the blink module."""

    def tearDown(self):
        """Tear down blink module."""

    async def test_throttle(self):
        """Test the throttle decorator."""
        calls = []

        @Throttle(seconds=5)
        async def test_throttle(force=False):
            calls.append(1)

        now = int(time.time())
        now_plus_four = now + 4
        now_plus_six = now + 6

        await test_throttle()
        self.assertEqual(1, len(calls))

        # Call again, still shouldn't fire
        await test_throttle()
        self.assertEqual(1, len(calls))

        # Call with force
        await test_throttle(force=True)
        self.assertEqual(2, len(calls))

        # Call without throttle, shouldn't fire
        await test_throttle()
        self.assertEqual(2, len(calls))

        # Fake time as 4 seconds from now
        with mock.patch("time.time", return_value=now_plus_four):
            await test_throttle()
        self.assertEqual(2, len(calls))

        # Fake time as 6 seconds from now
        with mock.patch("time.time", return_value=now_plus_six):
            await test_throttle()
        self.assertEqual(3, len(calls))

    async def test_throttle_per_instance(self):
        """Test that throttle is done once per instance of class."""

        class Tester:
            """A tester class for throttling."""

            async def test(self):
                """Test the throttle."""
                return True

        tester = Tester()
        throttled = Throttle(seconds=1)(tester.test)
        self.assertEqual(await throttled(), True)
        self.assertEqual(await throttled(), None)

    async def test_throttle_multiple_objects(self):
        """Test that function is throttled even if called by multiple objects."""

        @Throttle(seconds=5)
        async def test_throttle_method():
            return True

        class Tester:
            """A tester class for throttling."""

            def test(self):
                """Test function for throttle."""
                return test_throttle_method()

        tester1 = Tester()
        tester2 = Tester()
        self.assertEqual(await tester1.test(), True)
        self.assertEqual(await tester2.test(), None)

    async def test_throttle_on_two_methods(self):
        """Test that throttle works for multiple methods."""

        class Tester:
            """A tester class for throttling."""

            @Throttle(seconds=3)
            async def test1(self):
                """Test function for throttle."""
                return True

            @Throttle(seconds=5)
            async def test2(self):
                """Test function for throttle."""
                return True

        tester = Tester()
        now = time.time()
        now_plus_4 = now + 4
        now_plus_6 = now + 6

        self.assertEqual(await tester.test1(), True)
        self.assertEqual(await tester.test2(), True)
        self.assertEqual(await tester.test1(), None)
        self.assertEqual(await tester.test2(), None)

        with mock.patch("time.time", return_value=now_plus_4):
            self.assertEqual(await tester.test1(), True)
            self.assertEqual(await tester.test2(), None)

        with mock.patch("time.time", return_value=now_plus_6):
            self.assertEqual(await tester.test1(), None)
            self.assertEqual(await tester.test2(), True)

    def test_time_to_seconds(self):
        """Test time to seconds conversion."""
        correct_time = "1970-01-01T00:00:05+00:00"
        wrong_time = "1/1/1970 00:00:03"
        self.assertEqual(time_to_seconds(correct_time), 5)
        self.assertFalse(time_to_seconds(wrong_time))

    async def test_json_save(self):
        """Check that the file is saved."""
        mock_file = mock.MagicMock()
        aiofiles.threadpool.wrap.register(mock.MagicMock)(
            lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(
                *args, **kwargs
            )
        )
        with mock.patch(
            "aiofiles.threadpool.sync_open", return_value=mock_file
        ) as mock_open:
            await json_save('{"test":1,"test2":2}', "face.file")
            mock_open.assert_called_once()

    async def test_json_load_data(self):
        """Check that bad file is handled."""
        filename = "fake.file"
        aiofiles.threadpool.wrap.register(mock.MagicMock)(
            lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(
                *args, **kwargs
            )
        )
        self.assertEqual(await json_load(filename), None)

        mock_file = mock.MagicMock(spec=BufferedIOBase)
        mock_file.name = filename
        mock_file.read.return_value = '{"some data":"more"}'
        with mock.patch("aiofiles.threadpool.sync_open", return_value=mock_file):
            self.assertNotEqual(await json_load(filename), None)

    async def test_json_load_bad_data(self):
        """Check that bad file is handled."""
        self.assertEqual(await json_load("fake.file"), None)
        filename = "fake.file"
        aiofiles.threadpool.wrap.register(mock.MagicMock)(
            lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(
                *args, **kwargs
            )
        )
        self.assertEqual(await json_load(filename), None)

        mock_file = mock.MagicMock(spec=BufferedIOBase)
        mock_file.name = filename
        mock_file.read.return_value = ""
        with mock.patch("aiofiles.threadpool.sync_open", return_value=mock_file):
            self.assertEqual(await json_load("fake.file"), None)

    def test_gen_uid(self):
        """Test gen_uid formatting."""
        val1 = gen_uid(8)
        val2 = gen_uid(8, uid_format=True)

        self.assertEqual(len(val1), 16)

        self.assertTrue(val2.startswith("BlinkCamera_"))
        val2_cut = val2.split("_")
        val2_split = val2_cut[1].split("-")
        self.assertEqual(len(val2_split[0]), 8)
        self.assertEqual(len(val2_split[1]), 4)
        self.assertEqual(len(val2_split[2]), 4)
        self.assertEqual(len(val2_split[3]), 4)
        self.assertEqual(len(val2_split[4]), 12)

    def test_get_time(self):
        """Test the get time util."""
        self.assertEqual(
            get_time(), time.strftime(const.TIMESTAMP_FORMAT, time.gmtime(time.time()))
        )

    def test_merge_dicts(self):
        """Test for duplicates message in merge dicts."""
        dict_A = {"key1": "value1", "key2": "value2"}
        dict_B = {"key1": "value1"}

        expected_log = [
            "WARNING:blinkpy.helpers.util:Duplicates found during merge: ['key1']. "
            "Renaming is recommended."
        ]

        with self.assertLogs(level="DEBUG") as merge_log:
            merge_dicts(dict_A, dict_B)
        self.assertListEqual(merge_log.output, expected_log)

    def test_backoff_seconds(self):
        """Test the backoff seconds function."""
        self.assertNotEqual(backoff_seconds(), None)

    def test_blink_exception(self):
        """Test the Blink Exception class."""
        test_exception = BlinkException([1, "No good"])
        self.assertEqual(test_exception.errid, 1)
        self.assertEqual(test_exception.message, "No good")
