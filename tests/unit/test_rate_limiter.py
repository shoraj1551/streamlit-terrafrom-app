"""
Unit Tests for Rate Limiter

Tests rate limiting functionality.
"""

import pytest
import time
from app.middleware.rate_limiter import RateLimiter, RateLimitBucket


class TestRateLimitBucket:
    """Test RateLimitBucket (token bucket algorithm)"""
    
    def test_bucket_creation(self):
        """Test creating a token bucket"""
        bucket = RateLimitBucket(
            capacity=10,
            tokens=10,
            refill_rate=1.0,  # 1 token per second
        )
        
        assert bucket.capacity == 10
        assert bucket.tokens == 10
        assert bucket.refill_rate == 1.0
    
    def test_consume_tokens_success(self):
        """Test consuming tokens when available"""
        bucket = RateLimitBucket(capacity=10, tokens=10, refill_rate=1.0)
        
        # Should succeed
        assert bucket.consume(5)
        assert bucket.tokens == 5
    
    def test_consume_tokens_failure(self):
        """Test consuming tokens when not available"""
        bucket = RateLimitBucket(capacity=10, tokens=3, refill_rate=1.0)
        
        # Should fail (need 5, only have 3)
        assert not bucket.consume(5)
        assert bucket.tokens == 3  # Tokens unchanged
    
    def test_token_refill(self):
        """Test that tokens refill over time"""
        bucket = RateLimitBucket(capacity=10, tokens=5, refill_rate=2.0)  # 2 tokens/sec
        
        # Wait 1 second
        time.sleep(1.1)
        
        # Refill should happen
        bucket.refill()
        
        # Should have ~7 tokens (5 + 2*1)
        assert bucket.tokens >= 6.5
        assert bucket.tokens <= 7.5
    
    def test_refill_does_not_exceed_capacity(self):
        """Test that refill doesn't exceed capacity"""
        bucket = RateLimitBucket(capacity=10, tokens=9, refill_rate=10.0)
        
        # Wait 1 second
        time.sleep(1.1)
        
        bucket.refill()
        
        # Should not exceed capacity
        assert bucket.tokens == 10
    
    def test_time_until_available(self):
        """Test calculating time until tokens available"""
        bucket = RateLimitBucket(capacity=10, tokens=3, refill_rate=2.0)  # 2 tokens/sec
        
        # Need 5 tokens, have 3, need 2 more
        # At 2 tokens/sec, should take 1 second
        time_needed = bucket.time_until_available(5)
        
        assert 0.9 <= time_needed <= 1.1


class TestRateLimiter:
    """Test RateLimiter"""
    
    def test_rate_limiter_creation(self):
        """Test creating rate limiter"""
        limiter = RateLimiter()
        
        assert limiter.limits is not None
        assert "default" in limiter.limits
    
    def test_check_rate_limit_allows_first_request(self):
        """Test that first request is allowed"""
        limiter = RateLimiter()
        
        allowed, retry_after = limiter.check_rate_limit("user123", "default")
        
        assert allowed
        assert retry_after is None
    
    def test_check_rate_limit_blocks_after_burst(self):
        """Test that requests are blocked after burst capacity"""
        limiter = RateLimiter()
        
        # Get burst capacity for default action
        _, burst_capacity = limiter.limits["default"]
        
        # Consume all tokens
        for i in range(burst_capacity):
            allowed, _ = limiter.check_rate_limit("user123", "default")
            assert allowed, f"Request {i+1} should be allowed"
        
        # Next request should be blocked
        allowed, retry_after = limiter.check_rate_limit("user123", "default")
        
        assert not allowed
        assert retry_after is not None
        assert retry_after > 0
    
    def test_different_users_independent_limits(self):
        """Test that different users have independent rate limits"""
        limiter = RateLimiter()
        
        # User1 consumes all tokens
        _, burst_capacity = limiter.limits["default"]
        for _ in range(burst_capacity):
            limiter.check_rate_limit("user1", "default")
        
        # User1 should be blocked
        allowed, _ = limiter.check_rate_limit("user1", "default")
        assert not allowed
        
        # User2 should still be allowed
        allowed, _ = limiter.check_rate_limit("user2", "default")
        assert allowed
    
    def test_different_actions_independent_limits(self):
        """Test that different actions have independent limits"""
        limiter = RateLimiter()
        
        # Consume all tokens for "login" action
        _, burst_capacity = limiter.limits["login"]
        for _ in range(burst_capacity):
            limiter.check_rate_limit("user123", "login")
        
        # Login should be blocked
        allowed, _ = limiter.check_rate_limit("user123", "login")
        assert not allowed
        
        # But "deployment" should still be allowed
        allowed, _ = limiter.check_rate_limit("user123", "deployment")
        assert allowed
    
    def test_reset_limit(self):
        """Test resetting rate limit"""
        limiter = RateLimiter()
        
        # Consume all tokens
        _, burst_capacity = limiter.limits["default"]
        for _ in range(burst_capacity):
            limiter.check_rate_limit("user123", "default")
        
        # Should be blocked
        allowed, _ = limiter.check_rate_limit("user123", "default")
        assert not allowed
        
        # Reset limit
        limiter.reset_limit("user123", "default")
        
        # Should be allowed again
        allowed, _ = limiter.check_rate_limit("user123", "default")
        assert allowed
    
    def test_get_remaining_tokens(self):
        """Test getting remaining tokens"""
        limiter = RateLimiter()
        
        # Get initial capacity
        _, burst_capacity = limiter.limits["default"]
        
        # Check remaining before any requests
        remaining = limiter.get_remaining("user123", "default")
        assert remaining == burst_capacity
        
        # Consume some tokens
        limiter.check_rate_limit("user123", "default", tokens=5)
        
        # Check remaining
        remaining = limiter.get_remaining("user123", "default")
        assert remaining == burst_capacity - 5
