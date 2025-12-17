import yaml
import json
from typing import Dict, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class InfrastructureConfig(BaseModel):
    """Schema for infrastructure configuration"""
    
    provider: str = Field(..., description="Cloud provider (aws, azure, gcp)")
    region: str = Field(..., description="Deployment region")
    instance_type: str = Field(..., description="Instance/VM type")
    ami_id: str = Field(None, description="AMI ID for AWS (optional)")
    tags: Dict[str, str] = Field(default_factory=dict, description="Resource tags")
    
    @validator("provider")
    def validate_provider(cls, v):
        allowed = ["aws", "azure", "gcp"]
        if v.lower() not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v.lower()
    
    @validator("instance_type")
    def validate_instance_type(cls, v, values):
        provider = values.get("provider", "").lower()
        
        # Basic validation - expand based on actual requirements
        if provider == "aws" and not v.startswith(("t2.", "t3.", "m5.", "c5.", "t4g.")):
            logger.warning(f"Unusual AWS instance type: {v}")
        
        return v


class ConfigParser:
    """Parse and validate infrastructure configuration files"""
    
    SUPPORTED_FORMATS = ["json", "yaml", "yml"]
    MAX_FILE_SIZE_MB = 10
    
    @staticmethod
    def parse_file(file_path: Union[str, Path]) -> InfrastructureConfig:
        """
        Parse configuration file and return validated config
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            InfrastructureConfig object
            
        Raises:
            ValueError: If file format is unsupported or validation fails
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        # Check file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > ConfigParser.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File size ({file_size_mb:.2f}MB) exceeds maximum "
                f"allowed size ({ConfigParser.MAX_FILE_SIZE_MB}MB)"
            )
        
        # Check file extension
        extension = file_path.suffix.lstrip(".").lower()
        if extension not in ConfigParser.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {ConfigParser.SUPPORTED_FORMATS}"
            )
        
        # Parse file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if extension == "json":
                    data = json.load(f)
                else:  # yaml or yml
                    data = yaml.safe_load(f)
            
            logger.info(f"Successfully parsed configuration file: {file_path}")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")
        
        # Validate against schema
        try:
            config = InfrastructureConfig(**data)
            logger.info(f"Configuration validated successfully")
            return config
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Configuration validation failed: {e}")
    
    @staticmethod
    def parse_uploaded_file(uploaded_file) -> InfrastructureConfig:
        """
        Parse Streamlit uploaded file
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            InfrastructureConfig object
        """
        # Check file size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > ConfigParser.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File size ({file_size_mb:.2f}MB) exceeds maximum "
                f"allowed size ({ConfigParser.MAX_FILE_SIZE_MB}MB)"
            )
        
        # Get file extension
        extension = uploaded_file.name.split(".")[-1].lower()
        if extension not in ConfigParser.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {ConfigParser.SUPPORTED_FORMATS}"
            )
        
        # Parse content
        try:
            content = uploaded_file.read().decode("utf-8")
            
            if extension == "json":
                data = json.loads(content)
            else:  # yaml or yml
                data = yaml.safe_load(content)
            
            logger.info(f"Successfully parsed uploaded file: {uploaded_file.name}")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")
        
        # Validate against schema
        try:
            config = InfrastructureConfig(**data)
            logger.info("Configuration validated successfully")
            return config
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Configuration validation failed: {e}")
