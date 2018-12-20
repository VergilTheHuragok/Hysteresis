from time import sleep
import os.path
import subprocess

from update_server import update


def close():
    """Close listeners."""
    pass


def get_running():
    """Check if any servers are running."""
    return False


updated = False

while True:
    sleep(1)

    if not updated:
        updated = update()
    if updated and not get_running():
        updated = False
        close()
        subprocess.Popen(
            ["python", "server.py"], creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        break
