"""
Pytest Configuration and Fixtures

Provides shared fixtures and configuration for all tests.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary directory for test data"""
    temp_dir = tempfile.mkdtemp(prefix="terraform_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    from app.auth.auth_provider import User, UserRole
    
    return User(
        user_id="test_user_123",
        email="test@example.com",
        name="Test User",
        role=UserRole.ADMIN,
        provider="test",
        created_at=datetime.now(),
    )


@pytest.fixture
def mock_deployer_user():
    """Mock deployer user"""
    from app.auth.auth_provider import User, UserRole
    
    return User(
        user_id="deployer_456",
        email="deployer@example.com",
        name="Deployer User",
        role=UserRole.DEPLOYER,
        provider="test",
    )


@pytest.fixture
def mock_viewer_user():
    """Mock viewer user"""
    from app.auth.auth_provider import User, UserRole
    
    return User(
        user_id="viewer_789",
        email="viewer@example.com",
        name="Viewer User",
        role=UserRole.VIEWER,
        provider="test",
    )


@pytest.fixture
def sample_terraform_config():
    """Sample Terraform configuration"""
    return {
        "provider": "aws",
        "region": "us-east-1",
        "instance_type": "t2.micro",
        "ami_id": "ami-12345678",
        "tags": {
            "Environment": "test",
            "ManagedBy": "terraform-app",
        }
    }


@pytest.fixture
def mock_secrets_manager(monkeypatch):
    """Mock AWS Secrets Manager"""
    mock_client = MagicMock()
    
    # Mock get_secret_value
    mock_client.get_secret_value.return_value = {
        "SecretString": '{"key": "value"}',
        "VersionId": "v1",
    }
    
    # Mock create_secret
    mock_client.create_secret.return_value = {
        "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test",
    }
    
    def mock_boto3_client(service_name, **kwargs):
        if service_name == "secretsmanager":
            return mock_client
        return MagicMock()
    
    monkeypatch.setattr("boto3.client", mock_boto3_client)
    
    return mock_client


@pytest.fixture
def mock_cognito_client(monkeypatch):
    """Mock AWS Cognito client"""
    mock_client = MagicMock()
    
    # Mock initiate_auth
    mock_client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "mock_access_token",
            "RefreshToken": "mock_refresh_token",
            "IdToken": "mock_id_token",
            "ExpiresIn": 3600,
        }
    }
    
    # Mock get_user
    mock_client.get_user.return_value = {
        "Username": "test_user",
        "UserAttributes": [
            {"Name": "email", "Value": "test@example.com"},
            {"Name": "name", "Value": "Test User"},
            {"Name": "custom:role", "Value": "admin"},
        ],
    }
    
    def mock_boto3_client(service_name, **kwargs):
        if service_name == "cognito-idp":
            return mock_client
        return MagicMock()
    
    monkeypatch.setattr("boto3.client", mock_boto3_client)
    
    return mock_client


@pytest.fixture
def temp_db(test_data_dir):
    """Temporary database for testing"""
    db_path = test_data_dir / "test.db"
    yield str(db_path)
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def clean_environment(monkeypatch):
    """Clean environment variables for testing"""
    # Set test environment variables
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-12345")
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", "test-encryption-key-12345")
    
    yield
    
    # Cleanup is automatic with monkeypatch


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Mock Streamlit for testing"""
    mock_st = MagicMock()
    mock_st.session_state = {}
    
    monkeypatch.setattr("streamlit", mock_st)
    
    return mock_st
