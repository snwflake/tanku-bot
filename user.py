import datetime

from peewee import *

class User(Model):
    account_id = IntegerField(unique=True)
    nickname = CharField()
    access_token = CharField()
    expires_at = DateTimeField()
    updated_at = DateTimeField()