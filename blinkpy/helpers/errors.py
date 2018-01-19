"""Module to define error types."""

USERNAME = (0, "Username must be a string")
PASSWORD = (1, "Password must be a string")
AUTHENTICATE = (
    2,
    "Cannot authenticate since either password or username has not been set"
)
AUTH_TOKEN = (
    3,
    "Authentication header incorrect.  Are you sure you received your token?"
)
REQUEST = (4, "Cannot perform request (get/post type incorrect)")
