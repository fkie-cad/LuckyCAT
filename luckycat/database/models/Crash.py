from mongoengine import Document
from mongoengine.fields import IntField, StringField, DateTimeField,\
    BooleanField, ObjectIdField


class Crash(Document):
    job_id = ObjectIdField()
    crash_signal = IntField()
    exploitability = StringField()
    date = DateTimeField()
    crash_hash = StringField()
    verified = BooleanField()
    crash_path = StringField()
    additional = StringField()
