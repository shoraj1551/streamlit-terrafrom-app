"""
AWS Secrets Manager Integration

Provides secure storage and retrieval of sensitive credentials using AWS Secrets Manager.
Supports automatic rotation, versioning, and encryption at rest.

Features:
- Store/retrieve secrets securely
- Automatic credential rotation
- Secret versioning
- Caching for performance
- Encryption at rest (AWS KMS)
"""

import boto3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SecretsManager:
    """
    AWS Secrets Manager integration for secure credential storage
    
    Provides a scalable, secure way to manage application secrets with:
    - Automatic encryption at rest (AWS KMS)
    - Automatic rotation support
    - Version control
    - Audit logging
    - In-memory caching for performance
    """
    
    def __init__(self, region: str = "us-east-1", cache_ttl: int = 300):
        """
        Initialize Secrets Manager
        
        Args:
            region: AWS region for Secrets Manager
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.region = region
        self.cache_ttl = cache_ttl
        self.client = boto3.client("secretsmanager", region_name=region)
        
        # In-memory cache for performance
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"Initialized SecretsManager in region: {region}")
    
    def create_secret(
        self,
        name: str,
        secret_value: Dict[str, Any],
        description: Optional[str] = None,
        kms_key_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Create a new secret in AWS Secrets Manager
        
        Args:
            name: Secret name (must be unique)
            secret_value: Secret data as dictionary
            description: Optional description
            kms_key_id: Optional KMS key for encryption
            tags: Optional tags for organization
            
        Returns:
            Secret ARN
        """
        try:
            params = {
                "Name": name,
                "SecretString": json.dumps(secret_value),
            }
            
            if description:
                params["Description"] = description
            
            if kms_key_id:
                params["KmsKeyId"] = kms_key_id
            
            if tags:
                params["Tags"] = [{"Key": k, "Value": v} for k, v in tags.items()]
            
            response = self.client.create_secret(**params)
            
            logger.info(f"Created secret: {name}")
            return response["ARN"]
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceExistsException":
                logger.warning(f"Secret already exists: {name}")
                raise ValueError(f"Secret '{name}' already exists")
            else:
                logger.error(f"Failed to create secret: {e}")
                raise
    
    def get_secret(self, name: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Retrieve secret value from AWS Secrets Manager
        
        Args:
            name: Secret name
            use_cache: Whether to use cached value (default: True)
            
        Returns:
            Secret value as dictionary
        """
        # Check cache first
        if use_cache and name in self._cache:
            cached = self._cache[name]
            if datetime.now() < cached["expires_at"]:
                logger.debug(f"Retrieved secret from cache: {name}")
                return cached["value"]
        
        try:
            response = self.client.get_secret_value(SecretId=name)
            
            # Parse secret string
            secret_value = json.loads(response["SecretString"])
            
            # Update cache
            self._cache[name] = {
                "value": secret_value,
                "expires_at": datetime.now() + timedelta(seconds=self.cache_ttl),
                "version_id": response.get("VersionId"),
            }
            
            logger.info(f"Retrieved secret: {name}")
            return secret_value
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            
            if error_code == "ResourceNotFoundException":
                logger.error(f"Secret not found: {name}")
                raise ValueError(f"Secret '{name}' not found")
            elif error_code == "InvalidRequestException":
                logger.error(f"Invalid request for secret: {name}")
                raise ValueError(f"Invalid request for secret '{name}'")
            else:
                logger.error(f"Failed to retrieve secret: {e}")
                raise
    
    def update_secret(
        self,
        name: str,
        secret_value: Dict[str, Any],
        description: Optional[str] = None,
    ) -> str:
        """
        Update an existing secret
        
        Args:
            name: Secret name
            secret_value: New secret value
            description: Optional new description
            
        Returns:
            Version ID of the new secret version
        """
        try:
            params = {
                "SecretId": name,
                "SecretString": json.dumps(secret_value),
            }
            
            if description:
                params["Description"] = description
            
            response = self.client.update_secret(**params)
            
            # Invalidate cache
            if name in self._cache:
                del self._cache[name]
            
            logger.info(f"Updated secret: {name}")
            return response["VersionId"]
            
        except ClientError as e:
            logger.error(f"Failed to update secret: {e}")
            raise
    
    def delete_secret(
        self,
        name: str,
        recovery_window_days: int = 30,
        force_delete: bool = False,
    ) -> bool:
        """
        Delete a secret (with optional recovery window)
        
        Args:
            name: Secret name
            recovery_window_days: Days before permanent deletion (7-30)
            force_delete: Force immediate deletion (no recovery)
            
        Returns:
            True if deletion scheduled successfully
        """
        try:
            params = {"SecretId": name}
            
            if force_delete:
                params["ForceDeleteWithoutRecovery"] = True
            else:
                params["RecoveryWindowInDays"] = recovery_window_days
            
            self.client.delete_secret(**params)
            
            # Remove from cache
            if name in self._cache:
                del self._cache[name]
            
            logger.info(f"Deleted secret: {name} (recovery window: {recovery_window_days} days)")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete secret: {e}")
            return False
    
    def rotate_secret(
        self,
        name: str,
        rotation_lambda_arn: str,
        rotation_rules: Optional[Dict[str, int]] = None,
    ) -> bool:
        """
        Enable automatic rotation for a secret
        
        Args:
            name: Secret name
            rotation_lambda_arn: ARN of Lambda function for rotation
            rotation_rules: Rotation schedule (e.g., {"AutomaticallyAfterDays": 30})
            
        Returns:
            True if rotation enabled successfully
        """
        try:
            params = {
                "SecretId": name,
                "RotationLambdaARN": rotation_lambda_arn,
            }
            
            if rotation_rules:
                params["RotationRules"] = rotation_rules
            else:
                # Default: rotate every 30 days
                params["RotationRules"] = {"AutomaticallyAfterDays": 30}
            
            self.client.rotate_secret(**params)
            
            logger.info(f"Enabled rotation for secret: {name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to enable rotation: {e}")
            return False
    
    def list_secrets(
        self,
        filters: Optional[List[Dict[str, Any]]] = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List all secrets (with optional filters)
        
        Args:
            filters: Optional filters (e.g., [{"Key": "name", "Values": ["db-*"]}])
            max_results: Maximum number of results
            
        Returns:
            List of secret metadata
        """
        try:
            params = {"MaxResults": max_results}
            
            if filters:
                params["Filters"] = filters
            
            response = self.client.list_secrets(**params)
            
            secrets = response.get("SecretList", [])
            
            logger.info(f"Listed {len(secrets)} secrets")
            return secrets
            
        except ClientError as e:
            logger.error(f"Failed to list secrets: {e}")
            return []
    
    def get_secret_versions(self, name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a secret
        
        Args:
            name: Secret name
            
        Returns:
            List of version metadata
        """
        try:
            response = self.client.list_secret_version_ids(SecretId=name)
            
            versions = response.get("Versions", [])
            
            logger.info(f"Found {len(versions)} versions for secret: {name}")
            return versions
            
        except ClientError as e:
            logger.error(f"Failed to list secret versions: {e}")
            return []
    
    def clear_cache(self, name: Optional[str] = None):
        """
        Clear secret cache
        
        Args:
            name: Optional secret name (if None, clears entire cache)
        """
        if name:
            if name in self._cache:
                del self._cache[name]
                logger.debug(f"Cleared cache for secret: {name}")
        else:
            self._cache.clear()
            logger.debug("Cleared entire secret cache")


# Convenience functions for common secrets

def get_database_credentials(secrets_manager: SecretsManager, db_name: str = "terraform-app-db") -> Dict[str, str]:
    """
    Get database credentials from Secrets Manager
    
    Args:
        secrets_manager: SecretsManager instance
        db_name: Database secret name
        
    Returns:
        Dictionary with host, port, username, password, database
    """
    return secrets_manager.get_secret(db_name)


def get_aws_credentials(secrets_manager: SecretsManager, name: str = "terraform-app-aws") -> Dict[str, str]:
    """
    Get AWS credentials from Secrets Manager
    
    Args:
        secrets_manager: SecretsManager instance
        name: AWS credentials secret name
        
    Returns:
        Dictionary with access_key_id, secret_access_key, region
    """
    return secrets_manager.get_secret(name)


def get_auth_provider_config(secrets_manager: SecretsManager, provider: str = "auth0") -> Dict[str, str]:
    """
    Get authentication provider configuration from Secrets Manager
    
    Args:
        secrets_manager: SecretsManager instance
        provider: Provider name (auth0, cognito, etc.)
        
    Returns:
        Dictionary with provider-specific configuration
    """
    secret_name = f"terraform-app-auth-{provider}"
    return secrets_manager.get_secret(secret_name)
