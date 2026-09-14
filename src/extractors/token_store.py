import json

from config.settings import TOKEN_FILE
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def _read_token_file():
    """
    Read the raw JSON off disk, or None if nothing has been saved yet.
    """
    if not TOKEN_FILE.exists():
        return None
    return json.loads(TOKEN_FILE.read_text())

def save_credentials(creds):
    """
    Save the credentials to a JSON file.

    Google only hands out a refresh_token on the first consent, so if these
    credentials arrived without one, carry over the token already on disk
    rather than overwriting it with nothing.
    """
    payload = json.loads(creds.to_json())

    if not payload.get("refresh_token"):
        stored = _read_token_file() or {}
        if not stored.get("refresh_token"):
            raise ValueError(
                "No refresh_token on the new credentials and none saved "
                "previously. Re-run /login with prompt='consent'."
            )
        payload["refresh_token"] = stored["refresh_token"]

    TOKEN_FILE.write_text(json.dumps(payload))
    TOKEN_FILE.chmod(0o600)  # long-lived credential, keep it owner-only

def load_credentials():
    """
    Load the credentials from a JSON file.
    """
    creds_data = _read_token_file()
    if creds_data is None:
        return None
    return Credentials.from_authorized_user_info(creds_data)

def get_credentials():
    """
    Get the credentials.
    """
    creds = load_credentials()
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(creds)
    return creds
