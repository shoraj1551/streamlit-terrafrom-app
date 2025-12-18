"""
Authentication Service - Business Logic Layer

Handles authentication, authorization, and session management.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.services.auth0_integration import Auth0Service
from app.services.session_manager import get_session_manager
from app.services.audit_logger import get_audit_logger, AuditEventType, AuditSeverity
from app.core.circuit_breaker import CircuitBreakerError
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthenticationService:
    """
    Authentication and authorization business logic
    
    Separates auth logic from UI/API layers.
    """
    
    def __init__(
        self,
        auth0_service: Optional[Auth0Service] = None,
        session_manager: Optional[Any] = None,
        audit_logger: Optional[Any] = None
    ):
        """
        Initialize authentication service
        
        Args:
            auth0_service: Auth0 integration service (injected)
            session_manager: Session manager (injected)
            audit_logger: Audit logger (injected)
        """
        self.auth0 = auth0_service or Auth0Service()
        self.session_manager = session_manager or get_session_manager()
        self.audit = audit_logger or get_audit_logger()
    
    def login(self, email: str, password: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Authenticate user
        
        Args:
            email: User email
            password: User password
            ip_address: Client IP address
            
        Returns:
            Authentication result with tokens
            
        Raises:
            ValueError: If authentication fails
            CircuitBreakerError: If Auth0 is unavailable
        """
        try:
            # Authenticate with Auth0
            auth_result = self.auth0.authenticate(email, password)
            
            if not auth_result or 'access_token' not in auth_result:
                # Log failed attempt
                self.audit.log_event(
                    event_type=AuditEventType.AUTH_LOGIN_FAILED,
                    user_id=email,
                    details={"reason": "Invalid credentials"},
                    severity=AuditSeverity.WARNING,
                    ip_address=ip_address
                )
                raise ValueError("Authentication failed")
            
            # Create session
            session_id = self.session_manager.create_session(
                user_id=auth_result.get('user_id', email),
                user_email=email,
                access_token=auth_result['access_token'],
                refresh_token=auth_result.get('refresh_token'),
                id_token=auth_result.get('id_token'),
                user_data=auth_result.get('user_info', {})
            )
            
            # Log successful login
            self.audit.log_event(
                event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
                user_id=email,
                details={"session_id": session_id},
                severity=AuditSeverity.INFO,
                ip_address=ip_address
            )
            
            logger.info(f"User logged in successfully: {email}")
            
            return {
                "success": True,
                "session_id": session_id,
                "access_token": auth_result['access_token'],
                "user_info": auth_result.get('user_info', {})
            }
            
        except CircuitBreakerError as e:
            logger.error(f"Auth0 unavailable: {e}")
            self.audit.log_event(
                event_type=AuditEventType.AUTH_LOGIN_FAILED,
                user_id=email,
                details={"reason": "Auth0 unavailable", "error": str(e)},
                severity=AuditSeverity.ERROR,
                ip_address=ip_address
            )
            raise ValueError("Authentication service temporarily unavailable")
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise
    
    def logout(self, session_id: str, user_email: str, reason: str = "User logout") -> bool:
        """
        Logout user
        
        Args:
            session_id: Session ID
            user_email: User email
            reason: Logout reason
            
        Returns:
            True if successful
        """
        # Revoke session
        success = self.session_manager.revoke_session(session_id, reason)
        
        if success:
            # Log logout
            self.audit.log_event(
                event_type=AuditEventType.AUTH_LOGOUT,
                user_id=user_email,
                details={"session_id": session_id, "reason": reason},
                severity=AuditSeverity.INFO
            )
            
            logger.info(f"User logged out: {user_email}")
        
        return success
    
    def verify_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Verify and retrieve session
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if invalid
        """
        session = self.session_manager.get_session(session_id)
        
        if not session:
            logger.debug(f"Invalid session: {session_id}")
            return None
        
        # Update last activity
        self.session_manager.update_activity(session_id)
        
        return session
    
    def refresh_token(self, session_id: str, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token
        
        Args:
            session_id: Session ID
            refresh_token: Refresh token
            
        Returns:
            New tokens or None if failed
        """
        try:
            # Refresh with Auth0
            new_tokens = self.auth0.refresh_access_token(refresh_token)
            
            if not new_tokens:
                return None
            
            # Update session
            self.session_manager.refresh_tokens(
                session_id=session_id,
                new_access_token=new_tokens['access_token'],
                new_refresh_token=new_tokens.get('refresh_token')
            )
            
            logger.info(f"Tokens refreshed for session: {session_id}")
            
            return new_tokens
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    def check_permission(
        self,
        user_email: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if user has permission for action on resource
        
        Args:
            user_email: User email
            resource: Resource type (deployment, config, etc.)
            action: Action (read, write, delete, etc.)
            
        Returns:
            True if permitted
        """
        # TODO: Implement RBAC
        # For now, all authenticated users have all permissions
        # This should be replaced with proper role-based access control
        
        logger.debug(f"Permission check: {user_email} -> {action} on {resource}")
        return True
    
    def get_user_sessions(self, user_email: str) -> list:
        """
        Get all active sessions for user
        
        Args:
            user_email: User email
            
        Returns:
            List of session dictionaries
        """
        return self.session_manager.get_user_sessions(user_email)
    
    def revoke_all_sessions(
        self,
        user_email: str,
        reason: str = "Security: All sessions revoked"
    ) -> int:
        """
        Revoke all sessions for user
        
        Args:
            user_email: User email
            reason: Revocation reason
            
        Returns:
            Number of sessions revoked
        """
        count = self.session_manager.revoke_all_user_sessions(user_email, reason)
        
        if count > 0:
            self.audit.log_event(
                event_type=AuditEventType.AUTH_LOGOUT,
                user_id=user_email,
                details={"sessions_revoked": count, "reason": reason},
                severity=AuditSeverity.WARNING
            )
            
            logger.warning(f"Revoked {count} sessions for user: {user_email}")
        
        return count


# Global service instance (will be replaced with DI)
_auth_service = None


def get_auth_service() -> AuthenticationService:
    """Get global authentication service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service
