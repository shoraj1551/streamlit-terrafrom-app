"""
Celery Application Configuration

Configures Celery for background job processing with Redis as broker and backend.
"""

from celery import Celery
import os

# Create Celery application
celery_app = Celery(
    'terraform_app',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={'master_name': 'mymaster'},
    
    # Worker
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Broker
    broker_connection_retry_on_startup=True,
    
    # Task routes
    task_routes={
        'app.tasks.deployment_tasks.*': {'queue': 'deployments'},
        'app.tasks.notification_tasks.*': {'queue': 'notifications'},
    },
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        'cleanup-old-deployments': {
            'task': 'app.tasks.maintenance_tasks.cleanup_old_deployments',
            'schedule': 86400.0,  # Daily
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])
