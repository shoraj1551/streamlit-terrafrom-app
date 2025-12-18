"""
Deployment Service - Business Logic Layer

Separates business logic from UI and API layers for better testability
and maintainability.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.database import Deployment
from app.services.deployment_db import DeploymentDatabase
from app.services.deployment_queue import get_queue_manager, DeploymentPriority
from app.services.audit_logger import get_audit_logger, AuditEventType, AuditSeverity
from app.services.cache_service import get_cache_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DeploymentService:
    """
    Business logic for deployments
    
    This service can be used by both Streamlit UI and FastAPI.
    Provides a clean separation between presentation and business logic.
    """
    
    def __init__(
        self,
        db: Optional[DeploymentDatabase] = None,
        queue: Optional[Any] = None,
        audit: Optional[Any] = None,
        cache: Optional[Any] = None
    ):
        """
        Initialize deployment service
        
        Args:
            db: Database service (injected)
            queue: Queue manager (injected)
            audit: Audit logger (injected)
            cache: Cache service (injected)
        """
        self.db = db or DeploymentDatabase()
        self.queue = queue or get_queue_manager()
        self.audit = audit or get_audit_logger()
        self.cache = cache or get_cache_service()
    
    def create_deployment(
        self,
        user_email: str,
        provider: str,
        region: str,
        instance_type: str,
        variables: Dict[str, Any],
        priority: str = "normal"
    ) -> str:
        """
        Create new deployment
        
        Args:
            user_email: User email
            provider: Cloud provider (aws, azure, gcp)
            region: Deployment region
            instance_type: Instance type
            variables: Terraform variables
            priority: Deployment priority
            
        Returns:
            deployment_id
            
        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        self._validate_deployment_config(provider, region, instance_type)
        
        # Generate deployment ID
        deployment_id = str(uuid.uuid4())
        
        # Convert priority string to enum
        try:
            priority_enum = DeploymentPriority[priority.upper()]
        except KeyError:
            priority_enum = DeploymentPriority.NORMAL
        
        # Add to queue
        self.queue.enqueue(
            deployment_id=deployment_id,
            user_email=user_email,
            provider=provider,
            region=region,
            priority=priority_enum,
            metadata={
                "instance_type": instance_type,
                "variables": variables
            }
        )
        
        # Audit log
        self.audit.log_event(
            event_type=AuditEventType.DEPLOY_CREATE,
            user_id=user_email,
            resource_type="deployment",
            resource_id=deployment_id,
            details={
                "provider": provider,
                "region": region,
                "priority": priority
            },
            severity=AuditSeverity.INFO
        )
        
        logger.info(f"Created deployment {deployment_id} for user {user_email}")
        
        return deployment_id
    
    def get_user_deployments(
        self,
        user_email: str,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get deployments for user
        
        Args:
            user_email: User email
            limit: Maximum results
            offset: Pagination offset
            status_filter: Optional status filter
            
        Returns:
            List of deployment dictionaries
        """
        # Check cache first
        cache_key = f"user_deployments:{user_email}:{status_filter}:{limit}:{offset}"
        cached = self.cache.get(cache_key)
        
        if cached:
            logger.debug(f"Cache hit for user deployments: {user_email}")
            return cached
        
        # Get from database
        deployments = self.db.get_all_deployments(
            user_email=user_email,
            limit=limit
        )
        
        # Filter by status if provided
        if status_filter:
            deployments = [
                d for d in deployments
                if d.get('status') == status_filter
            ]
        
        # Cache results
        self.cache.set(cache_key, deployments, ttl=60)  # 1 minute cache
        
        return deployments
    
    def get_deployment(
        self,
        deployment_id: str,
        user_email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get deployment by ID
        
        Args:
            deployment_id: Deployment ID
            user_email: Optional user email for authorization
            
        Returns:
            Deployment dictionary or None
        """
        # Check cache first
        cached = self.cache.get_deployment_result(deployment_id)
        if cached:
            # Verify user authorization if provided
            if user_email and cached.get('user_email') != user_email:
                logger.warning(f"Unauthorized access attempt: {user_email} -> {deployment_id}")
                return None
            return cached
        
        # Get from database
        deployment = self.db.get_deployment(deployment_id)
        
        if not deployment:
            return None
        
        # Verify user authorization
        if user_email and deployment.get('user_email') != user_email:
            logger.warning(f"Unauthorized access attempt: {user_email} -> {deployment_id}")
            return None
        
        # Cache result
        self.cache.cache_deployment_result(deployment_id, deployment)
        
        return deployment
    
    def cancel_deployment(
        self,
        deployment_id: str,
        user_email: str,
        reason: str = "User cancelled"
    ) -> bool:
        """
        Cancel deployment
        
        Args:
            deployment_id: Deployment ID
            user_email: User email (for authorization)
            reason: Cancellation reason
            
        Returns:
            True if cancelled successfully
        """
        # Verify ownership
        deployment = self.get_deployment(deployment_id, user_email)
        if not deployment:
            logger.warning(f"Cannot cancel deployment {deployment_id}: not found or unauthorized")
            return False
        
        # Cancel in queue
        cancelled = self.queue.cancel_deployment(deployment_id)
        
        if cancelled:
            # Audit log
            self.audit.log_event(
                event_type=AuditEventType.DEPLOY_CANCEL,
                user_id=user_email,
                resource_type="deployment",
                resource_id=deployment_id,
                details={"reason": reason},
                severity=AuditSeverity.INFO
            )
            
            # Invalidate cache
            self.cache.delete(f"deployment:{deployment_id}")
            
            logger.info(f"Cancelled deployment {deployment_id}")
        
        return cancelled
    
    def get_deployment_stats(self, user_email: str) -> Dict[str, Any]:
        """
        Get deployment statistics for user
        
        Args:
            user_email: User email
            
        Returns:
            Statistics dictionary
        """
        deployments = self.get_user_deployments(user_email, limit=1000)
        
        stats = {
            "total": len(deployments),
            "by_status": {},
            "by_provider": {},
            "success_rate": 0.0
        }
        
        for deployment in deployments:
            # Count by status
            status = deployment.get('status', 'unknown')
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Count by provider
            provider = deployment.get('provider', 'unknown')
            stats["by_provider"][provider] = stats["by_provider"].get(provider, 0) + 1
        
        # Calculate success rate
        completed = stats["by_status"].get('completed', 0)
        failed = stats["by_status"].get('failed', 0)
        total_finished = completed + failed
        
        if total_finished > 0:
            stats["success_rate"] = (completed / total_finished) * 100
        
        return stats
    
    def _validate_deployment_config(
        self,
        provider: str,
        region: str,
        instance_type: str
    ):
        """
        Validate deployment configuration
        
        Args:
            provider: Cloud provider
            region: Deployment region
            instance_type: Instance type
            
        Raises:
            ValueError: If validation fails
        """
        # Validate provider
        allowed_providers = ["aws", "azure", "gcp"]
        if provider.lower() not in allowed_providers:
            raise ValueError(
                f"Invalid provider: {provider}. "
                f"Allowed: {', '.join(allowed_providers)}"
            )
        
        # Validate region (basic check)
        if not region or len(region) < 2:
            raise ValueError(f"Invalid region: {region}")
        
        # Validate instance type (basic check)
        if not instance_type or len(instance_type) < 2:
            raise ValueError(f"Invalid instance type: {instance_type}")
        
        logger.debug(f"Validated deployment config: {provider}/{region}/{instance_type}")


# Global service instance (will be replaced with DI)
_deployment_service = None


def get_deployment_service() -> DeploymentService:
    """Get global deployment service instance"""
    global _deployment_service
    if _deployment_service is None:
        _deployment_service = DeploymentService()
    return _deployment_service
