"""
Horizontal Scaling Configuration

Enables running multiple application instances with shared state.
"""

import os
from typing import Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ScalingConfig:
    """
    Configuration for horizontal scaling
    
    Ensures all state is stored in Redis/PostgreSQL for multi-instance deployment.
    """
    
    def __init__(self):
        """Initialize scaling configuration"""
        self.instance_id = os.getenv("INSTANCE_ID", self._generate_instance_id())
        self.enable_sticky_sessions = os.getenv("STICKY_SESSIONS", "false").lower() == "true"
        self.max_instances = int(os.getenv("MAX_INSTANCES", "10"))
        
        logger.info(f"✅ Scaling config initialized - Instance: {self.instance_id}")
    
    def _generate_instance_id(self) -> str:
        """Generate unique instance ID"""
        import uuid
        import socket
        
        hostname = socket.gethostname()
        unique_id = str(uuid.uuid4())[:8]
        return f"{hostname}-{unique_id}"
    
    def is_stateless(self) -> bool:
        """
        Verify instance is stateless
        
        Returns:
            True if all state is externalized
        """
        # Check that we're using Redis for sessions
        redis_host = os.getenv("REDIS_HOST")
        if not redis_host:
            logger.warning("Redis not configured - not stateless!")
            return False
        
        # Check that we're using PostgreSQL for data
        db_url = os.getenv("DATABASE_URL")
        if not db_url or not db_url.startswith("postgresql"):
            logger.warning("PostgreSQL not configured - not stateless!")
            return False
        
        logger.info("✅ Instance is stateless - ready for horizontal scaling")
        return True
    
    def get_load_balancer_config(self) -> dict:
        """
        Get load balancer configuration
        
        Returns:
            Load balancer settings
        """
        return {
            "algorithm": "round_robin",  # or "least_connections"
            "sticky_sessions": self.enable_sticky_sessions,
            "health_check_path": "/health/ready",
            "health_check_interval": 10,  # seconds
            "health_check_timeout": 5,  # seconds
            "unhealthy_threshold": 3,  # failures before marking unhealthy
            "healthy_threshold": 2  # successes before marking healthy
        }
    
    def get_session_affinity_config(self) -> Optional[dict]:
        """
        Get session affinity configuration
        
        Returns:
            Session affinity settings or None
        """
        if not self.enable_sticky_sessions:
            return None
        
        return {
            "type": "cookie",
            "cookie_name": "INSTANCE_ID",
            "cookie_ttl": 3600  # 1 hour
        }


# Global config instance
_scaling_config = None


def get_scaling_config() -> ScalingConfig:
    """Get global scaling configuration"""
    global _scaling_config
    if _scaling_config is None:
        _scaling_config = ScalingConfig()
    return _scaling_config
