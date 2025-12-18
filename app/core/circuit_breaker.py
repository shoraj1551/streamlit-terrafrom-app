"""
Circuit Breaker Pattern Implementation

Prevents cascading failures by failing fast when external services are down.
Based on Martin Fowler's Circuit Breaker pattern.
"""

from enum import Enum
from typing import Callable, Any, Optional, Type
from datetime import datetime, timedelta
import time
from functools import wraps
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is OPEN"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker implementation
    
    Monitors failures and opens circuit when threshold is reached.
    Automatically attempts to close after timeout period.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        expected_exception: Type[Exception] = Exception,
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker
        
        Args:
            name: Circuit breaker name (for logging/metrics)
            failure_threshold: Number of failures before opening
            timeout_seconds: Seconds to wait before attempting reset
            expected_exception: Exception type to catch
            half_open_max_calls: Max calls to allow in HALF_OPEN state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.expected_exception = expected_exception
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is OPEN
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                logger.warning(f"Circuit breaker '{self.name}' is OPEN - rejecting call")
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable. Retry after {self._time_until_retry()}s"
                )
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                logger.warning(
                    f"Circuit breaker '{self.name}' HALF_OPEN limit reached - "
                    f"reopening circuit"
                )
                self.state = CircuitState.OPEN
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is OPEN")
            
            self.half_open_calls += 1
        
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            self._on_success(duration)
            return result
            
        except self.expected_exception as e:
            self._on_failure(e)
            raise
        except Exception as e:
            # Unexpected exception - don't count as failure
            logger.error(f"Unexpected exception in circuit breaker '{self.name}': {e}")
            raise
    
    def _on_success(self, duration: float):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                f"Circuit breaker '{self.name}' HALF_OPEN success "
                f"({self.success_count}/{self.half_open_max_calls})"
            )
            
            if self.success_count >= self.half_open_max_calls:
                logger.info(f"Circuit breaker '{self.name}' closing - service recovered")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        else:
            # Reset failure count on success
            if self.failure_count > 0:
                logger.debug(f"Circuit breaker '{self.name}' resetting failure count")
                self.failure_count = 0
    
    def _on_failure(self, exception: Exception):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(
            f"Circuit breaker '{self.name}' failure "
            f"({self.failure_count}/{self.failure_threshold}): {str(exception)}"
        )
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit breaker '{self.name}' failed in HALF_OPEN - reopening")
            self.state = CircuitState.OPEN
            self.success_count = 0
        elif self.failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit breaker '{self.name}' OPENING - "
                f"threshold reached ({self.failure_count} failures)"
            )
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return False
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure > timedelta(seconds=self.timeout_seconds)
    
    def _time_until_retry(self) -> int:
        """Calculate seconds until retry is allowed"""
        if not self.last_failure_time:
            return 0
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        timeout_delta = timedelta(seconds=self.timeout_seconds)
        
        if time_since_failure >= timeout_delta:
            return 0
        
        remaining = timeout_delta - time_since_failure
        return int(remaining.total_seconds())
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "time_until_retry": self._time_until_retry() if self.state == CircuitState.OPEN else 0
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        logger.info(f"Circuit breaker '{self.name}' manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout_seconds: int = 60,
    expected_exception: Type[Exception] = Exception
):
    """
    Decorator for circuit breaker pattern
    
    Usage:
        @circuit_breaker('auth0', failure_threshold=3, timeout_seconds=30)
        def call_auth0_api():
            # API call that might fail
            pass
    """
    cb = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        timeout_seconds=timeout_seconds,
        expected_exception=expected_exception
    )
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        
        # Attach circuit breaker to function for inspection
        wrapper.circuit_breaker = cb
        return wrapper
    
    return decorator


# Global circuit breakers registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """Get circuit breaker by name"""
    return _circuit_breakers.get(name)


def register_circuit_breaker(circuit_breaker: CircuitBreaker):
    """Register circuit breaker for monitoring"""
    _circuit_breakers[circuit_breaker.name] = circuit_breaker


def get_all_circuit_breakers() -> dict[str, dict]:
    """Get state of all circuit breakers"""
    return {
        name: cb.get_state()
        for name, cb in _circuit_breakers.items()
    }
