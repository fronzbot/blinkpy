"""Implements known blink API calls."""

import logging
from json import dumps
import blinkpy.helpers.errors as ERROR
from blinkpy.helpers.util import http_req, BlinkException
from blinkpy.helpers.constants import DEFAULT_URL

_LOGGER = logging.getLogger(__name__)


def request_login(blink, url, username, password):
    """Login request."""
    headers = {
        'Host': DEFAULT_URL,
        'Content-Type': 'application/json'
    }
    data = dumps({
        'email': username,
        'password': password,
        'client_specifier': 'iPhone 9.2 | 2.2 | 222'
    })
    return http_req(blink, url=url, headers=headers, data=data,
                    json_resp=False, reqtype='post')


def request_networks(blink):
    """Request network information."""
    url = "{}/networks".format(blink.urls.base_url)
    return http_get(blink, url)


def request_syncmodule(blink, network):
    """Request sync module info."""
    url = "{}/network/{}/syncmodules".format(blink.urls.base_url, network)
    return http_get(blink, url)


def request_system_arm(blink, network):
    """Arm system."""
    url = "{}/network/{}/arm".format(blink.urls.base_url, network)
    return http_post(blink, url)


def request_system_disarm(blink, network):
    """Disarm system."""
    url = "{}/network/{}/disarm".format(blink.urls.base_url, network)
    return http_post(blink, url)


def request_command_status(blink, network, command_id):
    """Request command status."""
    url = "{}/network/{}/command_id/{}".format(blink.urls.base_url,
                                               network,
                                               command_id)
    return http_get(blink, url)


def request_homescreen(blink):
    """Request homescreen info."""
    url = "{}/homescreen".format(blink.urls.base_url)
    return http_get(blink, url)


def request_sync_events(blink, network):
    """Request events from sync module."""
    url = "{}/events/network/{}".format(blink.urls.base_url, network)
    return http_get(blink, url)


def request_new_image(blink, network, camera_id):
    """Request to capture new thumbnail for camera."""
    url = "{}/network/{}/camera/{}/thumbnail".format(blink.urls.base_url,
                                                     network,
                                                     camera_id)
    return http_post(blink, url)


def request_new_video(blink, network, camera_id):
    """Request to capture new video clip."""
    url = "{}/network/{}/camera/{}/clip".format(blink.urls.base_url,
                                                network,
                                                camera_id)
    return http_post(blink, url)


def request_video_count(blink, headers):
    """Request total video count."""
    url = "{}/api/v2/videos/count".format(blink.urls.base_url)
    return http_get(blink, url)


def request_videos(blink, page=0):
    """Perform a request for videos."""
    url = "{}/api/v2/videos/page/{}".format(blink.urls.base_url, page)
    return http_get(blink, url)


def request_cameras(blink, network):
    """Request all camera information."""
    url = "{}/network/{}/cameras".format(blink.urls.base_url, network)
    return http_get(blink, url)


def request_camera_info(blink, network, camera_id):
    """Request camera info for one camera."""
    url = "{}/network/{}/camera/{}".format(blink.urls.base_url,
                                           network,
                                           camera_id)
    return http_get(blink, url)


def request_camera_sensors(blink, network, camera_id):
    """Request camera sensor info for one camera."""
    url = "{}/network/{}/camera/{}/signals".format(blink.urls.base_url,
                                                   network,
                                                   camera_id)
    return http_get(blink, url)


def request_motion_detection_enable(blink, network, camera_id):
    """Enable motion detection for a camera."""
    url = "{}/network/{}/camera/{}/enable".format(blink.urls.base_url,
                                                  network,
                                                  camera_id)
    return http_post(blink, url)


def request_motion_detection_disable(blink, network, camera_id):
    """Disable motion detection for a camera."""
    url = "{}/network/{}/camera/{}/disable".format(blink.urls.base_url,
                                                   network,
                                                   camera_id)
    return http_post(blink, url)


def http_get(blink, url, stream=False, json=True):
    """
    Perform an http get request.

    :param url: URL to perform get request.
    :param stream: Stream response? True/FALSE
    :param json: Return json response? TRUE/False
    """
    if blink.auth_header is None:
        raise BlinkException(ERROR.AUTH_TOKEN)
    return http_req(blink, url=url, headers=blink.auth_header,
                    reqtype='get', stream=stream, json_resp=json)


def http_post(blink, url):
    """
    Perform an http post request.

    :param url: URL to perfom post request.
    """
    if blink.auth_header is None:
        raise BlinkException(ERROR.AUTH_TOKEN)
    return http_req(blink, url=url, headers=blink.auth_header, reqtype='post')
