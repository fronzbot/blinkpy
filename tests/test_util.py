"""Test various api functions."""

import unittest
from unittest import mock
import time
from blinkpy.helpers.util import json_load, Throttle, time_to_seconds, gen_uid


class TestUtil(unittest.TestCase):
    """Test the helpers/util module."""

    def setUp(self):
        """Initialize the blink module."""

    def tearDown(self):
        """Tear down blink module."""

    def test_throttle(self):
        """Test the throttle decorator."""
        calls = []

        @Throttle(seconds=5)
        def test_throttle():
            calls.append(1)

        now = int(time.time())
        now_plus_four = now + 4
        now_plus_six = now + 6

        test_throttle()
        self.assertEqual(1, len(calls))

        # Call again, still shouldn't fire
        test_throttle()
        self.assertEqual(1, len(calls))

        # Call with force
        test_throttle(force=True)
        self.assertEqual(2, len(calls))

        # Call without throttle, shouldn't fire
        test_throttle()
        self.assertEqual(2, len(calls))

        # Fake time as 4 seconds from now
        with mock.patch("time.time", return_value=now_plus_four):
            test_throttle()
        self.assertEqual(2, len(calls))

        # Fake time as 6 seconds from now
        with mock.patch("time.time", return_value=now_plus_six):
            test_throttle()
        self.assertEqual(3, len(calls))

    def test_throttle_per_instance(self):
        """Test that throttle is done once per instance of class."""

        class Tester:
            """A tester class for throttling."""

            def test(self):
                """Test the throttle."""
                return True

        tester = Tester()
        throttled = Throttle(seconds=1)(tester.test)
        self.assertEqual(throttled(), True)
        self.assertEqual(throttled(), None)

    def test_throttle_multiple_objects(self):
        """Test that function is throttled even if called by multiple objects."""

        @Throttle(seconds=5)
        def test_throttle_method():
            return True

        class Tester:
            """A tester class for throttling."""

            def test(self):
                """Test function for throttle."""
                return test_throttle_method()

        tester1 = Tester()
        tester2 = Tester()
        self.assertEqual(tester1.test(), True)
        self.assertEqual(tester2.test(), None)

    def test_throttle_on_two_methods(self):
        """Test that throttle works for multiple methods."""

        class Tester:
            """A tester class for throttling."""

            @Throttle(seconds=3)
            def test1(self):
                """Test function for throttle."""
                return True

            @Throttle(seconds=5)
            def test2(self):
                """Test function for throttle."""
                return True

        tester = Tester()
        now = time.time()
        now_plus_4 = now + 4
        now_plus_6 = now + 6

        self.assertEqual(tester.test1(), True)
        self.assertEqual(tester.test2(), True)
        self.assertEqual(tester.test1(), None)
        self.assertEqual(tester.test2(), None)

        with mock.patch("time.time", return_value=now_plus_4):
            self.assertEqual(tester.test1(), True)
            self.assertEqual(tester.test2(), None)

        with mock.patch("time.time", return_value=now_plus_6):
            self.assertEqual(tester.test1(), None)
            self.assertEqual(tester.test2(), True)

    def test_time_to_seconds(self):
        """Test time to seconds conversion."""
        correct_time = "1970-01-01T00:00:05+00:00"
        wrong_time = "1/1/1970 00:00:03"
        self.assertEqual(time_to_seconds(correct_time), 5)
        self.assertFalse(time_to_seconds(wrong_time))

    def test_json_load_bad_data(self):
        """Check that bad file is handled."""
        self.assertEqual(json_load("fake.file"), None)
        with mock.patch("builtins.open", mock.mock_open(read_data="")):
            self.assertEqual(json_load("fake.file"), None)

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
