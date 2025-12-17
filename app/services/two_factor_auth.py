"""
Two-Factor Authentication System

TOTP-based 2FA for sensitive operations like infrastructure destruction.
"""

import pyotp
import qrcode
from io import BytesIO
from typing import Optional, Tuple
from pathlib import Path
import json
from datetime import datetime


class TwoFactorAuth:
    """Two-factor authentication using TOTP"""
    
    def __init__(self):
        self.secrets_file = Path("data/2fa_secrets.json")
        self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.secrets_file.exists():
            self._save_secrets({})
    
    def setup_2fa(self, user_email: str) -> Tuple[str, BytesIO]:
        """
        Setup 2FA for user
        
        Args:
            user_email: User's email
            
        Returns:
            (secret, qr_code_image)
        """
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create TOTP
        totp = pyotp.TOTP(secret)
        
        # Generate provisioning URI
        uri = totp.provisioning_uri(
            name=user_email,
            issuer_name="Cloud Infrastructure Deployer"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Save secret
        secrets = self._load_secrets()
        secrets[user_email] = {
            'secret': secret,
            'enabled': False,
            'setup_at': datetime.utcnow().isoformat(),
            'backup_codes': self._generate_backup_codes()
        }
        self._save_secrets(secrets)
        
        return secret, img_buffer
    
    def enable_2fa(self, user_email: str, verification_code: str) -> Tuple[bool, str]:
        """
        Enable 2FA after verifying initial code
        
        Args:
            user_email: User's email
            verification_code: 6-digit code from authenticator app
            
        Returns:
            (success, message)
        """
        secrets = self._load_secrets()
        
        if user_email not in secrets:
            return False, "2FA not set up for this user"
        
        user_data = secrets[user_email]
        
        # Verify code
        if self.verify_code(user_email, verification_code):
            user_data['enabled'] = True
            user_data['enabled_at'] = datetime.utcnow().isoformat()
            secrets[user_email] = user_data
            self._save_secrets(secrets)
            
            return True, "2FA enabled successfully"
        else:
            return False, "Invalid verification code"
    
    def verify_code(self, user_email: str, code: str) -> bool:
        """
        Verify TOTP code
        
        Args:
            user_email: User's email
            code: 6-digit code
            
        Returns:
            True if valid
        """
        secrets = self._load_secrets()
        
        if user_email not in secrets:
            return False
        
        user_data = secrets[user_email]
        secret = user_data['secret']
        
        # Check TOTP code
        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):  # Allow 30s window
            return True
        
        # Check backup codes
        if code in user_data.get('backup_codes', []):
            # Remove used backup code
            user_data['backup_codes'].remove(code)
            secrets[user_email] = user_data
            self._save_secrets(secrets)
            return True
        
        return False
    
    def is_2fa_enabled(self, user_email: str) -> bool:
        """Check if 2FA is enabled for user"""
        secrets = self._load_secrets()
        
        if user_email not in secrets:
            return False
        
        return secrets[user_email].get('enabled', False)
    
    def disable_2fa(self, user_email: str, verification_code: str) -> Tuple[bool, str]:
        """
        Disable 2FA
        
        Args:
            user_email: User's email
            verification_code: 6-digit code for verification
            
        Returns:
            (success, message)
        """
        if not self.verify_code(user_email, verification_code):
            return False, "Invalid verification code"
        
        secrets = self._load_secrets()
        
        if user_email in secrets:
            del secrets[user_email]
            self._save_secrets(secrets)
        
        return True, "2FA disabled successfully"
    
    def get_backup_codes(self, user_email: str) -> Optional[list]:
        """Get backup codes for user"""
        secrets = self._load_secrets()
        
        if user_email not in secrets:
            return None
        
        return secrets[user_email].get('backup_codes', [])
    
    def regenerate_backup_codes(self, user_email: str) -> list:
        """Regenerate backup codes"""
        secrets = self._load_secrets()
        
        if user_email not in secrets:
            return []
        
        new_codes = self._generate_backup_codes()
        secrets[user_email]['backup_codes'] = new_codes
        self._save_secrets(secrets)
        
        return new_codes
    
    def _generate_backup_codes(self, count: int = 10) -> list:
        """Generate backup codes"""
        import random
        import string
        
        codes = []
        for _ in range(count):
            code = ''.join(random.choices(string.digits, k=8))
            codes.append(f"{code[:4]}-{code[4:]}")
        
        return codes
    
    def _load_secrets(self) -> dict:
        """Load secrets from file"""
        try:
            with open(self.secrets_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_secrets(self, secrets: dict):
        """Save secrets to file"""
        with open(self.secrets_file, 'w') as f:
            json.dump(secrets, f, indent=2)


def render_2fa_setup(user_email: str):
    """Render 2FA setup UI"""
    import streamlit as st
    
    st.markdown("### 🔐 Two-Factor Authentication Setup")
    
    if '2fa_system' not in st.session_state:
        st.session_state['2fa_system'] = TwoFactorAuth()
    
    tfa = st.session_state['2fa_system']
    
    # Check if already enabled
    if tfa.is_2fa_enabled(user_email):
        st.success("✅ 2FA is enabled for your account")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("View Backup Codes"):
                codes = tfa.get_backup_codes(user_email)
                if codes:
                    st.markdown("**Backup Codes** (save these securely):")
                    for code in codes:
                        st.code(code)
        
        with col2:
            if st.button("Disable 2FA"):
                st.session_state['disable_2fa_mode'] = True
        
        if st.session_state.get('disable_2fa_mode'):
            code = st.text_input("Enter 2FA code to disable", max_chars=6)
            if st.button("Confirm Disable"):
                success, message = tfa.disable_2fa(user_email, code)
                if success:
                    st.success(message)
                    st.session_state['disable_2fa_mode'] = False
                    st.rerun()
                else:
                    st.error(message)
        
        return True
    
    # Setup flow
    st.info("Enable 2FA to secure sensitive operations like infrastructure destruction")
    
    if st.button("Setup 2FA", type="primary"):
        st.session_state['2fa_setup_started'] = True
    
    if st.session_state.get('2fa_setup_started'):
        # Generate QR code
        secret, qr_image = tfa.setup_2fa(user_email)
        
        st.markdown("#### Step 1: Scan QR Code")
        st.markdown("Use an authenticator app (Google Authenticator, Authy, etc.) to scan this QR code:")
        
        st.image(qr_image, width=300)
        
        st.markdown("#### Step 2: Enter Verification Code")
        st.markdown("Enter the 6-digit code from your authenticator app:")
        
        verification_code = st.text_input("Verification Code", max_chars=6, key="2fa_verify")
        
        if st.button("Verify and Enable"):
            if len(verification_code) == 6:
                success, message = tfa.enable_2fa(user_email, verification_code)
                
                if success:
                    st.success(message)
                    
                    # Show backup codes
                    backup_codes = tfa.get_backup_codes(user_email)
                    st.markdown("#### ⚠️ Important: Save Your Backup Codes")
                    st.warning("Store these codes securely. You can use them if you lose access to your authenticator app.")
                    
                    for code in backup_codes:
                        st.code(code)
                    
                    st.session_state['2fa_setup_started'] = False
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please enter a 6-digit code")
    
    return False


def verify_2fa_for_action(user_email: str, action_name: str) -> bool:
    """
    Verify 2FA before performing sensitive action
    
    Args:
        user_email: User's email
        action_name: Name of action (for display)
        
    Returns:
        True if verified or not required
    """
    import streamlit as st
    
    if '2fa_system' not in st.session_state:
        st.session_state['2fa_system'] = TwoFactorAuth()
    
    tfa = st.session_state['2fa_system']
    
    # Check if 2FA is enabled
    if not tfa.is_2fa_enabled(user_email):
        st.warning("⚠️ 2FA is not enabled. Please enable 2FA for enhanced security.")
        return True  # Allow action if 2FA not set up
    
    # Request 2FA code
    st.markdown(f"### 🔐 2FA Verification Required")
    st.info(f"Please enter your 2FA code to proceed with: **{action_name}**")
    
    code = st.text_input("Enter 6-digit code", max_chars=6, key=f"2fa_{action_name}")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("Verify", type="primary"):
            if tfa.verify_code(user_email, code):
                st.success("✅ Verified!")
                return True
            else:
                st.error("❌ Invalid code")
                return False
    
    with col2:
        if st.button("Cancel"):
            return False
    
    return False
