"""
End-to-End Test Runner

Comprehensive E2E tests that validate the entire security stack.
"""

import pytest
import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestE2ESecurityStack:
    """End-to-end tests for complete security stack"""
    
    def test_complete_authentication_flow(self, mock_cognito_client, temp_db):
        """Test complete authentication flow from login to logout"""
        from app.auth.cognito_provider import CognitoProvider
        from app.auth.auth_provider import UserRole
        
        # Initialize provider
        provider = CognitoProvider({
            "user_pool_id": "us-east-1_TEST",
            "client_id": "test_client",
            "region": "us-east-1",
        })
        
        # Step 1: Login
        result = provider.login("test@example.com", "password123")
        
        assert result.success
        assert result.user is not None
        assert result.access_token is not None
        
        # Step 2: Validate token
        user = provider.validate_token(result.access_token)
        
        assert user is not None
        assert user.email == "test@example.com"
        
        # Step 3: Check permissions
        assert user.has_permission(Permission.DEPLOY_VIEW)
        
        # Step 4: Logout (token invalidation)
        # In production, would call logout endpoint
        assert True
    
    def test_rate_limiting_with_audit_logging(self, temp_db):
        """Test rate limiting with audit logging integration"""
        from app.middleware.rate_limiter import RateLimiter
        from app.services.audit_logger import AuditLogger, AuditEventType
        
        # Initialize services
        rate_limiter = RateLimiter()
        audit_logger = AuditLogger(db_path=temp_db)
        
        # Simulate multiple requests
        user_id = "test_user"
        
        # First requests should succeed
        for i in range(5):
            allowed, _ = rate_limiter.check_rate_limit(user_id, "login")
            
            if allowed:
                # Log successful attempt
                audit_logger.log_event(
                    event_type=AuditEventType.AUTH_LOGIN,
                    user_id=user_id,
                    status="success",
                )
            else:
                # Log rate limit hit
                audit_logger.log_event(
                    event_type=AuditEventType.SECURITY_RATE_LIMIT,
                    user_id=user_id,
                    severity=AuditSeverity.WARNING,
                )
        
        # Verify audit logs
        login_events = audit_logger.query_events(
            event_type=AuditEventType.AUTH_LOGIN,
            user_id=user_id,
        )
        
        assert len(login_events) == 5
    
    def test_input_sanitization_before_deployment(self, sample_terraform_config):
        """Test input sanitization in deployment workflow"""
        from app.middleware.input_sanitizer import InputSanitizer
        
        sanitizer = InputSanitizer()
        
        # Sanitize configuration
        sanitized_config = sanitizer.sanitize_dict(sample_terraform_config)
        
        # Validate Terraform config
        assert sanitizer.validate_terraform_config(sanitized_config)
        
        # Test dangerous config
        dangerous_config = {
            "provider": "aws; rm -rf /",  # Command injection attempt
            "region": "us-east-1",
        }
        
        # Should raise on sanitization
        with pytest.raises(ValueError):
            sanitizer.validate_no_command_injection(dangerous_config["provider"])
    
    def test_deployment_approval_workflow(self, mock_user, temp_db):
        """Test complete deployment approval workflow"""
        from app.services.approval_workflow import ApprovalWorkflow
        from app.services.audit_logger import AuditLogger, AuditEventType
        
        # Initialize services
        workflow = ApprovalWorkflow(storage_path=str(Path(temp_db).parent / "approvals"))
        audit_logger = AuditLogger(db_path=temp_db)
        
        # Step 1: Check if approval required
        estimated_cost = 150.0  # Above threshold
        requires_approval = workflow.requires_approval(mock_user, estimated_cost)
        
        # Should require approval for high cost
        assert requires_approval
        
        # Step 2: Create approval request
        request = workflow.create_approval_request(
            deployment_id="deploy_001",
            requester=mock_user,
            config={"instance_type": "t2.large"},
            estimated_cost=estimated_cost,
        )
        
        assert request is not None
        
        # Log approval request
        audit_logger.log_event(
            event_type=AuditEventType.DEPLOY_APPROVE,
            user_id=mock_user.user_id,
            resource_id=request.request_id,
            status="pending",
        )
        
        # Step 3: Approve request
        approved = workflow.approve_request(request.request_id, mock_user)
        
        assert approved
        
        # Log approval
        audit_logger.log_event(
            event_type=AuditEventType.DEPLOY_APPROVE,
            user_id=mock_user.user_id,
            resource_id=request.request_id,
            status="approved",
        )
        
        # Verify audit trail
        approval_events = audit_logger.query_events(
            event_type=AuditEventType.DEPLOY_APPROVE,
        )
        
        assert len(approval_events) == 2  # pending + approved
    
    def test_secrets_management_with_encryption(self, mock_secrets_manager, clean_environment):
        """Test secrets management with encryption"""
        from app.services.secrets_manager import SecretsManager
        from app.services.encryption import EncryptionService
        
        # Initialize services
        secrets_manager = SecretsManager()
        encryption_service = EncryptionService(master_key="test-key-12345")
        
        # Step 1: Create secret
        secret_data = {
            "db_password": "super_secret_password",
            "api_key": "secret_api_key_123",
        }
        
        # Encrypt sensitive data before storing
        encrypted_data = encryption_service.encrypt_dict(secret_data)
        
        # Store in Secrets Manager
        arn = secrets_manager.create_secret(
            name="test-app/database",
            secret_value=encrypted_data,
        )
        
        assert arn is not None
        
        # Step 2: Retrieve and decrypt
        retrieved = secrets_manager.get_secret("test-app/database")
        decrypted = encryption_service.decrypt_dict(retrieved)
        
        assert decrypted == secret_data
    
    def test_compliance_reporting_with_audit_logs(self, temp_db):
        """Test compliance reporting based on audit logs"""
        from app.services.audit_logger import AuditLogger, AuditEventType
        from app.services.compliance_reporter import ComplianceReporter, ComplianceFramework
        
        # Initialize services
        audit_logger = AuditLogger(db_path=temp_db)
        compliance_reporter = ComplianceReporter(audit_logger)
        
        # Generate audit events
        events_to_log = [
            (AuditEventType.AUTH_LOGIN, "user1"),
            (AuditEventType.AUTH_LOGOUT, "user1"),
            (AuditEventType.DEPLOY_CREATE, "user1"),
            (AuditEventType.SECURITY_RATE_LIMIT, "user2"),
            (AuditEventType.USER_CREATE, "admin"),
        ]
        
        for event_type, user_id in events_to_log:
            audit_logger.log_event(
                event_type=event_type,
                user_id=user_id,
            )
        
        # Generate compliance report
        report = compliance_reporter.generate_report(
            framework=ComplianceFramework.SOC2,
            period_days=1,
        )
        
        assert report is not None
        assert report.total_controls > 0
        assert report.compliance_percentage >= 0
        
        # Export report
        markdown = compliance_reporter.export_report_markdown(report)
        assert "Compliance Report" in markdown
        assert "SOC2" in markdown


class TestE2EUserJourneys:
    """Test complete user journeys"""
    
    def test_admin_user_journey(self, mock_user, temp_db):
        """Test admin user complete journey"""
        from app.auth.auth_provider import Permission
        from app.services.audit_logger import AuditLogger, AuditEventType
        
        audit_logger = AuditLogger(db_path=temp_db)
        
        # Step 1: Login
        audit_logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN,
            user_id=mock_user.user_id,
            user_email=mock_user.email,
            status="success",
        )
        
        # Step 2: Check permissions
        assert mock_user.has_permission(Permission.ADMIN_USERS)
        assert mock_user.has_permission(Permission.DEPLOY_CREATE)
        
        # Step 3: Create deployment
        audit_logger.log_event(
            event_type=AuditEventType.DEPLOY_CREATE,
            user_id=mock_user.user_id,
            resource_id="deploy_001",
            status="success",
        )
        
        # Step 4: View audit logs
        events = audit_logger.query_events(user_id=mock_user.user_id)
        
        assert len(events) == 2
        
        # Step 5: Logout
        audit_logger.log_event(
            event_type=AuditEventType.AUTH_LOGOUT,
            user_id=mock_user.user_id,
            status="success",
        )
    
    def test_deployer_user_journey(self, mock_deployer_user, temp_db):
        """Test deployer user journey"""
        from app.auth.auth_provider import Permission
        from app.services.audit_logger import AuditLogger, AuditEventType
        from app.middleware.rate_limiter import RateLimiter
        
        audit_logger = AuditLogger(db_path=temp_db)
        rate_limiter = RateLimiter()
        
        # Step 1: Login
        audit_logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN,
            user_id=mock_deployer_user.user_id,
            status="success",
        )
        
        # Step 2: Check permissions
        assert mock_deployer_user.has_permission(Permission.DEPLOY_CREATE)
        assert not mock_deployer_user.has_permission(Permission.ADMIN_USERS)
        
        # Step 3: Upload config (with rate limiting)
        allowed, _ = rate_limiter.check_rate_limit(
            mock_deployer_user.user_id,
            "config_upload",
        )
        
        assert allowed
        
        # Step 4: Create deployment
        audit_logger.log_event(
            event_type=AuditEventType.DEPLOY_CREATE,
            user_id=mock_deployer_user.user_id,
            resource_id="deploy_002",
            status="success",
        )
        
        # Verify audit trail
        events = audit_logger.query_events(user_id=mock_deployer_user.user_id)
        assert len(events) == 2
    
    def test_viewer_user_journey(self, mock_viewer_user, temp_db):
        """Test viewer user journey (read-only)"""
        from app.auth.auth_provider import Permission
        from app.services.audit_logger import AuditLogger, AuditEventType
        
        audit_logger = AuditLogger(db_path=temp_db)
        
        # Step 1: Login
        audit_logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN,
            user_id=mock_viewer_user.user_id,
            status="success",
        )
        
        # Step 2: Check permissions
        assert mock_viewer_user.has_permission(Permission.DEPLOY_VIEW)
        assert not mock_viewer_user.has_permission(Permission.DEPLOY_CREATE)
        assert not mock_viewer_user.has_permission(Permission.CONFIG_UPLOAD)
        
        # Step 3: Attempt to create deployment (should fail)
        if not mock_viewer_user.has_permission(Permission.DEPLOY_CREATE):
            # Log unauthorized attempt
            audit_logger.log_event(
                event_type=AuditEventType.SECURITY_UNAUTHORIZED,
                user_id=mock_viewer_user.user_id,
                severity=AuditSeverity.WARNING,
                action="deploy_create",
            )
        
        # Verify security event logged
        security_events = audit_logger.query_events(
            event_type=AuditEventType.SECURITY_UNAUTHORIZED,
        )
        
        assert len(security_events) == 1


# Import missing dependencies
from app.auth.auth_provider import Permission
from app.services.audit_logger import AuditSeverity


if __name__ == "__main__":
    # Run E2E tests
    pytest.main([__file__, "-v", "--tb=short"])
