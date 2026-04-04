"""
Configuration Settings
Purpose: Centralized configuration management for AI services
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    app_name: str = "AI Smart Agriculture Services"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Settings
    allowed_origins: list = ["http://localhost:3000", "http://localhost:3001"]
    
    # AI Model Settings
    model_cache_dir: str = "./models"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # OCR Settings
    tesseract_cmd: Optional[str] = None
    ocr_languages: list = ["eng"]
    
    # ML Model Settings
    classification_threshold: float = 0.7
    fraud_detection_threshold: float = 0.8
    
    # External Services
    backend_url: str = "http://localhost:3001"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
