"""Login testing script."""
import sys
import os
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load, json_save

save_session = False
print("")
print("Blink Login Debug Script ...")
print(" ... Loading previous session information.")
cwd = os.getcwd()
print(f" ... Looking in {cwd}.")
session_path = os.path.join(cwd, ".session_debug")
session = json_load(session_path)

try:
    auth_file = session["file"]
except (TypeError, KeyError):
    print(" ... Please input location of auth file")
    auth_file = input("     Must contain username and password: ")
    save_session = True

data = json_load(auth_file)
if data is None:
    print(f" ... Please fix file contents of {auth_file}.")
    print(" ... Exiting.")
    sys.exit(1)

try:
    username = data["username"]
    password = data["password"]
except KeyError:
    print(f" ... File contents of {auth_file} incorrect.")
    print(" ... Require username and password at minimum.")
    print(" ... Exiting.")
    sys.exit(1)

if save_session:
    print(f" ... Saving session file to {session_path}.")
    json_save({"file": auth_file}, session_path)

blink = Blink()
auth = Auth(data)
blink.auth = auth

print(" ... Starting Blink.")
print("")
blink.start()
print("")
print(" ... Printing login response.")
print("")
print(blink.auth.login_response)
print("")
print(" ... Printing login attributes.")
print("")
print(blink.auth.login_attributes)
print("")
input(" ... Press any key to continue: ")
print(" ... Deactivating auth token.")
blink.auth.token = "foobar"
print(f"\t - blink.auth.token = {blink.auth.token}")

print(" ... Attempting login.")
print("")
blink.start()
print("")
print(" ... Printing login response.")
print("")
print(blink.auth.login_response)
print("")
print(" ... Printing login attributes.")
print("")
print(blink.auth.login_attributes)
print("")
rint(" ... Done.")
print("")
