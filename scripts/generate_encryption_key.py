"""
Generate Encryption Master Key

Simple script to generate a secure encryption master key for the application.
"""

import secrets
import base64

def generate_encryption_key():
    """Generate a secure 32-byte encryption key"""
    # Generate 32 random bytes
    key_bytes = secrets.token_bytes(32)
    
    # Encode as base64 for easy storage
    key_base64 = base64.urlsafe_b64encode(key_bytes).decode('utf-8')
    
    return key_base64

if __name__ == "__main__":
    print("=" * 60)
    print("Encryption Master Key Generator")
    print("=" * 60)
    print()
    
    key = generate_encryption_key()
    
    print("Generated Encryption Master Key:")
    print(key)
    print()
    print("Add this to your .env file:")
    print(f"ENCRYPTION_MASTER_KEY={key}")
    print()
    print("⚠️  IMPORTANT:")
    print("1. Keep this key secret - never commit to git")
    print("2. Store in AWS Secrets Manager for production")
    print("3. Use different keys for dev/staging/prod")
    print("4. Back up this key securely")
    print("=" * 60)
