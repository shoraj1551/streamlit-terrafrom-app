"""
Unit Tests for Encryption Service

Tests encryption, decryption, and password hashing.
"""

import pytest
from app.services.encryption import (
    EncryptionService,
    FernetEncryption,
    hash_password,
    verify_password,
    generate_api_key,
)


class TestEncryptionService:
    """Test EncryptionService (AES-256-GCM)"""
    
    def test_encrypt_decrypt_string(self):
        """Test encrypting and decrypting a string"""
        service = EncryptionService(master_key="test-master-key-12345")
        
        plaintext = "sensitive data"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
        assert encrypted != plaintext
    
    def test_encrypt_decrypt_bytes(self):
        """Test encrypting and decrypting bytes"""
        service = EncryptionService(master_key="test-master-key-12345")
        
        plaintext = b"sensitive bytes"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext.decode()
    
    def test_different_encryptions_produce_different_ciphertexts(self):
        """Test that same plaintext produces different ciphertexts (due to random IV)"""
        service = EncryptionService(master_key="test-master-key-12345")
        
        plaintext = "test data"
        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)
        
        # Should be different due to random IV
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same plaintext
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext
    
    def test_encrypt_decrypt_dict(self):
        """Test encrypting and decrypting dictionary"""
        service = EncryptionService(master_key="test-master-key-12345")
        
        data = {
            "password": "secret123",
            "api_key": "key456",
            "nested": {
                "value": "nested_secret",
            }
        }
        
        encrypted = service.encrypt_dict(data)
        decrypted = service.decrypt_dict(encrypted)
        
        assert decrypted == data
        assert encrypted != data
        assert encrypted["password"] != data["password"]
    
    def test_decrypt_invalid_ciphertext_raises_error(self):
        """Test that decrypting invalid ciphertext raises error"""
        service = EncryptionService(master_key="test-master-key-12345")
        
        with pytest.raises(Exception):
            service.decrypt("invalid_ciphertext")
    
    def test_different_keys_cannot_decrypt(self):
        """Test that different keys cannot decrypt each other's data"""
        service1 = EncryptionService(master_key="key1")
        service2 = EncryptionService(master_key="key2")
        
        plaintext = "test data"
        encrypted = service1.encrypt(plaintext)
        
        with pytest.raises(Exception):
            service2.decrypt(encrypted)


class TestFernetEncryption:
    """Test FernetEncryption"""
    
    def test_encrypt_decrypt(self):
        """Test Fernet encryption and decryption"""
        key = FernetEncryption.generate_key()
        service = FernetEncryption(key)
        
        plaintext = "test data"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_generate_key(self):
        """Test key generation"""
        key1 = FernetEncryption.generate_key()
        key2 = FernetEncryption.generate_key()
        
        # Keys should be different
        assert key1 != key2
        
        # Keys should be valid
        assert len(key1) > 0
        assert len(key2) > 0


class TestPasswordHashing:
    """Test password hashing functions"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "my_secure_password"
        hashed, salt = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert len(salt) > 0
    
    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "my_secure_password"
        hashed, salt = hash_password(password)
        
        assert verify_password(password, hashed, salt)
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "my_secure_password"
        wrong_password = "wrong_password"
        hashed, salt = hash_password(password)
        
        assert not verify_password(wrong_password, hashed, salt)
    
    def test_same_password_different_salts(self):
        """Test that same password with different salts produces different hashes"""
        password = "my_secure_password"
        hashed1, salt1 = hash_password(password)
        hashed2, salt2 = hash_password(password)
        
        assert salt1 != salt2
        assert hashed1 != hashed2


class TestAPIKeyGeneration:
    """Test API key generation"""
    
    def test_generate_api_key(self):
        """Test generating API key"""
        key = generate_api_key()
        
        assert len(key) > 0
        assert isinstance(key, str)
    
    def test_generate_api_key_different_lengths(self):
        """Test generating API keys of different lengths"""
        key16 = generate_api_key(16)
        key32 = generate_api_key(32)
        key64 = generate_api_key(64)
        
        # Longer keys should produce longer strings (roughly)
        assert len(key64) > len(key32) > len(key16)
    
    def test_generate_api_key_uniqueness(self):
        """Test that generated keys are unique"""
        keys = [generate_api_key() for _ in range(100)]
        
        # All keys should be unique
        assert len(set(keys)) == 100
