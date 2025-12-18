"""
Deployment Queue Manager

Manages deployment queue with priority, scheduling, and concurrency limits.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from app.services.redis_client import get_redis_client
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DeploymentPriority(str, Enum):
    """Deployment priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QueuedDeployment:
    """Queued deployment item"""
    deployment_id: str
    user_email: str
    provider: str
    region: str
    priority: DeploymentPriority
    scheduled_at: Optional[datetime] = None
    queued_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.queued_at is None:
            self.queued_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class DeploymentQueueManager:
    """
    Manages deployment queue with Redis backend
    
    Features:
    - Priority-based queuing
    - Deployment scheduling
    - Concurrency limits
    - Queue monitoring
    """
    
    # Priority scores for sorting
    PRIORITY_SCORES = {
        DeploymentPriority.LOW: 1,
        DeploymentPriority.NORMAL: 2,
        DeploymentPriority.HIGH: 3,
        DeploymentPriority.CRITICAL: 4
    }
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize queue manager
        
        Args:
            max_concurrent: Maximum concurrent deployments
        """
        try:
            self.redis = get_redis_client()
            self.max_concurrent = max_concurrent
            self.queue_key = "deployment:queue"
            self.active_key = "deployment:active"
            logger.info(f"✅ DeploymentQueueManager initialized (max concurrent: {max_concurrent})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize DeploymentQueueManager: {e}")
            raise
    
    def enqueue(
        self,
        deployment_id: str,
        user_email: str,
        provider: str,
        region: str,
        priority: DeploymentPriority = DeploymentPriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add deployment to queue
        
        Args:
            deployment_id: Deployment ID
            user_email: User email
            provider: Cloud provider
            region: Deployment region
            priority: Deployment priority
            scheduled_at: Scheduled execution time (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            True if enqueued successfully
        """
        deployment = QueuedDeployment(
            deployment_id=deployment_id,
            user_email=user_email,
            provider=provider,
            region=region,
            priority=priority,
            scheduled_at=scheduled_at,
            metadata=metadata or {}
        )
        
        # Calculate priority score (higher = more important)
        # Include timestamp for FIFO within same priority
        priority_score = self.PRIORITY_SCORES[priority]
        timestamp_score = deployment.queued_at.timestamp()
        
        # Combined score: priority * 1e10 + timestamp
        # This ensures priority takes precedence, then FIFO
        score = (priority_score * 1e10) + timestamp_score
        
        # Serialize deployment
        deployment_data = {
            **asdict(deployment),
            'queued_at': deployment.queued_at.isoformat(),
            'scheduled_at': deployment.scheduled_at.isoformat() if deployment.scheduled_at else None,
            'priority': deployment.priority.value
        }
        
        # Add to sorted set (priority queue)
        self.redis.zadd(
            self.queue_key,
            {json.dumps(deployment_data): score}
        )
        
        logger.info(
            f"Enqueued deployment {deployment_id} "
            f"(priority: {priority.value}, user: {user_email})"
        )
        
        return True
    
    def dequeue(self) -> Optional[QueuedDeployment]:
        """
        Get next deployment from queue with distributed locking
        
        Returns:
            Next deployment or None if queue is empty or at capacity
        """
        from app.core.distributed_lock import DistributedLock
        
        # Check if we're at max concurrent deployments
        active_count = self.get_active_count()
        if active_count >= self.max_concurrent:
            logger.debug(f"At max concurrent deployments ({active_count}/{self.max_concurrent})")
            return None
        
        # Use distributed lock to prevent race conditions
        lock = DistributedLock(
            redis_client=self.redis.client,
            lock_name="deployment_queue_dequeue",
            timeout=5,
            blocking=True,
            blocking_timeout=2
        )
        
        with lock() as acquired:
            if not acquired:
                logger.warning("Could not acquire lock for dequeue operation")
                return None
            
            # Now atomic - get highest priority item
            items = self.redis.zpopmax(self.queue_key, 1)
            
            if not items:
                return None
            
            deployment_json, score = items[0]
            deployment_data = json.loads(deployment_json)
            
            # Convert back to QueuedDeployment
            deployment = QueuedDeployment(
                deployment_id=deployment_data['deployment_id'],
                user_email=deployment_data['user_email'],
                provider=deployment_data['provider'],
                region=deployment_data['region'],
                priority=DeploymentPriority(deployment_data['priority']),
                scheduled_at=datetime.fromisoformat(deployment_data['scheduled_at']) if deployment_data['scheduled_at'] else None,
                queued_at=datetime.fromisoformat(deployment_data['queued_at']),
                metadata=deployment_data.get('metadata', {})
            )
            
            # Add to active set
            self.mark_active(deployment.deployment_id)
            
            logger.info(f"Dequeued deployment {deployment.deployment_id}")
            
            return deployment
    
    def mark_active(self, deployment_id: str):
        """Mark deployment as active"""
        self.redis.sadd(self.active_key, deployment_id)
    
    def mark_complete(self, deployment_id: str):
        """Mark deployment as complete"""
        self.redis.srem(self.active_key, deployment_id)
        logger.info(f"Deployment {deployment_id} marked as complete")
    
    def get_queue_size(self) -> int:
        """Get number of deployments in queue"""
        return self.redis.scard(self.queue_key) or 0
    
    def get_active_count(self) -> int:
        """Get number of active deployments"""
        return self.redis.scard(self.active_key) or 0
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get queue status
        
        Returns:
            Dictionary with queue statistics
        """
        queue_size = self.get_queue_size()
        active_count = self.get_active_count()
        
        return {
            'queue_size': queue_size,
            'active_count': active_count,
            'max_concurrent': self.max_concurrent,
            'available_slots': max(0, self.max_concurrent - active_count),
            'at_capacity': active_count >= self.max_concurrent
        }
    
    def get_queued_deployments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get queued deployments (highest priority first)
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of queued deployment dictionaries
        """
        # Get items with scores (highest first)
        items = self.redis.client.zrevrange(
            self.queue_key,
            0,
            limit - 1,
            withscores=True
        )
        
        deployments = []
        for item_json, score in items:
            deployment_data = json.loads(item_json)
            deployments.append(deployment_data)
        
        return deployments
    
    def cancel_deployment(self, deployment_id: str) -> bool:
        """
        Cancel queued deployment
        
        Args:
            deployment_id: Deployment ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        # Get all items
        items = self.redis.client.zrange(self.queue_key, 0, -1)
        
        for item_json in items:
            deployment_data = json.loads(item_json)
            if deployment_data['deployment_id'] == deployment_id:
                # Remove from queue
                self.redis.client.zrem(self.queue_key, item_json)
                logger.info(f"Cancelled deployment {deployment_id}")
                return True
        
        return False


# Global queue manager instance
_queue_manager = None


def get_queue_manager() -> DeploymentQueueManager:
    """Get global queue manager instance"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = DeploymentQueueManager()
    return _queue_manager
