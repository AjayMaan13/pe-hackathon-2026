from dotenv import load_dotenv
from flask import Flask, jsonify

from app.database import db, init_db
from app.routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(__name__)

    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee

    register_routes(app)

    from app.models.url import URL
    with app.app_context():
        db.create_tables([URL], safe=True)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    return app
