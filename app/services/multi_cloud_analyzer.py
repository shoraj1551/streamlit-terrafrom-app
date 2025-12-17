"""
Multi-Cloud Cost Analyzer

Comprehensive cost analysis across AWS, Azure, and GCP for all environments.
Generates intelligent recommendations based on requirements and priorities.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from app.services.cloud_provider_factory import CloudProviderFactory
from app.services.priority_engine import PriorityType


@dataclass
class EnvironmentCost:
    """Cost breakdown for a single environment"""
    environment: str
    monthly_cost: float
    yearly_cost: float
    instance_count: int
    instance_type: str
    compute_cost: float
    storage_cost: float
    network_cost: float
    additional_cost: float


@dataclass
class CloudProviderAnalysis:
    """Complete analysis for a cloud provider"""
    provider: str
    dev_cost: EnvironmentCost
    staging_cost: EnvironmentCost
    prod_cost: EnvironmentCost
    total_monthly: float
    total_yearly: float
    three_year_tco: float
    
    # Scoring
    cost_score: float  # 0-10
    performance_score: float
    security_score: float
    scalability_score: float
    compliance_score: float
    support_score: float
    overall_score: float
    
    # Recommendations
    strengths: List[str]
    weaknesses: List[str]
    best_for: List[str]


class MultiCloudAnalyzer:
    """Analyze and compare costs across multiple cloud providers"""
    
    # Provider capability scores (0-10)
    PROVIDER_SCORES = {
        "aws": {
            "performance": 9.0,
            "security": 9.5,
            "scalability": 10.0,
            "compliance": 9.5,
            "support": 9.0,
            "ease_of_use": 7.0,
            "strengths": [
                "Largest service portfolio",
                "Best global infrastructure",
                "Excellent auto-scaling",
                "Mature compliance certifications"
            ],
            "weaknesses": [
                "Can be expensive",
                "Complex pricing",
                "Steep learning curve"
            ],
            "best_for": [
                "Enterprise applications",
                "Complex architectures",
                "Global deployments"
            ]
        },
        "azure": {
            "performance": 8.5,
            "security": 9.0,
            "scalability": 8.5,
            "compliance": 9.5,
            "support": 8.5,
            "ease_of_use": 8.0,
            "strengths": [
                "Excellent for Microsoft stack",
                "Strong HIPAA/healthcare support",
                "Good hybrid cloud capabilities",
                "Enterprise-friendly"
            ],
            "weaknesses": [
                "Smaller service catalog than AWS",
                "Some regional limitations",
                "Mid-range pricing"
            ],
            "best_for": [
                "Healthcare applications",
                "Microsoft-based workloads",
                "Hybrid cloud scenarios"
            ]
        },
        "gcp": {
            "performance": 9.5,
            "security": 8.5,
            "scalability": 9.0,
            "compliance": 8.0,
            "support": 7.5,
            "ease_of_use": 9.0,
            "strengths": [
                "Best pricing (often 20-30% cheaper)",
                "Excellent for AI/ML (TPUs)",
                "Superior network performance",
                "Simple, transparent pricing"
            ],
            "weaknesses": [
                "Smaller market share",
                "Fewer compliance certifications",
                "Less enterprise support"
            ],
            "best_for": [
                "Startups and cost-conscious companies",
                "AI/ML workloads",
                "Data analytics",
                "Modern cloud-native apps"
            ]
        }
    }
    
    def __init__(self):
        self.analyses_file = Path("data/cloud_analyses.json")
        self.analyses_file.parent.mkdir(parents=True, exist_ok=True)
    
    def analyze_all_providers(
        self,
        requirements: Dict[str, Any],
        priority_scores: Dict[str, float],
        industry: str
    ) -> Dict[str, CloudProviderAnalysis]:
        """
        Analyze all cloud providers
        
        Args:
            requirements: Infrastructure requirements
            priority_scores: User priority scores
            industry: Industry type
            
        Returns:
            Analysis for each provider
        """
        analyses = {}
        
        for provider in ["aws", "azure", "gcp"]:
            analysis = self._analyze_provider(
                provider,
                requirements,
                priority_scores,
                industry
            )
            analyses[provider] = analysis
        
        return analyses
    
    def _analyze_provider(
        self,
        provider: str,
        requirements: Dict[str, Any],
        priority_scores: Dict[str, float],
        industry: str
    ) -> CloudProviderAnalysis:
        """Analyze a single cloud provider"""
        
        # Calculate costs for each environment
        dev_cost = self._calculate_environment_cost(
            provider, requirements, "dev"
        )
        
        staging_cost = self._calculate_environment_cost(
            provider, requirements, "staging"
        )
        
        prod_cost = self._calculate_environment_cost(
            provider, requirements, "prod"
        )
        
        # Calculate totals
        total_monthly = (
            dev_cost.monthly_cost +
            staging_cost.monthly_cost +
            prod_cost.monthly_cost
        )
        
        total_yearly = total_monthly * 12
        
        # 3-year TCO with 10% discount for reserved instances
        three_year_tco = total_yearly * 3 * 0.9
        
        # Calculate scores
        cost_score = self._calculate_cost_score(total_monthly)
        
        provider_scores = self.PROVIDER_SCORES[provider]
        
        # Calculate overall score based on priorities
        overall_score = self._calculate_overall_score(
            provider,
            cost_score,
            provider_scores,
            priority_scores
        )
        
        return CloudProviderAnalysis(
            provider=provider,
            dev_cost=dev_cost,
            staging_cost=staging_cost,
            prod_cost=prod_cost,
            total_monthly=round(total_monthly, 2),
            total_yearly=round(total_yearly, 2),
            three_year_tco=round(three_year_tco, 2),
            cost_score=cost_score,
            performance_score=provider_scores["performance"],
            security_score=provider_scores["security"],
            scalability_score=provider_scores["scalability"],
            compliance_score=provider_scores["compliance"],
            support_score=provider_scores["support"],
            overall_score=round(overall_score, 2),
            strengths=provider_scores["strengths"],
            weaknesses=provider_scores["weaknesses"],
            best_for=provider_scores["best_for"]
        )
    
    def _calculate_environment_cost(
        self,
        provider: str,
        requirements: Dict[str, Any],
        environment: str
    ) -> EnvironmentCost:
        """Calculate cost for a specific environment"""
        
        # Environment-specific multipliers
        env_config = {
            "dev": {
                "instance_count": 1,
                "instance_size_multiplier": 0.5,  # Smaller instances
                "storage_multiplier": 0.3,
                "network_multiplier": 0.2
            },
            "staging": {
                "instance_count": requirements['scaling']['min_instances'],
                "instance_size_multiplier": 0.75,
                "storage_multiplier": 0.6,
                "network_multiplier": 0.5
            },
            "prod": {
                "instance_count": requirements['scaling']['max_instances'],
                "instance_size_multiplier": 1.0,
                "storage_multiplier": 1.0,
                "network_multiplier": 1.0
            }
        }
        
        config = env_config[environment]
        
        # Base compute cost (per instance per month)
        base_compute = self._get_base_compute_cost(
            provider,
            requirements['compute']['cpu_cores'],
            requirements['compute']['ram_gb'],
            requirements['compute']['gpu_required']
        )
        
        compute_cost = base_compute * config['instance_size_multiplier'] * config['instance_count']
        
        # Storage cost
        storage_gb = requirements['storage']['size_gb'] * config['storage_multiplier']
        storage_cost = self._get_storage_cost(provider, storage_gb, requirements['storage']['type'])
        
        # Network cost
        network_cost = self._get_network_cost(
            provider,
            requirements['network']['bandwidth_gbps'] * config['network_multiplier'],
            requirements['network']['load_balancer']
        )
        
        # Additional costs (backups, monitoring, etc.)
        additional_cost = 0
        if environment == "prod":
            additional_cost += 50  # Monitoring
            if requirements['availability']['multi_region']:
                additional_cost += 100  # Multi-region
        
        monthly_cost = compute_cost + storage_cost + network_cost + additional_cost
        
        # Determine instance type
        instance_type = self._get_instance_type(
            provider,
            requirements['compute']['cpu_cores'] * config['instance_size_multiplier'],
            requirements['compute']['ram_gb'] * config['instance_size_multiplier']
        )
        
        return EnvironmentCost(
            environment=environment,
            monthly_cost=round(monthly_cost, 2),
            yearly_cost=round(monthly_cost * 12, 2),
            instance_count=config['instance_count'],
            instance_type=instance_type,
            compute_cost=round(compute_cost, 2),
            storage_cost=round(storage_cost, 2),
            network_cost=round(network_cost, 2),
            additional_cost=round(additional_cost, 2)
        )
    
    def _get_base_compute_cost(
        self,
        provider: str,
        cpu_cores: int,
        ram_gb: int,
        gpu_required: bool
    ) -> float:
        """Get base compute cost per month"""
        
        if gpu_required:
            # GPU instance pricing
            gpu_costs = {
                "aws": 650,  # p3.2xlarge
                "azure": 700,  # NC6s_v3
                "gcp": 550  # n1-standard-8 + T4
            }
            return gpu_costs[provider]
        
        # Regular instance pricing (approximate)
        # Cost per vCPU per month
        cpu_cost_per_core = {
            "aws": 15,
            "azure": 13,
            "gcp": 11
        }
        
        # Cost per GB RAM per month
        ram_cost_per_gb = {
            "aws": 4,
            "azure": 3.5,
            "gcp": 3
        }
        
        cpu_cost = cpu_cores * cpu_cost_per_core[provider]
        ram_cost = ram_gb * ram_cost_per_gb[provider]
        
        return cpu_cost + ram_cost
    
    def _get_storage_cost(self, provider: str, size_gb: int, storage_type: str) -> float:
        """Get storage cost per month"""
        
        # Cost per GB per month
        storage_costs = {
            "aws": {"ssd": 0.10, "hdd": 0.045},
            "azure": {"ssd": 0.12, "hdd": 0.05},
            "gcp": {"ssd": 0.17, "hdd": 0.04}
        }
        
        cost_per_gb = storage_costs[provider][storage_type]
        return size_gb * cost_per_gb
    
    def _get_network_cost(self, provider: str, bandwidth_gbps: float, load_balancer: bool) -> float:
        """Get network cost per month"""
        
        # Base network cost
        network_costs = {
            "aws": 50,
            "azure": 45,
            "gcp": 40
        }
        
        base_cost = network_costs[provider] * bandwidth_gbps
        
        # Load balancer cost
        if load_balancer:
            lb_costs = {"aws": 20, "azure": 18, "gcp": 15}
            base_cost += lb_costs[provider]
        
        return base_cost
    
    def _get_instance_type(self, provider: str, cpu_cores: float, ram_gb: float) -> str:
        """Get recommended instance type"""
        
        instance_types = {
            "aws": {
                (2, 8): "t3.medium",
                (4, 16): "t3.xlarge",
                (8, 32): "t3.2xlarge",
                (16, 64): "m5.4xlarge"
            },
            "azure": {
                (2, 8): "Standard_B2s",
                (4, 16): "Standard_D4s_v3",
                (8, 32): "Standard_D8s_v3",
                (16, 64): "Standard_D16s_v3"
            },
            "gcp": {
                (2, 8): "e2-standard-2",
                (4, 16): "e2-standard-4",
                (8, 32): "e2-standard-8",
                (16, 64): "e2-standard-16"
            }
        }
        
        # Find closest match
        for (cores, ram), instance in instance_types[provider].items():
            if cpu_cores <= cores and ram_gb <= ram:
                return instance
        
        return "custom"
    
    def _calculate_cost_score(self, monthly_cost: float) -> float:
        """Calculate cost score (0-10, higher is better/cheaper)"""
        
        # Score based on monthly cost
        # $0-500: 10
        # $500-1000: 8
        # $1000-2000: 6
        # $2000-5000: 4
        # $5000+: 2
        
        if monthly_cost < 500:
            return 10.0
        elif monthly_cost < 1000:
            return 8.0
        elif monthly_cost < 2000:
            return 6.0
        elif monthly_cost < 5000:
            return 4.0
        else:
            return 2.0
    
    def _calculate_overall_score(
        self,
        provider: str,
        cost_score: float,
        provider_scores: Dict[str, float],
        priority_scores: Dict[str, float]
    ) -> float:
        """Calculate weighted overall score based on priorities"""
        
        # Map priorities to provider capabilities
        score_mapping = {
            "cost": cost_score,
            "performance": provider_scores["performance"],
            "security": provider_scores["security"],
            "scalability": provider_scores["scalability"],
            "compliance": provider_scores["compliance"],
            "support": provider_scores["support"],
            "ease_of_use": provider_scores["ease_of_use"],
            "availability": provider_scores["scalability"]  # Use scalability as proxy
        }
        
        # Calculate weighted score
        total_weight = sum(priority_scores.values())
        if total_weight == 0:
            total_weight = 1
        
        weighted_score = 0
        for priority, weight in priority_scores.items():
            if priority in score_mapping:
                weighted_score += score_mapping[priority] * (weight / total_weight)
        
        return weighted_score
    
    def get_recommendation(
        self,
        analyses: Dict[str, CloudProviderAnalysis],
        priority_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Get intelligent recommendation
        
        Returns:
            Recommendation with primary and optional secondary provider
        """
        # Sort by overall score
        sorted_providers = sorted(
            analyses.items(),
            key=lambda x: x[1].overall_score,
            reverse=True
        )
        
        primary = sorted_providers[0]
        secondary = sorted_providers[1] if len(sorted_providers) > 1 else None
        
        # Determine if multi-cloud is recommended
        multi_cloud_recommended = False
        multi_cloud_strategy = None
        
        if secondary and (primary[1].overall_score - secondary[1].overall_score) < 1.0:
            # Scores are close, consider multi-cloud
            if priority_scores.get("cost", 0) > 7:
                # Cost-conscious: use cheaper for dev/staging
                multi_cloud_recommended = True
                multi_cloud_strategy = f"Use {secondary[0].upper()} for dev/staging (cheaper), {primary[0].upper()} for production (better overall)"
        
        return {
            "primary_provider": primary[0],
            "primary_analysis": primary[1],
            "secondary_provider": secondary[0] if secondary else None,
            "secondary_analysis": secondary[1] if secondary else None,
            "multi_cloud_recommended": multi_cloud_recommended,
            "multi_cloud_strategy": multi_cloud_strategy,
            "confidence": "high" if primary[1].overall_score > 7.5 else "medium",
            "reasoning": self._generate_reasoning(primary[1], priority_scores)
        }
    
    def _generate_reasoning(
        self,
        analysis: CloudProviderAnalysis,
        priority_scores: Dict[str, float]
    ) -> str:
        """Generate human-readable reasoning"""
        
        top_priority = max(priority_scores.items(), key=lambda x: x[1])[0]
        
        reasoning = f"Recommended {analysis.provider.upper()} based on your priorities. "
        
        if top_priority == "cost":
            reasoning += f"With a total monthly cost of ${analysis.total_monthly}, it offers the best value. "
        elif top_priority == "performance":
            reasoning += f"It scores {analysis.performance_score}/10 for performance. "
        elif top_priority == "security":
            reasoning += f"It scores {analysis.security_score}/10 for security. "
        
        reasoning += f"Overall score: {analysis.overall_score}/10."
        
        return reasoning
    
    def save_analysis(
        self,
        user_email: str,
        analyses: Dict[str, CloudProviderAnalysis],
        recommendation: Dict[str, Any]
    ) -> str:
        """Save analysis results"""
        
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Convert to dict for JSON serialization
        analyses_dict = {
            provider: {
                "provider": analysis.provider,
                "total_monthly": analysis.total_monthly,
                "total_yearly": analysis.total_yearly,
                "three_year_tco": analysis.three_year_tco,
                "overall_score": analysis.overall_score,
                "dev_cost": analysis.dev_cost.monthly_cost,
                "staging_cost": analysis.staging_cost.monthly_cost,
                "prod_cost": analysis.prod_cost.monthly_cost
            }
            for provider, analysis in analyses.items()
        }
        
        data = {
            "analysis_id": analysis_id,
            "user_email": user_email,
            "analyses": analyses_dict,
            "recommendation": {
                "primary_provider": recommendation["primary_provider"],
                "confidence": recommendation["confidence"],
                "reasoning": recommendation["reasoning"]
            },
            "created_at": datetime.utcnow().isoformat()
        }
        
        analysis_file = Path(f"data/analyses/{analysis_id}.json")
        analysis_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(analysis_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return analysis_id
