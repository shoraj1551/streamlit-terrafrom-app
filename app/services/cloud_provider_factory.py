"""
Cloud Provider Factory

Creates appropriate cloud provider instances based on configuration.
"""

from typing import Dict, Any
from app.services.cloud_provider import CloudProvider, CloudProviderType
from app.services.providers.azure_provider import AzureProvider
from app.services.providers.gcp_provider import GCPProvider


class CloudProviderFactory:
    """Factory for creating cloud provider instances"""
    
    _providers = {
        CloudProviderType.AZURE: AzureProvider,
        CloudProviderType.GCP: GCPProvider,
    }
    
    @classmethod
    def create(cls, provider_type: str) -> CloudProvider:
        """
        Create a cloud provider instance
        
        Args:
            provider_type: Type of provider ('aws', 'azure', 'gcp')
            
        Returns:
            CloudProvider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        provider_type = provider_type.lower()
        
        # Handle AWS separately (existing implementation)
        if provider_type == CloudProviderType.AWS:
            # AWS uses the existing TerraformGenerator
            from app.services.terraform_generator import TerraformGenerator
            return AWSProviderAdapter()
        
        provider_class = cls._providers.get(provider_type)
        if not provider_class:
            raise ValueError(
                f"Unsupported provider: {provider_type}. "
                f"Supported providers: {', '.join([p.value for p in CloudProviderType])}"
            )
        
        return provider_class()
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names"""
        return [p.value for p in CloudProviderType]


class AWSProviderAdapter(CloudProvider):
    """Adapter for existing AWS implementation"""
    
    @property
    def name(self) -> str:
        return "AWS"
    
    @property
    def regions(self) -> list[str]:
        return [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1",
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
        ]
    
    def generate_terraform(self, config: Dict[str, Any]) -> str:
        """Use existing TerraformGenerator"""
        from app.services.terraform_generator import TerraformGenerator
        from config_parser import InfrastructureConfig
        
        # Convert dict to InfrastructureConfig
        infra_config = InfrastructureConfig(**config)
        return TerraformGenerator.preview_config(infra_config)
    
    def estimate_cost(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Use existing AWSCostEstimator"""
        from app.services.cost_estimator import AWSCostEstimator
        
        estimator = AWSCostEstimator()
        return estimator.estimate_ec2_cost(config.get('instance_type', 't2.micro'))
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, str | None]:
        """Validate AWS configuration"""
        required_fields = ['region', 'instance_type']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        return True, None
    
    def get_instance_types(self) -> Dict[str, Dict[str, Any]]:
        """Get AWS instance types"""
        from app.services.cost_estimator import AWSCostEstimator
        return AWSCostEstimator.INSTANCE_PRICING
