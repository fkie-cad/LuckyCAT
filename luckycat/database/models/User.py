from flask_security import UserMixin
from luckycat.database.database import db
from luckycat.database.models.Role import Role


class User(db.Document, UserMixin):
    email = db.StringField(max_length=255)
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    api_key = db.StringField(max_length=255)
    roles = db.ListField(db.ReferenceField(Role), default=[])
