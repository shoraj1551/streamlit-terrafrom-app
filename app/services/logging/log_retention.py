"""
Log Retention Configuration and Management
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional


class LogRetentionPeriod(str, Enum):
    """Supported log retention periods"""
    ONE_MONTH = "1_month"
    SIX_MONTHS = "6_months"  # Default
    ONE_YEAR = "1_year"
    TWO_YEARS = "2_years"
    
    def to_days(self) -> int:
        """Convert retention period to days"""
        mapping = {
            self.ONE_MONTH: 30,
            self.SIX_MONTHS: 180,
            self.ONE_YEAR: 365,
            self.TWO_YEARS: 730,
        }
        return mapping[self]
    
    def to_timedelta(self) -> timedelta:
        """Convert to timedelta"""
        return timedelta(days=self.to_days())
    
    @classmethod
    def get_default(cls) -> 'LogRetentionPeriod':
        """Get default retention period (6 months)"""
        return cls.SIX_MONTHS


class LogRetentionManager:
    """Manage log retention and cleanup"""
    
    def __init__(self, retention_period: LogRetentionPeriod = None):
        self.retention_period = retention_period or LogRetentionPeriod.get_default()
    
    def get_cutoff_date(self) -> datetime:
        """Get the cutoff date for log retention"""
        return datetime.utcnow() - self.retention_period.to_timedelta()
    
    def should_delete_log(self, log_timestamp: datetime) -> bool:
        """Check if a log should be deleted based on retention policy"""
        return log_timestamp < self.get_cutoff_date()
    
    def cleanup_old_logs(self, db):
        """Delete logs older than retention period"""
        cutoff_date = self.get_cutoff_date()
        deleted_count = db.delete_logs_before(cutoff_date)
        return deleted_count
