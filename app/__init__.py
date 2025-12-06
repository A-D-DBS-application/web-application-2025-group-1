from flask import Flask
from flask_migrate import Migrate # 1 importeren van flask-migrate
from .models import db
from .config import Config

migrate = Migrate()  # 2 migratie-object aanmaken

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    # Flask-SQLAlchemy 3.x automatically reads SQLALCHEMY_ENGINE_OPTIONS from config
    # This handles Supabase connection issues where connections are closed unexpectedly
    db.init_app(app)
    
    migrate.init_app(app, db)  # <— 3 verbinden van migratiesysteem koppel flask-migrate aan app en db

    from .routes import main
    app.register_blueprint(main)

    return app

# Create app instance for gunicorn (fallback for 'gunicorn app:app')
app = create_app()