import os
import web
import calendar
import random
from random import randint
from datetime import datetime

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


def init_web_db():
    db = web.database(dbn='mysql', db="nightmare", user="fuzzing", pw="fuzzing", host="127.0.0.1", port=3306)
    db.query('SET NAMES utf8;')
    db.query('SET CHARACTER SET utf8;')
    db.query('SET character_set_connection=utf8;')
    return db


def insert_crash(project_id, crash_signal, exploitability, date, verified):
    init_web_db().insert("crashes",
                         project_id=project_id,
                         crash_signal=crash_signal,
                         crash_path="ddd",
                         # sample_id=3,
                         # total_samples=1,
                         verified=verified,
                         date=date,
                         exploitability=exploitability,
                         additional="",
                         crash_hash="a")


def generate_random_crash_samples(number_of_samples):
    project_ids = [1]
    crash_signals = ["SIGKILL(137)", "SIGSEGV(139)", "SIGHUP(129)"]
    booleans = [True, False]
    from_timestamp = calendar.timegm((2018, 5, 10, 1, 59, 27))
    to_timestamp = calendar.timegm((2018, 6, 12, 13, 59, 27))

    for i in range(number_of_samples):
        project_id = random.choice(project_ids)
        crash_signal = random.choice(crash_signals)
        exploitability = random.choice(booleans)
        verified = random.choice(booleans)
        date = datetime.fromtimestamp(randint(from_timestamp, to_timestamp))
        insert_crash(project_id, crash_signal, exploitability, date, verified)


generate_random_crash_samples(100)
