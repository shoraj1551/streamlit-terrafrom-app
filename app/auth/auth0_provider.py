"""
Auth0 Authentication Provider

Implements authentication using Auth0 as the identity provider.
Supports OAuth, JWT tokens, and user management.

Configuration required:
- AUTH0_DOMAIN: Your Auth0 domain
- AUTH0_CLIENT_ID: Application client ID
- AUTH0_CLIENT_SECRET: Application client secret
- AUTH0_AUDIENCE: API audience (optional)
"""

import requests
import jwt
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.auth.auth_provider import (
    AuthenticationProvider,
    AuthenticationResult,
    User,
    UserRole,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class Auth0Provider(AuthenticationProvider):
    """Auth0 authentication provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Auth0 provider
        
        Args:
            config: Configuration dictionary with Auth0 settings
                - domain: Auth0 domain
                - client_id: Application client ID
                - client_secret: Application client secret
                - audience: API audience (optional)
        """
        super().__init__(config)
        
        self.domain = config.get("domain")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.audience = config.get("audience", f"https://{self.domain}/api/v2/")
        
        if not all([self.domain, self.client_id, self.client_secret]):
            raise ValueError("Auth0 configuration incomplete: domain, client_id, and client_secret required")
        
        self.base_url = f"https://{self.domain}"
        logger.info(f"Initialized Auth0Provider for domain: {self.domain}")
    
    def login(self, username: str, password: str) -> AuthenticationResult:
        """
        Authenticate user with username/password using Resource Owner Password Grant
        
        Note: This flow should only be used for trusted first-party applications.
        For web apps, use login_with_oauth instead.
        """
        try:
            url = f"{self.base_url}/oauth/token"
            payload = {
                "grant_type": "password",
                "username": username,
                "password": password,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "audience": self.audience,
                "scope": "openid profile email",
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token")
                expires_in = data.get("expires_in", 3600)
                
                # Get user info from token
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
            else:
                error_msg = response.json().get("error_description", "Authentication failed")
                logger.warning(f"Login failed for {username}: {error_msg}")
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
        
        Args:
            provider: OAuth provider (not used for Auth0, kept for interface compatibility)
            code: Authorization code from OAuth flow
        """
        try:
            url = f"{self.base_url}/oauth/token"
            payload = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.config.get("redirect_uri", "http://localhost:8501/callback"),
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token")
                expires_in = data.get("expires_in", 3600)
                
                user = self.validate_token(access_token)
                
                if user:
                    logger.info(f"OAuth login successful: {user.email}")
                    return AuthenticationResult(
                        success=True,
                        user=user,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_in=expires_in,
                    )
            
            return AuthenticationResult(
                success=False,
                error="OAuth authentication failed",
            )
            
        except Exception as e:
            logger.exception(f"OAuth login error: {e}")
            return AuthenticationResult(
                success=False,
                error=f"OAuth error: {str(e)}",
            )
    
    def logout(self, user_id: str, access_token: str) -> bool:
        """
        Logout user (Auth0 doesn't require server-side logout for JWTs)
        
        Note: JWTs are stateless, so logout is typically handled client-side
        by deleting the token. This method is here for interface compliance.
        """
        logger.info(f"User logged out: {user_id}")
        return True
    
    def validate_token(self, access_token: str) -> Optional[User]:
        """
        Validate JWT access token and extract user information
        
        Args:
            access_token: JWT token from Auth0
            
        Returns:
            User object if token is valid, None otherwise
        """
        try:
            # Get JWKS (JSON Web Key Set) for token verification
            jwks_url = f"{self.base_url}/.well-known/jwks.json"
            jwks_response = requests.get(jwks_url, timeout=10)
            jwks = jwks_response.json()
            
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(access_token)
            rsa_key = {}
            
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
                    break
            
            if not rsa_key:
                logger.warning("Unable to find appropriate key for token validation")
                return None
            
            # Verify and decode token
            payload = jwt.decode(
                access_token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"{self.base_url}/",
            )
            
            # Extract user information
            user_id = payload.get("sub")
            email = payload.get("email", "")
            name = payload.get("name", email.split("@")[0])
            
            # Get role from custom claims (set in Auth0 rules/actions)
            role_str = payload.get("https://terraform-app/role", "viewer")
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
                provider="auth0",
                metadata=payload,
                last_login=datetime.now(),
            )
            
            return user
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTClaimsError as e:
            logger.warning(f"Token claims invalid: {e}")
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
            url = f"{self.base_url}/oauth/token"
            payload = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                new_refresh_token = data.get("refresh_token", refresh_token)
                expires_in = data.get("expires_in", 3600)
                
                user = self.validate_token(access_token)
                
                if user:
                    return AuthenticationResult(
                        success=True,
                        user=user,
                        access_token=access_token,
                        refresh_token=new_refresh_token,
                        expires_in=expires_in,
                    )
            
            return AuthenticationResult(
                success=False,
                error="Token refresh failed",
            )
            
        except Exception as e:
            logger.exception(f"Token refresh error: {e}")
            return AuthenticationResult(
                success=False,
                error=f"Refresh error: {str(e)}",
            )
    
    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user information from Auth0 Management API
        
        Requires Management API token with read:users scope
        """
        try:
            # Get Management API token
            mgmt_token = self._get_management_token()
            
            if not mgmt_token:
                logger.error("Failed to get management API token")
                return None
            
            url = f"{self.base_url}/api/v2/users/{user_id}"
            headers = {"Authorization": f"Bearer {mgmt_token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract role from app_metadata
                app_metadata = data.get("app_metadata", {})
                role_str = app_metadata.get("role", "viewer")
                
                try:
                    role = UserRole(role_str.lower())
                except ValueError:
                    role = UserRole.VIEWER
                
                return User(
                    user_id=data["user_id"],
                    email=data.get("email", ""),
                    name=data.get("name", ""),
                    role=role,
                    provider="auth0",
                    metadata=data,
                    created_at=datetime.fromisoformat(data.get("created_at", "").replace("Z", "+00:00")),
                    last_login=datetime.fromisoformat(data.get("last_login", "").replace("Z", "+00:00")) if data.get("last_login") else None,
                )
            
            return None
            
        except Exception as e:
            logger.exception(f"Get user error: {e}")
            return None
    
    def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """
        Update user's role using Auth0 Management API
        
        Requires Management API token with update:users scope
        """
        try:
            mgmt_token = self._get_management_token()
            
            if not mgmt_token:
                return False
            
            url = f"{self.base_url}/api/v2/users/{user_id}"
            headers = {
                "Authorization": f"Bearer {mgmt_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "app_metadata": {
                    "role": new_role.value,
                }
            }
            
            response = requests.patch(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Updated user {user_id} role to {new_role.value}")
                return True
            
            logger.error(f"Failed to update user role: {response.text}")
            return False
            
        except Exception as e:
            logger.exception(f"Update user role error: {e}")
            return False
    
    def list_users(self, limit: int = 50, offset: int = 0) -> List[User]:
        """
        List all users using Auth0 Management API
        
        Requires Management API token with read:users scope
        """
        try:
            mgmt_token = self._get_management_token()
            
            if not mgmt_token:
                return []
            
            url = f"{self.base_url}/api/v2/users"
            headers = {"Authorization": f"Bearer {mgmt_token}"}
            params = {
                "per_page": limit,
                "page": offset // limit,
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                users_data = response.json()
                users = []
                
                for data in users_data:
                    app_metadata = data.get("app_metadata", {})
                    role_str = app_metadata.get("role", "viewer")
                    
                    try:
                        role = UserRole(role_str.lower())
                    except ValueError:
                        role = UserRole.VIEWER
                    
                    user = User(
                        user_id=data["user_id"],
                        email=data.get("email", ""),
                        name=data.get("name", ""),
                        role=role,
                        provider="auth0",
                        metadata=data,
                        created_at=datetime.fromisoformat(data.get("created_at", "").replace("Z", "+00:00")),
                    )
                    users.append(user)
                
                return users
            
            return []
            
        except Exception as e:
            logger.exception(f"List users error: {e}")
            return []
    
    def _get_management_token(self) -> Optional[str]:
        """
        Get Auth0 Management API token
        
        Returns:
            Management API access token
        """
        try:
            url = f"{self.base_url}/oauth/token"
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "audience": f"{self.base_url}/api/v2/",
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return response.json().get("access_token")
            
            logger.error(f"Failed to get management token: {response.text}")
            return None
            
        except Exception as e:
            logger.exception(f"Management token error: {e}")
            return None
    
    def supports_mfa(self) -> bool:
        """Auth0 supports MFA"""
        return True
