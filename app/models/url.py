import random
import string
from datetime import datetime

from peewee import CharField, DateTimeField

from app.database import BaseModel


class URL(BaseModel):
    original_url = CharField()
    short_code = CharField(unique=True)
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "urls"


def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))