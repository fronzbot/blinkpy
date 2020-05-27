"""Simple mock responses definitions."""


class MockResponse:
    """Class for mock request response."""

    def __init__(self, json_data, status_code, raw_data=None):
        """Initialize mock get response."""
        self.json_data = json_data
        self.status_code = status_code
        self.raw_data = raw_data
        self.reason = "foobar"

    def json(self):
        """Return json data from get_request."""
        return self.json_data

    @property
    def raw(self):
        """Return raw data from get request."""
        return self.raw_data
