from typing import Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AWSCostEstimator:
    """Estimate AWS costs for infrastructure deployments"""
    
    # EC2 On-Demand Pricing (us-east-1, Linux, per hour)
    # Source: AWS Pricing as of Dec 2025 (approximate)
    EC2_PRICING = {
        # T2 instances
        "t2.nano": 0.0058,
        "t2.micro": 0.0116,
        "t2.small": 0.023,
        "t2.medium": 0.0464,
        "t2.large": 0.0928,
        "t2.xlarge": 0.1856,
        "t2.2xlarge": 0.3712,
        
        # T3 instances
        "t3.nano": 0.0052,
        "t3.micro": 0.0104,
        "t3.small": 0.0208,
        "t3.medium": 0.0416,
        "t3.large": 0.0832,
        "t3.xlarge": 0.1664,
        "t3.2xlarge": 0.3328,
        
        # T4g instances (ARM-based, cheaper)
        "t4g.nano": 0.0042,
        "t4g.micro": 0.0084,
        "t4g.small": 0.0168,
        "t4g.medium": 0.0336,
        "t4g.large": 0.0672,
        
        # M5 instances
        "m5.large": 0.096,
        "m5.xlarge": 0.192,
        "m5.2xlarge": 0.384,
        "m5.4xlarge": 0.768,
        
        # C5 instances (compute optimized)
        "c5.large": 0.085,
        "c5.xlarge": 0.17,
        "c5.2xlarge": 0.34,
    }
    
    # EBS Storage Pricing (per GB-month)
    EBS_PRICING = {
        "gp3": 0.08,    # General Purpose SSD (gp3)
        "gp2": 0.10,    # General Purpose SSD (gp2)
        "io2": 0.125,   # Provisioned IOPS SSD
        "st1": 0.045,   # Throughput Optimized HDD
        "sc1": 0.015,   # Cold HDD
    }
    
    # Data Transfer Pricing (per GB)
    DATA_TRANSFER_OUT = 0.09  # First 10 TB/month
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize cost estimator
        
        Args:
            region: AWS region (pricing may vary by region)
        """
        self.region = region
        logger.info(f"Initialized AWSCostEstimator for region: {region}")
    
    def estimate_ec2_cost(
        self,
        instance_type: str,
        hours_per_month: int = 730,  # ~30 days
        storage_gb: int = 30,
        storage_type: str = "gp3"
    ) -> Dict[str, Any]:
        """
        Estimate EC2 instance cost
        
        Args:
            instance_type: EC2 instance type (e.g., t2.micro)
            hours_per_month: Hours to run per month (default: 730 = 24/7)
            storage_gb: Root volume size in GB
            storage_type: EBS volume type
            
        Returns:
            Dictionary with cost breakdown
        """
        # Get hourly rate
        hourly_rate = self.EC2_PRICING.get(instance_type.lower())
        
        if hourly_rate is None:
            logger.warning(f"Unknown instance type: {instance_type}, using default estimate")
            hourly_rate = 0.05  # Default estimate
        
        # Calculate compute costs
        monthly_compute = hourly_rate * hours_per_month
        yearly_compute = hourly_rate * 8760  # 365 days
        
        # Calculate storage costs
        storage_rate = self.EBS_PRICING.get(storage_type, 0.08)
        monthly_storage = storage_gb * storage_rate
        yearly_storage = monthly_storage * 12
        
        # Total costs
        monthly_total = monthly_compute + monthly_storage
        yearly_total = yearly_compute + yearly_storage
        
        return {
            "instance_type": instance_type,
            "region": self.region,
            "compute": {
                "hourly": round(hourly_rate, 4),
                "daily": round(hourly_rate * 24, 4),
                "monthly": round(monthly_compute, 2),
                "yearly": round(yearly_compute, 2)
            },
            "storage": {
                "size_gb": storage_gb,
                "type": storage_type,
                "monthly": round(monthly_storage, 2),
                "yearly": round(yearly_storage, 2)
            },
            "total": {
                "monthly": round(monthly_total, 2),
                "yearly": round(yearly_total, 2)
            },
            "assumptions": {
                "hours_per_month": hours_per_month,
                "uptime_percentage": round((hours_per_month / 730) * 100, 1)
            }
        }
    
    def estimate_deployment_cost(
        self,
        config: Dict[str, Any],
        duration_months: int = 1
    ) -> Dict[str, Any]:
        """
        Estimate total deployment cost from configuration
        
        Args:
            config: Infrastructure configuration
            duration_months: Number of months to estimate
            
        Returns:
            Cost estimate dictionary
        """
        instance_type = config.get("instance_type", "t2.micro")
        
        # Get single month estimate
        monthly_estimate = self.estimate_ec2_cost(instance_type)
        
        # Calculate for duration
        total_cost = monthly_estimate["total"]["monthly"] * duration_months
        
        return {
            "monthly_breakdown": monthly_estimate,
            "duration_months": duration_months,
            "total_estimated_cost": round(total_cost, 2),
            "currency": "USD",
            "disclaimer": "Estimates are approximate. Actual costs may vary based on usage, region, and AWS pricing changes."
        }
    
    def get_free_tier_info(self, instance_type: str) -> Dict[str, Any]:
        """
        Get AWS Free Tier information for instance type
        
        Args:
            instance_type: EC2 instance type
            
        Returns:
            Free tier eligibility info
        """
        free_tier_eligible = instance_type.lower() in ["t2.micro", "t3.micro"]
        
        return {
            "eligible": free_tier_eligible,
            "details": {
                "hours_per_month": 750 if free_tier_eligible else 0,
                "storage_gb": 30 if free_tier_eligible else 0,
                "data_transfer_gb": 15 if free_tier_eligible else 0,
                "duration": "12 months from account creation"
            } if free_tier_eligible else None,
            "note": "Free tier eligible for new AWS accounts" if free_tier_eligible else "Not eligible for free tier"
        }
    
    def compare_instance_types(self, instance_types: list) -> Dict[str, Any]:
        """
        Compare costs across multiple instance types
        
        Args:
            instance_types: List of instance types to compare
            
        Returns:
            Comparison dictionary
        """
        comparisons = []
        
        for instance_type in instance_types:
            estimate = self.estimate_ec2_cost(instance_type)
            free_tier = self.get_free_tier_info(instance_type)
            
            comparisons.append({
                "instance_type": instance_type,
                "monthly_cost": estimate["total"]["monthly"],
                "yearly_cost": estimate["total"]["yearly"],
                "free_tier_eligible": free_tier["eligible"]
            })
        
        # Sort by monthly cost
        comparisons.sort(key=lambda x: x["monthly_cost"])
        
        return {
            "comparisons": comparisons,
            "cheapest": comparisons[0] if comparisons else None,
            "most_expensive": comparisons[-1] if comparisons else None
        }
