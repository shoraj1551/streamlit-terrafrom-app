"""
Enhanced Error Handling

Provides structured error responses, categorization, and tracking.
"""

from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import traceback
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ErrorCategory(str, Enum):
    """Error categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    INTERNAL = "internal"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    NETWORK = "network"


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorResponse:
    """Structured error response"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    trace_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['category'] = self.category.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ApplicationError(Exception):
    """Base application error"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}


class ValidationError(ApplicationError):
    """Validation error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details=details
        )


class AuthenticationError(ApplicationError):
    """Authentication error"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH
        )


class AuthorizationError(ApplicationError):
    """Authorization error"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH
        )


class NotFoundError(ApplicationError):
    """Resource not found error"""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            details={'resource': resource, 'identifier': identifier}
        )


class RateLimitError(ApplicationError):
    """Rate limit exceeded error"""
    
    def __init__(self, retry_after: float):
        super().__init__(
            message="Rate limit exceeded",
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            details={'retry_after': retry_after}
        )


class ErrorHandler:
    """
    Global error handler
    """
    
    @staticmethod
    def handle_error(error: Exception, trace_id: Optional[str] = None) -> ErrorResponse:
        """
        Handle error and create structured response
        
        Args:
            error: Exception to handle
            trace_id: Trace ID for distributed tracing
            
        Returns:
            ErrorResponse object
        """
        import secrets
        
        error_id = f"err_{secrets.token_hex(8)}"
        
        # Handle application errors
        if isinstance(error, ApplicationError):
            response = ErrorResponse(
                error_id=error_id,
                category=error.category,
                severity=error.severity,
                message=error.message,
                details=error.details,
                trace_id=trace_id
            )
            
            # Log based on severity
            if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                logger.error(f"Error {error_id}: {error.message}", extra=response.to_dict())
            else:
                logger.warning(f"Error {error_id}: {error.message}", extra=response.to_dict())
            
            return response
        
        # Handle unexpected errors
        logger.error(
            f"Unexpected error {error_id}: {str(error)}",
            exc_info=True
        )
        
        response = ErrorResponse(
            error_id=error_id,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
            message="An unexpected error occurred",
            details={
                'error_type': type(error).__name__,
                'error_message': str(error)
            },
            trace_id=trace_id
        )
        
        return response
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """
        Determine if operation should be retried
        
        Args:
            error: Exception to check
            
        Returns:
            True if should retry
        """
        # Retry on network and external service errors
        if isinstance(error, ApplicationError):
            return error.category in [
                ErrorCategory.NETWORK,
                ErrorCategory.EXTERNAL_SERVICE,
                ErrorCategory.DATABASE
            ]
        
        return False
    
    @staticmethod
    def get_retry_delay(attempt: int, max_delay: int = 60) -> int:
        """
        Calculate retry delay with exponential backoff
        
        Args:
            attempt: Retry attempt number (1-indexed)
            max_delay: Maximum delay in seconds
            
        Returns:
            Delay in seconds
        """
        delay = min(2 ** attempt, max_delay)
        return delay


def retry_on_error(max_attempts: int = 3, delay: int = 1):
    """
    Decorator to retry function on error
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Initial delay between retries
        
    Usage:
        @retry_on_error(max_attempts=3)
        def unreliable_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    
                    if ErrorHandler.should_retry(e):
                        retry_delay = ErrorHandler.get_retry_delay(attempt)
                        logger.warning(
                            f"Retry attempt {attempt}/{max_attempts} "
                            f"after {retry_delay}s: {str(e)}"
                        )
                        time.sleep(retry_delay)
                    else:
                        raise
        
        return wrapper
    return decorator
