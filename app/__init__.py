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
    
    # Register template filters for Supabase Storage URLs
    from .storage import get_activity_image_url, get_logo_url, get_public_url
    
    @app.template_filter('activity_image_url')
    def activity_image_url_filter(file_path):
        """Template filter to get activity image URL from Supabase."""
        from .storage import get_activity_image_url
        return get_activity_image_url(file_path)
    
    @app.template_filter('logo_url')
    def logo_url_filter(file_path):
        """Template filter to get logo URL from Supabase."""
        if not file_path:
            return None
        # Handle full URLs
        if file_path.startswith("http"):
            return file_path
        # Build Supabase URL
        supabase_url = app.config.get('SUPABASE_URL')
        bucket = app.config.get('SUPABASE_BUCKET_LOGOS', 'logos')
        if supabase_url:
            return f"{supabase_url}/storage/v1/object/public/{bucket}/{file_path}"
        return None
    
    # Make Mapbox token available to all templates
    @app.context_processor
    def inject_mapbox_token():
        return dict(MAPBOX_ACCESS_TOKEN=app.config.get('MAPBOX_ACCESS_TOKEN', ''))
    
    @app.template_filter('add_days')
    def add_days_filter(date, days):
        """Template filter to add days to a date."""
        from datetime import timedelta
        if date and days:
            return date + timedelta(days=days)
        return date

    return app

# Create app instance for gunicorn (fallback for 'gunicorn app:app')
app = create_app()