"""Test OAuth v2 functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from blinkpy.helpers.pkce import generate_pkce_pair
from blinkpy import api
from blinkpy.auth import Auth, BlinkTwoFARequiredError


def test_pkce_generation():
    """Test PKCE pair generation."""
    verifier, challenge = generate_pkce_pair()

    # Verify length requirements
    assert len(verifier) >= 43
    assert len(challenge) > 0

    # Verify they are different
    assert verifier != challenge

    # Verify URL-safe base64 (no padding)
    assert "=" not in verifier
    assert "=" not in challenge


def test_pkce_uniqueness():
    """Test that PKCE pairs are unique."""
    verifier1, challenge1 = generate_pkce_pair()
    verifier2, challenge2 = generate_pkce_pair()

    assert verifier1 != verifier2
    assert challenge1 != challenge2


@pytest.mark.asyncio
async def test_oauth_authorize_request():
    """Test OAuth authorization request."""
    auth = Mock()
    auth.session = Mock()

    # Mock response
    response = Mock()
    response.status = 200
    auth.session.get = AsyncMock(return_value=response)

    hardware_id = "TEST-HARDWARE-ID"
    code_challenge = "test_challenge"

    result = await api.oauth_authorize_request(auth, hardware_id, code_challenge)

    assert result is True
    auth.session.get.assert_called_once()


@pytest.mark.asyncio
async def test_oauth_get_signin_page():
    """Test getting signin page and extracting CSRF token."""
    auth = Mock()
    auth.session = Mock()

    # Mock HTML response with CSRF token
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <script id="oauth-args" type="application/json">
        {"csrf-token": "test_csrf_token_123"}
        </script>
    </head>
    <body></body>
    </html>
    """

    response = Mock()
    response.status = 200
    response.text = AsyncMock(return_value=html_content)
    auth.session.get = AsyncMock(return_value=response)

    csrf_token = await api.oauth_get_signin_page(auth)

    assert csrf_token == "test_csrf_token_123"


@pytest.mark.asyncio
async def test_oauth_signin_success():
    """Test successful OAuth signin without 2FA."""
    auth = Mock()
    auth.session = Mock()

    response = Mock()
    response.status = 302  # Redirect = success
    auth.session.post = AsyncMock(return_value=response)

    result = await api.oauth_signin(auth, "test@example.com", "password", "csrf_token")

    assert result == "SUCCESS"


@pytest.mark.asyncio
async def test_oauth_signin_2fa_required():
    """Test OAuth signin when 2FA is required."""
    auth = Mock()
    auth.session = Mock()

    response = Mock()
    response.status = 412  # 2FA required
    auth.session.post = AsyncMock(return_value=response)

    result = await api.oauth_signin(auth, "test@example.com", "password", "csrf_token")

    assert result == "2FA_REQUIRED"


@pytest.mark.asyncio
async def test_oauth_verify_2fa():
    """Test 2FA verification."""
    auth = Mock()
    auth.session = Mock()

    response = Mock()
    response.status = 201  # Changed from 200 to 201 to match actual API behavior
    response.json = AsyncMock(return_value={"status": "auth-completed"})
    auth.session.post = AsyncMock(return_value=response)

    result = await api.oauth_verify_2fa(auth, "csrf_token", "123456")

    assert result is True


@pytest.mark.asyncio
async def test_oauth_get_authorization_code():
    """Test getting authorization code from redirect."""
    auth = Mock()
    auth.session = Mock()

    response = Mock()
    response.status = 302
    response.headers = {
        "Location": "https://blink.com/end?code=AUTH_CODE_123&state=STATE"
    }
    auth.session.get = AsyncMock(return_value=response)

    code = await api.oauth_get_authorization_code(auth)

    assert code == "AUTH_CODE_123"


@pytest.mark.asyncio
async def test_oauth_exchange_code_for_token():
    """Test exchanging authorization code for access token."""
    auth = Mock()
    auth.session = Mock()

    token_response = {
        "access_token": "access_token_123",
        "refresh_token": "refresh_token_456",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    response = Mock()
    response.status = 200
    response.json = AsyncMock(return_value=token_response)
    auth.session.post = AsyncMock(return_value=response)

    result = await api.oauth_exchange_code_for_token(
        auth, "AUTH_CODE", "code_verifier", "hardware_id"
    )

    assert result == token_response
    assert result["access_token"] == "access_token_123"


@pytest.mark.asyncio
async def test_oauth_refresh_token():
    """Test refreshing access token."""
    auth = Mock()
    auth.session = Mock()

    token_response = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    response = Mock()
    response.status = 200
    response.json = AsyncMock(return_value=token_response)
    auth.session.post = AsyncMock(return_value=response)

    result = await api.oauth_refresh_token(auth, "old_refresh_token", "hardware_id")

    assert result == token_response
    assert result["access_token"] == "new_access_token"


@pytest.mark.asyncio
async def test_auth_process_token_data():
    """Test processing token data in Auth class."""
    auth = Auth({"username": "test@example.com", "password": "password"})

    token_data = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 7200,
    }

    # Mock get_tier_info to avoid actual API call
    with patch.object(auth, "get_tier_info", new=AsyncMock(return_value={})):
        await auth._process_token_data(token_data)

    assert auth.token == "test_access_token"
    assert auth.refresh_token == "test_refresh_token"
    assert auth.expires_in == 7200
    assert auth.expiration_date is not None


@pytest.mark.asyncio
async def test_auth_hardware_id_generation():
    """Test that hardware_id is generated if not provided."""
    auth = Auth({"username": "test@example.com", "password": "password"})

    assert auth.hardware_id is not None
    assert len(auth.hardware_id) > 0


@pytest.mark.asyncio
async def test_auth_hardware_id_persistence():
    """Test that hardware_id is preserved from login_data."""
    hardware_id = "EXISTING-HARDWARE-ID"
    auth = Auth(
        {
            "username": "test@example.com",
            "password": "password",
            "hardware_id": hardware_id,
        }
    )

    assert auth.hardware_id == hardware_id


@pytest.mark.asyncio
async def test_login_attributes_includes_hardware_id():
    """Test that login_attributes includes hardware_id."""
    auth = Auth({"username": "test@example.com", "password": "password"})

    attributes = auth.login_attributes

    assert "hardware_id" in attributes
    assert attributes["hardware_id"] == auth.hardware_id


@pytest.mark.asyncio
async def test_oauth_login_flow_raises_2fa_required():
    """Test that OAuth login flow raises BlinkTwoFARequiredError when 2FA is needed."""

    auth = Auth({"username": "test@example.com", "password": "password"})

    # Mock all the API calls
    with patch("blinkpy.api.oauth_authorize_request", new=AsyncMock(return_value=True)):
        with patch(
            "blinkpy.api.oauth_get_signin_page",
            new=AsyncMock(return_value="csrf_token"),
        ):
            with patch(
                "blinkpy.api.oauth_signin", new=AsyncMock(return_value="2FA_REQUIRED")
            ):
                # Should raise BlinkTwoFARequiredError
                with pytest.raises(BlinkTwoFARequiredError):
                    await auth._oauth_login_flow()

                # Verify state was saved
                assert hasattr(auth, "_oauth_csrf_token")
                assert hasattr(auth, "_oauth_code_verifier")


@pytest.mark.asyncio
async def test_complete_2fa_login():
    """Test completing OAuth v2 login after 2FA."""
    auth = Auth({"username": "test@example.com", "password": "password"})

    # Set up OAuth state as if 2FA was requested
    auth._oauth_csrf_token = "test_csrf_token"
    auth._oauth_code_verifier = "test_code_verifier"

    # Mock the API calls
    with patch("blinkpy.api.oauth_verify_2fa", new=AsyncMock(return_value=True)):
        with patch(
            "blinkpy.api.oauth_get_authorization_code",
            new=AsyncMock(return_value="AUTH_CODE"),
        ):
            with patch(
                "blinkpy.api.oauth_exchange_code_for_token",
                new=AsyncMock(
                    return_value={
                        "access_token": "token_123",
                        "refresh_token": "refresh_456",
                        "expires_in": 3600,
                    }
                ),
            ):
                result = await auth.complete_2fa_login("123456")

                assert result is True
                assert auth.token == "token_123"
                assert auth.refresh_token == "refresh_456"
                # State should be cleaned up
                assert not hasattr(auth, "_oauth_csrf_token")
                assert not hasattr(auth, "_oauth_code_verifier")
