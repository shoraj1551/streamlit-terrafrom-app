"""
Distributed Lock using Redis

Prevents race conditions in distributed systems using Redis-based locking.
"""

import redis
import time
import uuid
from contextlib import contextmanager
from typing import Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DistributedLock:
    """
    Distributed lock implementation using Redis
    
    Provides mutex synchronization across multiple processes/servers.
    Uses Redis SET with NX and EX options for atomic lock acquisition.
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        lock_name: str,
        timeout: int = 10,
        blocking: bool = True,
        blocking_timeout: Optional[int] = None
    ):
        """
        Initialize distributed lock
        
        Args:
            redis_client: Redis client instance
            lock_name: Name of the lock
            timeout: Lock expiration timeout in seconds
            blocking: Whether to block waiting for lock
            blocking_timeout: Max time to wait for lock (None = infinite)
        """
        self.redis = redis_client
        self.lock_name = f"lock:{lock_name}"
        self.timeout = timeout
        self.blocking = blocking
        self.blocking_timeout = blocking_timeout
        self.identifier = str(uuid.uuid4())
        self.acquired = False
    
    def acquire(self) -> bool:
        """
        Acquire lock
        
        Returns:
            True if lock acquired, False otherwise
        """
        end_time = None
        if self.blocking and self.blocking_timeout is not None:
            end_time = time.time() + self.blocking_timeout
        
        while True:
            # Try to acquire lock atomically
            # SET key value NX EX timeout
            acquired = self.redis.set(
                self.lock_name,
                self.identifier,
                nx=True,  # Only set if not exists
                ex=self.timeout  # Expiration time
            )
            
            if acquired:
                self.acquired = True
                logger.debug(f"Acquired lock: {self.lock_name}")
                return True
            
            # If not blocking, return immediately
            if not self.blocking:
                logger.debug(f"Failed to acquire lock (non-blocking): {self.lock_name}")
                return False
            
            # Check if blocking timeout exceeded
            if end_time and time.time() >= end_time:
                logger.warning(f"Lock acquisition timeout: {self.lock_name}")
                return False
            
            # Wait a bit before retrying
            time.sleep(0.001)  # 1ms
    
    def release(self) -> bool:
        """
        Release lock
        
        Returns:
            True if lock released, False if not held
        """
        if not self.acquired:
            logger.warning(f"Attempted to release unacquired lock: {self.lock_name}")
            return False
        
        # Use Lua script for atomic check-and-delete
        # Only delete if the lock is still held by this identifier
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = self.redis.eval(lua_script, 1, self.lock_name, self.identifier)
        
        if result:
            self.acquired = False
            logger.debug(f"Released lock: {self.lock_name}")
            return True
        else:
            logger.warning(f"Lock was already released or expired: {self.lock_name}")
            self.acquired = False
            return False
    
    def extend(self, additional_time: int) -> bool:
        """
        Extend lock expiration time
        
        Args:
            additional_time: Additional seconds to add
            
        Returns:
            True if extended successfully
        """
        if not self.acquired:
            return False
        
        # Use Lua script to atomically check and extend
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        
        result = self.redis.eval(
            lua_script,
            1,
            self.lock_name,
            self.identifier,
            self.timeout + additional_time
        )
        
        return bool(result)
    
    def __enter__(self):
        """Context manager entry"""
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock: {self.lock_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
        return False  # Don't suppress exceptions
    
    @contextmanager
    def __call__(self):
        """
        Alternative context manager usage
        
        Usage:
            lock = DistributedLock(redis, "my_lock")
            with lock():
                # Critical section
                pass
        """
        acquired = self.acquire()
        try:
            yield acquired
        finally:
            if acquired:
                self.release()


class ReentrantDistributedLock(DistributedLock):
    """
    Reentrant distributed lock
    
    Allows same process to acquire lock multiple times.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.acquisition_count = 0
    
    def acquire(self) -> bool:
        """Acquire lock (reentrant)"""
        # Check if we already hold the lock
        current_holder = self.redis.get(self.lock_name)
        
        if current_holder == self.identifier:
            # We already hold the lock
            self.acquisition_count += 1
            logger.debug(
                f"Reentrant lock acquisition: {self.lock_name} "
                f"(count: {self.acquisition_count})"
            )
            return True
        
        # Try to acquire normally
        if super().acquire():
            self.acquisition_count = 1
            return True
        
        return False
    
    def release(self) -> bool:
        """Release lock (reentrant)"""
        if self.acquisition_count > 1:
            self.acquisition_count -= 1
            logger.debug(
                f"Reentrant lock partial release: {self.lock_name} "
                f"(count: {self.acquisition_count})"
            )
            return True
        
        # Final release
        if super().release():
            self.acquisition_count = 0
            return True
        
        return False
