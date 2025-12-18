"""
Notification Service

Handles user notifications for deployment events.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.services.audit_logger import get_audit_logger, AuditEventType, AuditSeverity
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class NotificationType(str, Enum):
    """Notification types"""
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"
    DEPLOYMENT_CANCELLED = "deployment_cancelled"
    SYSTEM_ALERT = "system_alert"
    SECURITY_ALERT = "security_alert"


class NotificationChannel(str, Enum):
    """Notification channels"""
    EMAIL = "email"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationService:
    """
    Notification service
    
    Sends notifications through multiple channels.
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None
    ):
        """
        Initialize notification service
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        
        self.audit = get_audit_logger()
        
        # In-app notification storage (should be database)
        self._in_app_notifications: Dict[str, List[Dict]] = {}
    
    def send_notification(
        self,
        user_email: str,
        notification_type: NotificationType,
        subject: str,
        message: str,
        channels: List[NotificationChannel] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send notification through specified channels
        
        Args:
            user_email: Recipient email
            notification_type: Type of notification
            subject: Notification subject
            message: Notification message
            channels: Channels to use (default: all)
            metadata: Additional metadata
            
        Returns:
            True if sent successfully
        """
        if channels is None:
            channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
        
        success = True
        
        # Send through each channel
        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                success &= self._send_email(user_email, subject, message)
            elif channel == NotificationChannel.IN_APP:
                success &= self._send_in_app(user_email, notification_type, subject, message, metadata)
            elif channel == NotificationChannel.WEBHOOK:
                success &= self._send_webhook(user_email, notification_type, subject, message, metadata)
        
        # Audit log
        self.audit.log_event(
            event_type=AuditEventType.NOTIFICATION_SENT,
            user_id=user_email,
            details={
                "type": notification_type.value,
                "channels": [c.value for c in channels],
                "success": success
            },
            severity=AuditSeverity.INFO
        )
        
        return success
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        message: str
    ) -> bool:
        """
        Send email notification
        
        Args:
            to_email: Recipient email
            subject: Email subject
            message: Email message
            
        Returns:
            True if sent successfully
        """
        if not self.smtp_host:
            logger.warning("SMTP not configured, skipping email notification")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            
            # HTML version
            html = f"""
            <html>
              <body>
                <h2>{subject}</h2>
                <p>{message}</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                  Infrastructure Platform - Automated Notification
                </p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(message, 'plain'))
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _send_in_app(
        self,
        user_email: str,
        notification_type: NotificationType,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send in-app notification
        
        Args:
            user_email: User email
            notification_type: Notification type
            subject: Subject
            message: Message
            metadata: Additional metadata
            
        Returns:
            True if sent successfully
        """
        try:
            notification = {
                "id": f"notif_{datetime.utcnow().timestamp()}",
                "type": notification_type.value,
                "subject": subject,
                "message": message,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "read": False
            }
            
            if user_email not in self._in_app_notifications:
                self._in_app_notifications[user_email] = []
            
            self._in_app_notifications[user_email].append(notification)
            
            logger.info(f"In-app notification sent to {user_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send in-app notification: {e}")
            return False
    
    def _send_webhook(
        self,
        user_email: str,
        notification_type: NotificationType,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send webhook notification
        
        Args:
            user_email: User email
            notification_type: Notification type
            subject: Subject
            message: Message
            metadata: Additional metadata
            
        Returns:
            True if sent successfully
        """
        # TODO: Implement webhook notifications
        logger.info("Webhook notifications not yet implemented")
        return True
    
    def get_user_notifications(
        self,
        user_email: str,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get user's in-app notifications
        
        Args:
            user_email: User email
            unread_only: Only return unread notifications
            
        Returns:
            List of notifications
        """
        notifications = self._in_app_notifications.get(user_email, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.get('read')]
        
        return notifications
    
    def mark_as_read(
        self,
        user_email: str,
        notification_id: str
    ) -> bool:
        """
        Mark notification as read
        
        Args:
            user_email: User email
            notification_id: Notification ID
            
        Returns:
            True if marked successfully
        """
        notifications = self._in_app_notifications.get(user_email, [])
        
        for notification in notifications:
            if notification.get('id') == notification_id:
                notification['read'] = True
                return True
        
        return False
    
    def notify_deployment_completed(
        self,
        user_email: str,
        deployment_id: str,
        provider: str,
        region: str
    ):
        """
        Send deployment completion notification
        
        Args:
            user_email: User email
            deployment_id: Deployment ID
            provider: Cloud provider
            region: Region
        """
        self.send_notification(
            user_email=user_email,
            notification_type=NotificationType.DEPLOYMENT_COMPLETED,
            subject="Deployment Completed Successfully",
            message=f"Your {provider} deployment in {region} has completed successfully.\n\nDeployment ID: {deployment_id}",
            metadata={
                "deployment_id": deployment_id,
                "provider": provider,
                "region": region
            }
        )
    
    def notify_deployment_failed(
        self,
        user_email: str,
        deployment_id: str,
        provider: str,
        region: str,
        error: str
    ):
        """
        Send deployment failure notification
        
        Args:
            user_email: User email
            deployment_id: Deployment ID
            provider: Cloud provider
            region: Region
            error: Error message
        """
        self.send_notification(
            user_email=user_email,
            notification_type=NotificationType.DEPLOYMENT_FAILED,
            subject="Deployment Failed",
            message=f"Your {provider} deployment in {region} has failed.\n\nDeployment ID: {deployment_id}\nError: {error}",
            metadata={
                "deployment_id": deployment_id,
                "provider": provider,
                "region": region,
                "error": error
            }
        )


# Global service instance
_notification_service = None


def get_notification_service() -> NotificationService:
    """Get global notification service instance"""
    global _notification_service
    if _notification_service is None:
        import os
        _notification_service = NotificationService(
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER"),
            smtp_password=os.getenv("SMTP_PASSWORD")
        )
    return _notification_service
