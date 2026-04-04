from app import create_app
from app.database import db
from app.models.url import URL

app = create_app()

with app.app_context():
    db.create_tables([URL])
    print("✅ Tables created successfully")