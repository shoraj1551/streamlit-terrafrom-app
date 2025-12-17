"""
Unit Tests for Authentication Provider

Tests authentication provider base class and implementations.
"""

import pytest
from datetime import datetime
from app.auth.auth_provider import (
    User,
    UserRole,
    Permission,
    ROLE_PERMISSIONS,
    AuthenticationResult,
)


class TestUser:
    """Test User model"""
    
    def test_user_creation(self):
        """Test creating a user"""
        user = User(
            user_id="123",
            email="test@example.com",
            name="Test User",
            role=UserRole.ADMIN,
            provider="test",
        )
        
        assert user.user_id == "123"
        assert user.email == "test@example.com"
        assert user.role == UserRole.ADMIN
    
    def test_admin_has_all_permissions(self):
        """Test that admin has all permissions"""
        user = User(
            user_id="123",
            email="admin@example.com",
            name="Admin",
            role=UserRole.ADMIN,
            provider="test",
        )
        
        # Admin should have all permissions
        for permission in Permission:
            assert user.has_permission(permission), f"Admin missing {permission}"
    
    def test_deployer_permissions(self):
        """Test deployer role permissions"""
        user = User(
            user_id="123",
            email="deployer@example.com",
            name="Deployer",
            role=UserRole.DEPLOYER,
            provider="test",
        )
        
        # Should have deployment permissions
        assert user.has_permission(Permission.DEPLOY_CREATE)
        assert user.has_permission(Permission.DEPLOY_VIEW)
        assert user.has_permission(Permission.CONFIG_UPLOAD)
        
        # Should NOT have admin permissions
        assert not user.has_permission(Permission.ADMIN_USERS)
        assert not user.has_permission(Permission.ADMIN_SETTINGS)
    
    def test_viewer_permissions(self):
        """Test viewer role permissions"""
        user = User(
            user_id="123",
            email="viewer@example.com",
            name="Viewer",
            role=UserRole.VIEWER,
            provider="test",
        )
        
        # Should have view permissions
        assert user.has_permission(Permission.DEPLOY_VIEW)
        assert user.has_permission(Permission.CONFIG_VIEW)
        
        # Should NOT have create/delete permissions
        assert not user.has_permission(Permission.DEPLOY_CREATE)
        assert not user.has_permission(Permission.DEPLOY_DELETE)
        assert not user.has_permission(Permission.CONFIG_UPLOAD)
    
    def test_has_any_permission(self):
        """Test has_any_permission method"""
        user = User(
            user_id="123",
            email="viewer@example.com",
            name="Viewer",
            role=UserRole.VIEWER,
            provider="test",
        )
        
        # Should return True if has at least one permission
        assert user.has_any_permission([
            Permission.DEPLOY_VIEW,
            Permission.DEPLOY_CREATE,
        ])
        
        # Should return False if has none
        assert not user.has_any_permission([
            Permission.DEPLOY_CREATE,
            Permission.ADMIN_USERS,
        ])
    
    def test_has_all_permissions(self):
        """Test has_all_permissions method"""
        user = User(
            user_id="123",
            email="deployer@example.com",
            name="Deployer",
            role=UserRole.DEPLOYER,
            provider="test",
        )
        
        # Should return True if has all permissions
        assert user.has_all_permissions([
            Permission.DEPLOY_VIEW,
            Permission.DEPLOY_CREATE,
        ])
        
        # Should return False if missing any
        assert not user.has_all_permissions([
            Permission.DEPLOY_CREATE,
            Permission.ADMIN_USERS,
        ])


class TestRolePermissions:
    """Test RBAC configuration"""
    
    def test_all_roles_have_permissions(self):
        """Test that all roles have permissions defined"""
        for role in UserRole:
            assert role in ROLE_PERMISSIONS, f"Role {role} missing permissions"
            assert len(ROLE_PERMISSIONS[role]) > 0, f"Role {role} has no permissions"
    
    def test_admin_has_most_permissions(self):
        """Test that admin has more permissions than other roles"""
        admin_perms = len(ROLE_PERMISSIONS[UserRole.ADMIN])
        deployer_perms = len(ROLE_PERMISSIONS[UserRole.DEPLOYER])
        viewer_perms = len(ROLE_PERMISSIONS[UserRole.VIEWER])
        
        assert admin_perms > deployer_perms
        assert deployer_perms > viewer_perms
    
    def test_viewer_is_subset_of_deployer(self):
        """Test that viewer permissions are subset of deployer"""
        viewer_perms = set(ROLE_PERMISSIONS[UserRole.VIEWER])
        deployer_perms = set(ROLE_PERMISSIONS[UserRole.DEPLOYER])
        
        assert viewer_perms.issubset(deployer_perms)


class TestAuthenticationResult:
    """Test AuthenticationResult"""
    
    def test_successful_authentication(self):
        """Test successful authentication result"""
        user = User(
            user_id="123",
            email="test@example.com",
            name="Test",
            role=UserRole.ADMIN,
            provider="test",
        )
        
        result = AuthenticationResult(
            success=True,
            user=user,
            access_token="token123",
            refresh_token="refresh123",
            expires_in=3600,
        )
        
        assert result.success
        assert result.user == user
        assert result.access_token == "token123"
        assert result.error is None
    
    def test_failed_authentication(self):
        """Test failed authentication result"""
        result = AuthenticationResult(
            success=False,
            error="Invalid credentials",
        )
        
        assert not result.success
        assert result.user is None
        assert result.error == "Invalid credentials"
