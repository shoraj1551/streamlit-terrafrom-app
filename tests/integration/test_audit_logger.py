"""
Integration Tests for Audit Logger

Tests audit logging with database integration.
"""

import pytest
from datetime import datetime, timedelta
from app.services.audit_logger import (
    AuditLogger,
    AuditEventType,
    AuditSeverity,
    log_auth_event,
    log_deployment_event,
)


class TestAuditLogger:
    """Test AuditLogger with database"""
    
    def test_audit_logger_creation(self, temp_db):
        """Test creating audit logger"""
        logger = AuditLogger(db_path=temp_db)
        
        assert logger.db_path.exists()
    
    def test_log_event(self, temp_db):
        """Test logging an event"""
        logger = AuditLogger(db_path=temp_db)
        
        event_id = logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN,
            severity=AuditSeverity.INFO,
            user_id="user123",
            user_email="test@example.com",
            status="success",
        )
        
        assert event_id is not None
        assert event_id.startswith("evt_")
    
    def test_query_events(self, temp_db):
        """Test querying events"""
        logger = AuditLogger(db_path=temp_db)
        
        # Log some events
        logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN,
            user_id="user123",
            user_email="test@example.com",
        )
        
        logger.log_event(
            event_type=AuditEventType.DEPLOY_CREATE,
            user_id="user123",
            resource_id="deploy_001",
        )
        
        # Query all events
        events = logger.query_events(limit=10)
        
        assert len(events) == 2
    
    def test_query_events_by_type(self, temp_db):
        """Test querying events by type"""
        logger = AuditLogger(db_path=temp_db)
        
        # Log different event types
        logger.log_event(event_type=AuditEventType.AUTH_LOGIN, user_id="user123")
        logger.log_event(event_type=AuditEventType.AUTH_LOGIN, user_id="user456")
        logger.log_event(event_type=AuditEventType.DEPLOY_CREATE, user_id="user123")
        
        # Query login events only
        login_events = logger.query_events(event_type=AuditEventType.AUTH_LOGIN)
        
        assert len(login_events) == 2
        assert all(e.event_type == AuditEventType.AUTH_LOGIN for e in login_events)
    
    def test_query_events_by_user(self, temp_db):
        """Test querying events by user"""
        logger = AuditLogger(db_path=temp_db)
        
        # Log events for different users
        logger.log_event(event_type=AuditEventType.AUTH_LOGIN, user_id="user123")
        logger.log_event(event_type=AuditEventType.AUTH_LOGIN, user_id="user123")
        logger.log_event(event_type=AuditEventType.AUTH_LOGIN, user_id="user456")
        
        # Query user123 events
        user_events = logger.query_events(user_id="user123")
        
        assert len(user_events) == 2
        assert all(e.user_id == "user123" for e in user_events)
    
    def test_query_events_by_severity(self, temp_db):
        """Test querying events by severity"""
        logger = AuditLogger(db_path=temp_db)
        
        # Log events with different severities
        logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN,
            severity=AuditSeverity.INFO,
        )
        logger.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            severity=AuditSeverity.ERROR,
        )
        logger.log_event(
            event_type=AuditEventType.SECURITY_UNAUTHORIZED,
            severity=AuditSeverity.CRITICAL,
        )
        
        # Query critical events
        critical_events = logger.query_events(severity=AuditSeverity.CRITICAL)
        
        assert len(critical_events) == 1
        assert critical_events[0].severity == AuditSeverity.CRITICAL
    
    def test_query_events_by_date_range(self, temp_db):
        """Test querying events by date range"""
        logger = AuditLogger(db_path=temp_db)
        
        # Log events
        logger.log_event(event_type=AuditEventType.AUTH_LOGIN)
        
        # Query events from last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        events = logger.query_events(start_date=one_hour_ago)
        
        assert len(events) == 1
    
    def test_get_event_count(self, temp_db):
        """Test getting event count"""
        logger = AuditLogger(db_path=temp_db)
        
        # Log events
        for i in range(5):
            logger.log_event(event_type=AuditEventType.AUTH_LOGIN, user_id=f"user{i}")
        
        count = logger.get_event_count()
        
        assert count == 5
    
    def test_get_event_count_filtered(self, temp_db):
        """Test getting filtered event count"""
        logger = AuditLogger(db_path=temp_db)
        
        # Log different event types
        logger.log_event(event_type=AuditEventType.AUTH_LOGIN)
        logger.log_event(event_type=AuditEventType.AUTH_LOGIN)
        logger.log_event(event_type=AuditEventType.DEPLOY_CREATE)
        
        count = logger.get_event_count(event_type=AuditEventType.AUTH_LOGIN)
        
        assert count == 2
    
    def test_cleanup_old_events(self, temp_db):
        """Test cleaning up old events"""
        logger = AuditLogger(db_path=temp_db)
        
        # Log some events
        for i in range(10):
            logger.log_event(event_type=AuditEventType.AUTH_LOGIN)
        
        # Cleanup events older than 0 days (all events)
        deleted_count = logger.cleanup_old_events(retention_days=0)
        
        # All events should be deleted
        assert deleted_count == 10
        
        # Verify no events remain
        remaining = logger.get_event_count()
        assert remaining == 0


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_log_auth_event(self, temp_db, monkeypatch):
        """Test log_auth_event function"""
        logger = AuditLogger(db_path=temp_db)
        
        # Mock get_audit_logger
        monkeypatch.setattr("app.services.audit_logger._audit_logger", logger)
        
        event_id = log_auth_event(
            event_type=AuditEventType.AUTH_LOGIN,
            user_id="user123",
            user_email="test@example.com",
            status="success",
        )
        
        assert event_id is not None
        
        # Verify event was logged
        events = logger.query_events(event_type=AuditEventType.AUTH_LOGIN)
        assert len(events) == 1
    
    def test_log_deployment_event(self, temp_db, monkeypatch):
        """Test log_deployment_event function"""
        logger = AuditLogger(db_path=temp_db)
        
        monkeypatch.setattr("app.services.audit_logger._audit_logger", logger)
        
        event_id = log_deployment_event(
            event_type=AuditEventType.DEPLOY_CREATE,
            user_id="user123",
            deployment_id="deploy_001",
            status="success",
        )
        
        assert event_id is not None
        
        # Verify event was logged
        events = logger.query_events(event_type=AuditEventType.DEPLOY_CREATE)
        assert len(events) == 1
        assert events[0].resource_id == "deploy_001"
