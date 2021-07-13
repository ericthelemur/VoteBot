import os
import psycopg2

from os.path import join
BUILD_PATH = join(".", "db", "build.sql")


try: DATABASE_URL = os.environ['DATABASE_URL']
except KeyError: DATABASE_URL = None

if DATABASE_URL is None:
    DATABASE_URL = "postgres://localhost"
    conn = psycopg2.connect(DATABASE_URL, user="postgres")
else: conn = psycopg2.connect(DATABASE_URL)

# cxn = connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()


def with_commit(func):
    def inner(*args, **kwargs):
        v = func(*args, **kwargs)
        commit()
        return v
    return inner


@with_commit
def build():
    scriptexec(BUILD_PATH)


def close():
    cur.close()
    conn.close()


def commit():
    conn.commit()


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


def executeF1(command, *values):
    cur.execute(command, tuple(values))
    return cur.fetchone()


def executeFAll(command, *values):
    cur.execute(command, tuple(values))
    return cur.fetchall()


def multiexec(command, valueset):
    return cur.executemany(command, valueset)


def scriptexec(path):
    with open(path, "r", encoding="utf-8") as script:
        cur.execute(script.read())
    print("PG Ran", path)
