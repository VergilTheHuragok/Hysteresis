from time import sleep, time
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
    sleep(5)

    with open("/home/reece/update.txt", "a") as f:
        f.write("checked " + str(time()))

    if not updated:
        updated = update()
    if updated and not get_running():
        with open("/home/reece/update.txt", "a") as f:
            f.write("updated " + str(time()))
        updated = False
        close()
        subprocess.Popen(
            ["/etc/python3.7/python", "/home/reece/server/Hysteresis/server/server.py"],
            cwd="/home/reece/server/Hysteresis/server/",
        )
        break
