from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
import google_auth_oauthlib.flow

from config.settings import (
    GOOGLE_REDIRECT_URI as REDIRECT_URI,
    GOOGLE_CLIENT_SECRETS_FILE as CLIENT_SECRETS_FILE,
)

app = FastAPI()

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/googlehealth.sleep.readonly'
]

# Each request builds its own Flow object, so the PKCE code_verifier generated
# in /login has to be handed off to /oauth2callback explicitly, keyed by state.
_code_verifiers: dict[str, str | None] = {}

@app.get("/login")
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

@app.get("/oauth2callback")
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

    # 3. Extract the credentials
    credentials = flow.credentials
    
    access_token = credentials.token
    refresh_token = credentials.refresh_token
    # You can also extract the user's ID token here to get their email address
    
    # TODO: Save the user's email, access_token, and refresh_token to your SQL database here
    # print(access_token, refresh_token)
    
    
    return {"message": "Tokens successfully acquired and saved!"}