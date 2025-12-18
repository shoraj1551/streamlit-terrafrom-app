"""
Token Rotation Service

Handles automatic rotation of access and refresh tokens.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.services.auth0_integration import Auth0Service
from app.services.session_manager import get_session_manager
from app.services.audit_logger import get_audit_logger, AuditEventType, AuditSeverity
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TokenRotationService:
    """
    Token rotation service
    
    Automatically rotates tokens before expiration for security.
    """
    
    def __init__(
        self,
        auth0_service: Optional[Auth0Service] = None,
        session_manager: Optional[Any] = None,
        audit_logger: Optional[Any] = None
    ):
        """
        Initialize token rotation service
        
        Args:
            auth0_service: Auth0 service (injected)
            session_manager: Session manager (injected)
            audit_logger: Audit logger (injected)
        """
        self.auth0 = auth0_service or Auth0Service()
        self.session_manager = session_manager or get_session_manager()
        self.audit = audit_logger or get_audit_logger()
        
        # Rotation settings
        self.rotation_threshold_minutes = 15  # Rotate 15 min before expiry
        self.max_token_age_hours = 24  # Force rotation after 24 hours
    
    def should_rotate_token(
        self,
        token_issued_at: datetime,
        token_expires_at: datetime
    ) -> bool:
        """
        Check if token should be rotated
        
        Args:
            token_issued_at: When token was issued
            token_expires_at: When token expires
            
        Returns:
            True if token should be rotated
        """
        now = datetime.utcnow()
        
        # Check if token is close to expiration
        time_until_expiry = token_expires_at - now
        if time_until_expiry < timedelta(minutes=self.rotation_threshold_minutes):
            logger.debug("Token close to expiration, should rotate")
            return True
        
        # Check if token is too old
        token_age = now - token_issued_at
        if token_age > timedelta(hours=self.max_token_age_hours):
            logger.debug("Token too old, should rotate")
            return True
        
        return False
    
    def rotate_token(
        self,
        session_id: str,
        user_email: str,
        refresh_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Rotate access token
        
        Args:
            session_id: Session ID
            user_email: User email
            refresh_token: Current refresh token
            
        Returns:
            New tokens or None if failed
        """
        try:
            # Get new tokens from Auth0
            new_tokens = self.auth0.refresh_access_token(refresh_token)
            
            if not new_tokens:
                logger.error(f"Failed to rotate token for session {session_id}")
                return None
            
            # Update session with new tokens
            self.session_manager.refresh_tokens(
                session_id=session_id,
                new_access_token=new_tokens['access_token'],
                new_refresh_token=new_tokens.get('refresh_token', refresh_token)
            )
            
            # Audit log
            self.audit.log_event(
                event_type=AuditEventType.AUTH_TOKEN_REFRESH,
                user_id=user_email,
                details={
                    "session_id": session_id,
                    "rotation_type": "automatic"
                },
                severity=AuditSeverity.INFO
            )
            
            logger.info(f"Token rotated successfully for session {session_id}")
            
            return new_tokens
            
        except Exception as e:
            logger.error(f"Token rotation error: {e}")
            
            # Audit log failure
            self.audit.log_event(
                event_type=AuditEventType.AUTH_TOKEN_REFRESH,
                user_id=user_email,
                details={
                    "session_id": session_id,
                    "error": str(e),
                    "status": "failed"
                },
                severity=AuditSeverity.ERROR
            )
            
            return None
    
    def rotate_all_expiring_tokens(self) -> int:
        """
        Rotate all tokens that are close to expiration
        
        This should be called periodically (e.g., every 5 minutes)
        
        Returns:
            Number of tokens rotated
        """
        # TODO: Implement batch rotation
        # This would query all active sessions and rotate expiring tokens
        logger.info("Batch token rotation not yet implemented")
        return 0
    
    def force_rotate_user_tokens(
        self,
        user_email: str,
        reason: str = "Security policy"
    ) -> int:
        """
        Force rotation of all tokens for a user
        
        Args:
            user_email: User email
            reason: Rotation reason
            
        Returns:
            Number of sessions rotated
        """
        sessions = self.session_manager.get_user_sessions(user_email)
        rotated = 0
        
        for session in sessions:
            result = self.rotate_token(
                session_id=session['session_id'],
                user_email=user_email,
                refresh_token=session.get('refresh_token', '')
            )
            
            if result:
                rotated += 1
        
        if rotated > 0:
            self.audit.log_event(
                event_type=AuditEventType.AUTH_TOKEN_REFRESH,
                user_id=user_email,
                details={
                    "sessions_rotated": rotated,
                    "reason": reason,
                    "forced": True
                },
                severity=AuditSeverity.WARNING
            )
        
        logger.info(f"Force rotated {rotated} tokens for user {user_email}")
        
        return rotated


# Global service instance
_token_rotation_service = None


def get_token_rotation_service() -> TokenRotationService:
    """Get global token rotation service instance"""
    global _token_rotation_service
    if _token_rotation_service is None:
        _token_rotation_service = TokenRotationService()
    return _token_rotation_service
