import importlib
import os

dotenv_spec = importlib.util.find_spec("dotenv") #bekijken, want zelfde wordt gedaan. Eerst zoeken naar dotenv en wanneer gevonden 
if dotenv_spec:
    load_dotenv = importlib.import_module("dotenv").load_dotenv  # type: ignore[attr-defined]
else:  # pragma: no cover - optional dependency
    def load_dotenv(*_, **__):
        return None

# Load environment variables from a .env file if present so every developer
# can keep credentials local without committing them.
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    
    # Get database URL and convert to use psycopg3 driver
    # DATABASE_URL must be set via environment variable (or use SQLite for local dev)
    _db_url = os.getenv("DATABASE_URL")
    if not _db_url:
        # Fallback to SQLite for local development if DATABASE_URL not set
        _db_url = "sqlite:///app.db"
    
    # Connection pool settings - only for PostgreSQL (Supabase)
    # SQLite doesn't need these settings
    if _db_url.startswith("postgresql"):
        # Convert postgresql:// to postgresql+psycopg:// to use psycopg3 (required by requirements.txt)
        if _db_url.startswith("postgresql://") and not _db_url.startswith("postgresql+psycopg://"):
            _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,  # Verify connections before using them
            'pool_recycle': 300,   # Recycle connections after 5 minutes
            'pool_size': 5,        # Number of connections to maintain
            'max_overflow': 10,     # Maximum overflow connections
            'connect_args': {
                'connect_timeout': 10,  # Connection timeout in seconds
                'prepare_threshold': None,  # Disable prepared statements to avoid DuplicatePreparedStatement errors
            }
        }
    else:
        # SQLite doesn't need connection pool settings
        SQLALCHEMY_ENGINE_OPTIONS = {}
    
    SQLALCHEMY_DATABASE_URI = _db_url
    
    # Supabase Storage Configuration
    # Note: Using service_role key for server-side uploads (has full access)
    # SUPABASE_URL and SUPABASE_KEY should be set via environment variables
    # For local development, these can be None (but features requiring Supabase won't work)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_BUCKET_ACTIVITIES = "activities"
    SUPABASE_BUCKET_LOGOS = "logos"
    
    # Mapbox Configuration
    # MAPBOX_ACCESS_TOKEN should be set via environment variable
    MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN", "")

