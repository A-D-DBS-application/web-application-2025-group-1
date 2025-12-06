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
    _db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres.eoysewmdlgotspzgbpkb:Group1_ADDBS!@aws-1-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require",
    )
    # Convert postgresql:// to postgresql+psycopg:// to use psycopg3 (required by requirements.txt)
    if _db_url.startswith("postgresql://") and not _db_url.startswith("postgresql+psycopg://"):
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    # Connection pool settings to handle Supabase connection issues
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

