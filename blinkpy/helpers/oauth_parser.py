"""HTML parser for OAuth CSRF token extraction."""

import json
from html.parser import HTMLParser


class OAuthArgsParser(HTMLParser):
    """HTML parser to extract CSRF token from oauth-args script tag."""

    def __init__(self):
        """Initialize parser."""
        super().__init__()
        self.csrf_token = None
        self._in_oauth_script = False

    def handle_starttag(self, tag, attrs):
        """Handle opening tags."""
        if tag == "script":
            attrs_dict = dict(attrs)
            if (
                attrs_dict.get("id") == "oauth-args"
                and attrs_dict.get("type") == "application/json"
            ):
                self._in_oauth_script = True

    def handle_data(self, data):
        """Handle tag content."""
        if self._in_oauth_script:
            try:
                oauth_data = json.loads(data)
                self.csrf_token = oauth_data.get("csrf-token")
            except (json.JSONDecodeError, AttributeError):
                pass
            self._in_oauth_script = False

    def handle_endtag(self, tag):
        """Handle closing tags."""
        if tag == "script":
            self._in_oauth_script = False
