"""
Session Management for Streamlit

Manages user sessions, token storage, and authentication state in Streamlit.
Provides a clean interface for authentication in Streamlit apps.
"""

import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.auth.auth_provider import AuthenticationProvider, User, Permission
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SessionManager:
    """
    Manages user sessions in Streamlit
    
    Stores authentication state in Streamlit session state for persistence
    across reruns.
    """
    
    # Session state keys
    KEY_USER = "auth_user"
    KEY_ACCESS_TOKEN = "auth_access_token"
    KEY_REFRESH_TOKEN = "auth_refresh_token"
    KEY_TOKEN_EXPIRES = "auth_token_expires"
    KEY_PROVIDER = "auth_provider"
    
    def __init__(self, auth_provider: AuthenticationProvider):
        """
        Initialize session manager
        
        Args:
            auth_provider: Authentication provider instance
        """
        self.auth_provider = auth_provider
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session state if not already initialized"""
        if self.KEY_USER not in st.session_state:
            st.session_state[self.KEY_USER] = None
        if self.KEY_ACCESS_TOKEN not in st.session_state:
            st.session_state[self.KEY_ACCESS_TOKEN] = None
        if self.KEY_REFRESH_TOKEN not in st.session_state:
            st.session_state[self.KEY_REFRESH_TOKEN] = None
        if self.KEY_TOKEN_EXPIRES not in st.session_state:
            st.session_state[self.KEY_TOKEN_EXPIRES] = None
        if self.KEY_PROVIDER not in st.session_state:
            st.session_state[self.KEY_PROVIDER] = self.auth_provider.get_provider_name()
    
    def login(self, username: str, password: str) -> bool:
        """
        Login user with username/password
        
        Args:
            username: User's username or email
            password: User's password
            
        Returns:
            True if login successful, False otherwise
        """
        result = self.auth_provider.login(username, password)
        
        if result.success and result.user:
            self._store_session(result.user, result.access_token, result.refresh_token, result.expires_in)
            logger.info(f"User logged in: {result.user.email}")
            return True
        else:
            logger.warning(f"Login failed: {result.error}")
            return False
    
    def logout(self) -> bool:
        """
        Logout current user
        
        Returns:
            True if logout successful
        """
        user = self.get_current_user()
        access_token = st.session_state.get(self.KEY_ACCESS_TOKEN)
        
        if user and access_token:
            self.auth_provider.logout(user.user_id, access_token)
        
        self._clear_session()
        logger.info("User logged out")
        return True
    
    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated
        
        Returns:
            True if user is authenticated with valid token
        """
        user = st.session_state.get(self.KEY_USER)
        token_expires = st.session_state.get(self.KEY_TOKEN_EXPIRES)
        
        if not user or not token_expires:
            return False
        
        # Check if token is expired
        if datetime.now() > token_expires:
            # Try to refresh token
            if self._refresh_token():
                return True
            else:
                self._clear_session()
                return False
        
        return True
    
    def get_current_user(self) -> Optional[User]:
        """
        Get currently authenticated user
        
        Returns:
            User object if authenticated, None otherwise
        """
        if self.is_authenticated():
            return st.session_state.get(self.KEY_USER)
        return None
    
    def get_access_token(self) -> Optional[str]:
        """
        Get current access token
        
        Returns:
            Access token if authenticated, None otherwise
        """
        if self.is_authenticated():
            return st.session_state.get(self.KEY_ACCESS_TOKEN)
        return None
    
    def require_authentication(self) -> Optional[User]:
        """
        Require authentication - redirect to login if not authenticated
        
        Returns:
            User object if authenticated, None if not (will show login UI)
        """
        if not self.is_authenticated():
            self._show_login_ui()
            return None
        return self.get_current_user()
    
    def require_permission(self, permission: Permission) -> bool:
        """
        Check if current user has required permission
        
        Args:
            permission: Required permission
            
        Returns:
            True if user has permission, False otherwise
        """
        user = self.get_current_user()
        if not user:
            return False
        return user.has_permission(permission)
    
    def require_role(self, *roles) -> bool:
        """
        Check if current user has one of the required roles
        
        Args:
            *roles: Required roles (UserRole enum values)
            
        Returns:
            True if user has one of the roles, False otherwise
        """
        user = self.get_current_user()
        if not user:
            return False
        return user.role in roles
    
    def _store_session(self, user: User, access_token: str, refresh_token: str, expires_in: int):
        """Store session data in Streamlit session state"""
        st.session_state[self.KEY_USER] = user
        st.session_state[self.KEY_ACCESS_TOKEN] = access_token
        st.session_state[self.KEY_REFRESH_TOKEN] = refresh_token
        st.session_state[self.KEY_TOKEN_EXPIRES] = datetime.now() + timedelta(seconds=expires_in)
    
    def _clear_session(self):
        """Clear session data"""
        st.session_state[self.KEY_USER] = None
        st.session_state[self.KEY_ACCESS_TOKEN] = None
        st.session_state[self.KEY_REFRESH_TOKEN] = None
        st.session_state[self.KEY_TOKEN_EXPIRES] = None
    
    def _refresh_token(self) -> bool:
        """
        Refresh access token using refresh token
        
        Returns:
            True if refresh successful, False otherwise
        """
        refresh_token = st.session_state.get(self.KEY_REFRESH_TOKEN)
        
        if not refresh_token:
            return False
        
        result = self.auth_provider.refresh_token(refresh_token)
        
        if result.success and result.user:
            self._store_session(result.user, result.access_token, result.refresh_token, result.expires_in)
            logger.info("Token refreshed successfully")
            return True
        else:
            logger.warning("Token refresh failed")
            return False
    
    def _show_login_ui(self):
        """Show login UI in Streamlit"""
        st.title("🔐 Login Required")
        
        with st.form("login_form"):
            username = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if self.login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Login failed. Please check your credentials.")


def require_auth(permission: Optional[Permission] = None):
    """
    Decorator to require authentication for Streamlit pages/functions
    
    Args:
        permission: Optional permission required
        
    Usage:
        @require_auth(Permission.DEPLOY_CREATE)
        def deployment_page():
            st.write("Deployment page")
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get session manager from session state
            session_manager = st.session_state.get("session_manager")
            
            if not session_manager:
                st.error("Session manager not initialized")
                return
            
            user = session_manager.require_authentication()
            
            if not user:
                return  # Login UI will be shown
            
            # Check permission if specified
            if permission and not user.has_permission(permission):
                st.error(f"⛔ Access Denied: You don't have permission to access this page.")
                st.info(f"Required permission: {permission.value}")
                st.info(f"Your role: {user.role.value}")
                return
            
            # Call the original function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
