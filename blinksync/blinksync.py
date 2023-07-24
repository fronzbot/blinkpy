import json
import asyncio
import wx
import logging
import aiohttp
import sys
from sortedcontainers import SortedSet
from forms import LoginDialog, VideosForm, DELAY, CLOSE, DELETE, DOWNLOAD, REFRESH
from blinkpy.blinkpy import Blink, BlinkSyncModule
from blinkpy.auth import Auth


async def main():
    """Main loop for blink test."""
    session = aiohttp.ClientSession()
    blink = Blink(session=session)
    app = wx.App()
    try:
        with wx.DirDialog(None) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
            else:
                sys.exit(0)

        with open(f"{path}/blink.json", "rt", encoding="ascii") as j:
            blink.auth = Auth(json.loads(j.read()), session=session)

    except (StopIteration, FileNotFoundError):
        with LoginDialog() as userdlg:
            userdlg.ShowModal()
            userpass = userdlg.getUserPassword()
        if userpass is not None:
            blink.auth = Auth(
                userpass,
                session=session,
            )
            await blink.save(f"{path}/blink.json")
        else:
            sys.exit(0)
    with wx.BusyInfo("Blink is Working....") as working:
        cursor = wx.BusyCursor()
        if await blink.start():
            await blink.setup_post_verify()
        elif blink.auth.check_key_required():
            print("I failed to authenticate")

        print(f"Sync status: {blink.network_ids}")
        print(f"Sync :{blink.networks}")
        if len(blink.networks) == 0:
            exit()
        my_sync: BlinkSyncModule = blink.sync[
            blink.networks[list(blink.networks)[0]]["name"]
        ]
        cursor = None
        working = None

    while True:
        with wx.BusyInfo("Blink is Working....") as working:
            cursor = wx.BusyCursor()
            for name, camera in blink.cameras.items():
                print(name)
                print(camera.attributes)

            my_sync._local_storage["manifest"] = SortedSet()
            await my_sync.refresh()
            if my_sync.local_storage and my_sync.local_storage_manifest_ready:
                print("Manifest is ready")
                print(f"Manifest {my_sync._local_storage['manifest']}")
            else:
                print("Manifest not ready")
            for name, camera in blink.cameras.items():
                print(f"{camera.name} status: {blink.cameras[name].arm}")
            new_vid = await my_sync.check_new_videos()
            print(f"New videos?: {new_vid}")

            manifest = my_sync._local_storage["manifest"]
            cursor = None
            working = None
        frame = VideosForm(manifest)
        button = frame.ShowModal()
        with wx.BusyInfo("Blink is Working....") as working:
            cursor = wx.BusyCursor()
            if button == CLOSE:
                break
            if button == REFRESH:
                continue
            # Download and delete all videos from sync module
            for item in reversed(manifest):
                if item.id in frame.ItemList:
                    if button == DOWNLOAD:
                        await item.prepare_download(blink)
                        await item.download_video(
                            blink,
                            f"{path}/{item.name}_{item.created_at.astimezone().isoformat().replace(':','_')}.mp4",
                        )
                    if button == DELETE:
                        await item.delete_video(blink)
                    await asyncio.sleep(DELAY)
            cursor = None
            working = None
        frame = None
    await session.close()


# Run the program
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
