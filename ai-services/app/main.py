"""
FastAPI Main Application
Purpose: Initialize and configure the AI services microservice
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.modules.document_processing.document_processing_router import router as document_processing_router
from app.api.application_priority import router as application_priority_router
from app.api.fraud_detection import router as fraud_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Smart Agriculture Services",
    description="Microservice for AI-powered agriculture administration features",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
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

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Smart Agriculture Services",
        "version": "1.0.0"
    }

app.include_router(document_processing_router, prefix="/api/document-processing", tags=["Document Processing"])
app.include_router(application_priority_router, prefix="/api/application-priority-scoring", tags=["Application Priority"])
app.include_router(fraud_router, prefix="/api/fraud-detection", tags=["Fraud Detection"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)