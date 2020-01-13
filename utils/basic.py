from flask import jsonify
from decimal import Decimal

import json
import os
import random
import string
import time
import sys

osjoin = os.path.join
cwd = os.getcwd()


def createToken(length=10):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def makeResponse(extra=None, status="ok", code=200):
    response = {
        "status": status,
        "code": code,
        "timestamp": int(time.time())
    }

    if isinstance(extra, dict):
        response = {**extra, **response}
    
    return jsonify(response), code


def join(path, cwd=cwd):
    # Just makes it so that you can do "root/folder/file" instead of join("root", "folder", "file")
    # Idk its faster

    if isinstance(path, list):
        path = "/".join(path)

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

def round_num(n, decimals):
    '''
    Params:
    n - number to round
    decimals - number of decimal places to round to
    Round number to 2 decimal places
    For example:
    10.0 -> 10
    10.222 -> 10.22
    '''
    return n.to_integral() if n == n.to_integral() else round(n.normalize(), decimals)

def drop_zero(n):
    '''
    Drop trailing 0s
    For example:
    10.100 -> 10.1
    '''
    n = str(n)
    return n.rstrip('0').rstrip('.') if '.' in n else n

def numerize(n, decimals=2):
    '''
    Params:
    n - number to be numerized
    decimals - number of decimal places to round to
    Converts numbers like:
    1,000 -> 1K
    1,000,000 -> 1M
    1,000,000,000 -> 1B
    1,000,000,000,000 -> 1T
    '''
    is_negative_string = ""
    if n < 0:
        is_negative_string = "-"
    n = abs(Decimal(n))
    if n < 1000:
        return is_negative_string + str(drop_zero(round_num(n, decimals)))
    elif n >= 1000 and n < 1000000:
        if n % 1000 == 0:
            return is_negative_string + str(int(n / 1000)) + "K"
        else:
            n = n / 1000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "K"
    elif n >= 1000000 and n < 1000000000:
        if n % 1000000 == 0:
            return is_negative_string + str(int(n / 1000000)) + "M"
        else:
            n = n / 1000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "M"
    elif n >= 1000000000 and n < 1000000000000:
        if n % 1000000000 == 0:
            return is_negative_string + str(int(n / 1000000000)) + "B"
        else:
            n = n / 1000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "B"
    elif n >= 1000000000000 and n < 1000000000000000:
        if n % 1000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000)) + "T"
        else:
            n = n / 1000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "T"
    else:
        return is_negative_string + str(n)



def settings():
    return readJson("settings.json")
