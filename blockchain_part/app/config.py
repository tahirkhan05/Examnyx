from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    APP_NAME: str = "OMR_Blockchain_Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "dev-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Database
    DATABASE_URL: str = "sqlite:///./omr_blockchain.db"
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "omr-evaluation-storage"
    
    # Blockchain
    BLOCKCHAIN_DIFFICULTY: int = 4
    GENESIS_BLOCK_HASH: str = "0" * 64
    REQUIRED_SIGNATURES: int = 3
    
    # Multi-Signature Keys
    AI_VERIFIER_KEY: str = "ai-verifier-public-key"
    HUMAN_VERIFIER_KEY: str = "human-verifier-public-key"
    ADMIN_CONTROLLER_KEY: str = "admin-controller-public-key"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/blockchain_backend.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
