"""
Audit Logging System

Comprehensive audit logging for security, compliance, and debugging.
Tracks all user actions, system events, and security-relevant activities.

Features:
- Structured logging (JSON)
- Multiple log levels
- User action tracking
- Security event logging
- Database storage
- Log retention policies
- Query and search capabilities
"""

import json
import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events"""
    # Authentication
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"
    
    # Deployment
    DEPLOY_CREATE = "deploy.create"
    DEPLOY_APPROVE = "deploy.approve"
    DEPLOY_REJECT = "deploy.reject"
    DEPLOY_EXECUTE = "deploy.execute"
    DEPLOY_DELETE = "deploy.delete"
    DEPLOY_FAILED = "deploy.failed"
    
    # Configuration
    CONFIG_UPLOAD = "config.upload"
    CONFIG_VIEW = "config.view"
    CONFIG_VALIDATE = "config.validate"
    
    # User Management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role_change"
    
    # Security
    SECURITY_RATE_LIMIT = "security.rate_limit"
    SECURITY_CSRF_FAIL = "security.csrf_fail"
    SECURITY_INPUT_SANITIZE = "security.input_sanitize"
    SECURITY_UNAUTHORIZED = "security.unauthorized"
    
    # System
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"
    SYSTEM_CONFIG_CHANGE = "system.config_change"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event record"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        data["timestamp"] = self.timestamp.isoformat()
        if self.details:
            data["details"] = json.dumps(self.details)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create from dictionary"""
        return cls(
            event_id=data["event_id"],
            event_type=AuditEventType(data["event_type"]),
            severity=AuditSeverity(data["severity"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            user_email=data.get("user_email"),
            user_role=data.get("user_role"),
            ip_address=data.get("ip_address"),
            resource_type=data.get("resource_type"),
            resource_id=data.get("resource_id"),
            action=data.get("action"),
            status=data.get("status"),
            details=json.loads(data["details"]) if data.get("details") else None,
            error_message=data.get("error_message"),
        )


class AuditLogger:
    """
    Audit logging system with database storage
    
    Provides comprehensive audit trail for compliance and security.
    """
    
    def __init__(self, db_path: str = "./data/audit.db"):
        """
        Initialize audit logger
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Initialized AuditLogger at {db_path}")
    
    def _init_database(self):
        """Initialize audit database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create audit_events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                user_email TEXT,
                user_role TEXT,
                ip_address TEXT,
                resource_type TEXT,
                resource_id TEXT,
                action TEXT,
                status TEXT,
                details TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_type 
            ON audit_events(event_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id 
            ON audit_events(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON audit_events(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_severity 
            ON audit_events(severity)
        """)
        
        conn.commit()
        conn.close()
    
    def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> str:
        """
        Log an audit event
        
        Returns:
            Event ID
        """
        import secrets
        
        # Generate event ID
        event_id = f"evt_{secrets.token_hex(8)}"
        
        # Create event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(),
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status=status,
            details=details,
            error_message=error_message,
        )
        
        # Store in database
        self._store_event(event)
        
        # Also log to application logger
        log_msg = f"Audit: {event_type.value}"
        if user_email:
            log_msg += f" by {user_email}"
        if resource_id:
            log_msg += f" on {resource_type}:{resource_id}"
        
        if severity == AuditSeverity.CRITICAL:
            logger.critical(log_msg, extra=event.to_dict())
        elif severity == AuditSeverity.ERROR:
            logger.error(log_msg, extra=event.to_dict())
        elif severity == AuditSeverity.WARNING:
            logger.warning(log_msg, extra=event.to_dict())
        else:
            logger.info(log_msg, extra=event.to_dict())
        
        return event_id
    
    def _store_event(self, event: AuditEvent):
        """Store event in database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        event_dict = event.to_dict()
        
        cursor.execute("""
            INSERT INTO audit_events (
                event_id, event_type, severity, timestamp,
                user_id, user_email, user_role, ip_address,
                resource_type, resource_id, action, status,
                details, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_dict["event_id"],
            event_dict["event_type"],
            event_dict["severity"],
            event_dict["timestamp"],
            event_dict.get("user_id"),
            event_dict.get("user_email"),
            event_dict.get("user_role"),
            event_dict.get("ip_address"),
            event_dict.get("resource_type"),
            event_dict.get("resource_id"),
            event_dict.get("action"),
            event_dict.get("status"),
            event_dict.get("details"),
            event_dict.get("error_message"),
        ))
        
        conn.commit()
        conn.close()
    
    def query_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """
        Query audit events with filters
        
        Returns:
            List of AuditEvent objects
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if severity:
            query += " AND severity = ?"
            params.append(severity.value)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        events = []
        for row in cursor.fetchall():
            event_dict = dict(row)
            events.append(AuditEvent.from_dict(event_dict))
        
        conn.close()
        
        return events
    
    def get_event_count(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Get count of events matching filters"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM audit_events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count
    
    def cleanup_old_events(self, retention_days: int = 90) -> int:
        """
        Delete events older than retention period
        
        Args:
            retention_days: Number of days to retain
            
        Returns:
            Number of events deleted
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM audit_events 
            WHERE timestamp < ?
        """, (cutoff_date.isoformat(),))
        
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted_count} old audit events (retention: {retention_days} days)")
        
        return deleted_count


# Global audit logger instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Convenience functions

def log_auth_event(event_type: AuditEventType, user_id: str, user_email: str, status: str, **kwargs):
    """Log authentication event"""
    audit_logger = get_audit_logger()
    return audit_logger.log_event(
        event_type=event_type,
        user_id=user_id,
        user_email=user_email,
        status=status,
        **kwargs
    )


def log_deployment_event(event_type: AuditEventType, user_id: str, deployment_id: str, status: str, **kwargs):
    """Log deployment event"""
    audit_logger = get_audit_logger()
    return audit_logger.log_event(
        event_type=event_type,
        user_id=user_id,
        resource_type="deployment",
        resource_id=deployment_id,
        status=status,
        **kwargs
    )


def log_security_event(event_type: AuditEventType, severity: AuditSeverity, **kwargs):
    """Log security event"""
    audit_logger = get_audit_logger()
    return audit_logger.log_event(
        event_type=event_type,
        severity=severity,
        **kwargs
    )
