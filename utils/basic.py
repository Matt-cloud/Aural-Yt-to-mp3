import json
import os
import random
import string

osjoin = os.path.join
cwd = os.getcwd()


def createToken(length=10):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def join(path, cwd=cwd):
    # Just makes it so that you can do "root/folder/file" instead of join("root", "folder", "file")
    # Idk its faster
    if not "/" in path:
        if not cwd:
            return osjoin(path)
        return osjoin(cwd, path)
    paths = path.split("/")
    if not cwd:
        return osjoin(*paths)
    return osjoin(cwd, *paths)


def readJson(path, cwd=cwd):
    fp = join(path, cwd=cwd)
    with open(fp) as f:
        data = json.load(f)
    return data


def writeJson(path, data, cwd=cwd):
    fp = join(path, cwd=cwd)
    with open(fp, "w") as f:
        f.seek(0)
        json.dump(data, f, indent=4)
    written = readJson(path, cwd=cwd)
    return written


def settings():
    return readJson("settings.json")
