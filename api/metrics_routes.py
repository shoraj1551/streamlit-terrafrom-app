"""
Prometheus Metrics Endpoints

Exposes application metrics for Prometheus scraping.
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.observability.metrics import MetricsCollector
from app.core.circuit_breaker import get_all_circuit_breakers

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format.
    """
    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/metrics/circuit-breakers")
async def circuit_breaker_metrics():
    """
    Circuit breaker status metrics
    
    Returns current state of all circuit breakers.
    """
    return get_all_circuit_breakers()


@router.get("/metrics/health-summary")
async def health_summary():
    """
    Health metrics summary
    
    Quick overview of system health.
    """
    from app.services.deployment_queue import get_queue_manager
    from app.services.cache_service import get_cache_service
    
    queue = get_queue_manager()
    cache = get_cache_service()
    
    return {
        "queue": queue.get_queue_status(),
        "cache": cache.get_cache_stats(),
        "circuit_breakers": get_all_circuit_breakers()
    }
