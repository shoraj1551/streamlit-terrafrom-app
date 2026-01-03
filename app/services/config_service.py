"""
Configuration Service - Business Logic Layer

Handles application configuration management.
"""

from typing import Optional, Dict, Any
import os

from app.services.secure_config import SecureConfig
from app.services.secrets_manager import SecretsManager as AWSSecretsManager
from app.services.audit_logger import get_audit_logger, AuditEventType, AuditSeverity
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConfigurationService:
    """
    Configuration management business logic
    
    Provides centralized configuration access with security.
    """
    
    def __init__(
        self,
        secure_config: Optional[SecureConfig] = None,
        secrets_manager: Optional[AWSSecretsManager] = None,
        audit_logger: Optional[Any] = None
    ):
        """
        Initialize configuration service
        
        Args:
            secure_config: Secure config service (injected)
            secrets_manager: Secrets manager (injected)
            audit_logger: Audit logger (injected)
        """
        self.config = secure_config or SecureConfig()
        self.secrets = secrets_manager
        self.audit = audit_logger or get_audit_logger()
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        # Try environment variable first
        value = os.getenv(key)
        
        if value is not None:
            return value
        
        # Try secure config
        if hasattr(self.config, key.lower()):
            return getattr(self.config, key.lower())
        
        return default
    
    def get_secret(self, secret_name: str, use_cache: bool = True) -> Optional[str]:
        """
        Get secret from AWS Secrets Manager
        
        Args:
            secret_name: Secret name
            use_cache: Whether to use cache
            
        Returns:
            Secret value or None
        """
        if not self.secrets:
            logger.warning("Secrets manager not configured")
            return None
        
        try:
            secret = self.secrets.get_secret(secret_name)
            logger.debug(f"Retrieved secret: {secret_name}")
            return secret
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            return None
    
    def update_config(
        self,
        key: str,
        value: Any,
        user_email: str,
        persist: bool = False
    ) -> bool:
        """
        Update configuration value
        
        Args:
            key: Configuration key
            value: New value
            user_email: User making the change
            persist: Whether to persist to storage
            
        Returns:
            True if successful
        """
        try:
            # Update in-memory config
            if hasattr(self.config, key.lower()):
                setattr(self.config, key.lower(), value)
            else:
                os.environ[key] = str(value)
            
            # Audit log
            self.audit.log_event(
                event_type=AuditEventType.CONFIG_UPDATE,
                user_id=user_email,
                resource_type="configuration",
                resource_id=key,
                details={"key": key, "persist": persist},
                severity=AuditSeverity.INFO
            )
            
            logger.info(f"Configuration updated: {key} by {user_email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update config {key}: {e}")
            return False
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration
        
        Returns:
            Database configuration dictionary
        """
        return {
            "host": self.get_config("DB_HOST", "localhost"),
            "port": int(self.get_config("DB_PORT", "5432")),
            "database": self.get_config("DB_NAME", "terraform_app"),
            "user": self.get_config("DB_USER", "postgres"),
            "password": self.get_secret("db_password") or self.get_config("DB_PASSWORD"),
            "pool_size": int(self.get_config("DB_POOL_SIZE", "50")),
            "max_overflow": int(self.get_config("DB_MAX_OVERFLOW", "100"))
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """
        Get Redis configuration
        
        Returns:
            Redis configuration dictionary
        """
        return {
            "host": self.get_config("REDIS_HOST", "localhost"),
            "port": int(self.get_config("REDIS_PORT", "6379")),
            "db": int(self.get_config("REDIS_DB", "0")),
            "password": self.get_secret("redis_password") or self.get_config("REDIS_PASSWORD"),
            "max_connections": int(self.get_config("REDIS_MAX_CONNECTIONS", "50"))
        }
    
    def get_auth0_config(self) -> Dict[str, Any]:
        """
        Get Auth0 configuration
        
        Returns:
            Auth0 configuration dictionary
        """
        return {
            "domain": self.get_config("AUTH0_DOMAIN"),
            "client_id": self.get_config("AUTH0_CLIENT_ID"),
            "client_secret": self.get_secret("auth0_client_secret") or self.get_config("AUTH0_CLIENT_SECRET"),
            "audience": self.get_config("AUTH0_AUDIENCE"),
            "redirect_uri": self.get_config("AUTH0_REDIRECT_URI", "http://localhost:8501/callback")
        }
    
    def validate_config(self) -> Dict[str, bool]:
        """
        Validate all required configuration
        
        Returns:
            Dictionary of validation results
        """
        results = {}
        
        # Database
        db_config = self.get_database_config()
        results["database"] = all([
            db_config["host"],
            db_config["database"],
            db_config["user"],
            db_config["password"]
        ])
        
        # Redis
        redis_config = self.get_redis_config()
        results["redis"] = all([
            redis_config["host"],
            redis_config["port"]
        ])
        
        # Auth0
        auth0_config = self.get_auth0_config()
        results["auth0"] = all([
            auth0_config["domain"],
            auth0_config["client_id"],
            auth0_config["client_secret"]
        ])
        
        return results


# Global service instance (will be replaced with DI)
_config_service = None


def get_config_service() -> ConfigurationService:
    """Get global configuration service instance"""
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService()
    return _config_service
