from dotenv import load_dotenv

from app.database import db, init_peewee_db
from app.models.url import URL

load_dotenv()
init_peewee_db()
db.create_tables([URL])
print("✅ Tables created successfully")
