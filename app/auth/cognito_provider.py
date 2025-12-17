"""
AWS Cognito Authentication Provider

Implements authentication using AWS Cognito as the identity provider.
Supports username/password authentication, OAuth, and user management.

Configuration required:
- COGNITO_USER_POOL_ID: Cognito User Pool ID
- COGNITO_CLIENT_ID: App client ID
- COGNITO_CLIENT_SECRET: App client secret (optional)
- COGNITO_REGION: AWS region (default: us-east-1)
"""

import boto3
from botocore.exceptions import ClientError
import hmac
import hashlib
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.auth.auth_provider import (
    AuthenticationProvider,
    AuthenticationResult,
    User,
    UserRole,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CognitoProvider(AuthenticationProvider):
    """AWS Cognito authentication provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Cognito provider
        
        Args:
            config: Configuration dictionary with Cognito settings
                - user_pool_id: Cognito User Pool ID
                - client_id: App client ID
                - client_secret: App client secret (optional)
                - region: AWS region (default: us-east-1)
        """
        super().__init__(config)
        
        self.user_pool_id = config.get("user_pool_id")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.region = config.get("region", "us-east-1")
        
        if not all([self.user_pool_id, self.client_id]):
            raise ValueError("Cognito configuration incomplete: user_pool_id and client_id required")
        
        # Initialize Cognito client
        self.client = boto3.client("cognito-idp", region_name=self.region)
        
        logger.info(f"Initialized CognitoProvider for user pool: {self.user_pool_id}")
    
    def _calculate_secret_hash(self, username: str) -> Optional[str]:
        """
        Calculate SECRET_HASH for Cognito authentication
        
        Required when app client has a client secret configured
        """
        if not self.client_secret:
            return None
        
        message = username + self.client_id
        dig = hmac.new(
            self.client_secret.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(dig).decode()
    
    def login(self, username: str, password: str) -> AuthenticationResult:
        """
        Authenticate user with username/password using Cognito
        
        Args:
            username: User's username or email
            password: User's password
        """
        try:
            auth_params = {
                "USERNAME": username,
                "PASSWORD": password,
            }
            
            # Add SECRET_HASH if client secret is configured
            secret_hash = self._calculate_secret_hash(username)
            if secret_hash:
                auth_params["SECRET_HASH"] = secret_hash
            
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters=auth_params,
            )
            
            # Handle MFA challenge if required
            if response.get("ChallengeName") == "SMS_MFA" or response.get("ChallengeName") == "SOFTWARE_TOKEN_MFA":
                logger.info(f"MFA required for user: {username}")
                return AuthenticationResult(
                    success=False,
                    error="MFA_REQUIRED",
                    # In production, you'd return challenge session for MFA verification
                )
            
            # Extract tokens
            auth_result = response.get("AuthenticationResult", {})
            access_token = auth_result.get("AccessToken")
            refresh_token = auth_result.get("RefreshToken")
            id_token = auth_result.get("IdToken")
            expires_in = auth_result.get("ExpiresIn", 3600)
            
            # Get user info
            user = self.validate_token(access_token)
            
            if user:
                logger.info(f"User logged in successfully: {user.email}")
                return AuthenticationResult(
                    success=True,
                    user=user,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=expires_in,
                )
            else:
                return AuthenticationResult(
                    success=False,
                    error="Failed to retrieve user information",
                )
                
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            
            logger.warning(f"Login failed for {username}: {error_code} - {error_msg}")
            
            # Map Cognito errors to user-friendly messages
            if error_code == "NotAuthorizedException":
                error_msg = "Incorrect username or password"
            elif error_code == "UserNotFoundException":
                error_msg = "User not found"
            elif error_code == "UserNotConfirmedException":
                error_msg = "User email not confirmed"
            
            return AuthenticationResult(
                success=False,
                error=error_msg,
            )
            
        except Exception as e:
            logger.exception(f"Login error: {e}")
            return AuthenticationResult(
                success=False,
                error=f"Authentication error: {str(e)}",
            )
    
    def login_with_oauth(self, provider: str, code: str) -> AuthenticationResult:
        """
        Authenticate user with OAuth authorization code
        
        Note: Cognito OAuth requires additional setup in Cognito User Pool
        """
        # OAuth implementation would go here
        # This requires setting up OAuth providers in Cognito User Pool
        logger.warning("OAuth login not yet implemented for Cognito provider")
        return AuthenticationResult(
            success=False,
            error="OAuth not implemented",
        )
    
    def logout(self, user_id: str, access_token: str) -> bool:
        """
        Logout user and revoke tokens
        
        Args:
            user_id: User's ID (not used for Cognito global sign-out)
            access_token: User's access token
        """
        try:
            self.client.global_sign_out(AccessToken=access_token)
            logger.info(f"User logged out: {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def validate_token(self, access_token: str) -> Optional[User]:
        """
        Validate access token and extract user information
        
        Args:
            access_token: Access token from Cognito
        """
        try:
            # Get user info using access token
            response = self.client.get_user(AccessToken=access_token)
            
            # Extract user attributes
            attributes = {attr["Name"]: attr["Value"] for attr in response.get("UserAttributes", [])}
            
            user_id = response.get("Username")
            email = attributes.get("email", "")
            name = attributes.get("name", email.split("@")[0])
            
            # Get role from custom attribute
            role_str = attributes.get("custom:role", "viewer")
            try:
                role = UserRole(role_str.lower())
            except ValueError:
                logger.warning(f"Invalid role '{role_str}', defaulting to VIEWER")
                role = UserRole.VIEWER
            
            user = User(
                user_id=user_id,
                email=email,
                name=name,
                role=role,
                provider="cognito",
                metadata=attributes,
                last_login=datetime.now(),
            )
            
            return user
            
        except ClientError as e:
            logger.warning(f"Token validation failed: {e}")
            return None
        except Exception as e:
            logger.exception(f"Token validation error: {e}")
            return None
    
    def refresh_token(self, refresh_token: str) -> AuthenticationResult:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token from previous authentication
        """
        try:
            auth_params = {
                "REFRESH_TOKEN": refresh_token,
            }
            
            # Note: SECRET_HASH is not needed for REFRESH_TOKEN_AUTH
            
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters=auth_params,
            )
            
            auth_result = response.get("AuthenticationResult", {})
            access_token = auth_result.get("AccessToken")
            id_token = auth_result.get("IdToken")
            expires_in = auth_result.get("ExpiresIn", 3600)
            
            user = self.validate_token(access_token)
            
            if user:
                return AuthenticationResult(
                    success=True,
                    user=user,
                    access_token=access_token,
                    refresh_token=refresh_token,  # Refresh token doesn't change
                    expires_in=expires_in,
                )
            
            return AuthenticationResult(
                success=False,
                error="Token refresh failed",
            )
            
        except ClientError as e:
            logger.error(f"Token refresh error: {e}")
            return AuthenticationResult(
                success=False,
                error=f"Refresh error: {e.response['Error']['Message']}",
            )
    
    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user information from Cognito User Pool
        
        Args:
            user_id: User's username in Cognito
        """
        try:
            response = self.client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=user_id,
            )
            
            # Extract user attributes
            attributes = {attr["Name"]: attr["Value"] for attr in response.get("UserAttributes", [])}
            
            email = attributes.get("email", "")
            name = attributes.get("name", email.split("@")[0])
            role_str = attributes.get("custom:role", "viewer")
            
            try:
                role = UserRole(role_str.lower())
            except ValueError:
                role = UserRole.VIEWER
            
            # Parse timestamps
            created_at = response.get("UserCreateDate")
            last_modified = response.get("UserLastModifiedDate")
            
            return User(
                user_id=response.get("Username"),
                email=email,
                name=name,
                role=role,
                provider="cognito",
                metadata=attributes,
                created_at=created_at,
                last_login=last_modified,
            )
            
        except ClientError as e:
            logger.error(f"Get user error: {e}")
            return None
    
    def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """
        Update user's role in Cognito User Pool
        
        Args:
            user_id: User's username
            new_role: New role to assign
        """
        try:
            self.client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=user_id,
                UserAttributes=[
                    {
                        "Name": "custom:role",
                        "Value": new_role.value,
                    }
                ],
            )
            
            logger.info(f"Updated user {user_id} role to {new_role.value}")
            return True
            
        except ClientError as e:
            logger.error(f"Update user role error: {e}")
            return False
    
    def list_users(self, limit: int = 50, offset: int = 0) -> List[User]:
        """
        List all users in Cognito User Pool
        
        Args:
            limit: Maximum number of users to return
            offset: Offset for pagination (not directly supported, using pagination token)
        """
        try:
            params = {
                "UserPoolId": self.user_pool_id,
                "Limit": limit,
            }
            
            response = self.client.list_users(**params)
            
            users = []
            for user_data in response.get("Users", []):
                attributes = {attr["Name"]: attr["Value"] for attr in user_data.get("Attributes", [])}
                
                email = attributes.get("email", "")
                name = attributes.get("name", email.split("@")[0])
                role_str = attributes.get("custom:role", "viewer")
                
                try:
                    role = UserRole(role_str.lower())
                except ValueError:
                    role = UserRole.VIEWER
                
                user = User(
                    user_id=user_data.get("Username"),
                    email=email,
                    name=name,
                    role=role,
                    provider="cognito",
                    metadata=attributes,
                    created_at=user_data.get("UserCreateDate"),
                    last_login=user_data.get("UserLastModifiedDate"),
                )
                users.append(user)
            
            return users
            
        except ClientError as e:
            logger.error(f"List users error: {e}")
            return []
    
    def supports_mfa(self) -> bool:
        """Cognito supports MFA"""
        return True
