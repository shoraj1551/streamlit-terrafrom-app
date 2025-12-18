"""
Database Models using SQLAlchemy

Replaces SQLite with PostgreSQL for production-ready deployment tracking.
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Float, Text, Boolean,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os

Base = declarative_base()


class Deployment(Base):
    """Deployment tracking model"""
    __tablename__ = 'deployments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    deployment_id = Column(String(36), unique=True, nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    
    # Infrastructure details
    provider = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False)
    instance_type = Column(String(50))
    
    # Status tracking
    status = Column(String(20), nullable=False, index=True)
    current_step = Column(String(200))
    progress_percentage = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    error_message = Column(Text)
    outputs = Column(Text)  # Encrypted JSON
    
    # Cost tracking
    cost_estimate = Column(Float)
    actual_cost = Column(Float)
    
    # File paths
    deployment_dir = Column(String(500))
    config_file = Column(String(500))
    
    # Relationships
    logs = relationship("DeploymentLog", back_populates="deployment", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_deployment_user_status', 'user_email', 'status'),
        Index('idx_deployment_created_status', 'created_at', 'status'),
        Index('idx_deployment_provider_region', 'provider', 'region'),
    )
    
    def __repr__(self):
        return f"<Deployment(id={self.deployment_id}, status={self.status})>"


class DeploymentLog(Base):
    """Deployment log entries"""
    __tablename__ = 'deployment_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    deployment_id = Column(String(36), ForeignKey('deployments.deployment_id', ondelete='CASCADE'), nullable=False, index=True)
    
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    log_level = Column(String(20), default='INFO')
    message = Column(Text, nullable=False)
    
    # Relationship
    deployment = relationship("Deployment", back_populates="logs")
    
    __table_args__ = (
        Index('idx_log_deployment_timestamp', 'deployment_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<DeploymentLog(deployment={self.deployment_id}, level={self.log_level})>"


class AuditLog(Base):
    """Audit log for security events"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)  # auth, deployment, config, etc.
    severity = Column(String(20), nullable=False, index=True)  # info, warning, error, critical
    
    # User/Actor information
    user_id = Column(String(255), index=True)
    user_email = Column(String(255), index=True)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    
    # Event data
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    action = Column(String(100))
    status = Column(String(20))  # success, failure, pending
    
    # Details
    details = Column(Text)  # JSON
    error_message = Column(Text)
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Indexes for audit queries
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_email', 'timestamp'),
        Index('idx_audit_event_timestamp', 'event_type', 'timestamp'),
        Index('idx_audit_severity_timestamp', 'severity', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AuditLog(event={self.event_type}, user={self.user_email})>"


class UserSession(Base):
    """User session tracking (Redis backup)"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # User information
    user_id = Column(String(255), nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    
    # Session data
    access_token = Column(Text)  # Encrypted
    refresh_token = Column(Text)  # Encrypted
    id_token = Column(Text)  # Encrypted
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Session metadata
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    revoked_at = Column(DateTime)
    revocation_reason = Column(String(200))
    
    __table_args__ = (
        Index('idx_session_user_active', 'user_email', 'is_active'),
        Index('idx_session_expires', 'expires_at', 'is_active'),
    )
    
    def __repr__(self):
        return f"<UserSession(user={self.user_email}, active={self.is_active})>"


# Database connection and session management
class Database:
    """Database connection manager"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database connection
        
        Args:
            database_url: PostgreSQL connection URL
                         Format: postgresql://user:password@host:port/database
        """
        if database_url is None:
            database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            # Fallback to SQLite for development (not recommended)
            database_url = "sqlite:///./data/deployments.db"
            print("WARNING: Using SQLite. Set DATABASE_URL for PostgreSQL.")
        
        # Production-ready connection pool configuration
        pool_config = {
            'pool_size': 50,  # Increased from 10 for production load
            'max_overflow': 100,  # Increased from 20
            'pool_pre_ping': True,  # Verify connections before use
            'pool_recycle': 3600,  # Recycle connections after 1 hour
            'pool_timeout': 30,  # Wait max 30s for connection from pool
            'echo': False,  # Set to True for SQL debugging
            'echo_pool': 'debug' if os.getenv('DEBUG') else False  # Pool checkout/checkin logging
        }
        
        # Add PostgreSQL-specific settings
        if database_url.startswith('postgresql'):
            pool_config['connect_args'] = {
                'connect_timeout': 10,  # Connection timeout
                'application_name': 'terraform_deployment_app',
                'options': '-c statement_timeout=30000'  # 30s query timeout
            }
        
        self.engine = create_engine(database_url, **pool_config)
        
        # Add event listeners for monitoring
        from sqlalchemy import event
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Set connection parameters on new connections"""
            if database_url.startswith('postgresql'):
                cursor = dbapi_conn.cursor()
                try:
                    # Set statement timeout for all queries
                    cursor.execute("SET statement_timeout = 30000")  # 30 seconds
                    # Set idle in transaction timeout
                    cursor.execute("SET idle_in_transaction_session_timeout = 60000")  # 60 seconds
                finally:
                    cursor.close()
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Log pool checkouts in debug mode"""
            if os.getenv('DEBUG'):
                import logging
                logging.debug(f"Connection checked out from pool")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Log pool checkins in debug mode"""
            if os.getenv('DEBUG'):
                import logging
                logging.debug(f"Connection returned to pool")
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()


# Global database instance
_db_instance = None


def get_database() -> Database:
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
