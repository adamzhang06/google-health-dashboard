import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def _require(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value

# .env
GOOGLE_CLIENT_ID = _require("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = _require("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = _require("GOOGLE_REDIRECT_URI")
GOOGLE_CLIENT_SECRETS_FILE = os.environ.get("GOOGLE_CLIENT_SECRETS_FILE", "client_secret.json")
DATABASE_URL = _require("DATABASE_URL")

# Token storage
TOKEN_FILE = Path(__file__).resolve().parent.parent / "token.json"
