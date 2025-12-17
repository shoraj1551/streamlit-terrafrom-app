"""
Encryption Utilities

Provides encryption/decryption utilities for sensitive data at rest.
Uses industry-standard algorithms (AES-256-GCM) with proper key management.

Features:
- AES-256-GCM encryption
- Secure key derivation (PBKDF2)
- Automatic IV generation
- Base64 encoding for storage
- Fernet encryption (simpler alternative)
"""

import os
import base64
import hashlib
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class EncryptionService:
    """
    Encryption service for sensitive data
    
    Provides AES-256-GCM encryption with proper key management.
    Suitable for encrypting database fields, configuration files, etc.
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption service
        
        Args:
            master_key: Master encryption key (if None, reads from environment)
        """
        if master_key is None:
            master_key = os.getenv("ENCRYPTION_MASTER_KEY")
            
        if not master_key:
            raise ValueError("ENCRYPTION_MASTER_KEY must be set")
        
        # Derive a 32-byte key from master key using PBKDF2
        self.key = self._derive_key(master_key)
        
        logger.info("Initialized EncryptionService")
    
    def _derive_key(self, master_key: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive encryption key from master key using PBKDF2
        
        Args:
            master_key: Master key string
            salt: Optional salt (if None, uses fixed salt - not ideal for production)
            
        Returns:
            32-byte derived key
        """
        if salt is None:
            # In production, use a unique salt per secret and store it
            # For simplicity, using a fixed salt here
            salt = b"terraform-app-salt-v1"
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        
        return kdf.derive(master_key.encode())
    
    def encrypt(self, plaintext: Union[str, bytes]) -> str:
        """
        Encrypt plaintext using AES-256-GCM
        
        Args:
            plaintext: Data to encrypt (string or bytes)
            
        Returns:
            Base64-encoded ciphertext with IV prepended
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()
        
        # Generate random IV (12 bytes for GCM)
        iv = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(iv),
            backend=default_backend(),
        )
        
        encryptor = cipher.encryptor()
        
        # Encrypt
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        # Get authentication tag
        tag = encryptor.tag
        
        # Combine IV + tag + ciphertext and encode as base64
        encrypted_data = iv + tag + ciphertext
        
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext using AES-256-GCM
        
        Args:
            ciphertext: Base64-encoded encrypted data
            
        Returns:
            Decrypted plaintext as string
        """
        # Decode from base64
        encrypted_data = base64.b64decode(ciphertext)
        
        # Extract IV (12 bytes), tag (16 bytes), and ciphertext
        iv = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext_bytes = encrypted_data[28:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(iv, tag),
            backend=default_backend(),
        )
        
        decryptor = cipher.decryptor()
        
        # Decrypt
        plaintext = decryptor.update(ciphertext_bytes) + decryptor.finalize()
        
        return plaintext.decode()
    
    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt all string values in a dictionary
        
        Args:
            data: Dictionary with string values
            
        Returns:
            Dictionary with encrypted values
        """
        encrypted = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            elif isinstance(value, dict):
                encrypted[key] = self.encrypt_dict(value)
            else:
                encrypted[key] = value
        
        return encrypted
    
    def decrypt_dict(self, data: dict) -> dict:
        """
        Decrypt all encrypted values in a dictionary
        
        Args:
            data: Dictionary with encrypted values
            
        Returns:
            Dictionary with decrypted values
        """
        decrypted = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    decrypted[key] = self.decrypt(value)
                except Exception:
                    # If decryption fails, assume it's not encrypted
                    decrypted[key] = value
            elif isinstance(value, dict):
                decrypted[key] = self.decrypt_dict(value)
            else:
                decrypted[key] = value
        
        return decrypted


class FernetEncryption:
    """
    Simpler encryption using Fernet (symmetric encryption)
    
    Fernet is easier to use but less flexible than AES-GCM.
    Good for simple use cases.
    """
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize Fernet encryption
        
        Args:
            key: Fernet key (if None, generates new key)
        """
        if key is None:
            key = Fernet.generate_key()
        
        self.fernet = Fernet(key)
        self.key = key
        
        logger.info("Initialized FernetEncryption")
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a new Fernet key"""
        return Fernet.generate_key()
    
    def encrypt(self, plaintext: Union[str, bytes]) -> str:
        """
        Encrypt plaintext
        
        Args:
            plaintext: Data to encrypt
            
        Returns:
            Base64-encoded ciphertext
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()
        
        encrypted = self.fernet.encrypt(plaintext)
        return encrypted.decode()
    
    def decrypt(self, ciphertext: Union[str, bytes]) -> str:
        """
        Decrypt ciphertext
        
        Args:
            ciphertext: Encrypted data
            
        Returns:
            Decrypted plaintext
        """
        if isinstance(ciphertext, str):
            ciphertext = ciphertext.encode()
        
        decrypted = self.fernet.decrypt(ciphertext)
        return decrypted.decode()


def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """
    Hash password using PBKDF2-SHA256
    
    Args:
        password: Password to hash
        salt: Optional salt (if None, generates random salt)
        
    Returns:
        Tuple of (hashed_password, salt) as base64 strings
    """
    if salt is None:
        salt = os.urandom(32)
    elif isinstance(salt, str):
        salt = base64.b64decode(salt)
    
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )
    
    hashed = kdf.derive(password.encode())
    
    return (
        base64.b64encode(hashed).decode(),
        base64.b64encode(salt).decode(),
    )


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify password against hash
    
    Args:
        password: Password to verify
        hashed_password: Stored hash (base64)
        salt: Stored salt (base64)
        
    Returns:
        True if password matches
    """
    new_hash, _ = hash_password(password, salt)
    return new_hash == hashed_password


def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key
    
    Args:
        length: Length of the key in bytes
        
    Returns:
        Base64-encoded API key
    """
    key = os.urandom(length)
    return base64.urlsafe_b64encode(key).decode().rstrip("=")
