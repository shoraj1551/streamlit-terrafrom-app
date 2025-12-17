"""
Authentication Provider Base Class

This module defines the abstract base class for authentication providers.
Supports multiple providers (Auth0, AWS Cognito, etc.) with a unified interface.

Design Pattern: Strategy Pattern for scalability
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    DEPLOYER = "deployer"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Granular permissions for fine-grained access control"""
    # Deployment permissions
    DEPLOY_CREATE = "deploy:create"
    DEPLOY_VIEW = "deploy:view"
    DEPLOY_DELETE = "deploy:delete"
    DEPLOY_APPROVE = "deploy:approve"
    
    # Configuration permissions
    CONFIG_UPLOAD = "config:upload"
    CONFIG_VIEW = "config:view"
    
    # Cost permissions
    COST_VIEW = "cost:view"
    COST_ESTIMATE = "cost:estimate"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_AUDIT = "admin:audit"


# Role to permissions mapping (scalable RBAC)
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.VIEWER: [
        Permission.DEPLOY_VIEW,
        Permission.CONFIG_VIEW,
        Permission.COST_VIEW,
    ],
    UserRole.DEPLOYER: [
        Permission.DEPLOY_CREATE,
        Permission.DEPLOY_VIEW,
        Permission.DEPLOY_DELETE,
        Permission.CONFIG_UPLOAD,
        Permission.CONFIG_VIEW,
        Permission.COST_VIEW,
        Permission.COST_ESTIMATE,
    ],
    UserRole.ADMIN: [
        # Admins have all permissions
        *[p for p in Permission],
    ],
}


@dataclass
class User:
    """User model for authenticated users"""
    user_id: str
    email: str
    name: str
    role: UserRole
    provider: str  # e.g., "auth0", "cognito"
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    last_login: datetime = None
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        return permission in ROLE_PERMISSIONS.get(self.role, [])
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(p) for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions"""
        return all(self.has_permission(p) for p in permissions)


@dataclass
class AuthenticationResult:
    """Result of authentication attempt"""
    success: bool
    user: Optional[User] = None
    error: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None  # seconds


class AuthenticationProvider(ABC):
    """
    Abstract base class for authentication providers.
    
    This enables easy switching between Auth0, Cognito, or custom providers
    without changing application code (Open/Closed Principle).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize authentication provider
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.provider_name = self.__class__.__name__
    
    @abstractmethod
    def login(self, username: str, password: str) -> AuthenticationResult:
        """
        Authenticate user with username/password
        
        Args:
            username: User's username or email
            password: User's password
            
        Returns:
            AuthenticationResult with user info and tokens
        """
        pass
    
    @abstractmethod
    def login_with_oauth(self, provider: str, code: str) -> AuthenticationResult:
        """
        Authenticate user with OAuth code (for social login)
        
        Args:
            provider: OAuth provider (google, github, etc.)
            code: Authorization code from OAuth flow
            
        Returns:
            AuthenticationResult with user info and tokens
        """
        pass
    
    @abstractmethod
    def logout(self, user_id: str, access_token: str) -> bool:
        """
        Logout user and invalidate tokens
        
        Args:
            user_id: User's ID
            access_token: User's access token
            
        Returns:
            True if logout successful
        """
        pass
    
    @abstractmethod
    def validate_token(self, access_token: str) -> Optional[User]:
        """
        Validate access token and return user info
        
        Args:
            access_token: JWT or session token
            
        Returns:
            User object if token is valid, None otherwise
        """
        pass
    
    @abstractmethod
    def refresh_token(self, refresh_token: str) -> AuthenticationResult:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            AuthenticationResult with new tokens
        """
        pass
    
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            user_id: User's ID
            
        Returns:
            User object if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """
        Update user's role (admin only)
        
        Args:
            user_id: User's ID
            new_role: New role to assign
            
        Returns:
            True if update successful
        """
        pass
    
    @abstractmethod
    def list_users(self, limit: int = 50, offset: int = 0) -> List[User]:
        """
        List all users (admin only)
        
        Args:
            limit: Maximum number of users to return
            offset: Offset for pagination
            
        Returns:
            List of User objects
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return self.provider_name
    
    def supports_oauth(self) -> bool:
        """Check if provider supports OAuth"""
        return True  # Override in subclass if not supported
    
    def supports_mfa(self) -> bool:
        """Check if provider supports MFA"""
        return False  # Override in subclass if supported
