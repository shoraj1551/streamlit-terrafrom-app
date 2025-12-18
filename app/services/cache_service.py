"""
Cache Service

Provides caching layer using Redis for improved performance.
Caches deployment results, Terraform plans, and frequently accessed data.
"""

from typing import Optional, Any, Callable
from functools import wraps
import json
import hashlib
from app.services.redis_client import get_redis_client
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CacheService:
    """
    Redis-based caching service
    
    Provides caching for deployment results, Terraform plans, and other data.
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache service
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        try:
            self.redis = get_redis_client()
            self.default_ttl = default_ttl
            self.enabled = True
            logger.info("✅ CacheService initialized with Redis backend")
        except Exception as e:
            logger.warning(f"⚠️  Redis not available, caching disabled: {e}")
            self.enabled = False
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and arguments
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create deterministic hash from arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        return f"cache:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.enabled:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return value
            else:
                logger.debug(f"Cache MISS: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache GET error for key '{key}': {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional)
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            self.redis.set(key, value, ttl)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache SET error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache DELETE error for key '{key}': {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "cache:deployment:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            # Get all keys matching pattern
            keys = list(self.redis.client.scan_iter(match=pattern))
            
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Cache INVALIDATE: {pattern} ({deleted} keys)")
                return deleted
            
            return 0
        except Exception as e:
            logger.error(f"Cache INVALIDATE error for pattern '{pattern}': {e}")
            return 0
    
    def cache_deployment_result(self, deployment_id: str, result: dict, ttl: int = 86400):
        """
        Cache deployment result
        
        Args:
            deployment_id: Deployment ID
            result: Deployment result dictionary
            ttl: Time-to-live in seconds (default: 24 hours)
        """
        key = f"cache:deployment:result:{deployment_id}"
        self.set(key, result, ttl)
    
    def get_deployment_result(self, deployment_id: str) -> Optional[dict]:
        """
        Get cached deployment result
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            Cached result or None
        """
        key = f"cache:deployment:result:{deployment_id}"
        return self.get(key)
    
    def cache_terraform_plan(self, config_hash: str, plan_output: str, ttl: int = 3600):
        """
        Cache Terraform plan output
        
        Args:
            config_hash: Hash of Terraform configuration
            plan_output: Plan output
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        key = f"cache:terraform:plan:{config_hash}"
        self.set(key, plan_output, ttl)
    
    def get_terraform_plan(self, config_hash: str) -> Optional[str]:
        """
        Get cached Terraform plan
        
        Args:
            config_hash: Hash of Terraform configuration
            
        Returns:
            Cached plan output or None
        """
        key = f"cache:terraform:plan:{config_hash}"
        return self.get(key)
    
    def invalidate_deployment_cache(self, deployment_id: str):
        """
        Invalidate all cache entries for a deployment
        
        Args:
            deployment_id: Deployment ID
        """
        pattern = f"cache:deployment:*:{deployment_id}"
        self.invalidate_pattern(pattern)
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {'enabled': False}
        
        try:
            info = self.redis.client.info('stats')
            return {
                'enabled': True,
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


def cached(prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache function results
    
    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds (optional)
        
    Usage:
        @cached('user_data', ttl=300)
        def get_user_data(user_id):
            # Expensive operation
            return data
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = CacheService()
            
            # Generate cache key
            cache_key = cache._generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache instance
_cache_service = None


def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
