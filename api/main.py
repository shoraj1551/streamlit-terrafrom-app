"""
FastAPI Application

REST API for Terraform Deployment Platform with authentication,
deployment management, and monitoring endpoints.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.services.auth0_integration import Auth0Service
from app.services.deployment_db import DeploymentDatabase
from app.services.deployment_queue import get_queue_manager, DeploymentPriority
from app.services.audit_logger import get_audit_logger, AuditEventType, AuditSeverity
from app.services.cache_service import get_cache_service
from app.services.query_optimizer import get_query_profiler
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Terraform Deployment Platform API",
    description="Enterprise-grade Terraform deployment and management API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
auth_service = Auth0Service()


# Pydantic Models
class DeploymentCreate(BaseModel):
    """Deployment creation request"""
    provider: str
    region: str
    instance_type: str
    variables: dict = {}
    priority: DeploymentPriority = DeploymentPriority.NORMAL


class DeploymentResponse(BaseModel):
    """Deployment response"""
    deployment_id: str
    status: str
    provider: str
    region: str
    created_at: datetime
    user_email: str


class QueueStatusResponse(BaseModel):
    """Queue status response"""
    queue_size: int
    active_count: int
    max_concurrent: int
    available_slots: int
    at_capacity: bool


class CacheStatsResponse(BaseModel):
    """Cache statistics response"""
    enabled: bool
    hits: Optional[int] = None
    misses: Optional[int] = None
    hit_rate: Optional[float] = None


# Dependency: Get current user from JWT
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Validate JWT token and return user info
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User information dictionary
        
    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    
    try:
        # Verify token with Auth0
        user_info = auth_service.verify_token(token)
        return user_info
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Health check endpoints
@app.get("/health")
async def health_check():
    """
    Comprehensive health check
    
    Checks all critical dependencies and returns detailed status.
    """
    from app.services.deployment_db import DeploymentDatabase
    from app.services.redis_client import get_redis_client
    from app.celery_app import celery_app
    from app.core.circuit_breaker import get_all_circuit_breakers
    import shutil
    import psutil
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
        "circuit_breakers": {}
    }
    
    # Database check
    try:
        db = DeploymentDatabase()
        # Simple query to test connection
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "pool_size": db.engine.pool.size(),
            "checked_out": db.engine.pool.checkedout()
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Redis check
    try:
        redis_client = get_redis_client()
        redis_client.client.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "host": redis_client.host,
            "port": redis_client.port
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "degraded",
            "error": str(e)
        }
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    
    # Celery worker check
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats and len(stats) > 0:
            health_status["checks"]["celery"] = {
                "status": "healthy",
                "workers": len(stats)
            }
        else:
            health_status["checks"]["celery"] = {
                "status": "degraded",
                "workers": 0,
                "message": "No workers available"
            }
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["celery"] = {
            "status": "degraded",
            "error": str(e)
        }
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    
    # Disk space check
    try:
        disk = shutil.disk_usage("/")
        disk_usage_percent = (disk.used / disk.total) * 100
        
        if disk_usage_percent > 90:
            health_status["checks"]["disk"] = {
                "status": "critical",
                "usage_percent": round(disk_usage_percent, 1),
                "free_gb": round(disk.free / (1024**3), 2)
            }
            health_status["status"] = "unhealthy"
        elif disk_usage_percent > 80:
            health_status["checks"]["disk"] = {
                "status": "warning",
                "usage_percent": round(disk_usage_percent, 1),
                "free_gb": round(disk.free / (1024**3), 2)
            }
        else:
            health_status["checks"]["disk"] = {
                "status": "healthy",
                "usage_percent": round(disk_usage_percent, 1),
                "free_gb": round(disk.free / (1024**3), 2)
            }
    except Exception as e:
        health_status["checks"]["disk"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # Memory check
    try:
        memory = psutil.virtual_memory()
        memory_usage_percent = memory.percent
        
        if memory_usage_percent > 90:
            health_status["checks"]["memory"] = {
                "status": "critical",
                "usage_percent": round(memory_usage_percent, 1),
                "available_gb": round(memory.available / (1024**3), 2)
            }
            health_status["status"] = "unhealthy"
        elif memory_usage_percent > 80:
            health_status["checks"]["memory"] = {
                "status": "warning",
                "usage_percent": round(memory_usage_percent, 1),
                "available_gb": round(memory.available / (1024**3), 2)
            }
        else:
            health_status["checks"]["memory"] = {
                "status": "healthy",
                "usage_percent": round(memory_usage_percent, 1),
                "available_gb": round(memory.available / (1024**3), 2)
            }
    except Exception as e:
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # Circuit breaker status
    health_status["circuit_breakers"] = get_all_circuit_breakers()
    
    # Check if any circuit breakers are OPEN
    for cb_name, cb_state in health_status["circuit_breakers"].items():
        if cb_state["state"] == "open":
            health_status["status"] = "degraded"
            break
    
    # Set HTTP status code based on health
    status_code = 200
    if health_status["status"] == "unhealthy":
        status_code = 503
    elif health_status["status"] == "degraded":
        status_code = 200  # Still serving traffic
    
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness probe
    
    Returns 200 if app can serve traffic, 503 otherwise.
    """
    from app.services.deployment_db import DeploymentDatabase
    
    try:
        # Check critical dependencies
        db = DeploymentDatabase()
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {"ready": True, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return JSONResponse(
            content={"ready": False, "error": str(e)},
            status_code=503
        )


@app.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe
    
    Returns 200 if app process is alive.
    """
    return {"alive": True, "timestamp": datetime.utcnow().isoformat()}


# Authentication endpoints
@app.post("/api/auth/login")
async def login(email: EmailStr, password: str):
    """Login endpoint (redirects to Auth0)"""
    auth_url = auth_service.get_authorization_url()
    return {"auth_url": auth_url}


# Deployment endpoints
@app.post("/api/deployments", response_model=DeploymentResponse)
async def create_deployment(
    deployment: DeploymentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create new deployment
    
    Args:
        deployment: Deployment configuration
        current_user: Current authenticated user
        
    Returns:
        Created deployment information
    """
    import uuid
    
    deployment_id = str(uuid.uuid4())
    user_email = current_user.get("email")
    
    # Add to queue
    queue_manager = get_queue_manager()
    queue_manager.enqueue(
        deployment_id=deployment_id,
        user_email=user_email,
        provider=deployment.provider,
        region=deployment.region,
        priority=deployment.priority,
        metadata={
            "instance_type": deployment.instance_type,
            "variables": deployment.variables
        }
    )
    
    # Log audit event
    audit_logger = get_audit_logger()
    audit_logger.log_event(
        event_type=AuditEventType.DEPLOY_CREATE,
        user_id=user_email,
        resource_type="deployment",
        resource_id=deployment_id,
        details={
            "provider": deployment.provider,
            "region": deployment.region,
            "priority": deployment.priority.value
        },
        severity=AuditSeverity.INFO
    )
    
    return DeploymentResponse(
        deployment_id=deployment_id,
        status="queued",
        provider=deployment.provider,
        region=deployment.region,
        created_at=datetime.utcnow(),
        user_email=user_email
    )


@app.get("/api/deployments", response_model=List[DeploymentResponse])
async def list_deployments(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    List user's deployments
    
    Args:
        limit: Maximum number of results
        offset: Offset for pagination
        current_user: Current authenticated user
        
    Returns:
        List of deployments
    """
    db = DeploymentDatabase()
    user_email = current_user.get("email")
    
    deployments = db.get_all_deployments(
        user_email=user_email,
        limit=limit
    )
    
    return [
        DeploymentResponse(
            deployment_id=d["deployment_id"],
            status=d["status"],
            provider=d["provider"],
            region=d["region"],
            created_at=datetime.fromisoformat(d["created_at"]),
            user_email=d["user_email"]
        )
        for d in deployments
    ]


@app.get("/api/deployments/{deployment_id}")
async def get_deployment(
    deployment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get deployment details
    
    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        
    Returns:
        Deployment details
    """
    # Check cache first
    cache = get_cache_service()
    cached_result = cache.get_deployment_result(deployment_id)
    
    if cached_result:
        return cached_result
    
    # Get from database
    db = DeploymentDatabase()
    deployment = db.get_deployment(deployment_id)
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Cache result
    cache.cache_deployment_result(deployment_id, deployment)
    
    return deployment


# Queue endpoints
@app.get("/api/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(current_user: dict = Depends(get_current_user)):
    """
    Get deployment queue status
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Queue status information
    """
    queue_manager = get_queue_manager()
    status = queue_manager.get_queue_status()
    
    return QueueStatusResponse(**status)


@app.get("/api/queue/deployments")
async def get_queued_deployments(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get queued deployments
    
    Args:
        limit: Maximum number of results
        current_user: Current authenticated user
        
    Returns:
        List of queued deployments
    """
    queue_manager = get_queue_manager()
    deployments = queue_manager.get_queued_deployments(limit=limit)
    
    return {"deployments": deployments}


# Monitoring endpoints
@app.get("/api/metrics/cache", response_model=CacheStatsResponse)
async def get_cache_metrics(current_user: dict = Depends(get_current_user)):
    """
    Get cache statistics
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Cache statistics
    """
    cache = get_cache_service()
    stats = cache.get_cache_stats()
    
    return CacheStatsResponse(**stats)


@app.get("/api/metrics/database")
async def get_database_metrics(current_user: dict = Depends(get_current_user)):
    """
    Get database query statistics
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Database query statistics
    """
    profiler = get_query_profiler()
    stats = profiler.get_query_stats()
    slow_queries = profiler.get_slow_queries(limit=5)
    
    return {
        "stats": stats,
        "slow_queries": slow_queries
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
