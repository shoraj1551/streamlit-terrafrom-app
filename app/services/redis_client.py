"""
Redis Client Service

Provides Redis connection and common operations for caching, 
session management, and rate limiting.
"""

import redis
import os
from typing import Optional, Any, Dict, List
import json
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RedisClient:
    """
    Redis client wrapper with connection pooling and error handling
    """
    
    def __init__(self):
        """Initialize Redis client from environment configuration"""
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD")
        
        # Create connection pool
        pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            max_connections=50
        )
        
        self.client = redis.Redis(connection_pool=pool)
        
        # Test connection
        try:
            self.client.ping()
            logger.info(f"✅ Connected to Redis at {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set key-value pair with optional TTL
        
        Args:
            key: Redis key
            value: Value to store (will be JSON-encoded if dict/list)
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful
        """
        try:
            # Serialize complex types to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value by key
        
        Args:
            key: Redis key
            
        Returns:
            Value (JSON-decoded if applicable) or None
        """
        try:
            value = self.client.get(key)
            
            if value is None:
                return None
            
            # Try to decode JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None
    
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys
        
        Args:
            keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists
        
        Args:
            key: Redis key
            
        Returns:
            True if key exists
        """
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on key
        
        Args:
            key: Redis key
            seconds: Seconds until expiration
            
        Returns:
            True if successful
        """
        try:
            return self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment key value
        
        Args:
            key: Redis key
            amount: Amount to increment by
            
        Returns:
            New value or None on error
        """
        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for key '{key}': {e}")
            return None
    
    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Decrement key value
        
        Args:
            key: Redis key
            amount: Amount to decrement by
            
        Returns:
            New value or None on error
        """
        try:
            return self.client.decr(key, amount)
        except Exception as e:
            logger.error(f"Redis DECR error for key '{key}': {e}")
            return None
    
    def hset(self, name: str, key: str, value: Any) -> bool:
        """
        Set hash field
        
        Args:
            name: Hash name
            key: Field key
            value: Field value
            
        Returns:
            True if successful
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.client.hset(name, key, value)
        except Exception as e:
            logger.error(f"Redis HSET error for hash '{name}': {e}")
            return False
    
    def hget(self, name: str, key: str) -> Optional[Any]:
        """
        Get hash field
        
        Args:
            name: Hash name
            key: Field key
            
        Returns:
            Field value or None
        """
        try:
            value = self.client.hget(name, key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis HGET error for hash '{name}': {e}")
            return None
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """
        Get all hash fields
        
        Args:
            name: Hash name
            
        Returns:
            Dictionary of all fields
        """
        try:
            data = self.client.hgetall(name)
            
            # Try to decode JSON values
            result = {}
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            
            return result
        except Exception as e:
            logger.error(f"Redis HGETALL error for hash '{name}': {e}")
            return {}
    
    def sadd(self, key: str, *members: str) -> int:
        """
        Add members to set
        
        Args:
            key: Set key
            members: Members to add
            
        Returns:
            Number of members added
        """
        try:
            return self.client.sadd(key, *members)
        except Exception as e:
            logger.error(f"Redis SADD error for set '{key}': {e}")
            return 0
    
    def srem(self, key: str, *members: str) -> int:
        """
        Remove members from set
        
        Args:
            key: Set key
            members: Members to remove
            
        Returns:
            Number of members removed
        """
        try:
            return self.client.srem(key, *members)
        except Exception as e:
            logger.error(f"Redis SREM error for set '{key}': {e}")
            return 0
    
    def smembers(self, key: str) -> set:
        """
        Get all set members
        
        Args:
            key: Set key
            
        Returns:
            Set of members
        """
        try:
            return self.client.smembers(key)
        except Exception as e:
            logger.error(f"Redis SMEMBERS error for set '{key}': {e}")
            return set()
    
    def scard(self, key: str) -> int:
        """
        Get set cardinality (size)
        
        Args:
            key: Set key
            
        Returns:
            Number of members in set
        """
        try:
            return self.client.scard(key)
        except Exception as e:
            logger.error(f"Redis SCARD error for set '{key}': {e}")
            return 0
    
    def zadd(self, name: str, mapping: Dict[str, float]) -> int:
        """
        Add members to sorted set
        
        Args:
            name: Sorted set name
            mapping: Dictionary of member:score pairs
            
        Returns:
            Number of members added
        """
        try:
            return self.client.zadd(name, mapping)
        except Exception as e:
            logger.error(f"Redis ZADD error for sorted set '{name}': {e}")
            return 0
    
    def zpopmax(self, name: str, count: int = 1) -> List[tuple]:
        """
        Remove and return highest scoring members
        
        Args:
            name: Sorted set name
            count: Number of members to pop
            
        Returns:
            List of (member, score) tuples
        """
        try:
            return self.client.zpopmax(name, count)
        except Exception as e:
            logger.error(f"Redis ZPOPMAX error for sorted set '{name}': {e}")
            return []
    
    def ping(self) -> bool:
        """
        Test Redis connection
        
        Returns:
            True if connected
        """
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis PING error: {e}")
            return False
    
    def flushdb(self):
        """
        Clear all keys in current database (USE WITH CAUTION!)
        """
        logger.warning("⚠️  Flushing Redis database!")
        return self.client.flushdb()


# Global Redis client instance
_redis_client = None


def get_redis_client() -> RedisClient:
    """
    Get global Redis client instance
    
    Returns:
        RedisClient instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
