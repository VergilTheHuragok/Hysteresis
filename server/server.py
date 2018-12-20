from time import sleep
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
            ["/etc/python3.7/python", "/home/reece/server/Hysteresis/server/server.py"],
            cwd="/home/reece/server/Hysteresis/server/",
        )
        break
