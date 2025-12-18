"""
RBAC (Role-Based Access Control) Implementation

Provides role and permission management for the application.
"""

from enum import Enum
from typing import List, Set, Optional, Dict, Any
from dataclasses import dataclass
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class Role(str, Enum):
    """User roles"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    OPERATOR = "operator"


class Permission(str, Enum):
    """System permissions"""
    # Deployment permissions
    DEPLOY_CREATE = "deploy:create"
    DEPLOY_READ = "deploy:read"
    DEPLOY_UPDATE = "deploy:update"
    DEPLOY_DELETE = "deploy:delete"
    DEPLOY_CANCEL = "deploy:cancel"
    
    # Configuration permissions
    CONFIG_READ = "config:read"
    CONFIG_UPDATE = "config:update"
    
    # User management permissions
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Audit permissions
    AUDIT_READ = "audit:read"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    METRICS_READ = "metrics:read"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # All permissions
        Permission.DEPLOY_CREATE,
        Permission.DEPLOY_READ,
        Permission.DEPLOY_UPDATE,
        Permission.DEPLOY_DELETE,
        Permission.DEPLOY_CANCEL,
        Permission.CONFIG_READ,
        Permission.CONFIG_UPDATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.AUDIT_READ,
        Permission.SYSTEM_ADMIN,
        Permission.METRICS_READ,
    },
    Role.OPERATOR: {
        # Deployment and monitoring
        Permission.DEPLOY_CREATE,
        Permission.DEPLOY_READ,
        Permission.DEPLOY_UPDATE,
        Permission.DEPLOY_CANCEL,
        Permission.CONFIG_READ,
        Permission.AUDIT_READ,
        Permission.METRICS_READ,
    },
    Role.USER: {
        # Basic deployment operations
        Permission.DEPLOY_CREATE,
        Permission.DEPLOY_READ,
        Permission.DEPLOY_CANCEL,
        Permission.CONFIG_READ,
    },
    Role.VIEWER: {
        # Read-only access
        Permission.DEPLOY_READ,
        Permission.CONFIG_READ,
        Permission.METRICS_READ,
    }
}


@dataclass
class UserRole:
    """User role assignment"""
    user_email: str
    role: Role
    granted_by: str
    granted_at: str
    expires_at: Optional[str] = None


class RBACManager:
    """
    Role-Based Access Control Manager
    
    Manages user roles and permission checks.
    """
    
    def __init__(self):
        """Initialize RBAC manager"""
        # In-memory role storage (should be replaced with database)
        self._user_roles: Dict[str, Role] = {}
        logger.info("✅ RBAC Manager initialized")
    
    def assign_role(
        self,
        user_email: str,
        role: Role,
        granted_by: str
    ) -> bool:
        """
        Assign role to user
        
        Args:
            user_email: User email
            role: Role to assign
            granted_by: Admin who granted the role
            
        Returns:
            True if successful
        """
        self._user_roles[user_email] = role
        logger.info(f"Assigned role {role.value} to {user_email} by {granted_by}")
        return True
    
    def get_user_role(self, user_email: str) -> Role:
        """
        Get user's role
        
        Args:
            user_email: User email
            
        Returns:
            User's role (defaults to USER)
        """
        return self._user_roles.get(user_email, Role.USER)
    
    def get_user_permissions(self, user_email: str) -> Set[Permission]:
        """
        Get all permissions for user
        
        Args:
            user_email: User email
            
        Returns:
            Set of permissions
        """
        role = self.get_user_role(user_email)
        return ROLE_PERMISSIONS.get(role, set())
    
    def has_permission(
        self,
        user_email: str,
        permission: Permission
    ) -> bool:
        """
        Check if user has specific permission
        
        Args:
            user_email: User email
            permission: Permission to check
            
        Returns:
            True if user has permission
        """
        user_permissions = self.get_user_permissions(user_email)
        has_perm = permission in user_permissions
        
        if not has_perm:
            logger.warning(
                f"Permission denied: {user_email} -> {permission.value}"
            )
        
        return has_perm
    
    def has_any_permission(
        self,
        user_email: str,
        permissions: List[Permission]
    ) -> bool:
        """
        Check if user has any of the specified permissions
        
        Args:
            user_email: User email
            permissions: List of permissions
            
        Returns:
            True if user has at least one permission
        """
        user_permissions = self.get_user_permissions(user_email)
        return any(perm in user_permissions for perm in permissions)
    
    def has_all_permissions(
        self,
        user_email: str,
        permissions: List[Permission]
    ) -> bool:
        """
        Check if user has all specified permissions
        
        Args:
            user_email: User email
            permissions: List of permissions
            
        Returns:
            True if user has all permissions
        """
        user_permissions = self.get_user_permissions(user_email)
        return all(perm in user_permissions for perm in permissions)
    
    def is_admin(self, user_email: str) -> bool:
        """Check if user is admin"""
        return self.get_user_role(user_email) == Role.ADMIN
    
    def revoke_role(self, user_email: str) -> bool:
        """
        Revoke user's role (reset to default USER)
        
        Args:
            user_email: User email
            
        Returns:
            True if successful
        """
        if user_email in self._user_roles:
            del self._user_roles[user_email]
            logger.info(f"Revoked role for {user_email}")
            return True
        return False


# Global RBAC manager instance
_rbac_manager = None


def get_rbac_manager() -> RBACManager:
    """Get global RBAC manager instance"""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


def require_permission(permission: Permission):
    """
    Decorator to require specific permission
    
    Usage:
        @require_permission(Permission.DEPLOY_CREATE)
        def create_deployment(user_email: str):
            pass
    """
    def decorator(func):
        def wrapper(user_email: str, *args, **kwargs):
            rbac = get_rbac_manager()
            if not rbac.has_permission(user_email, permission):
                raise PermissionError(
                    f"User {user_email} does not have permission: {permission.value}"
                )
            return func(user_email, *args, **kwargs)
        return wrapper
    return decorator
