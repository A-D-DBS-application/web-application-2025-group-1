from flask import Flask
from flask_migrate import Migrate
from .models import db
from .config import Config

migrate = Migrate()  # <— toevoegen

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)  # <— verbinden van migratiesysteem

    from .routes import main
    app.register_blueprint(main)

    return app
