from mongoengine import Document
from mongoengine.fields import IntField, StringField, DateTimeField,\
    BooleanField, BinaryField


class Job(Document):
    name = StringField()
    description = StringField()
    date = DateTimeField()
    maximum_samples = IntField()
    maximum_iteration = IntField()
    timeout = IntField()
    enabled = BooleanField()
    archived = BooleanField()
    mutation_engine = StringField()
    fuzzer = StringField()
    samples = BinaryField()
    firmware_root = BinaryField()
    fuzzing_target = BinaryField()
