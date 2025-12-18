"""
CSRF Protection Middleware

Implements CSRF token generation and validation for Streamlit forms.
Protects against Cross-Site Request Forgery attacks.
"""

import secrets
import streamlit as st
from typing import Optional, Callable
from functools import wraps
import time

class CSRFProtection:
    """CSRF protection for Streamlit applications"""
    
    TOKEN_LENGTH = 32
    TOKEN_EXPIRY = 3600  # 1 hour in seconds
    
    @staticmethod
    def generate_token() -> str:
        """
        Generate a new CSRF token
        
        Returns:
            Secure random token
        """
        token = secrets.token_urlsafe(CSRFProtection.TOKEN_LENGTH)
        
        # Store token with timestamp in session
        st.session_state.csrf_token = token
        st.session_state.csrf_token_time = time.time()
        
        return token
    
    @staticmethod
    def get_token() -> Optional[str]:
        """
        Get current CSRF token, generate new one if expired or missing
        
        Returns:
            Current valid CSRF token
        """
        # Check if token exists and is not expired
        if 'csrf_token' in st.session_state and 'csrf_token_time' in st.session_state:
            token_age = time.time() - st.session_state.csrf_token_time
            
            if token_age < CSRFProtection.TOKEN_EXPIRY:
                return st.session_state.csrf_token
        
        # Generate new token if expired or missing
        return CSRFProtection.generate_token()
    
    @staticmethod
    def validate_token(submitted_token: str) -> bool:
        """
        Validate submitted CSRF token
        
        Args:
            submitted_token: Token submitted with form
            
        Returns:
            True if token is valid, False otherwise
        """
        if not submitted_token:
            return False
        
        stored_token = st.session_state.get('csrf_token')
        
        if not stored_token:
            return False
        
        # Check token age
        token_time = st.session_state.get('csrf_token_time', 0)
        token_age = time.time() - token_time
        
        if token_age >= CSRFProtection.TOKEN_EXPIRY:
            return False
        
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(submitted_token, stored_token)
    
    @staticmethod
    def protect_form(form_key: str):
        """
        Decorator to protect form submissions with CSRF tokens
        
        Args:
            form_key: Unique key for the form
            
        Usage:
            @CSRFProtection.protect_form('password_change')
            def render_password_form():
                with st.form("password_form"):
                    # ... form fields ...
                    submitted = st.form_submit_button("Submit")
                    if submitted:
                        # Form processing
                        pass
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get or generate CSRF token
                csrf_token = CSRFProtection.get_token()
                
                # Store token for this specific form
                form_token_key = f'{form_key}_csrf_token'
                st.session_state[form_token_key] = csrf_token
                
                # Execute the form rendering function
                result = func(*args, **kwargs)
                
                # Check if form was submitted
                form_submitted_key = f'{form_key}_submitted'
                if st.session_state.get(form_submitted_key):
                    # Validate CSRF token
                    submitted_token = st.session_state.get(form_token_key)
                    
                    if not CSRFProtection.validate_token(submitted_token):
                        st.error("⚠️ Security validation failed. Please try again.")
                        st.stop()
                    
                    # Clear submission flag
                    st.session_state[form_submitted_key] = False
                
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def add_token_to_form(form_key: str):
        """
        Add CSRF token as hidden field to form
        
        Args:
            form_key: Unique key for the form
            
        Usage:
            with st.form("my_form"):
                CSRFProtection.add_token_to_form('my_form')
                # ... other form fields ...
                submitted = st.form_submit_button("Submit")
        """
        csrf_token = CSRFProtection.get_token()
        
        # Store token for validation
        form_token_key = f'{form_key}_csrf_token'
        st.session_state[form_token_key] = csrf_token
        
        # Display token info (for debugging, remove in production)
        # st.caption(f"🔒 Form protected with CSRF token")


def require_csrf_token(form_key: str) -> bool:
    """
    Validate CSRF token for a form submission
    
    Args:
        form_key: Unique key for the form
        
    Returns:
        True if token is valid, False otherwise
        
    Usage:
        with st.form("my_form"):
            CSRFProtection.add_token_to_form('my_form')
            # ... form fields ...
            submitted = st.form_submit_button("Submit")
            
            if submitted:
                if not require_csrf_token('my_form'):
                    st.error("Security validation failed")
                    st.stop()
                # Process form...
    """
    form_token_key = f'{form_key}_csrf_token'
    submitted_token = st.session_state.get(form_token_key)
    
    return CSRFProtection.validate_token(submitted_token)


# Example usage in Streamlit app
def example_protected_form():
    """Example of how to use CSRF protection"""
    
    with st.form("example_form"):
        # Add CSRF protection
        CSRFProtection.add_token_to_form('example_form')
        
        # Form fields
        name = st.text_input("Name")
        email = st.text_input("Email")
        
        # Submit button
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            # Validate CSRF token
            if not require_csrf_token('example_form'):
                st.error("⚠️ Security validation failed. Please try again.")
                st.stop()
            
            # Process form
            st.success(f"Form submitted successfully for {name}")
