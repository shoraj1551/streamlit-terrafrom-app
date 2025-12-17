"""
Secure Configuration Manager

Manages application configuration with automatic secret retrieval from AWS Secrets Manager.
Replaces environment variables with secure secret storage.

Features:
- Automatic secret retrieval
- Configuration validation
- Environment-specific configs
- Fallback to environment variables
- Caching for performance
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from app.services.secrets_manager import SecretsManager
from app.services.encryption import EncryptionService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class SecureConfig:
    """Secure configuration container"""
    
    # Application
    environment: str
    debug: bool
    secret_key: str
    
    # AWS
    aws_region: str
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Authentication
    auth_provider: str = "auth0"
    auth0_domain: Optional[str] = None
    auth0_client_id: Optional[str] = None
    auth0_client_secret: Optional[str] = None
    cognito_user_pool_id: Optional[str] = None
    cognito_client_id: Optional[str] = None
    cognito_client_secret: Optional[str] = None
    
    # Database
    db_host: Optional[str] = None
    db_port: int = 5432
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    
    # Encryption
    encryption_master_key: Optional[str] = None
    
    # Terraform
    terraform_state_backend: str = "local"
    terraform_state_bucket: Optional[str] = None
    
    @classmethod
    def from_secrets_manager(
        cls,
        secrets_manager: SecretsManager,
        environment: str = "development",
    ) -> "SecureConfig":
        """
        Load configuration from AWS Secrets Manager
        
        Args:
            secrets_manager: SecretsManager instance
            environment: Environment name (development, staging, production)
            
        Returns:
            SecureConfig instance
        """
        # Get application secrets
        try:
            app_secrets = secrets_manager.get_secret(f"terraform-app/{environment}/app")
        except ValueError:
            logger.warning(f"App secrets not found in Secrets Manager, using environment variables")
            app_secrets = {}
        
        # Get AWS credentials
        try:
            aws_secrets = secrets_manager.get_secret(f"terraform-app/{environment}/aws")
        except ValueError:
            logger.warning(f"AWS secrets not found in Secrets Manager")
            aws_secrets = {}
        
        # Get auth provider secrets
        auth_provider = os.getenv("AUTH_PROVIDER", "auth0")
        try:
            auth_secrets = secrets_manager.get_secret(f"terraform-app/{environment}/auth-{auth_provider}")
        except ValueError:
            logger.warning(f"Auth secrets not found in Secrets Manager")
            auth_secrets = {}
        
        # Get database secrets
        try:
            db_secrets = secrets_manager.get_secret(f"terraform-app/{environment}/database")
        except ValueError:
            logger.warning(f"Database secrets not found in Secrets Manager")
            db_secrets = {}
        
        # Merge with environment variables (Secrets Manager takes precedence)
        return cls(
            environment=environment,
            debug=app_secrets.get("debug", os.getenv("DEBUG", "false").lower() == "true"),
            secret_key=app_secrets.get("secret_key", os.getenv("SECRET_KEY", "change-me")),
            
            # AWS
            aws_region=aws_secrets.get("region", os.getenv("AWS_REGION", "us-east-1")),
            aws_access_key_id=aws_secrets.get("access_key_id", os.getenv("AWS_ACCESS_KEY_ID")),
            aws_secret_access_key=aws_secrets.get("secret_access_key", os.getenv("AWS_SECRET_ACCESS_KEY")),
            
            # Authentication
            auth_provider=auth_provider,
            auth0_domain=auth_secrets.get("domain", os.getenv("AUTH0_DOMAIN")),
            auth0_client_id=auth_secrets.get("client_id", os.getenv("AUTH0_CLIENT_ID")),
            auth0_client_secret=auth_secrets.get("client_secret", os.getenv("AUTH0_CLIENT_SECRET")),
            cognito_user_pool_id=auth_secrets.get("user_pool_id", os.getenv("COGNITO_USER_POOL_ID")),
            cognito_client_id=auth_secrets.get("client_id", os.getenv("COGNITO_CLIENT_ID")),
            cognito_client_secret=auth_secrets.get("client_secret", os.getenv("COGNITO_CLIENT_SECRET")),
            
            # Database
            db_host=db_secrets.get("host", os.getenv("DB_HOST")),
            db_port=int(db_secrets.get("port", os.getenv("DB_PORT", "5432"))),
            db_name=db_secrets.get("database", os.getenv("DB_NAME")),
            db_user=db_secrets.get("username", os.getenv("DB_USER")),
            db_password=db_secrets.get("password", os.getenv("DB_PASSWORD")),
            
            # Encryption
            encryption_master_key=app_secrets.get("encryption_master_key", os.getenv("ENCRYPTION_MASTER_KEY")),
            
            # Terraform
            terraform_state_backend=app_secrets.get("terraform_state_backend", os.getenv("TERRAFORM_STATE_BACKEND", "local")),
            terraform_state_bucket=app_secrets.get("terraform_state_bucket", os.getenv("TERRAFORM_STATE_BUCKET")),
        )
    
    @classmethod
    def from_environment(cls, environment: str = "development") -> "SecureConfig":
        """
        Load configuration from environment variables (fallback)
        
        Args:
            environment: Environment name
            
        Returns:
            SecureConfig instance
        """
        return cls(
            environment=environment,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            secret_key=os.getenv("SECRET_KEY", "change-me"),
            
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            
            auth_provider=os.getenv("AUTH_PROVIDER", "auth0"),
            auth0_domain=os.getenv("AUTH0_DOMAIN"),
            auth0_client_id=os.getenv("AUTH0_CLIENT_ID"),
            auth0_client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
            cognito_user_pool_id=os.getenv("COGNITO_USER_POOL_ID"),
            cognito_client_id=os.getenv("COGNITO_CLIENT_ID"),
            cognito_client_secret=os.getenv("COGNITO_CLIENT_SECRET"),
            
            db_host=os.getenv("DB_HOST"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME"),
            db_user=os.getenv("DB_USER"),
            db_password=os.getenv("DB_PASSWORD"),
            
            encryption_master_key=os.getenv("ENCRYPTION_MASTER_KEY"),
            
            terraform_state_backend=os.getenv("TERRAFORM_STATE_BACKEND", "local"),
            terraform_state_bucket=os.getenv("TERRAFORM_STATE_BUCKET"),
        )
    
    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication provider configuration"""
        if self.auth_provider == "auth0":
            return {
                "domain": self.auth0_domain,
                "client_id": self.auth0_client_id,
                "client_secret": self.auth0_client_secret,
            }
        elif self.auth_provider == "cognito":
            return {
                "user_pool_id": self.cognito_user_pool_id,
                "client_id": self.cognito_client_id,
                "client_secret": self.cognito_client_secret,
                "region": self.aws_region,
            }
        else:
            raise ValueError(f"Unsupported auth provider: {self.auth_provider}")
    
    def get_db_connection_string(self) -> str:
        """Get database connection string"""
        if not all([self.db_host, self.db_name, self.db_user, self.db_password]):
            raise ValueError("Database configuration incomplete")
        
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if configuration is valid
        """
        errors = []
        
        # Check critical fields
        if self.environment == "production" and self.secret_key == "change-me":
            errors.append("SECRET_KEY must be set in production")
        
        if self.environment == "production" and self.debug:
            errors.append("DEBUG must be False in production")
        
        if not self.aws_region:
            errors.append("AWS_REGION must be set")
        
        # Check auth configuration
        auth_config = self.get_auth_config()
        if not all(auth_config.values()):
            errors.append(f"Incomplete {self.auth_provider} configuration")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        return True


class ConfigurationManager:
    """
    Manages application configuration with automatic secret retrieval
    
    Provides a single interface for accessing configuration with:
    - Automatic secret retrieval from AWS Secrets Manager
    - Fallback to environment variables
    - Configuration validation
    - Caching
    """
    
    def __init__(
        self,
        environment: Optional[str] = None,
        use_secrets_manager: bool = True,
    ):
        """
        Initialize configuration manager
        
        Args:
            environment: Environment name (if None, reads from ENVIRONMENT env var)
            use_secrets_manager: Whether to use AWS Secrets Manager
        """
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.use_secrets_manager = use_secrets_manager
        
        # Initialize secrets manager if enabled
        if use_secrets_manager:
            try:
                self.secrets_manager = SecretsManager(
                    region=os.getenv("AWS_REGION", "us-east-1")
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Secrets Manager: {e}")
                logger.warning("Falling back to environment variables")
                self.use_secrets_manager = False
                self.secrets_manager = None
        else:
            self.secrets_manager = None
        
        # Load configuration
        self.config = self._load_config()
        
        # Validate configuration
        if not self.config.validate():
            logger.warning("Configuration validation failed")
        
        logger.info(f"Initialized ConfigurationManager for environment: {self.environment}")
    
    def _load_config(self) -> SecureConfig:
        """Load configuration from appropriate source"""
        if self.use_secrets_manager and self.secrets_manager:
            return SecureConfig.from_secrets_manager(
                self.secrets_manager,
                self.environment,
            )
        else:
            return SecureConfig.from_environment(self.environment)
    
    def get_config(self) -> SecureConfig:
        """Get current configuration"""
        return self.config
    
    def reload_config(self):
        """Reload configuration from source"""
        self.config = self._load_config()
        logger.info("Configuration reloaded")
    
    def get_encryption_service(self) -> EncryptionService:
        """Get encryption service with master key from config"""
        if not self.config.encryption_master_key:
            raise ValueError("ENCRYPTION_MASTER_KEY not configured")
        
        return EncryptionService(self.config.encryption_master_key)
