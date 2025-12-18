"""
Dependency Injection Container

Provides service lifecycle management and dependency injection.
"""

from typing import Dict, Type, Any, Callable, Optional
from dataclasses import dataclass
import inspect
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ServiceDescriptor:
    """Service descriptor for DI container"""
    service_type: Type
    implementation: Optional[Type] = None
    factory: Optional[Callable] = None
    singleton: bool = True
    instance: Any = None


class DIContainer:
    """
    Dependency Injection Container
    
    Manages service registration, resolution, and lifecycle.
    """
    
    def __init__(self):
        """Initialize DI container"""
        self._services: Dict[Type, ServiceDescriptor] = {}
        logger.info("✅ DIContainer initialized")
    
    def register(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable] = None,
        singleton: bool = True
    ):
        """
        Register service in container
        
        Args:
            service_type: Service interface/type
            implementation: Implementation class (optional)
            factory: Factory function (optional)
            singleton: Whether to create single instance
        """
        if implementation is None and factory is None:
            # Self-registration
            implementation = service_type
        
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            singleton=singleton
        )
        
        self._services[service_type] = descriptor
        logger.debug(f"Registered service: {service_type.__name__}")
    
    def resolve(self, service_type: Type) -> Any:
        """
        Resolve service from container
        
        Args:
            service_type: Service type to resolve
            
        Returns:
            Service instance
        """
        if service_type not in self._services:
            raise ValueError(f"Service not registered: {service_type.__name__}")
        
        descriptor = self._services[service_type]
        
        # Return singleton instance if exists
        if descriptor.singleton and descriptor.instance is not None:
            return descriptor.instance
        
        # Create new instance
        if descriptor.factory:
            instance = descriptor.factory()
        else:
            instance = self._create_instance(descriptor.implementation)
        
        # Store singleton instance
        if descriptor.singleton:
            descriptor.instance = instance
        
        return instance
    
    def _create_instance(self, implementation: Type) -> Any:
        """
        Create instance with dependency injection
        
        Args:
            implementation: Implementation class
            
        Returns:
            Created instance
        """
        # Get constructor signature
        sig = inspect.signature(implementation.__init__)
        
        # Resolve dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Check if parameter type is registered
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation
                if param_type in self._services:
                    kwargs[param_name] = self.resolve(param_type)
        
        # Create instance
        return implementation(**kwargs)
    
    def clear(self):
        """Clear all services"""
        self._services.clear()
        logger.info("Cleared DI container")


# Global container instance
_container = None


def get_container() -> DIContainer:
    """Get global DI container"""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def inject(service_type: Type):
    """
    Decorator for dependency injection
    
    Usage:
        @inject(MyService)
        def my_function(service: MyService):
            service.do_something()
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            container = get_container()
            service = container.resolve(service_type)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator


def setup_services():
    """
    Register all application services in DI container
    
    This should be called at application startup.
    """
    container = get_container()
    
    # Infrastructure services (singletons)
    from app.services.redis_client import RedisClient
    from app.services.deployment_db import DeploymentDatabase
    from app.services.audit_logger import AuditLogger
    from app.services.cache_service import CacheService
    from app.services.deployment_queue import DeploymentQueueManager
    from app.services.query_optimizer import QueryProfiler
    
    container.register(RedisClient, singleton=True)
    container.register(DeploymentDatabase, singleton=True)
    container.register(AuditLogger, singleton=True)
    container.register(CacheService, singleton=True)
    container.register(DeploymentQueueManager, singleton=True)
    container.register(QueryProfiler, singleton=True)
    
    # Business services (transient - new instance each time)
    from app.services.deployment_service import DeploymentService
    from app.services.auth_service import AuthenticationService
    from app.services.config_service import ConfigurationService
    
    container.register(DeploymentService, singleton=False)
    container.register(AuthenticationService, singleton=False)
    container.register(ConfigurationService, singleton=False)
    
    # Auth0 service (singleton)
    from app.services.auth0_integration import Auth0Service
    container.register(Auth0Service, singleton=True)
    
    # Session manager (singleton)
    from app.services.session_manager import SessionManager
    container.register(SessionManager, singleton=True)
    
    logger.info("✅ All services registered in DI container")
    
    return container
