"""
Session Management Service

Manages user sessions with Redis backend, integrating with Auth0 tokens.
Provides session storage, refresh, and revocation capabilities.
"""

import os
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.services.redis_client import get_redis_client
from app.services.encryption import EncryptionService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SessionManager:
    """
    Redis-based session manager for Auth0 integration
    
    Stores and manages user sessions with automatic expiration and refresh.
    """
    
    def __init__(self):
        """Initialize session manager"""
        try:
            self.redis = get_redis_client()
            self.encryption = EncryptionService()
            self.session_ttl = int(os.getenv("SESSION_TTL", 3600))  # 1 hour default
            self.refresh_token_ttl = int(os.getenv("REFRESH_TOKEN_TTL", 2592000))  # 30 days
            logger.info("✅ SessionManager initialized with Redis backend")
        except Exception as e:
            logger.error(f"❌ Failed to initialize SessionManager: {e}")
            raise
    
    def create_session(
        self,
        user_id: str,
        user_email: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        id_token: Optional[str] = None,
        user_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create new user session
        
        Args:
            user_id: User ID (Auth0 sub)
            user_email: User email
            access_token: Auth0 access token
            refresh_token: Auth0 refresh token (optional)
            id_token: Auth0 ID token (optional)
            user_data: Additional user data (optional)
            
        Returns:
            Session ID
        """
        import secrets
        
        # Generate session ID
        session_id = f"sess_{secrets.token_urlsafe(32)}"
        
        # Prepare session data
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'user_email': user_email,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'is_active': True,
            'user_data': user_data or {}
        }
        
        # Encrypt sensitive tokens
        encrypted_data = {
            'access_token': self.encryption.encrypt(access_token),
            'refresh_token': self.encryption.encrypt(refresh_token) if refresh_token else None,
            'id_token': self.encryption.encrypt(id_token) if id_token else None
        }
        
        # Store session data in Redis
        session_key = f"session:{session_id}"
        self.redis.hset(session_key, 'data', json.dumps(session_data))
        self.redis.hset(session_key, 'tokens', json.dumps(encrypted_data))
        self.redis.expire(session_key, self.session_ttl)
        
        # Store user-to-session mapping
        user_sessions_key = f"user_sessions:{user_id}"
        self.redis.sadd(user_sessions_key, session_id)
        self.redis.expire(user_sessions_key, self.refresh_token_ttl)
        
        logger.info(f"Created session {session_id} for user {user_email}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found/expired
        """
        session_key = f"session:{session_id}"
        
        if not self.redis.exists(session_key):
            return None
        
        # Get session data
        data_str = self.redis.hget(session_key, 'data')
        tokens_str = self.redis.hget(session_key, 'tokens')
        
        if not data_str:
            return None
        
        session_data = json.loads(data_str)
        
        # Check if session is active
        if not session_data.get('is_active', False):
            return None
        
        # Decrypt tokens
        if tokens_str:
            encrypted_tokens = json.loads(tokens_str)
            session_data['access_token'] = self.encryption.decrypt(encrypted_tokens['access_token'])
            
            if encrypted_tokens.get('refresh_token'):
                session_data['refresh_token'] = self.encryption.decrypt(encrypted_tokens['refresh_token'])
            
            if encrypted_tokens.get('id_token'):
                session_data['id_token'] = self.encryption.decrypt(encrypted_tokens['id_token'])
        
        return session_data
    
    def update_session_activity(self, session_id: str) -> bool:
        """
        Update session last activity timestamp
        
        Args:
            session_id: Session ID
            
        Returns:
            True if updated successfully
        """
        session_key = f"session:{session_id}"
        
        if not self.redis.exists(session_key):
            return False
        
        # Get current session data
        data_str = self.redis.hget(session_key, 'data')
        if not data_str:
            return False
        
        session_data = json.loads(data_str)
        session_data['last_activity'] = datetime.utcnow().isoformat()
        
        # Update session data
        self.redis.hset(session_key, 'data', json.dumps(session_data))
        
        # Extend TTL
        self.redis.expire(session_key, self.session_ttl)
        
        return True
    
    def refresh_session_tokens(
        self,
        session_id: str,
        new_access_token: str,
        new_refresh_token: Optional[str] = None
    ) -> bool:
        """
        Refresh session tokens
        
        Args:
            session_id: Session ID
            new_access_token: New access token
            new_refresh_token: New refresh token (optional)
            
        Returns:
            True if refreshed successfully
        """
        session_key = f"session:{session_id}"
        
        if not self.redis.exists(session_key):
            return False
        
        # Get current tokens
        tokens_str = self.redis.hget(session_key, 'tokens')
        if not tokens_str:
            return False
        
        encrypted_tokens = json.loads(tokens_str)
        
        # Update tokens
        encrypted_tokens['access_token'] = self.encryption.encrypt(new_access_token)
        
        if new_refresh_token:
            encrypted_tokens['refresh_token'] = self.encryption.encrypt(new_refresh_token)
        
        # Save updated tokens
        self.redis.hset(session_key, 'tokens', json.dumps(encrypted_tokens))
        
        # Update activity
        self.update_session_activity(session_id)
        
        logger.info(f"Refreshed tokens for session {session_id}")
        
        return True
    
    def revoke_session(self, session_id: str, reason: Optional[str] = None) -> bool:
        """
        Revoke session
        
        Args:
            session_id: Session ID
            reason: Revocation reason (optional)
            
        Returns:
            True if revoked successfully
        """
        session_key = f"session:{session_id}"
        
        if not self.redis.exists(session_key):
            return False
        
        # Get session data
        data_str = self.redis.hget(session_key, 'data')
        if not data_str:
            return False
        
        session_data = json.loads(data_str)
        
        # Mark as inactive
        session_data['is_active'] = False
        session_data['revoked_at'] = datetime.utcnow().isoformat()
        session_data['revocation_reason'] = reason
        
        # Update session
        self.redis.hset(session_key, 'data', json.dumps(session_data))
        
        # Remove from user sessions
        user_id = session_data.get('user_id')
        if user_id:
            user_sessions_key = f"user_sessions:{user_id}"
            self.redis.srem(user_sessions_key, session_id)
        
        logger.info(f"Revoked session {session_id}: {reason}")
        
        return True
    
    def revoke_all_user_sessions(self, user_id: str, reason: Optional[str] = None) -> int:
        """
        Revoke all sessions for a user
        
        Args:
            user_id: User ID
            reason: Revocation reason (optional)
            
        Returns:
            Number of sessions revoked
        """
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = self.redis.smembers(user_sessions_key)
        
        revoked_count = 0
        for session_id in session_ids:
            if self.revoke_session(session_id, reason):
                revoked_count += 1
        
        logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
        
        return revoked_count
    
    def get_user_sessions(self, user_id: str) -> list:
        """
        Get all active sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of session data
        """
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = self.redis.smembers(user_sessions_key)
        
        sessions = []
        for session_id in session_ids:
            session_data = self.get_session(session_id)
            if session_data and session_data.get('is_active'):
                # Remove sensitive tokens from response
                session_data.pop('access_token', None)
                session_data.pop('refresh_token', None)
                session_data.pop('id_token', None)
                sessions.append(session_data)
        
        return sessions
    
    def cleanup_expired_sessions(self) -> int:
        """
        Cleanup expired sessions (called by background task)
        
        Returns:
            Number of sessions cleaned up
        """
        # Redis automatically expires keys with TTL
        # This is a placeholder for additional cleanup logic if needed
        logger.info("Session cleanup completed (handled by Redis TTL)")
        return 0


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
