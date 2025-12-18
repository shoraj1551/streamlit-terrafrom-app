"""
Auth0 Integration Service

Implements OAuth2/OIDC authentication with Auth0.
Replaces the insecure custom authentication system.
"""

import os
import streamlit as st
from typing import Optional, Dict, Any
from authlib.integrations.requests_client import OAuth2Session
from authlib.common.security import generate_token
import requests
from datetime import datetime, timedelta
import jwt

class Auth0Service:
    """
    Auth0 authentication service
    
    Provides secure OAuth2/OIDC authentication using Auth0.
    """
    
    def __init__(self):
        """Initialize Auth0 service with configuration from environment"""
        self.domain = os.getenv("AUTH0_DOMAIN")
        self.client_id = os.getenv("AUTH0_CLIENT_ID")
        self.client_secret = os.getenv("AUTH0_CLIENT_SECRET")
        self.redirect_uri = os.getenv("AUTH0_REDIRECT_URI", "http://localhost:8501")
        self.audience = os.getenv("AUTH0_AUDIENCE", f"https://{self.domain}/api/v2/")
        
        # Validate configuration
        if not all([self.domain, self.client_id, self.client_secret]):
            raise ValueError(
                "Auth0 configuration missing. Please set AUTH0_DOMAIN, "
                "AUTH0_CLIENT_ID, and AUTH0_CLIENT_SECRET environment variables."
            )
        
        self.authorization_endpoint = f"https://{self.domain}/authorize"
        self.token_endpoint = f"https://{self.domain}/oauth/token"
        self.userinfo_endpoint = f"https://{self.domain}/userinfo"
        self.logout_endpoint = f"https://{self.domain}/v2/logout"
    
    def get_authorization_url(self) -> str:
        """
        Generate Auth0 authorization URL for login
        
        Returns:
            Authorization URL to redirect user to
        """
        # Generate state for CSRF protection
        state = generate_token(32)
        st.session_state.oauth_state = state
        
        # Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile email',
            'state': state,
            'audience': self.audience
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorization_endpoint}?{query_string}"
    
    def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for tokens
        
        Args:
            code: Authorization code from Auth0
            state: State parameter for CSRF validation
            
        Returns:
            User information dictionary
            
        Raises:
            ValueError: If state validation fails or token exchange fails
        """
        # Validate state (CSRF protection)
        stored_state = st.session_state.get('oauth_state')
        if not stored_state or state != stored_state:
            raise ValueError("Invalid state parameter - possible CSRF attack")
        
        # Exchange code for tokens
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(self.token_endpoint, data=token_data)
        
        if response.status_code != 200:
            raise ValueError(f"Token exchange failed: {response.text}")
        
        tokens = response.json()
        
        # Get user information
        headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        user_response = requests.get(self.userinfo_endpoint, headers=headers)
        
        if user_response.status_code != 200:
            raise ValueError(f"Failed to get user info: {user_response.text}")
        
        user_info = user_response.json()
        
        # Store tokens in session
        st.session_state.access_token = tokens['access_token']
        st.session_state.id_token = tokens.get('id_token')
        st.session_state.refresh_token = tokens.get('refresh_token')
        st.session_state.token_expires_at = datetime.now() + timedelta(seconds=tokens.get('expires_in', 3600))
        
        return user_info
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Auth0
        
        Args:
            access_token: Access token
            
        Returns:
            User information or None if token is invalid
        """
        headers = {'Authorization': f"Bearer {access_token}"}
        response = requests.get(self.userinfo_endpoint, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        
        return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New tokens or None if refresh fails
        """
        token_data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token
        }
        
        response = requests.post(self.token_endpoint, data=token_data)
        
        if response.status_code == 200:
            return response.json()
        
        return None
    
    def logout(self, return_to: str = None) -> str:
        """
        Generate logout URL
        
        Args:
            return_to: URL to redirect to after logout
            
        Returns:
            Logout URL
        """
        if return_to is None:
            return_to = self.redirect_uri
        
        params = {
            'client_id': self.client_id,
            'returnTo': return_to
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.logout_endpoint}?{query_string}"
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token
        
        Args:
            token: JWT token to validate
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            # Note: In production, you should verify the signature using Auth0's public keys
            # For now, we'll decode without verification (not recommended for production)
            payload = jwt.decode(
                token,
                options={"verify_signature": False}  # TODO: Implement proper signature verification
            )
            
            # Check expiration
            if 'exp' in payload:
                if datetime.fromtimestamp(payload['exp']) < datetime.now():
                    return None
            
            return payload
        except jwt.InvalidTokenError:
            return None


def check_authentication() -> Optional[Dict[str, Any]]:
    """
    Check if user is authenticated via Auth0
    
    Returns:
        User information if authenticated, None otherwise
    """
    # Initialize Auth0 service
    auth0 = Auth0Service()
    
    # Check if user is already authenticated
    if 'user' in st.session_state and 'access_token' in st.session_state:
        # Check if token is still valid
        token_expires_at = st.session_state.get('token_expires_at')
        
        if token_expires_at and datetime.now() < token_expires_at:
            return st.session_state.user
        
        # Try to refresh token
        refresh_token = st.session_state.get('refresh_token')
        if refresh_token:
            new_tokens = auth0.refresh_access_token(refresh_token)
            if new_tokens:
                st.session_state.access_token = new_tokens['access_token']
                st.session_state.token_expires_at = datetime.now() + timedelta(seconds=new_tokens.get('expires_in', 3600))
                return st.session_state.user
    
    # Check for OAuth callback
    query_params = st.query_params
    
    if 'code' in query_params and 'state' in query_params:
        try:
            code = query_params['code']
            state = query_params['state']
            
            # Handle callback
            user_info = auth0.handle_callback(code, state)
            
            # Store user in session
            st.session_state.user = {
                'email': user_info.get('email'),
                'full_name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'sub': user_info.get('sub'),
                'email_verified': user_info.get('email_verified', False)
            }
            
            # Clear query parameters
            st.query_params.clear()
            
            return st.session_state.user
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            return None
    
    # User not authenticated - show login
    return None


def render_login_page():
    """Render Auth0 login page"""
    auth0 = Auth0Service()
    
    st.markdown("## 🔐 Welcome to Infrastructure Platform")
    st.markdown("### Secure Authentication with Auth0")
    
    st.info("This application uses Auth0 for secure, enterprise-grade authentication.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔑 Login with Auth0", use_container_width=True, type="primary"):
            # Generate authorization URL
            auth_url = auth0.get_authorization_url()
            
            # Redirect to Auth0
            st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
            st.info("Redirecting to Auth0...")
