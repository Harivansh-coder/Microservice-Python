from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
marsh = Marshmallow()


def create_flask_app():
    app = Flask(__name__)

    # Load configurations from config.py
    app.config.from_object('app.config.Config')

    # Initialize the database and marshmallow
    db.init_app(app)
    marsh.init_app(app)

    from app.routes import routes

    # Importing routes
    app.register_blueprint(routes, url_prefix="/api/v1")

    return app
