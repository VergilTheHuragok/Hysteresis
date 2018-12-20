import subprocess
from time import sleep

path = None


def get_old_version():
    old_version = (
        subprocess.run(
            ["git", "rev-parse", "master"], stdout=subprocess.PIPE, cwd=path
        )
        .stdout.decode("utf-8")
        .strip("\n")
    )
    return old_version


def get_current_version():
    current_version = (
        subprocess.run(
            ["git", "ls-remote", "https://github.com/singofwalls/Hysteresis.git"], stdout=subprocess.PIPE, cwd=path
        )
        .stdout.decode("utf-8")
        .strip("\n").split("\t")[0]
    )
    return current_version

def update():
    if get_current_version() != get_old_version():
        # Not latest version
        subprocess.run(["git", "pull", "origin", "master"], cwd=path)
        return True
    return False