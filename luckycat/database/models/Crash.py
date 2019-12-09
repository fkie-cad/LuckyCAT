import datetime

from mongoengine import Document
from mongoengine.fields import IntField, StringField, DateTimeField, \
    BooleanField, ObjectIdField, BinaryField


class Crash(Document):
    job_id = ObjectIdField()
    crash_signal = IntField()
    exploitability = StringField()
    date = DateTimeField(default=datetime.datetime.now())
    crash_hash = StringField()
    verified = BooleanField()
    additional = StringField()
    test_case = BinaryField()
    iteration = IntField()
