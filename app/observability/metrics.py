"""
Prometheus Metrics Integration

Provides application and business metrics for monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from typing import Callable
from functools import wraps
import time
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# Application Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Business Metrics
deployments_total = Counter(
    'deployments_total',
    'Total deployments',
    ['provider', 'region', 'status']
)

deployments_active = Gauge(
    'deployments_active',
    'Currently active deployments'
)

deployment_queue_size = Gauge(
    'deployment_queue_size',
    'Number of deployments in queue'
)

deployment_duration_seconds = Histogram(
    'deployment_duration_seconds',
    'Deployment duration in seconds',
    ['provider', 'status']
)

# Infrastructure Metrics
redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']
)

database_queries_total = Counter(
    'database_queries_total',
    'Total database queries',
    ['operation']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation']
)

cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']
)

# Application Info
app_info = Info('app', 'Application information')
app_info.info({
    'version': '1.0.0',
    'name': 'Terraform Deployment Platform'
})


class MetricsCollector:
    """
    Metrics collector for application monitoring
    """
    
    @staticmethod
    def track_http_request(method: str, endpoint: str, status: int, duration: float):
        """Track HTTP request metrics"""
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    @staticmethod
    def track_deployment(provider: str, region: str, status: str, duration: float = None):
        """Track deployment metrics"""
        deployments_total.labels(provider=provider, region=region, status=status).inc()
        
        if duration is not None:
            deployment_duration_seconds.labels(provider=provider, status=status).observe(duration)
    
    @staticmethod
    def set_active_deployments(count: int):
        """Set active deployments gauge"""
        deployments_active.set(count)
    
    @staticmethod
    def set_queue_size(size: int):
        """Set deployment queue size"""
        deployment_queue_size.set(size)
    
    @staticmethod
    def track_redis_operation(operation: str, success: bool):
        """Track Redis operation"""
        status = 'success' if success else 'error'
        redis_operations_total.labels(operation=operation, status=status).inc()
    
    @staticmethod
    def track_database_query(operation: str, duration: float):
        """Track database query"""
        database_queries_total.labels(operation=operation).inc()
        database_query_duration_seconds.labels(operation=operation).observe(duration)
    
    @staticmethod
    def track_cache_operation(operation: str, hit: bool):
        """Track cache operation"""
        result = 'hit' if hit else 'miss'
        cache_operations_total.labels(operation=operation, result=result).inc()


def track_time(metric: Histogram, labels: dict = None):
    """
    Decorator to track function execution time
    
    Usage:
        @track_time(deployment_duration_seconds, {'provider': 'aws'})
        def deploy():
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        return wrapper
    return decorator


def get_metrics():
    """Get current metrics in Prometheus format"""
    return generate_latest()


def get_metrics_content_type():
    """Get Prometheus metrics content type"""
    return CONTENT_TYPE_LATEST
