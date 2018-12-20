import subprocess

path = None


def get_old_version():
    old_version = (
        subprocess.run(["git", "rev-parse", "server"], stdout=subprocess.PIPE, cwd=path)
        .stdout.decode("utf-8")
        .strip("\n")
    )
    return old_version


def get_current_version():
    current_version = (
        subprocess.run(
            ["git", "rev-parse", "origin/server"], stdout=subprocess.PIPE, cwd=path
        )
        .stdout.decode("utf-8")
        .strip("\n")
    )
    return current_version


def update():
    if get_current_version() != get_old_version():
        # Not latest version
        subprocess.run(["git", "pull", "origin", "master"], cwd=path)
        return True
    return False
