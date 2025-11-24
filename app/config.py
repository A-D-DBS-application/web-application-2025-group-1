import importlib
import os

dotenv_spec = importlib.util.find_spec("dotenv")
if dotenv_spec:
    load_dotenv = importlib.import_module("dotenv").load_dotenv  # type: ignore[attr-defined]
else:  # pragma: no cover - optional dependency
    def load_dotenv(*_, **__):
        return None

# Load environment variables from a .env file if present so every developer
# can keep credentials local without committing them.
load_dotenv()


class Config:
<<<<<<< Updated upstream
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///app.db"  # Local fallback so the app boots
    )
=======
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = (
    "postgresql+psycopg2://postgres:Group1_ADDBS!"
    "@db.eoysewmdlgotspzgbpkb.supabase.co:5432/postgres"
)

>>>>>>> Stashed changes
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
