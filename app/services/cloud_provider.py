"""
Cloud Provider Abstraction Layer

Provides a unified interface for all cloud providers (AWS, Azure, GCP).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum


class CloudProviderType(str, Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class CloudProvider(ABC):
    """Base class for all cloud providers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
    
    @property
    @abstractmethod
    def regions(self) -> List[str]:
        """Available regions"""
        pass
    
    @abstractmethod
    def generate_terraform(self, config: Dict[str, Any]) -> str:
        """
        Generate Terraform configuration for this provider
        
        Args:
            config: Deployment configuration
            
        Returns:
            Terraform HCL code as string
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate deployment cost
        
        Args:
            config: Deployment configuration
            
        Returns:
            Cost breakdown dictionary with hourly, monthly, yearly costs
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate configuration for this provider
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def get_instance_types(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available instance/VM types
        
        Returns:
            Dictionary of instance types with specs
        """
        pass
    
    def _format_tags(self, tags: Dict[str, str]) -> str:
        """Format tags for Terraform"""
        if not tags:
            return ""
        
        formatted = []
        for key, value in tags.items():
            formatted.append(f'    {key} = "{value}"')
        return "\n".join(formatted)
