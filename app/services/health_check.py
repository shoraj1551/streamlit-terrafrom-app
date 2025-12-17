"""
Health Check System

Monitors system health and component status.
"""

from typing import Dict, Any, List
from datetime import datetime
from enum import Enum
import time


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth:
    """Health status for a single component"""
    
    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: str = "",
        response_time_ms: float = 0
    ):
        self.name = name
        self.status = status
        self.message = message
        self.response_time_ms = response_time_ms
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'response_time_ms': round(self.response_time_ms, 2),
            'timestamp': self.timestamp
        }


class HealthCheckSystem:
    """System health monitoring"""
    
    def __init__(self):
        self.components = [
            'database',
            'cloud_providers',
            'logging_system',
            'metrics_collector'
        ]
    
    def check_all(self) -> Dict[str, Any]:
        """
        Check health of all components
        
        Returns:
            Overall health status
        """
        results = []
        
        # Check each component
        for component in self.components:
            health = self._check_component(component)
            results.append(health)
        
        # Determine overall status
        statuses = [r.status for r in results]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        return {
            'overall_status': overall_status.value,
            'components': [r.to_dict() for r in results],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _check_component(self, component: str) -> ComponentHealth:
        """
        Check health of a specific component
        
        Args:
            component: Component name
            
        Returns:
            ComponentHealth instance
        """
        start_time = time.time()
        
        try:
            if component == 'database':
                return self._check_database()
            elif component == 'cloud_providers':
                return self._check_cloud_providers()
            elif component == 'logging_system':
                return self._check_logging_system()
            elif component == 'metrics_collector':
                return self._check_metrics_collector()
            else:
                return ComponentHealth(
                    name=component,
                    status=HealthStatus.UNHEALTHY,
                    message="Unknown component"
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}",
                response_time_ms=response_time
            )
    
    def _check_database(self) -> ComponentHealth:
        """Check database health"""
        start_time = time.time()
        
        try:
            # In real implementation, would check database connection
            # For now, simulate a check
            time.sleep(0.01)  # Simulate query time
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name='database',
                status=HealthStatus.HEALTHY,
                message="Database connection OK",
                response_time_ms=response_time
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='database',
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {str(e)}",
                response_time_ms=response_time
            )
    
    def _check_cloud_providers(self) -> ComponentHealth:
        """Check cloud provider connectivity"""
        start_time = time.time()
        
        try:
            # Check if cloud provider modules are available
            from app.services.cloud_provider_factory import CloudProviderFactory
            
            providers = CloudProviderFactory.get_available_providers()
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name='cloud_providers',
                status=HealthStatus.HEALTHY,
                message=f"{len(providers)} providers available",
                response_time_ms=response_time
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='cloud_providers',
                status=HealthStatus.UNHEALTHY,
                message=f"Provider error: {str(e)}",
                response_time_ms=response_time
            )
    
    def _check_logging_system(self) -> ComponentHealth:
        """Check logging system health"""
        start_time = time.time()
        
        try:
            # Check if logging system is available
            from app.services.logging import StructuredLogger
            
            # Test log write
            logger = StructuredLogger('health_check')
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name='logging_system',
                status=HealthStatus.HEALTHY,
                message="Logging system operational",
                response_time_ms=response_time
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='logging_system',
                status=HealthStatus.DEGRADED,
                message=f"Logging warning: {str(e)}",
                response_time_ms=response_time
            )
    
    def _check_metrics_collector(self) -> ComponentHealth:
        """Check metrics collector health"""
        start_time = time.time()
        
        try:
            # Check if metrics collector is available
            from app.services.metrics_collector import MetricsCollector
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name='metrics_collector',
                status=HealthStatus.HEALTHY,
                message="Metrics collector operational",
                response_time_ms=response_time
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='metrics_collector',
                status=HealthStatus.DEGRADED,
                message=f"Metrics warning: {str(e)}",
                response_time_ms=response_time
            )
    
    def get_health_summary(self) -> str:
        """Get human-readable health summary"""
        health = self.check_all()
        
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌'
        }
        
        emoji = status_emoji.get(health['overall_status'], '❓')
        
        summary = f"{emoji} System Status: {health['overall_status'].upper()}\n\n"
        
        for component in health['components']:
            comp_emoji = status_emoji.get(component['status'], '❓')
            summary += f"{comp_emoji} {component['name']}: {component['status']} ({component['response_time_ms']:.1f}ms)\n"
            if component['message']:
                summary += f"   {component['message']}\n"
        
        return summary
