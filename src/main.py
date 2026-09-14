from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.extractors.auth import router as auth_router

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Google Health Dashboard")

# Everything under /static is served straight from disk (css, js, images).
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# OAuth routes: /login and /oauth2callback
app.include_router(auth_router)


@app.get("/", include_in_schema=False)
def index():
    """The landing page. Plain HTML - the browser fetches data from /api/*."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status():
    """Tiny JSON endpoint so the frontend has something real to call."""
    return {
        "status": "ok",
        "connected": False,  # TODO: flip once tokens are persisted in the DB
    }


@app.get("/api/sleep")
def sleep():
    """Placeholder for the sleep data the extractors will eventually return."""
    # TODO: pull from src.extractors.sleep_api once tokens are stored
    return {"nights": []}
