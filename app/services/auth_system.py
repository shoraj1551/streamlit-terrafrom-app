"""
User Authentication System

Handles user login, signup, session management, and password security.
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import streamlit as st
from pathlib import Path
import json


class AuthenticationSystem:
    """User authentication and session management"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        
        # BUG-001 FIX: Ensure data directory exists
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.users_file = self.data_dir / "users.json"
        
        # Initialize users file if not exists
        if not self.users_file.exists():
            self._save_users({})
    
    def _hash_password(self, password: str, salt: str = None) -> tuple:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return pwd_hash.hex(), salt
    
    def _load_users(self) -> Dict[str, Any]:
        """Load users from file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_users(self, users: Dict[str, Any]):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def signup(self, email: str, password: str, full_name: str) -> tuple[bool, str]:
        """
        Create new user account
        
        Args:
            email: User email
            password: User password
            full_name: User's full name
            
        Returns:
            (success, message)
        """
        users = self._load_users()
        
        # Check if user already exists
        if email in users:
            return False, "Email already registered"
        
        # Validate password strength
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        # Hash password
        pwd_hash, salt = self._hash_password(password)
        
        # Create user
        users[email] = {
            'email': email,
            'full_name': full_name,
            'password_hash': pwd_hash,
            'salt': salt,
            'created_at': datetime.utcnow().isoformat(),
            'survey_completed': False,
            'two_factor_enabled': False,
            'two_factor_secret': None
        }
        
        self._save_users(users)
        return True, "Account created successfully"
    
    def login(self, email: str, password: str) -> tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user
        
        Args:
            email: User email
            password: User password
            
        Returns:
            (success, message, user_data)
        """
        users = self._load_users()
        
        if email not in users:
            return False, "Invalid email or password", None
        
        user = users[email]
        
        # Hash provided password with stored salt
        pwd_hash, _ = self._hash_password(password, user['salt'])
        
        # Compare hashes
        if pwd_hash != user['password_hash']:
            return False, "Invalid email or password", None
        
        # Generate session token
        token = self._generate_token(email)
        
        # Update last login
        user['last_login'] = datetime.utcnow().isoformat()
        users[email] = user
        self._save_users(users)
        
        return True, "Login successful", {
            'email': email,
            'full_name': user['full_name'],
            'token': token,
            'survey_completed': user['survey_completed']
        }
    
    def _generate_token(self, email: str) -> str:
        """Generate JWT session token"""
        payload = {
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=7),  # 7 day expiry
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify JWT token
        
        Returns:
            Email if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['email']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user(self, email: str) -> Optional[Dict]:
        """Get user data"""
        users = self._load_users()
        user = users.get(email)
        
        if user:
            # Remove sensitive data
            return {
                'email': user['email'],
                'full_name': user['full_name'],
                'created_at': user['created_at'],
                'survey_completed': user['survey_completed'],
                'two_factor_enabled': user['two_factor_enabled']
            }
        
        return None
    
    def update_user(self, email: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        users = self._load_users()
        
        if email not in users:
            return False
        
        # Update allowed fields
        allowed_fields = ['full_name', 'survey_completed', 'two_factor_enabled', 'two_factor_secret']
        for field in allowed_fields:
            if field in updates:
                users[email][field] = updates[field]
        
        self._save_users(users)
        return True
    
    def change_password(self, email: str, old_password: str, new_password: str) -> tuple[bool, str]:
        """Change user password"""
        users = self._load_users()
        
        if email not in users:
            return False, "User not found"
        
        user = users[email]
        
        # Verify old password
        pwd_hash, _ = self._hash_password(old_password, user['salt'])
        if pwd_hash != user['password_hash']:
            return False, "Current password is incorrect"
        
        # Validate new password
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters"
        
        # Hash new password
        new_hash, new_salt = self._hash_password(new_password)
        
        # Update password
        users[email]['password_hash'] = new_hash
        users[email]['salt'] = new_salt
        
        self._save_users(users)
        return True, "Password changed successfully"


def render_login_page():
    """Render login/signup page"""
    st.markdown("## 🔐 Welcome to Cloud Infrastructure Deployer")
    
    # Initialize auth system
    if 'auth' not in st.session_state:
        st.session_state.auth = AuthenticationSystem()
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.markdown("### Login to Your Account")
        
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", use_container_width=True):
            if email and password:
                success, message, user_data = st.session_state.auth.login(email, password)
                
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user = user_data
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter email and password")
    
    with tab2:
        st.markdown("### Create New Account")
        
        full_name = st.text_input("Full Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
        
        if st.button("Sign Up", use_container_width=True):
            if full_name and email and password and confirm_password:
                if password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = st.session_state.auth.signup(email, password, full_name)
                    
                    if success:
                        st.success(message)
                        st.info("Please login with your credentials")
                    else:
                        st.error(message)
            else:
                st.warning("Please fill in all fields")


def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        render_login_page()
        st.stop()
    
    return st.session_state.user
