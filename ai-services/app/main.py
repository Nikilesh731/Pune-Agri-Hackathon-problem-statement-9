"""
FastAPI Main Application
Purpose: Initialize and configure the AI services microservice
"""

import logging
import os

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

