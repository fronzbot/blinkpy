"""PKCE (Proof Key for Code Exchange) utilities for OAuth 2.0."""

import hashlib
import base64
import secrets


def generate_pkce_pair():
    """
    Generate PKCE code_verifier and code_challenge.

    Returns:
        tuple: (code_verifier, code_challenge)

    Example:
        >>> verifier, challenge = generate_pkce_pair()
        >>> len(verifier) >= 43
        True

    """
    # Generate code_verifier (43-128 characters, URL-safe base64)
    code_verifier = (
        base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
    )

    # Generate code_challenge (SHA256 hash of verifier, URL-safe base64)
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest())
        .decode("utf-8")
        .rstrip("=")
    )

    return code_verifier, code_challenge
