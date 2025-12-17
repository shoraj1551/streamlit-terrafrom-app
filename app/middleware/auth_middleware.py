"""
Authentication Middleware for Streamlit

Provides middleware functions for authentication checks and access control.
"""

import streamlit as st
from functools import wraps
from typing import Optional, Callable, List
from app.auth.auth_provider import Permission, UserRole, User
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def check_authentication() -> bool:
    """
    Check if user is authenticated
    
    Returns:
        True if authenticated, False otherwise
    """
    session_manager = st.session_state.get("session_manager")
    if not session_manager:
        return False
    return session_manager.is_authenticated()


def get_current_user() -> Optional[User]:
    """
    Get current authenticated user
    
    Returns:
        User object if authenticated, None otherwise
    """
    session_manager = st.session_state.get("session_manager")
    if not session_manager:
        return None
    return session_manager.get_current_user()


def require_authentication() -> Optional[User]:
    """
    Require authentication - show login UI if not authenticated
    
    Returns:
        User object if authenticated, None if not authenticated
    """
    session_manager = st.session_state.get("session_manager")
    if not session_manager:
        st.error("⚠️ Authentication system not initialized")
        st.stop()
        return None
    
    return session_manager.require_authentication()


def require_permission(permission: Permission, show_error: bool = True) -> bool:
    """
    Check if current user has required permission
    
    Args:
        permission: Required permission
        show_error: Whether to show error message if permission denied
        
    Returns:
        True if user has permission, False otherwise
    """
    user = get_current_user()
    
    if not user:
        if show_error:
            st.error("⛔ Authentication required")
        return False
    
    has_perm = user.has_permission(permission)
    
    if not has_perm and show_error:
        st.error(f"⛔ Access Denied")
        st.warning(f"Required permission: **{permission.value}**")
        st.info(f"Your role: **{user.role.value}**")
        
        # Show what permissions the user has
        with st.expander("Your Permissions"):
            from app.auth.auth_provider import ROLE_PERMISSIONS
            user_perms = ROLE_PERMISSIONS.get(user.role, [])
            for perm in user_perms:
                st.write(f"✅ {perm.value}")
    
    return has_perm


def require_role(*roles: UserRole, show_error: bool = True) -> bool:
    """
    Check if current user has one of the required roles
    
    Args:
        *roles: Required roles
        show_error: Whether to show error message if role check fails
        
    Returns:
        True if user has one of the roles, False otherwise
    """
    user = get_current_user()
    
    if not user:
        if show_error:
            st.error("⛔ Authentication required")
        return False
    
    has_role = user.role in roles
    
    if not has_role and show_error:
        st.error(f"⛔ Access Denied")
        st.warning(f"Required role: **{' or '.join(r.value for r in roles)}**")
        st.info(f"Your role: **{user.role.value}**")
    
    return has_role


def show_user_info():
    """Display current user information in sidebar"""
    user = get_current_user()
    
    if user:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 User Info")
            st.write(f"**Name:** {user.name}")
            st.write(f"**Email:** {user.email}")
            st.write(f"**Role:** {user.role.value.upper()}")
            
            # Logout button
            if st.button("🚪 Logout", key="logout_button"):
                session_manager = st.session_state.get("session_manager")
                if session_manager:
                    session_manager.logout()
                    st.rerun()


def permission_gate(permission: Permission):
    """
    Decorator to require permission for a function
    
    Usage:
        @permission_gate(Permission.DEPLOY_CREATE)
        def create_deployment():
            st.write("Creating deployment...")
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not require_permission(permission):
                st.stop()
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def role_gate(*roles: UserRole):
    """
    Decorator to require role for a function
    
    Usage:
        @role_gate(UserRole.ADMIN, UserRole.DEPLOYER)
        def admin_page():
            st.write("Admin page")
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not require_role(*roles):
                st.stop()
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def audit_log_action(action: str, resource: Optional[str] = None, details: Optional[dict] = None):
    """
    Log user action for audit trail
    
    Args:
        action: Action performed (e.g., "deploy_create", "config_upload")
        resource: Resource affected (e.g., deployment_id, config_name)
        details: Additional details to log
    """
    user = get_current_user()
    
    if not user:
        logger.warning(f"Audit log: Unauthenticated action attempted: {action}")
        return
    
    log_entry = {
        "user_id": user.user_id,
        "user_email": user.email,
        "user_role": user.role.value,
        "action": action,
        "resource": resource,
        "details": details or {},
    }
    
    logger.info(f"Audit: {action}", extra=log_entry)
    
    # TODO: Store in audit database (Phase 1.4)


def rate_limit_check(action: str, max_per_minute: int = 10) -> bool:
    """
    Check if user has exceeded rate limit
    
    Args:
        action: Action to rate limit
        max_per_minute: Maximum actions per minute
        
    Returns:
        True if within rate limit, False if exceeded
    """
    # TODO: Implement actual rate limiting (Phase 1.3)
    # For now, always return True
    return True


def deployment_approval_required() -> bool:
    """
    Check if deployment requires approval
    
    Returns:
        True if approval required, False otherwise
    """
    user = get_current_user()
    
    if not user:
        return True  # Require approval if not authenticated
    
    # Admins don't need approval
    if user.role == UserRole.ADMIN:
        return False
    
    # TODO: Check deployment approval settings (Phase 1.3)
    # For now, require approval for all non-admin users
    return True
