"""Test blink Utils errors."""
import unittest
from blinkpy.helpers.errors import (
    USERNAME,
    PASSWORD,
    AUTH_TOKEN,
    AUTHENTICATE,
    REQUEST,
    BLINK_ERRORS,
)


class TestBlinkUtilsErrors(unittest.TestCase):
    """Test BlinkUtilErros functions in blinkpy."""

    def test_helpers_errors(self) -> None:
        """Test the helper errors."""
        assert USERNAME
        assert PASSWORD
        assert AUTH_TOKEN
        assert AUTHENTICATE
        assert REQUEST
        assert BLINK_ERRORS
