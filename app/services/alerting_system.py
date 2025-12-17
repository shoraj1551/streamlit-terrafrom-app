"""
Alerting System

Sends alerts for deployment events, failures, and cost thresholds.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class AlertType(str, Enum):
    """Types of alerts"""
    DEPLOYMENT_SUCCESS = "deployment_success"
    DEPLOYMENT_FAILURE = "deployment_failure"
    COST_THRESHOLD = "cost_threshold"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    HEALTH_CHECK_FAILURE = "health_check_failure"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alert:
    """Alert data structure"""
    
    def __init__(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class AlertingSystem:
    """Manage alerts and notifications"""
    
    def __init__(self):
        self.alerts_history: List[Alert] = []
        self.alert_rules = self._default_alert_rules()
    
    def _default_alert_rules(self) -> Dict[str, Any]:
        """Default alert rules"""
        return {
            'cost_threshold': {
                'enabled': True,
                'monthly_limit': 1000.0,  # $1000/month
                'warning_percentage': 80  # Alert at 80%
            },
            'deployment_failure': {
                'enabled': True,
                'notify_on_failure': True
            },
            'performance': {
                'enabled': True,
                'max_deployment_time': 600  # 10 minutes
            }
        }
    
    def check_cost_threshold(
        self,
        current_cost: float,
        deployment_id: str
    ) -> Optional[Alert]:
        """
        Check if cost exceeds threshold
        
        Args:
            current_cost: Current monthly cost
            deployment_id: Deployment ID
            
        Returns:
            Alert if threshold exceeded, None otherwise
        """
        rules = self.alert_rules['cost_threshold']
        if not rules['enabled']:
            return None
        
        limit = rules['monthly_limit']
        warning_threshold = limit * (rules['warning_percentage'] / 100)
        
        if current_cost >= limit:
            alert = Alert(
                alert_type=AlertType.COST_THRESHOLD,
                severity=AlertSeverity.CRITICAL,
                title="Cost Limit Exceeded",
                message=f"Monthly cost ${current_cost:.2f} exceeds limit of ${limit:.2f}",
                metadata={
                    'deployment_id': deployment_id,
                    'current_cost': current_cost,
                    'limit': limit
                }
            )
            self._send_alert(alert)
            return alert
        
        elif current_cost >= warning_threshold:
            alert = Alert(
                alert_type=AlertType.COST_THRESHOLD,
                severity=AlertSeverity.WARNING,
                title="Cost Warning",
                message=f"Monthly cost ${current_cost:.2f} is at {(current_cost/limit)*100:.1f}% of limit",
                metadata={
                    'deployment_id': deployment_id,
                    'current_cost': current_cost,
                    'limit': limit
                }
            )
            self._send_alert(alert)
            return alert
        
        return None
    
    def alert_deployment_failure(
        self,
        deployment_id: str,
        error_message: str,
        cloud_provider: str,
        environment: str
    ) -> Alert:
        """
        Send alert for deployment failure
        
        Args:
            deployment_id: Deployment ID
            error_message: Error message
            cloud_provider: Cloud provider
            environment: Environment
            
        Returns:
            Alert instance
        """
        alert = Alert(
            alert_type=AlertType.DEPLOYMENT_FAILURE,
            severity=AlertSeverity.ERROR,
            title=f"Deployment Failed: {deployment_id}",
            message=f"Deployment to {cloud_provider} ({environment}) failed: {error_message}",
            metadata={
                'deployment_id': deployment_id,
                'cloud_provider': cloud_provider,
                'environment': environment,
                'error': error_message
            }
        )
        
        self._send_alert(alert)
        return alert
    
    def alert_deployment_success(
        self,
        deployment_id: str,
        cloud_provider: str,
        environment: str,
        duration: float
    ) -> Alert:
        """
        Send alert for successful deployment
        
        Args:
            deployment_id: Deployment ID
            cloud_provider: Cloud provider
            environment: Environment
            duration: Deployment duration in seconds
            
        Returns:
            Alert instance
        """
        alert = Alert(
            alert_type=AlertType.DEPLOYMENT_SUCCESS,
            severity=AlertSeverity.INFO,
            title=f"Deployment Successful: {deployment_id}",
            message=f"Successfully deployed to {cloud_provider} ({environment}) in {duration:.1f}s",
            metadata={
                'deployment_id': deployment_id,
                'cloud_provider': cloud_provider,
                'environment': environment,
                'duration': duration
            }
        )
        
        self._send_alert(alert)
        return alert
    
    def check_performance_degradation(
        self,
        deployment_id: str,
        duration: float
    ) -> Optional[Alert]:
        """
        Check for performance degradation
        
        Args:
            deployment_id: Deployment ID
            duration: Deployment duration in seconds
            
        Returns:
            Alert if performance degraded, None otherwise
        """
        rules = self.alert_rules['performance']
        if not rules['enabled']:
            return None
        
        max_time = rules['max_deployment_time']
        
        if duration > max_time:
            alert = Alert(
                alert_type=AlertType.PERFORMANCE_DEGRADATION,
                severity=AlertSeverity.WARNING,
                title="Slow Deployment Detected",
                message=f"Deployment took {duration:.1f}s (max: {max_time}s)",
                metadata={
                    'deployment_id': deployment_id,
                    'duration': duration,
                    'max_duration': max_time
                }
            )
            self._send_alert(alert)
            return alert
        
        return None
    
    def _send_alert(self, alert: Alert):
        """
        Send alert through configured channels
        
        Args:
            alert: Alert to send
        """
        # Store in history
        self.alerts_history.append(alert)
        
        # In a real implementation, this would send to:
        # - Email (SMTP)
        # - Slack (webhook)
        # - PagerDuty (API)
        # - Custom webhooks
        
        print(f"[ALERT] {alert.severity.value.upper()}: {alert.title}")
        print(f"        {alert.message}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Alert]:
        """Get recent alerts"""
        return self.alerts_history[-limit:]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity"""
        return [a for a in self.alerts_history if a.severity == severity]
