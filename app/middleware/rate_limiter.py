"""
Rate Limiting Middleware

Implements rate limiting to prevent abuse and DoS attacks.
Supports per-user and per-IP rate limiting with configurable limits.

Features:
- Token bucket algorithm
- Per-user rate limiting
- Per-IP rate limiting
- Configurable time windows
- Redis backend for distributed systems
- In-memory fallback for single instance
"""

import time
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import streamlit as st
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting"""
    capacity: int  # Maximum tokens
    tokens: float  # Current tokens
    refill_rate: float  # Tokens per second
    last_refill: float = field(default_factory=time.time)
    
    def refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + (elapsed * self.refill_rate)
        )
        
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens
        
        Returns:
            True if tokens available, False otherwise
        """
        self.refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def time_until_available(self, tokens: int = 1) -> float:
        """
        Calculate time until tokens will be available
        
        Returns:
            Seconds until tokens available
        """
        self.refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class RateLimiter:
    """
    Rate limiter using token bucket algorithm
    
    Supports multiple rate limit tiers and automatic cleanup of old buckets.
    """
    
    def __init__(self):
        """Initialize rate limiter"""
        # In-memory storage (use Redis for distributed systems)
        self._buckets: Dict[str, RateLimitBucket] = {}
        self._last_cleanup = time.time()
        
        # Rate limit configurations
        self.limits = {
            # Action: (requests_per_minute, burst_capacity)
            "login": (5, 10),  # 5 req/min, burst of 10
            "deployment": (10, 20),  # 10 req/min, burst of 20
            "config_upload": (20, 40),  # 20 req/min, burst of 40
            "api_call": (60, 100),  # 60 req/min, burst of 100
            "default": (30, 60),  # 30 req/min, burst of 60
        }
        
        logger.info("Initialized RateLimiter")
    
    def _get_bucket_key(self, identifier: str, action: str) -> str:
        """Generate bucket key from identifier and action"""
        return f"{identifier}:{action}"
    
    def _get_or_create_bucket(self, key: str, action: str) -> RateLimitBucket:
        """Get existing bucket or create new one"""
        if key not in self._buckets:
            # Get rate limit config for action
            requests_per_minute, burst_capacity = self.limits.get(
                action,
                self.limits["default"]
            )
            
            # Create new bucket
            self._buckets[key] = RateLimitBucket(
                capacity=burst_capacity,
                tokens=burst_capacity,  # Start with full capacity
                refill_rate=requests_per_minute / 60.0,  # Convert to per-second
            )
        
        return self._buckets[key]
    
    def check_rate_limit(
        self,
        identifier: str,
        action: str = "default",
        tokens: int = 1,
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if request is within rate limit
        
        Args:
            identifier: User ID, IP address, or other identifier
            action: Action being rate limited
            tokens: Number of tokens to consume (default: 1)
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        # Periodic cleanup of old buckets
        self._cleanup_old_buckets()
        
        # Get or create bucket
        key = self._get_bucket_key(identifier, action)
        bucket = self._get_or_create_bucket(key, action)
        
        # Try to consume tokens
        if bucket.consume(tokens):
            logger.debug(f"Rate limit OK: {identifier} - {action}")
            return True, None
        else:
            # Calculate retry-after time
            retry_after = bucket.time_until_available(tokens)
            logger.warning(f"Rate limit exceeded: {identifier} - {action} (retry after {retry_after:.1f}s)")
            return False, retry_after
    
    def _cleanup_old_buckets(self, max_age_seconds: int = 3600):
        """Remove buckets that haven't been used recently"""
        now = time.time()
        
        # Only cleanup every 5 minutes
        if now - self._last_cleanup < 300:
            return
        
        # Find old buckets
        old_keys = [
            key for key, bucket in self._buckets.items()
            if now - bucket.last_refill > max_age_seconds
        ]
        
        # Remove old buckets
        for key in old_keys:
            del self._buckets[key]
        
        if old_keys:
            logger.info(f"Cleaned up {len(old_keys)} old rate limit buckets")
        
        self._last_cleanup = now
    
    def reset_limit(self, identifier: str, action: str = "default"):
        """Reset rate limit for identifier/action"""
        key = self._get_bucket_key(identifier, action)
        if key in self._buckets:
            del self._buckets[key]
            logger.info(f"Reset rate limit: {identifier} - {action}")
    
    def get_remaining(self, identifier: str, action: str = "default") -> int:
        """Get remaining tokens for identifier/action"""
        key = self._get_bucket_key(identifier, action)
        if key in self._buckets:
            bucket = self._buckets[key]
            bucket.refill()
            return int(bucket.tokens)
        else:
            # Return full capacity if no bucket exists
            _, burst_capacity = self.limits.get(action, self.limits["default"])
            return burst_capacity


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def check_rate_limit(action: str = "default", tokens: int = 1) -> bool:
    """
    Check rate limit for current user/IP
    
    Args:
        action: Action being rate limited
        tokens: Number of tokens to consume
        
    Returns:
        True if within rate limit, False otherwise
    """
    rate_limiter = get_rate_limiter()
    
    # Get identifier (user ID or IP address)
    from app.middleware.auth_middleware import get_current_user
    user = get_current_user()
    
    if user:
        identifier = f"user:{user.user_id}"
    else:
        # Use IP address for unauthenticated requests
        # Note: Streamlit doesn't expose client IP directly
        # In production, use reverse proxy headers (X-Forwarded-For)
        identifier = "ip:unknown"
    
    # Check rate limit
    allowed, retry_after = rate_limiter.check_rate_limit(identifier, action, tokens)
    
    if not allowed:
        # Show error to user
        st.error(f"⚠️ Rate limit exceeded. Please try again in {int(retry_after)} seconds.")
        st.stop()
    
    return allowed


def rate_limit(action: str = "default", tokens: int = 1):
    """
    Decorator for rate limiting functions
    
    Usage:
        @rate_limit(action="deployment", tokens=1)
        def deploy_infrastructure():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            check_rate_limit(action, tokens)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def show_rate_limit_info():
    """Display rate limit information in sidebar"""
    rate_limiter = get_rate_limiter()
    
    from app.middleware.auth_middleware import get_current_user
    user = get_current_user()
    
    if user:
        identifier = f"user:{user.user_id}"
    else:
        return  # Don't show for unauthenticated users
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⏱️ Rate Limits")
        
        # Show remaining requests for common actions
        for action in ["deployment", "config_upload", "api_call"]:
            remaining = rate_limiter.get_remaining(identifier, action)
            limit = rate_limiter.limits.get(action, rate_limiter.limits["default"])[1]
            
            st.progress(remaining / limit, text=f"{action}: {remaining}/{limit}")
