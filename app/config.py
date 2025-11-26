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
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres.eoysewmdlgotspzgbpkb:Group1_ADDBS!@aws-1-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
