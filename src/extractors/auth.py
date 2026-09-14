import psycopg

from typing import cast

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

import google_auth_oauthlib.flow
from google.auth.transport.requests import AuthorizedSession

from src.transformers.db_core import upsert_user
from .token_store import save_credentials

from config.settings import (
    GOOGLE_REDIRECT_URI as REDIRECT_URI,
    GOOGLE_CLIENT_SECRETS_FILE as CLIENT_SECRETS_FILE
)

router = APIRouter()

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/googlehealth.sleep.readonly',
    'https://www.googleapis.com/auth/googlehealth.sleep.writeonly',
    'https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly',
    'https://www.googleapis.com/auth/googlehealth.activity_and_fitness.writeonly',
    'https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly',
    'https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.writeonly',
    'https://www.googleapis.com/auth/googlehealth.nutrition.readonly',
    'https://www.googleapis.com/auth/googlehealth.nutrition.writeonly'
]

# Each request builds its own Flow object, so the PKCE code_verifier generated
# in /login has to be handed off to /oauth2callback explicitly, keyed by state.
_code_verifiers: dict[str, str | None] = {}

@router.get("/login")
def login():
    # 1. Initialize the flow
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI

    # 2. Generate the Google consent screen URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',          # Crucial: This requests the refresh token
        include_granted_scopes='true',  # Keeps any previously granted scopes
        prompt='consent'                # Forces a fresh refresh_token every time
    )
    _code_verifiers[state] = flow.code_verifier

    # 3. Redirect the tester's browser to Google
    return RedirectResponse(url=authorization_url)

@router.get("/oauth2callback")
def oauth2callback(request: Request):
    state = request.query_params.get("state")
    if state is None:
        raise HTTPException(status_code=400, detail="Missing state parameter")

    # 1. Initialize the flow again to catch the callback, restoring the
    # code_verifier that was paired with this state in /login.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        code_verifier=_code_verifiers.pop(state, None)
    )
    flow.redirect_uri = REDIRECT_URI

    # 2. Exchange the URL's auth code for actual tokens
    authorization_response = str(request.url)
    flow.fetch_token(authorization_response=authorization_response)

    # 3. Extract the credentials.
    credentials = flow.credentials
    
    save_credentials(credentials)
    
    user_id = None
    user_email = None
    
    try:
        response = AuthorizedSession(credentials).get("https://health.googleapis.com/v4/users/me/identity")
        if response.status_code == 200:
            user_id = response.json().get("healthUserId")
        else:
            print(f"getIdentity returned {response.status_code}: {response.text[:200]}")
    except Exception as exc:
        print(f"Failed to verify credentials with Google Health API: {exc}")
        
    
    try:
        response = AuthorizedSession(credentials).get("https://www.googleapis.com/oauth2/v3/userinfo")
        if response.status_code == 200:
            user_email = response.json().get("email")
        else:
            print(f"getUserInfo returned {response.status_code}: {response.text[:200]}")
    except Exception as exc:
        print(f"Failed to verify user info with Google OAuth2 API: {exc}")
    
    if user_id:
        try:          
            upsert_user(user_id=user_id, user_email=user_email)
        except psycopg.Error as exc:
            print(f"Failed to upsert user into database: {exc}")
        else:
            print(f"Logged in: {user_email} (id={user_id})")
    else:
        print("Failed to retrieve user_id from Google Health API")
    
    # Hand the browser back to the landing page so the user sees the result.
    return RedirectResponse(url="/?connected=1")
