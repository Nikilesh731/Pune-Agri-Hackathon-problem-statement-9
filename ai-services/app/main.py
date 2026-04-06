"""
FastAPI Main Application
Purpose: Initialize and configure the AI services microservice
"""

import logging
import os
import socket

import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.application_priority import router as application_priority_router
from app.api.fraud_detection import router as fraud_router
from app.modules.document_processing.document_processing_router import (
    router as document_processing_router,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_allowed_origins() -> list[str]:
    cors_env = os.getenv("CORS_ORIGIN", "")
    if cors_env.strip():
        return [origin.strip() for origin in cors_env.split(",") if origin.strip()]

    return [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]


app = FastAPI(
    title="AI Smart Agriculture Services",
    description="Microservice for AI-powered agriculture administration features",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("AI Services starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("AI Services shutting down...")


@app.get("/")
async def root():
    return {
        "message": "AI Smart Agriculture Services is running",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Smart Agriculture Services",
        "version": "1.0.0",
    }


app.include_router(
    document_processing_router,
    prefix="/api/document-processing",
    tags=["Document Processing"],
)
app.include_router(
    application_priority_router,
    prefix="/api/application-priority-scoring",
    tags=["Application Priority"],
)
app.include_router(
    fraud_router,
    prefix="/api/fraud-detection",
    tags=["Fraud Detection"],
)


def _is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.connect_ex((host, port)) != 0


def _suggest_available_ports(preferred_port: int) -> list[int]:
    suggestions = []
    for candidate_port in (8001, 8002):
        if candidate_port != preferred_port and _is_port_available(candidate_port):
            suggestions.append(candidate_port)
    return suggestions


def run_server() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    preferred_port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("RELOAD", "false").lower() == "true"

    if not _is_port_available(preferred_port):
        suggestions = _suggest_available_ports(preferred_port)
        if suggestions:
            logger.warning(
                f"[STARTUP] Port {preferred_port} is already in use. Try {', '.join(str(port) for port in suggestions)}."
            )
            preferred_port = suggestions[0]
        else:
            logger.warning(f"[STARTUP] Port {preferred_port} is already in use and no fallback port is currently free.")

    uvicorn.run("app.main:app", host=host, port=preferred_port, reload=reload_enabled)


if __name__ == "__main__":
    run_server()

