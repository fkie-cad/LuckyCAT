from mongoengine import Document
from mongoengine.fields import IntField, StringField, DateTimeField,\
    BooleanField, BinaryField, ReferenceField
from luckycat.database.models.User import User


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
    verifier = StringField()
    samples = BinaryField()
    firmware_root = BinaryField()
    fuzzing_target = BinaryField()
    owner = ReferenceField(User)
