"""Interactive test harness for floodlight on/off via blinkpy."""

import asyncio
import getpass
import logging
import os
import sys

from aiohttp import ClientSession
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth, BlinkTwoFARequiredError
from blinkpy.helpers.util import json_load, json_save

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
_LOGGER = logging.getLogger(__name__)

CRED_FILE = os.path.join(os.path.dirname(__file__), ".blink_session.json")


async def login(session: ClientSession) -> Blink:
    """Log in to Blink, reusing a cached session if available."""
    blink = Blink(session=session)

    cached = await json_load(CRED_FILE)
    if cached and cached.get("token"):
        print("Resuming cached session …")
        blink.auth = Auth(cached, session=session)
        try:
            await blink.start()
            print("Session restored.")
            return blink
        except Exception:
            print("Cached session expired or invalid, logging in again …")

    print("\n--- Blink login ---")
    username = input("Email: ").strip()
    password = getpass.getpass("Password: ")

    blink.auth = Auth({"username": username, "password": password}, session=session)

    try:
        await blink.start()
    except BlinkTwoFARequiredError:
        code = input("2FA code: ").strip()
        await blink.auth.complete_2fa_login(code)
        blink.setup_urls()
        await blink.setup_post_verify()

    await blink.save(CRED_FILE)
    print(f"Session saved to {CRED_FILE}")
    return blink


def find_floodlights(blink: Blink):
    """Return cameras whose product_type is 'superior'."""
    return {
        name: cam
        for name, cam in blink.cameras.items()
        if cam.product_type == "superior"
    }


def pick_camera(cameras: dict):
    """Prompt user to select one camera from the dict; return it."""
    names = list(cameras)
    if len(names) == 1:
        print(f"Using camera: {names[0]}")
        return cameras[names[0]]
    print("\nAvailable floodlight cameras:")
    for i, name in enumerate(names, 1):
        cam = cameras[name]
        print(f"  {i}. {name}  (id={cam.camera_id}, network={cam.network_id})")
    while True:
        raw = input(f"Select [1-{len(names)}]: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(names):
            return cameras[names[int(raw) - 1]]
        print("Invalid selection, try again.")


async def toggle_loop(camera):
    """Interactively toggle the floodlight until the user quits."""
    print(f"\nCamera ready: {camera.name}  product_type={camera.product_type}")
    accs = camera.get_light_accessories()
    if accs:
        print(f"  accessories: {accs}")
    else:
        print("  WARNING: no light accessories found in homescreen data")
    print("Commands:  on | off | config | set <key> <value> | accessories | status | quit\n")
    while True:
        cmd = input("> ").strip()
        parts = cmd.split(None, 2)
        verb = parts[0].lower() if parts else ""
        if verb in ("q", "quit", "exit"):
            break
        elif verb == "post":
            if len(parts) < 2:
                print("  Usage: post <relative-path> [json-body]")
                continue
            import json as _json
            from blinkpy import api as _api
            url = camera.sync.blink.urls.base_url + parts[1]
            data = parts[2] if len(parts) > 2 else None
            print(f"  POST {url}  data={data}")
            resp = await _api.http_post(camera.sync.blink, url, json=False, data=data)
            if resp is None:
                print("  result: None (request failed)")
            else:
                body = await resp.text()
                print(f"  status: {resp.status}  body: {body}")
        elif verb == "set":
            if len(parts) < 3:
                print("  Usage: set <key> <value>  (value parsed as JSON)")
                continue
            import json as _json
            from blinkpy import api as _api
            key, raw = parts[1], parts[2]
            try:
                value = _json.loads(raw)
            except _json.JSONDecodeError:
                value = raw
            payload = _json.dumps({key: value})
            print(f"  POSTing: {payload}")
            resp = await _api.request_update_config(
                camera.sync.blink, camera.network_id, camera.camera_id,
                product_type="owl", data=payload
            )
            if resp is None:
                print("  result: None (request failed)")
            else:
                body = await resp.text()
                print(f"  status: {resp.status}  body: {body}")
        elif verb == "config":
            import json as _json
            from blinkpy import api as _api
            result = await _api.request_get_config(
                camera.sync.blink, camera.network_id, camera.camera_id, product_type="owl"
            )
            print(_json.dumps(result, indent=2, default=str))
        elif verb == "accessories":
            import json as _json
            print(_json.dumps(camera.get_light_accessories(), indent=2))
        elif verb == "on":
            print("Turning ON …")
            result = await camera.async_set_floodlight(True)
            print(f"  result: {result}")
            print(f"  floodlight_enabled (cached): {camera.floodlight_enabled}")
        elif verb == "off":
            print("Turning OFF …")
            result = await camera.async_set_floodlight(False)
            print(f"  result: {result}")
            print(f"  floodlight_enabled (cached): {camera.floodlight_enabled}")
        elif verb == "status":
            print(f"  floodlight_enabled (cached): {camera.floodlight_enabled}")
            print(f"  product_type:  {camera.product_type}")
            print(f"  camera_id:     {camera.camera_id}")
            print(f"  network_id:    {camera.network_id}")
            import json as _json
            print(f"  accessories:   {_json.dumps(camera.get_light_accessories())}")
        else:
            print("Unknown command. Use: on | off | accessories | status | quit")


async def main():
    async with ClientSession() as session:
        blink = await login(session)

        floods = find_floodlights(blink)
        if not floods:
            print("\nNo cameras with product_type='superior' found.")
            print("All cameras detected:")
            for name, cam in blink.cameras.items():
                print(f"  {name}  product_type={cam.product_type!r}  id={cam.camera_id}")
            all_names = list(blink.cameras)
            if not all_names:
                print("No cameras found at all. Exiting.")
                sys.exit(1)
            raw = input(
                "\nEnter camera name to test anyway (or Enter to quit): "
            ).strip()
            if not raw or raw not in blink.cameras:
                sys.exit(0)
            camera = blink.cameras[raw]
        else:
            camera = pick_camera(floods)

        await toggle_loop(camera)


if __name__ == "__main__":
    asyncio.run(main())
