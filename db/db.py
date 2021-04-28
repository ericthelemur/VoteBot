from os.path import isfile
import os
from sqlite3 import connect

DB_PATH = "./data/database.db"
BUILD_PATH = "./db/build.sql"

cxn = connect(DB_PATH, check_same_thread=False)
cur = cxn.cursor()
cur.execute("PRAGMA foreign_keys = ON")


def with_commit(func):
    def inner(*args, **kwargs):
        v = func(*args, **kwargs)
        commit()
        return v
    return inner


@with_commit
def build():
    if not isfile(BUILD_PATH):
        with open(DB_PATH, "w"):
            pass
    scriptexec(BUILD_PATH)


def commit():
    cxn.commit()


def close():
    cxn.close()


def field(command, *values):
    cur.execute(command, tuple(values))

    if (fetch := cur.fetchone()) is not None:
        return fetch[0]


def record(command, *values):
    cur.execute(command, tuple(values))

    return cur.fetchone()


def records(command, *values):
    cur.execute(command, tuple(values))

    return cur.fetchall()


def column(command, *values):
    cur.execute(command, tuple(values))

    return [item[0] for item in cur.fetchall()]


def execute(command, *values):
    return cur.execute(command, tuple(values))


def multiexec(command, valueset):
    return cur.executemany(command, valueset)


def scriptexec(path):
    with open(path, "r", encoding="utf-8") as script:
        cur.executescript(script.read())
    print("Ran", path)
