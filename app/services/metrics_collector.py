"""
Deployment Metrics Collection

Tracks and stores deployment metrics for monitoring and analysis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json


@dataclass
class DeploymentMetric:
    """Single deployment metric data point"""
    deployment_id: str
    timestamp: str
    cloud_provider: str
    environment: str
    region: str
    instance_type: str
    
    # Performance metrics
    deployment_duration_seconds: float
    terraform_init_duration: float
    terraform_plan_duration: float
    terraform_apply_duration: float
    
    # Cost metrics
    estimated_monthly_cost: float
    estimated_yearly_cost: float
    
    # Resource metrics
    instances_deployed: int
    resources_created: int
    
    # Status
    status: str  # success, failed, cancelled
    error_message: Optional[str] = None


class MetricsCollector:
    """Collect and store deployment metrics"""
    
    def __init__(self, db):
        self.db = db
    
    def record_deployment_metric(
        self,
        deployment_id: str,
        cloud_provider: str,
        environment: str,
        region: str,
        instance_type: str,
        deployment_duration: float,
        cost_estimate: Dict[str, float],
        status: str,
        **kwargs
    ) -> DeploymentMetric:
        """
        Record a deployment metric
        
        Args:
            deployment_id: Unique deployment ID
            cloud_provider: Cloud provider used
            environment: Environment (dev/staging/prod)
            region: Deployment region
            instance_type: Instance type
            deployment_duration: Total deployment time in seconds
            cost_estimate: Cost estimate dictionary
            status: Deployment status
            **kwargs: Additional metrics
            
        Returns:
            DeploymentMetric instance
        """
        metric = DeploymentMetric(
            deployment_id=deployment_id,
            timestamp=datetime.utcnow().isoformat(),
            cloud_provider=cloud_provider,
            environment=environment,
            region=region,
            instance_type=instance_type,
            deployment_duration_seconds=deployment_duration,
            terraform_init_duration=kwargs.get('terraform_init_duration', 0),
            terraform_plan_duration=kwargs.get('terraform_plan_duration', 0),
            terraform_apply_duration=kwargs.get('terraform_apply_duration', 0),
            estimated_monthly_cost=cost_estimate.get('monthly', 0),
            estimated_yearly_cost=cost_estimate.get('yearly', 0),
            instances_deployed=kwargs.get('instances_deployed', 1),
            resources_created=kwargs.get('resources_created', 0),
            status=status,
            error_message=kwargs.get('error_message')
        )
        
        # Store in database
        self._save_metric(metric)
        
        return metric
    
    def _save_metric(self, metric: DeploymentMetric):
        """Save metric to database"""
        # This will be implemented with actual database storage
        pass
    
    def get_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        cloud_provider: Optional[str] = None,
        environment: Optional[str] = None,
        limit: int = 100
    ) -> List[DeploymentMetric]:
        """
        Retrieve deployment metrics with filters
        
        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            cloud_provider: Filter by cloud provider
            environment: Filter by environment
            limit: Maximum number of results
            
        Returns:
            List of DeploymentMetric
        """
        # This will query the database
        return []
    
    def get_aggregated_metrics(
        self,
        period: str = "7d"  # 7d, 30d, 90d
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for a time period
        
        Args:
            period: Time period (7d, 30d, 90d)
            
        Returns:
            Dictionary with aggregated metrics
        """
        # Calculate date range
        days = int(period.replace('d', ''))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        metrics = self.get_metrics(start_date=start_date)
        
        if not metrics:
            return {
                'total_deployments': 0,
                'successful_deployments': 0,
                'failed_deployments': 0,
                'success_rate': 0,
                'avg_deployment_time': 0,
                'total_cost': 0,
                'avg_cost_per_deployment': 0
            }
        
        successful = [m for m in metrics if m.status == 'success']
        failed = [m for m in metrics if m.status == 'failed']
        
        total_time = sum(m.deployment_duration_seconds for m in metrics)
        total_cost = sum(m.estimated_monthly_cost for m in metrics)
        
        return {
            'total_deployments': len(metrics),
            'successful_deployments': len(successful),
            'failed_deployments': len(failed),
            'success_rate': round((len(successful) / len(metrics)) * 100, 2) if metrics else 0,
            'avg_deployment_time': round(total_time / len(metrics), 2) if metrics else 0,
            'total_cost': round(total_cost, 2),
            'avg_cost_per_deployment': round(total_cost / len(metrics), 2) if metrics else 0,
            'by_provider': self._group_by_provider(metrics),
            'by_environment': self._group_by_environment(metrics)
        }
    
    def _group_by_provider(self, metrics: List[DeploymentMetric]) -> Dict[str, int]:
        """Group metrics by cloud provider"""
        providers = {}
        for metric in metrics:
            providers[metric.cloud_provider] = providers.get(metric.cloud_provider, 0) + 1
        return providers
    
    def _group_by_environment(self, metrics: List[DeploymentMetric]) -> Dict[str, int]:
        """Group metrics by environment"""
        environments = {}
        for metric in metrics:
            environments[metric.environment] = environments.get(metric.environment, 0) + 1
        return environments
    
    def get_cost_trend(
        self,
        period: str = "30d",
        granularity: str = "daily"  # daily, weekly, monthly
    ) -> List[Dict[str, Any]]:
        """
        Get cost trend over time
        
        Args:
            period: Time period
            granularity: Data granularity
            
        Returns:
            List of cost data points
        """
        days = int(period.replace('d', ''))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        metrics = self.get_metrics(start_date=start_date)
        
        # Group by date
        cost_by_date = {}
        for metric in metrics:
            date = datetime.fromisoformat(metric.timestamp).date()
            date_str = date.isoformat()
            
            if date_str not in cost_by_date:
                cost_by_date[date_str] = 0
            
            cost_by_date[date_str] += metric.estimated_monthly_cost
        
        # Convert to list
        trend = [
            {'date': date, 'cost': round(cost, 2)}
            for date, cost in sorted(cost_by_date.items())
        ]
        
        return trend
