from pydantic import BaseSettings, Field, validator
from typing import Optional, List
import os
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class Settings(BaseSettings):
    """Application configuration with validation"""
    
    # Application
    app_name: str = "Streamlit Terraform Deployer"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = Field(default=False)
    
    # Streamlit
    streamlit_port: int = Field(default=8501, ge=1024, le=65535)
    max_upload_size_mb: int = Field(default=10, ge=1, le=100)
    
    # Terraform
    terraform_working_dir: str = Field(default="./infra")
    terraform_state_backend: str = Field(default="local")
    terraform_state_bucket: Optional[str] = None
    terraform_lock_table: Optional[str] = None
    
    # AWS
    aws_region: str = Field(default="us-east-1")
    aws_profile: Optional[str] = None
    
    # Security
    enable_auth: bool = Field(default=True)
    secret_key: str = Field(default="change-me-in-production")
    allowed_file_types: List[str] = Field(default=["json", "yaml", "yml"])
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    # Redis (for async tasks)
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    
    @validator("terraform_state_backend")
    def validate_state_backend(cls, v, values):
        if v == "s3" and not values.get("terraform_state_bucket"):
            raise ValueError("terraform_state_bucket required when using S3 backend")
        return v
    
    @validator("secret_key")
    def validate_secret_key(cls, v, values):
        if values.get("environment") == Environment.PRODUCTION and v == "change-me-in-production":
            raise ValueError("Must set a secure secret_key in production")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
settings = Settings()
