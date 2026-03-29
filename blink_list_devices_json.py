#!/usr/bin/env python3
import asyncio
import builtins
import json
from pathlib import Path

from aiohttp import ClientSession
from blinkpy.auth import Auth
from blinkpy.auth import BlinkTwoFARequiredError
from blinkpy.blinkpy import Blink


CRED_FILE = Path("blink_credentials.json")


def load_credentials(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}
        return data
    except json.JSONDecodeError:
        return {}


def save_credentials(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def prompt_if_missing(creds: dict, key: str, prompt_text: str) -> str:
    value = (creds.get(key) or "").strip()
    if not value:
        value = input(prompt_text).strip()
        creds[key] = value
    return value


async def close_session_if_needed(session_obj) -> None:
    if session_obj is None:
        return
    if getattr(session_obj, "closed", False):
        return
    close_fn = getattr(session_obj, "close", None)
    if close_fn is None:
        return
    result = close_fn()
    if asyncio.iscoroutine(result):
        await result


async def prompt_2fa_with_optional_stored_code(blink: Blink, stored_code: str) -> str:
    code = (stored_code or "").strip()
    if not code:
        code = input("Enter Blink 2FA code: ").strip()

    # blinkpy 0.25.x exposes prompt_2fa(), but not send_auth_key().
    # Feed the stored code into the prompt automatically.
    original_input = builtins.input
    try:
        builtins.input = lambda _prompt="": code
        await blink.prompt_2fa()
        return code
    finally:
        builtins.input = original_input


async def main():
    creds = load_credentials(CRED_FILE)

    username = prompt_if_missing(creds, "username", "Blink username/email: ")
    password = prompt_if_missing(creds, "password", "Blink password: ")
    creds.setdefault("2fa_code", "")

    session = ClientSession()
    blink = None
    try:
        blink = Blink(session=session)
        auth_payload = dict(creds)
        auth_payload["username"] = username
        auth_payload["password"] = password
        auth_payload.pop("2fa_code", None)
        auth = Auth(auth_payload, no_prompt=True)
        blink.auth = auth

        try:
            await blink.start()
        except BlinkTwoFARequiredError:
            try:
                used_code = await prompt_2fa_with_optional_stored_code(
                    blink, creds.get("2fa_code", "")
                )
                if used_code:
                    creds["2fa_code"] = used_code
            except Exception:
                code = input("Stored 2FA code failed. Enter new 2FA code: ").strip()
                creds["2fa_code"] = code
                await prompt_2fa_with_optional_stored_code(blink, code)

        # Persist Blink auth cache/tokens so future runs avoid repeated 2FA.
        await blink.save(str(CRED_FILE))
        saved = load_credentials(CRED_FILE)
        saved["username"] = username
        saved["password"] = password
        saved["2fa_code"] = creds.get("2fa_code", "")
        save_credentials(CRED_FILE, saved)

        print("\n=== Cameras (including doorbells) ===")
        if blink.cameras:
            for name, camera in blink.cameras.items():
                cam_type = getattr(camera, "camera_type", "unknown")
                print(f"- {name} [{cam_type}]")
        else:
            print("No cameras found.")

        print("\n=== Doorbells ===")
        doorbells = getattr(blink, "doorbells", None)
        if doorbells:
            for name, bell in doorbells.items():
                bell_type = getattr(bell, "camera_type", "doorbell")
                print(f"- {name} [{bell_type}]")
        else:
            derived = [
                (name, cam)
                for name, cam in blink.cameras.items()
                if "doorbell" in str(getattr(cam, "camera_type", "")).lower()
            ]
            if derived:
                for name, bell in derived:
                    print(f"- {name} [{getattr(bell, 'camera_type', 'doorbell')}]")
            else:
                print("No doorbells found.")
    finally:
        # Some blinkpy flows can leave extra aiohttp sessions open.
        # Close all known session handles explicitly.
        seen = set()
        session_candidates = [
            getattr(blink, "session", None) if blink else None,
            getattr(getattr(blink, "auth", None), "session", None) if blink else None,
            session,
        ]
        for item in session_candidates:
            if item is None or id(item) in seen:
                continue
            seen.add(id(item))
            await close_session_if_needed(item)


if __name__ == "__main__":
    asyncio.run(main())
