"""
Environment Models and Configuration

Defines environment types and configurations for dev/staging/prod deployments.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class EnvironmentType(str, Enum):
    """Supported environment types"""
    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration"""
    
    # Basic info
    name: EnvironmentType
    cloud_provider: str
    region: str
    instance_type: str
    
    # Environment-specific settings
    auto_scaling: bool = False
    backup_enabled: bool = False
    monitoring_enabled: bool = True
    
    # Scaling configuration
    min_instances: int = 1
    max_instances: int = 1
    
    # Backup configuration
    backup_retention_days: int = 7
    
    # Tags and metadata
    tags: Dict[str, str] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    
    # Additional settings
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        use_enum_values = True


# Predefined environment templates
ENVIRONMENT_TEMPLATES = {
    EnvironmentType.DEVELOPMENT: {
        "auto_scaling": False,
        "backup_enabled": False,
        "monitoring_enabled": True,
        "min_instances": 1,
        "max_instances": 1,
        "backup_retention_days": 3,
        "tags": {
            "Environment": "Development",
            "CostCenter": "Engineering",
            "AutoShutdown": "true"
        },
        "description": "Development environment for testing and experimentation"
    },
    EnvironmentType.STAGING: {
        "auto_scaling": True,
        "backup_enabled": True,
        "monitoring_enabled": True,
        "min_instances": 1,
        "max_instances": 3,
        "backup_retention_days": 7,
        "tags": {
            "Environment": "Staging",
            "CostCenter": "Engineering",
            "AutoShutdown": "false"
        },
        "description": "Staging environment for pre-production testing"
    },
    EnvironmentType.PRODUCTION: {
        "auto_scaling": True,
        "backup_enabled": True,
        "monitoring_enabled": True,
        "min_instances": 2,
        "max_instances": 10,
        "backup_retention_days": 30,
        "tags": {
            "Environment": "Production",
            "CostCenter": "Operations",
            "AutoShutdown": "false",
            "Compliance": "required"
        },
        "description": "Production environment serving live traffic"
    }
}


def get_environment_template(env_type: EnvironmentType) -> Dict[str, Any]:
    """Get predefined template for environment type"""
    return ENVIRONMENT_TEMPLATES.get(env_type, {})


def create_environment_config(
    env_type: EnvironmentType,
    cloud_provider: str,
    region: str,
    instance_type: str,
    **overrides
) -> EnvironmentConfig:
    """
    Create environment configuration from template
    
    Args:
        env_type: Environment type (dev/staging/prod)
        cloud_provider: Cloud provider (aws/azure/gcp)
        region: Deployment region
        instance_type: Instance/VM type
        **overrides: Additional configuration overrides
        
    Returns:
        EnvironmentConfig instance
    """
    # Get template
    template = get_environment_template(env_type)
    
    # Merge with overrides
    config_dict = {
        "name": env_type,
        "cloud_provider": cloud_provider,
        "region": region,
        "instance_type": instance_type,
        **template,
        **overrides
    }
    
    return EnvironmentConfig(**config_dict)
