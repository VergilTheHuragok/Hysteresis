from time import sleep, time
import os
import subprocess

from update_server import update

LOG_PATH = "/home/reece/server/log.txt"
STOP_PATH = "/home/reece/server/STOP"
PYTHON_PATH = "/etc/python3.7/python"
SERVER_PATH = "/home/reece/server/Hysteresis/server/server.py"
SERVER_FOLDER = "/home/reece/server/Hysteresis/server/"


def close():
    """Close listeners."""
    pass


def get_running():
    """Check if any servers are running."""
    return False


updated = False

while True:

    if os.path.exists(STOP_PATH):
        with open(LOG_PATH, "a") as f:
            f.write("stop " + str(time()) + "\n")
        break

    with open(LOG_PATH, "a") as f:
        f.write("checked " + str(time()) + "\n")

    # Halve log if greater than 1000 lines
    lines = None
    with open(LOG_PATH, "r") as f:
        lines_num = f.read().count("\n")
        if lines_num > 1000:
            lines = f.read().split("\n")[500:]
    if not isinstance(lines, type(None)):
        os.remove(LOG_PATH)
        with open(LOG_PATH, "a") as f:
            for line in lines:
                f.write(line + "\n")

    if not updated:
        updated = update()
    if updated and not get_running():
        with open(LOG_PATH, "a") as f:
            f.write("updated " + str(time()) + "\n")
        updated = False
        close()
        subprocess.Popen([PYTHON_PATH, SERVER_PATH], cwd=SERVER_FOLDER)
        break

    sleep(5)
