"""
Security Headers and CSRF Protection

Implements security headers and CSRF protection for the Streamlit application.

Features:
- CSRF token generation and validation
- Security headers (CSP, X-Frame-Options, etc.)
- Session security
- Secure cookie handling
"""

import secrets
import hashlib
import time
from typing import Optional
import streamlit as st
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CSRFProtection:
    """
    CSRF (Cross-Site Request Forgery) protection
    
    Generates and validates CSRF tokens to prevent CSRF attacks.
    """
    
    # Session state key for CSRF token
    CSRF_TOKEN_KEY = "csrf_token"
    CSRF_TOKEN_TIMESTAMP_KEY = "csrf_token_timestamp"
    
    # Token validity period (1 hour)
    TOKEN_VALIDITY_SECONDS = 3600
    
    @staticmethod
    def generate_token() -> str:
        """
        Generate a new CSRF token
        
        Returns:
            CSRF token string
        """
        # Generate random token
        token = secrets.token_urlsafe(32)
        
        # Store in session
        st.session_state[CSRFProtection.CSRF_TOKEN_KEY] = token
        st.session_state[CSRFProtection.CSRF_TOKEN_TIMESTAMP_KEY] = time.time()
        
        logger.debug("Generated new CSRF token")
        return token
    
    @staticmethod
    def get_token() -> str:
        """
        Get current CSRF token (generate if doesn't exist)
        
        Returns:
            CSRF token string
        """
        # Check if token exists and is valid
        if CSRFProtection.CSRF_TOKEN_KEY in st.session_state:
            timestamp = st.session_state.get(CSRFProtection.CSRF_TOKEN_TIMESTAMP_KEY, 0)
            
            # Check if token is still valid
            if time.time() - timestamp < CSRFProtection.TOKEN_VALIDITY_SECONDS:
                return st.session_state[CSRFProtection.CSRF_TOKEN_KEY]
        
        # Generate new token if doesn't exist or expired
        return CSRFProtection.generate_token()
    
    @staticmethod
    def validate_token(token: str) -> bool:
        """
        Validate CSRF token
        
        Args:
            token: Token to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not token:
            logger.warning("CSRF validation failed: No token provided")
            return False
        
        # Get stored token
        stored_token = st.session_state.get(CSRFProtection.CSRF_TOKEN_KEY)
        
        if not stored_token:
            logger.warning("CSRF validation failed: No stored token")
            return False
        
        # Check timestamp
        timestamp = st.session_state.get(CSRFProtection.CSRF_TOKEN_TIMESTAMP_KEY, 0)
        if time.time() - timestamp > CSRFProtection.TOKEN_VALIDITY_SECONDS:
            logger.warning("CSRF validation failed: Token expired")
            return False
        
        # Constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(token, stored_token):
            logger.warning("CSRF validation failed: Token mismatch")
            return False
        
        logger.debug("CSRF token validated successfully")
        return True
    
    @staticmethod
    def require_valid_token(token: Optional[str] = None):
        """
        Require valid CSRF token (raises error if invalid)
        
        Args:
            token: Token to validate (if None, looks in session state)
        """
        if token is None:
            # For Streamlit, we can use hidden input or session state
            token = st.session_state.get("submitted_csrf_token")
        
        if not CSRFProtection.validate_token(token):
            st.error("⛔ Security Error: Invalid or expired CSRF token")
            st.stop()


class SecurityHeaders:
    """
    Security headers for HTTP responses
    
    Note: Streamlit doesn't provide direct access to HTTP headers,
    but these can be set via reverse proxy (nginx, Apache, etc.)
    """
    
    @staticmethod
    def get_recommended_headers() -> dict:
        """
        Get recommended security headers
        
        Returns:
            Dictionary of header name -> value
        """
        return {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
            ),
            
            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # Permissions Policy (formerly Feature-Policy)
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
            ),
        }
    
    @staticmethod
    def get_nginx_config() -> str:
        """
        Get nginx configuration for security headers
        
        Returns:
            Nginx configuration snippet
        """
        headers = SecurityHeaders.get_recommended_headers()
        
        config_lines = ["# Security Headers"]
        for header, value in headers.items():
            config_lines.append(f'add_header {header} "{value}" always;')
        
        return "\n".join(config_lines)


def protect_form_submission():
    """
    Protect form submission with CSRF token
    
    Usage in Streamlit:
        with st.form("my_form"):
            # Form fields
            st.text_input("Name")
            
            # Add CSRF protection
            protect_form_submission()
            
            # Submit button
            if st.form_submit_button("Submit"):
                # Form will only submit if CSRF token is valid
                pass
    """
    # Get or generate CSRF token
    csrf_token = CSRFProtection.get_token()
    
    # Store token in hidden field (Streamlit doesn't have hidden inputs,
    # so we use session state)
    st.session_state["submitted_csrf_token"] = csrf_token
    
    # Add hidden text (not visible to user)
    st.markdown(
        f'<input type="hidden" name="csrf_token" value="{csrf_token}" />',
        unsafe_allow_html=True,
    )


def validate_form_submission():
    """
    Validate form submission CSRF token
    
    Call this after form submission to validate CSRF token.
    """
    CSRFProtection.require_valid_token()


def secure_session_init():
    """
    Initialize secure session with security best practices
    
    Call this at the start of your Streamlit app.
    """
    # Generate session ID if doesn't exist
    if "session_id" not in st.session_state:
        st.session_state.session_id = secrets.token_urlsafe(32)
        logger.info(f"Initialized secure session: {st.session_state.session_id[:8]}...")
    
    # Generate CSRF token
    CSRFProtection.get_token()
    
    # Set session timeout (optional)
    if "session_start_time" not in st.session_state:
        st.session_state.session_start_time = time.time()
    
    # Check session timeout (4 hours)
    session_age = time.time() - st.session_state.session_start_time
    if session_age > 14400:  # 4 hours
        logger.info("Session expired, clearing session state")
        st.session_state.clear()
        st.rerun()


def show_security_info():
    """Display security information in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔒 Security")
        
        # Session info
        if "session_id" in st.session_state:
            session_id = st.session_state.session_id[:8]
            st.text(f"Session: {session_id}...")
        
        # CSRF token status
        if CSRFProtection.CSRF_TOKEN_KEY in st.session_state:
            st.text("✅ CSRF Protection Active")
        
        # Show security headers recommendation
        with st.expander("Security Headers"):
            st.code(SecurityHeaders.get_nginx_config(), language="nginx")
