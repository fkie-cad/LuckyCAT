from mongoengine import Document
from mongoengine.fields import IntField, ObjectIdField, DateTimeField


class Statistic(Document):
    job_id = ObjectIdField()
    iteration = IntField()
    runtime = IntField()
    execs_per_sec = IntField()
    date = DateTimeField()
