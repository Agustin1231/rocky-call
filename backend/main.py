"""Token issuer + room dispatcher for the Rocky call UI.

POST /api/token  { "name": "Agustin" }  ->  { "token": "...", "url": "wss://..." }

The web client POSTs its display name, we sign a LiveKit JWT for a fresh room
named `rocky-<uuid7chars>`, and return both the token and the LiveKit WS URL.
The agent worker subscribes to the "rocky" agent pool and joins rooms on
demand via LiveKit's job queue — no explicit dispatch from here is needed.
"""
from __future__ import annotations

import hmac
import os
import secrets

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from livekit import api
from pydantic import BaseModel, Field

load_dotenv()

LK_URL       = os.environ["LIVEKIT_URL"]
LK_KEY       = os.environ["LIVEKIT_API_KEY"]
LK_SECRET    = os.environ["LIVEKIT_API_SECRET"]
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")   # required to issue tokens
ALLOW_ORIG   = os.environ.get("ALLOW_ORIGIN", "*")
STATIC_DIR   = os.environ.get("STATIC_DIR", "/app/static")

app = FastAPI(title="rocky-call backend", version="0.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOW_ORIG] if ALLOW_ORIG != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TokenRequest(BaseModel):
    name: str = Field(min_length=1, max_length=60)


class TokenResponse(BaseModel):
    token: str
    url: str
    room: str


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/token", response_model=TokenResponse)
async def issue_token(
    req: TokenRequest,
    x_call_password: str | None = Header(default=None),
):
    if not LK_KEY or not LK_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit not configured")
    if not APP_PASSWORD:
        raise HTTPException(status_code=500, detail="APP_PASSWORD not configured")
    # Constant-time compare to avoid timing side-channel on short strings
    if not x_call_password or not hmac.compare_digest(x_call_password, APP_PASSWORD):
        raise HTTPException(status_code=401, detail="wrong password")

    room = f"rocky-{secrets.token_hex(4)}"
    identity = f"{req.name}-{secrets.token_hex(3)}"

    at = (
        api.AccessToken(LK_KEY, LK_SECRET)
        .with_identity(identity)
        .with_name(req.name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .to_jwt()
    )
    return TokenResponse(token=at, url=LK_URL, room=room)


# Serve the built web UI if the static dir exists (in prod it's copied in by
# the Dockerfile; in dev you run the Vite dev server separately).
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
