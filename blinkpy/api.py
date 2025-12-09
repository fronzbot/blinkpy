"""Implements known blink API calls."""

import logging
import string
from json import dumps
from asyncio import sleep
from urllib.parse import urlencode, urlparse, parse_qs
from blinkpy.helpers.util import (
    get_time,
    Throttle,
    local_storage_clip_url_template,
)
from blinkpy.helpers.oauth_parser import OAuthArgsParser
from blinkpy.helpers.constants import (
    TIMEOUT,
    DEFAULT_USER_AGENT,
    OAUTH_CLIENT_ID,
    OAUTH_GRANT_TYPE_PASSWORD,
    OAUTH_GRANT_TYPE_REFRESH_TOKEN,
    OAUTH_SCOPE,
    OAUTH_AUTHORIZE_URL,
    OAUTH_SIGNIN_URL,
    OAUTH_2FA_VERIFY_URL,
    OAUTH_TOKEN_URL,
    OAUTH_V2_CLIENT_ID,
    OAUTH_REDIRECT_URI,
    OAUTH_USER_AGENT,
    OAUTH_TOKEN_USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)

MIN_THROTTLE_TIME = 5
COMMAND_POLL_TIME = 1
MAX_RETRY = 120

# Camera action URL patterns
# Templates use {placeholder} for dynamic values filled at runtime
# Use "data" for static payloads, "data_template" for dynamic payloads
_CAMERA_ACTION_PATTERNS = {
    "mini": {
        "base_template": (
            "/api/v1/accounts/{account_id}/networks/{network}/owls/{camera_id}"
        ),
        "actions": {
            "arm": {
                "path": "config",
                "data_template": lambda p: {"enabled": p.get("arm_action") == "enable"},
            },
            "record": {"path": "clip"},
            "snap": {"path": "thumbnail"},
            "liveview": {
                "path": "liveview",
                "data": {"intent": "liveview"},  # static payload
            },
        },
    },
    "doorbell": {
        "base_template": (
            "/api/v1/accounts/{account_id}/networks/{network}/doorbells/{camera_id}"
        ),
        "actions": {
            "arm": {
                "path_template": "{arm_action}",  # "enable" or "disable"
            },
            "record": {"path": "clip"},
            "snap": {"path": "thumbnail"},
            "liveview": {
                "path": "liveview",
                "data": {"intent": "liveview"},  # static payload
            },
        },
    },
    "default": {
        "base_template": "/network/{network}/camera/{camera_id}",
        "actions": {
            "arm": {
                "path_template": "{arm_action}",  # "enable" or "disable"
            },
            "record": {"path": "clip"},
            "snap": {"path": "thumbnail"},
            "liveview": {
                "path": (
                    "/api/v5/accounts/{account_id}"
                    "/networks/{network}/cameras/{camera_id}/liveview"
                ),
                "data": {"intent": "liveview"},  # static payload
                "full_path": True,
            },
        },
    },
}


async def request_login(
    auth,
    url,
    login_data,
    is_refresh=False,
    is_retry=False,
):
    """
    OAuth login request.

    :param auth: Auth instance.
    :param url: Login url.
    :param login_data: Dictionary containing blink login data.
    :param is_retry:
    :param two_fa_code: 2FA code if required
    """

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": DEFAULT_USER_AGENT,
        "hardware_id": login_data.get("device_id", "Blinkpy"),
    }

    # Add 2FA code to headers if provided
    if "2fa_code" in login_data:
        headers["2fa-code"] = login_data["2fa_code"]

    # Prepare form data for OAuth
    form_data = {
        "username": login_data["username"],
        "client_id": OAUTH_CLIENT_ID,
        "scope": OAUTH_SCOPE,
    }

    if is_refresh:
        form_data["grant_type"] = OAUTH_GRANT_TYPE_REFRESH_TOKEN
        form_data["refresh_token"] = auth.refresh_token
    else:
        form_data["grant_type"] = OAUTH_GRANT_TYPE_PASSWORD
        form_data["password"] = login_data["password"]

    data = urlencode(form_data)

    return await auth.query(
        url=url,
        headers=headers,
        data=data,
        json_resp=False,
        reqtype="post",
        is_retry=is_retry,
        skip_refresh_check=True,
    )


async def request_tier(auth, url):
    """Get account tier information from blink servers."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": DEFAULT_USER_AGENT,
        "Authorization": f"Bearer {auth.token}",
    }

    return await auth.query(
        url=url,
        headers=headers,
        json_resp=True,
        reqtype="get",
    )


async def request_logout(blink):
    """Logout of blink servers."""
    url = (
        f"{blink.urls.base_url}/api/v4/account/{blink.account_id}"
        f"/client/{blink.client_id}/logout"
    )
    return await http_post(blink, url=url)


async def request_networks(blink):
    """Request all networks information."""
    url = f"{blink.urls.base_url}/networks"
    return await http_get(blink, url)


async def request_network_update(blink, network):
    """
    Request network update.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}/update"
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


async def request_user(blink):
    """Get user information from blink servers."""
    url = f"{blink.urls.base_url}/user"
    return await http_get(blink, url)


async def request_network_status(blink, network):
    """
    Request network information.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}"
    return await http_get(blink, url)


async def request_syncmodule(blink, network):
    """
    Request sync module info.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}/syncmodules"
    return await http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_system_arm(blink, network, **kwargs):
    """
    Arm system.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        f"/networks/{network}/state/arm"
    )
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_system_disarm(blink, network, **kwargs):
    """
    Disarm system.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        f"/networks/{network}/state/disarm"
    )
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


async def request_notification_flags(blink, **kwargs):
    """
    Get system notification flags.

    :param blink: Blink instance.
    """
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        "/notifications/configuration"
    )
    response = await http_get(blink, url)
    await wait_for_command(blink, response)
    return response


async def request_set_notification_flag(blink, data_dict):
    """
    Set a system notification flag.

    :param blink: Blink instance.
    :param data_dict: Dictionary of notifications to set.
    """
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        "/notifications/configuration"
    )
    data = dumps({"notifications": data_dict})
    response = await http_post(blink, url, data=data, json=False)
    await wait_for_command(blink, response)
    return response


async def request_command_status(blink, network, command_id):
    """
    Request command status.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param command_id: Command id to check.
    """
    url = f"{blink.urls.base_url}/network/{network}/command/{command_id}"
    return await http_get(blink, url)


async def request_command_done(blink, network, command_id):
    """
    Request command to be done.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param command_id: Command id to mark as done.
    """
    url = f"{blink.urls.base_url}/network/{network}/command/{command_id}/done/"
    return await http_post(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_homescreen(blink, **kwargs):
    """Request homescreen info."""
    url = f"{blink.urls.base_url}/api/v3/accounts/{blink.account_id}/homescreen"
    return await http_get(blink, url, json=False)


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_sync_events(blink, network, **kwargs):
    """
    Request events from sync module.

    :param blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/events/network/{network}"
    return await http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_new_image(blink, network, camera_id, camera_type="", **kwargs):
    """
    Request to capture new thumbnail for camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request new image from.
    :param camera_type: Camera type ("default", "mini", "doorbell").
    """
    return await request_camera_action(
        blink, network, camera_id, action="snap", camera_type=camera_type
    )


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_new_video(blink, network, camera_id, camera_type="", **kwargs):
    """
    Request to capture new video clip.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request new video from.
    :param camera_type: Camera type ("default", "mini", "doorbell").
    """
    return await request_camera_action(
        blink, network, camera_id, action="record", camera_type=camera_type
    )


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_video_count(blink, **kwargs):
    """Request total video count."""
    url = f"{blink.urls.base_url}/api/v2/videos/count"
    return await http_get(blink, url)


async def request_videos(blink, time=None, page=0):
    """
    Perform a request for videos.

    :param blink: Blink instance.
    :param time: Get videos since this time.  In epoch seconds.
    :param page: Page number to get videos from.
    """
    timestamp = get_time(time)
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        f"/media/changed?since={timestamp}&page={page}"
    )
    return await http_get(blink, url)


async def request_cameras(blink, network):
    """
    Request all camera information.

    :param Blink: Blink instance.
    :param network: Sync module network id.
    """
    url = f"{blink.urls.base_url}/network/{network}/cameras"
    return await http_get(blink, url)


async def request_camera_info(blink, network, camera_id):
    """
    Request camera info for one camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request info from.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/config"
    return await http_get(blink, url)


async def request_camera_usage(blink):
    """
    Request camera status.

    :param blink: Blink instance.
    """
    url = f"{blink.urls.base_url}/api/v1/camera/usage"
    return await http_get(blink, url)


async def request_camera_liveview(blink, network, camera_id, camera_type="", **kwargs):
    """
    Request camera liveview.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request liveview from.
    :param camera_type: Camera type ("default", "mini", "doorbell").
    """
    return await request_camera_action(
        blink, network, camera_id, action="liveview", camera_type=camera_type
    )


async def request_camera_sensors(blink, network, camera_id):
    """
    Request camera sensor info for one camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to request sensor info from.
    """
    url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/signals"
    return await http_get(blink, url)


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_motion_detection_enable(
    blink, network, camera_id, camera_type="", **kwargs
):
    """
    Enable motion detection for a camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to enable.
    :param camera_type: Camera type ("default", "mini", "doorbell").
    """
    return await request_camera_action(
        blink,
        network,
        camera_id,
        action="arm",
        camera_type=camera_type,
        arm_action="enable",
    )


@Throttle(seconds=MIN_THROTTLE_TIME)
async def request_motion_detection_disable(
    blink, network, camera_id, camera_type="", **kwargs
):
    """
    Disable motion detection for a camera.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID of camera to disable.
    :param camera_type: Camera type ("default", "mini", "doorbell").
    """
    return await request_camera_action(
        blink,
        network,
        camera_id,
        action="arm",
        camera_type=camera_type,
        arm_action="disable",
    )


async def request_local_storage_manifest(blink, network, sync_id):
    """
    Update local manifest.

    Request creation of an updated manifest of video clips stored in
    sync module local storage.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param sync_id: ID of sync module.
    """
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        f"/networks/{network}/sync_modules/{sync_id}"
        f"/local_storage/manifest/request"
    )
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


async def get_local_storage_manifest(blink, network, sync_id, manifest_request_id):
    """
    Request manifest of video clips stored in sync module local storage.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param sync_id: ID of sync module.
    :param manifest_request_id: Request ID of local storage manifest \
                                (requested creation of new manifest).
    """
    url = (
        f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
        f"/networks/{network}/sync_modules/{sync_id}"
        f"/local_storage/manifest/request/{manifest_request_id}"
    )
    return await http_get(blink, url)


async def request_local_storage_clip(blink, network, sync_id, manifest_id, clip_id):
    """
    Prepare video clip stored in the sync module to be downloaded.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param sync_id: ID of sync module.
    :param manifest_id: ID of local storage manifest (returned in manifest response).
    :param clip_id: ID of the clip.
    """
    url = blink.urls.base_url + string.Template(
        local_storage_clip_url_template()
    ).substitute(
        account_id=blink.account_id,
        network_id=network,
        sync_id=sync_id,
        manifest_id=manifest_id,
        clip_id=clip_id,
    )
    response = await http_post(blink, url)
    await wait_for_command(blink, response)
    return response


async def request_get_config(blink, network, camera_id, product_type="owl"):
    """
    Get camera configuration.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: ID of camera
    :param product_type: Camera product type "owl" or "catalina"
    """
    if product_type == "owl":
        url = (
            f"{blink.urls.base_url}/api/v1/accounts/{blink.account_id}"
            f"/networks/{network}/owls/{camera_id}/config"
        )
    elif product_type == "catalina":
        url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/config"
    else:
        _LOGGER.info(
            "Camera %s with product type %s config get not implemented.",
            camera_id,
            product_type,
        )
        return None
    return await http_get(blink, url)


async def request_update_config(
    blink, network, camera_id, product_type="owl", data=None
):
    """
    Update camera configuration.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: ID of camera
    :param product_type: Camera product type "owl" or "catalina"
    :param data: string w/JSON dict of parameters/values to update
    """
    if product_type == "owl":
        url = (
            f"{blink.urls.base_url}/api/v1/accounts/"
            f"{blink.account_id}/networks/{network}/owls/{camera_id}/config"
        )
    elif product_type == "catalina":
        url = f"{blink.urls.base_url}/network/{network}/camera/{camera_id}/update"
    else:
        _LOGGER.info(
            "Camera %s with product type %s config update not implemented.",
            camera_id,
            product_type,
        )
        return None
    return await http_post(blink, url, json=False, data=data)


async def http_get(
    blink, url, stream=False, json=True, is_retry=False, timeout=TIMEOUT
):
    """
    Perform an http get request.

    :param url: URL to perform get request.
    :param stream: Stream response? True/FALSE
    :param json: Return json response? TRUE/False
    :param is_retry: Is this part of a re-auth attempt?
    """
    _LOGGER.debug("Making GET request to %s", url)
    return await blink.auth.query(
        url=url,
        headers=blink.auth.header,
        reqtype="get",
        stream=stream,
        json_resp=json,
        is_retry=is_retry,
    )


async def http_post(blink, url, is_retry=False, data=None, json=True, timeout=TIMEOUT):
    """
    Perform an http post request.

    :param url: URL to perform post request.
    :param is_retry: Is this part of a re-auth attempt?
    :param data: str body for post request
    :param json: Return json response? TRUE/False
    """
    _LOGGER.debug("Making POST request to %s", url)
    return await blink.auth.query(
        url=url,
        headers=blink.auth.header,
        reqtype="post",
        is_retry=is_retry,
        json_resp=json,
        data=data,
    )


async def request_camera_action(
    blink, network, camera_id, action, camera_type="", **kwargs
):
    """
    Perform camera actions for different camera types.

    :param blink: Blink instance.
    :param network: Sync module network id.
    :param camera_id: Camera ID.
    :param action: Action type ("arm", "record", "snap", "liveview").
    :param camera_type: Camera type ("default", "mini", "doorbell").
    :param **kwargs: Additional parameters for substitution (e.g., arm_action).
    """
    camera_type = camera_type or "default"
    if camera_type not in _CAMERA_ACTION_PATTERNS:
        raise ValueError(f"Unsupported camera type: {camera_type}")

    pattern = _CAMERA_ACTION_PATTERNS[camera_type]
    if action not in pattern["actions"]:
        raise ValueError(
            f"Unsupported action '{action}' for camera type '{camera_type}'"
        )

    # Get action and build base URL
    action_config = pattern["actions"][action]
    base_url = pattern["base_template"].format(
        account_id=blink.account_id,
        network=network,
        camera_id=camera_id,
    )

    # Build action path
    if "path_template" in action_config:
        # Dynamic path using template substitution
        path = action_config["path_template"].format(**kwargs)
    else:
        # Static path
        path = action_config.get("path", "")

    # Build full URL
    if action_config.get("full_path"):
        # For liveview on default cameras, path contains full path template
        url = blink.urls.base_url + path.format(
            account_id=blink.account_id,
            network=network,
            camera_id=camera_id,
        )
    else:
        # Standard URL construction
        url = f"{blink.urls.base_url}{base_url}/{path}"

    # Prepare request data
    data = None
    if "data_template" in action_config:
        # Dynamic payload with runtime value substitution
        data = dumps(action_config["data_template"](kwargs))
    elif "data" in action_config:
        # Static payload
        data = dumps(action_config["data"])

    # Execute request
    response = await http_post(blink, url, data=data)
    await wait_for_command(blink, response)
    return response


async def wait_for_command(blink, json_data: dict) -> bool:
    """Wait for command to complete."""
    _LOGGER.debug("Command Wait %s", json_data)
    try:
        network_id = json_data.get("network_id")
        command_id = json_data.get("id")
    except AttributeError:
        _LOGGER.exception("No network_id or id in response")
        return False
    if command_id and network_id:
        for _ in range(0, MAX_RETRY):
            _LOGGER.debug("Making GET request waiting for command")
            status = await request_command_status(blink, network_id, command_id)
            _LOGGER.debug("command status %s", status)
            if status:
                if status.get("status_code", 0) != 908:
                    return False
                if status.get("complete"):
                    return True
            await sleep(COMMAND_POLL_TIME)
        return False  # Timeout after MAX_RETRY attempts
    else:
        _LOGGER.debug("No network_id or id in response")
        return False


# OAuth v2 Authorization Code Flow + PKCE functions


async def oauth_authorize_request(auth, hardware_id, code_challenge):
    """
    Step 1: Initial authorization request.

    Args:
        auth: Auth instance
        hardware_id: Device hardware ID (UUID)
        code_challenge: PKCE code challenge

    Returns:
        bool: True if successful

    """
    params = {
        "app_brand": "blink",
        "app_version": "50.1",
        "client_id": OAUTH_V2_CLIENT_ID,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "device_brand": "Apple",
        "device_model": "iPhone16,1",
        "device_os_version": "26.1",
        "hardware_id": hardware_id,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": OAUTH_SCOPE,
    }

    headers = {
        "User-Agent": OAUTH_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = await auth.session.get(
        OAUTH_AUTHORIZE_URL, params=params, headers=headers
    )

    return response.status == 200


async def oauth_get_signin_page(auth):
    """
    Step 2: Get signin page and extract CSRF token.

    Args:
        auth: Auth instance

    Returns:
        str: CSRF token or None

    """
    headers = {
        "User-Agent": OAUTH_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = await auth.session.get(OAUTH_SIGNIN_URL, headers=headers)

    if response.status != 200:
        return None

    html = await response.text()

    # Extract CSRF token from oauth-args script tag
    try:
        parser = OAuthArgsParser()
        parser.feed(html)
        if parser.csrf_token:
            return parser.csrf_token
    except Exception as error:
        _LOGGER.error("Failed to extract CSRF token: %s", error)

    return None


async def oauth_signin(auth, email, password, csrf_token):
    """
    Step 3: Submit login credentials.

    Args:
        auth: Auth instance
        email: User email
        password: User password
        csrf_token: CSRF token from signin page

    Returns:
        str: "SUCCESS", "2FA_REQUIRED", or None on failure

    """
    headers = {
        "User-Agent": OAUTH_USER_AGENT,
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://api.oauth.blink.com",
        "Referer": OAUTH_SIGNIN_URL,
    }

    data = {
        "username": email,
        "password": password,
        "csrf-token": csrf_token,
    }

    response = await auth.session.post(
        OAUTH_SIGNIN_URL, headers=headers, data=data, allow_redirects=False
    )

    if response.status == 412:
        # 2FA required
        return "2FA_REQUIRED"
    elif response.status in [301, 302, 303, 307, 308]:
        # Success without 2FA
        return "SUCCESS"

    return None


async def oauth_verify_2fa(auth, csrf_token, twofa_code):
    """
    Step 3b: Verify 2FA code.

    Args:
        auth: Auth instance
        csrf_token: CSRF token
        twofa_code: 2FA code from user

    Returns:
        bool: True if verification successful

    """
    headers = {
        "User-Agent": OAUTH_USER_AGENT,
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://api.oauth.blink.com",
        "Referer": OAUTH_SIGNIN_URL,
    }

    data = {
        "2fa_code": twofa_code,
        "csrf-token": csrf_token,
        "remember_me": "false",
    }

    response = await auth.session.post(OAUTH_2FA_VERIFY_URL, headers=headers, data=data)

    if response.status == 201:
        try:
            result = await response.json()
            return result.get("status") == "auth-completed"
        except Exception as error:
            _LOGGER.error("Failed to parse 2FA response: %s", error)

    return False


async def oauth_get_authorization_code(auth):
    """
    Step 4: Get authorization code from authorize endpoint.

    Args:
        auth: Auth instance

    Returns:
        str: Authorization code or None

    """
    headers = {
        "User-Agent": OAUTH_USER_AGENT,
        "Accept": "*/*",
        "Referer": OAUTH_SIGNIN_URL,
    }

    response = await auth.session.get(
        OAUTH_AUTHORIZE_URL, headers=headers, allow_redirects=False
    )

    if response.status in [301, 302, 303, 307, 308]:
        location = response.headers.get("Location", "")

        # Extract code from URL: https://blink.com/.../end?code=XXX&state=YYY
        parsed = urlparse(location)
        params = parse_qs(parsed.query)

        if "code" in params:
            return params["code"][0]

    return None


async def oauth_exchange_code_for_token(auth, code, code_verifier, hardware_id):
    """
    Step 5: Exchange authorization code for access token.

    Args:
        auth: Auth instance
        code: Authorization code
        code_verifier: PKCE code verifier
        hardware_id: Device hardware ID

    Returns:
        dict: Token data or None

    """
    headers = {
        "User-Agent": OAUTH_TOKEN_USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
    }

    data = {
        "app_brand": "blink",
        "client_id": OAUTH_V2_CLIENT_ID,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "hardware_id": hardware_id,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "scope": OAUTH_SCOPE,
    }

    response = await auth.session.post(
        OAUTH_TOKEN_URL, headers=headers, data=urlencode(data)
    )

    if response.status == 200:
        return await response.json()

    return None


async def oauth_refresh_token(auth, refresh_token, hardware_id):
    """
    Refresh access token using refresh_token.

    Args:
        auth: Auth instance
        refresh_token: Refresh token
        hardware_id: Device hardware ID

    Returns:
        dict: Token data or None

    """
    headers = {
        "User-Agent": OAUTH_TOKEN_USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": OAUTH_V2_CLIENT_ID,
        "scope": OAUTH_SCOPE,
        "hardware_id": hardware_id,
    }

    response = await auth.session.post(
        OAUTH_TOKEN_URL, headers=headers, data=urlencode(data)
    )

    if response.status == 200:
        return await response.json()

    return None
