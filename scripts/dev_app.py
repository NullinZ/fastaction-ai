from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastaction.interfaces import router as fastaction_router
from fastaction.persistence import close_fastaction_persistence, initialize_fastaction_persistence
from fastaction.registries import runtime
from fastaction.safe_errors import SafeErrorMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_fastaction_persistence(runtime)
    try:
        yield
    finally:
        close_fastaction_persistence()


app = FastAPI(title="FastAction Dev App", lifespan=lifespan)

app.add_middleware(SafeErrorMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fastaction_router)


@app.get("/")
def root():
    return {
        "service": "FastAction Dev App",
        "health": "/fastaction/health",
        "workbench": "http://127.0.0.1:5177",
    }
