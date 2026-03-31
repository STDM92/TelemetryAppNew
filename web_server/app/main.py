from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.proposals import router as proposals_router
from app.api.routes.runtime import router as runtime_router
from app.api.routes.state import router as state_router
from app.api.routes.ws import router as ws_router

app = FastAPI(title="Telemetry Web Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(runtime_router)
app.include_router(state_router)
app.include_router(sessions_router)
app.include_router(proposals_router)
app.include_router(ws_router)
