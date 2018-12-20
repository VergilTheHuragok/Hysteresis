import subprocess

# path = "/usr/local/bin/server/Hysteresis"
path = None


def get_current_version():
    current_version = (
        subprocess.run(
            ["git", "rev-parse", "origin/master"], stdout=subprocess.PIPE, cwd=path
        )
        .stdout.decode("utf-8")
        .strip("\n")
    )
    return current_version


def get_old_version():
    def _update_version(version):
        version_file = open("version", "w")
        version_file.write(version)
        version_file.close()

    try:
        version_file = open("version", "r")
        version = version_file.read()
        version_file.close()
        return version
    except FileNotFoundError:
        _update_version(get_current_version())
        return None

def update():
    if get_current_version() != get_old_version():
        # Not latest version
        subprocess.Popen(["git", "pull", "origin", "master"], cwd=path)
        return True
    return False