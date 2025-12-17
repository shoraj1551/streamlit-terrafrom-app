"""
Environment Manager

Manages multi-environment deployments and configurations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.environment import EnvironmentConfig, EnvironmentType, create_environment_config
from app.services.deployment_db import DeploymentDatabase


class EnvironmentManager:
    """Manage multi-environment deployments"""
    
    def __init__(self, db: DeploymentDatabase):
        self.db = db
    
    def create_environment(
        self,
        env_type: EnvironmentType,
        cloud_provider: str,
        region: str,
        instance_type: str,
        **kwargs
    ) -> EnvironmentConfig:
        """
        Create a new environment configuration
        
        Args:
            env_type: Environment type (dev/staging/prod)
            cloud_provider: Cloud provider
            region: Deployment region
            instance_type: Instance type
            **kwargs: Additional configuration
            
        Returns:
            Created EnvironmentConfig
        """
        # Create config from template
        env_config = create_environment_config(
            env_type=env_type,
            cloud_provider=cloud_provider,
            region=region,
            instance_type=instance_type,
            created_at=datetime.utcnow().isoformat(),
            **kwargs
        )
        
        # Store in database (to be implemented)
        # self.db.save_environment(env_config)
        
        return env_config
    
    def get_environment(self, env_name: str) -> Optional[EnvironmentConfig]:
        """
        Get environment configuration by name
        
        Args:
            env_name: Environment name
            
        Returns:
            EnvironmentConfig or None
        """
        # Retrieve from database (to be implemented)
        # return self.db.get_environment(env_name)
        return None
    
    def list_environments(self) -> List[EnvironmentConfig]:
        """
        List all environment configurations
        
        Returns:
            List of EnvironmentConfig
        """
        # Retrieve from database (to be implemented)
        # return self.db.list_environments()
        return []
    
    def update_environment(
        self,
        env_name: str,
        updates: Dict[str, Any]
    ) -> EnvironmentConfig:
        """
        Update environment configuration
        
        Args:
            env_name: Environment name
            updates: Configuration updates
            
        Returns:
            Updated EnvironmentConfig
        """
        env_config = self.get_environment(env_name)
        if not env_config:
            raise ValueError(f"Environment not found: {env_name}")
        
        # Update configuration
        updated_config = env_config.copy(update={
            **updates,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        # Save to database (to be implemented)
        # self.db.update_environment(env_name, updated_config)
        
        return updated_config
    
    def delete_environment(self, env_name: str) -> bool:
        """
        Delete environment configuration
        
        Args:
            env_name: Environment name
            
        Returns:
            True if deleted successfully
        """
        # Delete from database (to be implemented)
        # return self.db.delete_environment(env_name)
        return False
    
    def promote_to_environment(
        self,
        source_env: EnvironmentType,
        target_env: EnvironmentType,
        base_config: Dict[str, Any]
    ) -> EnvironmentConfig:
        """
        Promote configuration from one environment to another
        
        This applies the target environment's template settings
        while preserving the base configuration.
        
        Args:
            source_env: Source environment type
            target_env: Target environment type
            base_config: Base configuration to promote
            
        Returns:
            Promoted EnvironmentConfig
        """
        # Create new config with target environment template
        promoted_config = create_environment_config(
            env_type=target_env,
            cloud_provider=base_config['cloud_provider'],
            region=base_config['region'],
            instance_type=base_config['instance_type'],
            # Preserve certain fields from source
            tags={**base_config.get('tags', {}), "PromotedFrom": source_env.value}
        )
        
        return promoted_config
    
    def compare_environments(
        self,
        env1_name: str,
        env2_name: str
    ) -> Dict[str, Any]:
        """
        Compare two environment configurations
        
        Args:
            env1_name: First environment name
            env2_name: Second environment name
            
        Returns:
            Dictionary with differences
        """
        env1 = self.get_environment(env1_name)
        env2 = self.get_environment(env2_name)
        
        if not env1 or not env2:
            raise ValueError("One or both environments not found")
        
        differences = {}
        
        # Compare key fields
        fields_to_compare = [
            'cloud_provider', 'region', 'instance_type',
            'auto_scaling', 'backup_enabled', 'monitoring_enabled',
            'min_instances', 'max_instances', 'backup_retention_days'
        ]
        
        for field in fields_to_compare:
            val1 = getattr(env1, field)
            val2 = getattr(env2, field)
            if val1 != val2:
                differences[field] = {
                    env1_name: val1,
                    env2_name: val2
                }
        
        return differences
    
    def get_environment_cost_estimate(
        self,
        env_config: EnvironmentConfig
    ) -> Dict[str, float]:
        """
        Estimate cost for environment based on configuration
        
        Args:
            env_config: Environment configuration
            
        Returns:
            Cost estimate dictionary
        """
        from app.services.cloud_provider_factory import CloudProviderFactory
        
        provider = CloudProviderFactory.create(env_config.cloud_provider)
        
        # Get base cost
        base_cost = provider.estimate_cost({
            'instance_type': env_config.instance_type,
            'region': env_config.region
        })
        
        # Multiply by number of instances
        monthly_cost = base_cost['total']['monthly'] * env_config.max_instances
        yearly_cost = monthly_cost * 12
        
        return {
            'monthly': round(monthly_cost, 2),
            'yearly': round(yearly_cost, 2),
            'instances': env_config.max_instances,
            'per_instance': base_cost['total']['monthly']
        }
