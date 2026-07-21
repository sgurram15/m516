"""FastAPI app factory (docs/05_API_DESIGN.md). Run with:
`uvicorn m516.api.app:create_app --factory --reload`
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from m516.api.routes import router

_DESCRIPTION = "M516 - passive attack-surface + compliance-intelligence engine (POC API)."


def create_app() -> FastAPI:
    app = FastAPI(title="M516 API", description=_DESCRIPTION, version="0.1.0")
    # Permissive CORS: no auth/cookies exist to protect (ADR-010, no auth built for the POC) and the
    # frontend's origin isn't fixed yet. Tighten if this API is ever exposed beyond a local demo.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")
    return app
