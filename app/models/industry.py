"""
Industry-Specific Use Cases and Templates

Defines industry types and their specific infrastructure requirements.
"""

from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel


class IndustryType(str, Enum):
    """Supported industry types"""
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    EDTECH = "edtech"
    GAMING = "gaming"
    MEDIA = "media"
    IOT = "iot"
    AI_ML = "ai_ml"
    LOGISTICS = "logistics"


class IndustryProfile(BaseModel):
    """Industry-specific profile and requirements"""
    name: str
    display_name: str
    description: str
    icon: str
    
    # Infrastructure requirements
    recommended_provider: str
    recommended_regions: List[str]
    min_instances: int
    recommended_instance_types: Dict[str, str]  # provider -> instance_type
    
    # Compliance and features
    compliance_requirements: List[str]
    required_features: List[str]
    backup_critical: bool
    high_availability: bool
    
    # Cost profile
    typical_monthly_cost_range: str
    cost_optimization_tips: List[str]


# Industry templates
INDUSTRY_TEMPLATES = {
    IndustryType.FINTECH: IndustryProfile(
        name="fintech",
        display_name="FinTech & Banking",
        description="Financial services requiring high security, compliance, and reliability",
        icon="💰",
        recommended_provider="aws",
        recommended_regions=["us-east-1", "eu-west-1", "ap-southeast-1"],
        min_instances=2,
        recommended_instance_types={
            "aws": "t3.medium",
            "azure": "Standard_D2s_v3",
            "gcp": "n2-standard-2"
        },
        compliance_requirements=["PCI-DSS", "SOC 2", "GDPR", "ISO 27001"],
        required_features=["Encryption at rest", "Encryption in transit", "Audit logging", "Multi-region backup"],
        backup_critical=True,
        high_availability=True,
        typical_monthly_cost_range="$200-$1000",
        cost_optimization_tips=[
            "Use reserved instances for production",
            "Implement auto-scaling for peak hours",
            "Archive old transaction data to cold storage"
        ]
    ),
    
    IndustryType.HEALTHTECH: IndustryProfile(
        name="healthtech",
        display_name="HealthTech & Medical",
        description="Healthcare applications with HIPAA compliance and patient data protection",
        icon="🏥",
        recommended_provider="azure",
        recommended_regions=["eastus", "westeurope", "australiaeast"],
        min_instances=2,
        recommended_instance_types={
            "aws": "t3.medium",
            "azure": "Standard_D2s_v3",
            "gcp": "n2-standard-2"
        },
        compliance_requirements=["HIPAA", "HITECH", "GDPR", "SOC 2"],
        required_features=["PHI encryption", "Access controls", "Audit trails", "Data residency"],
        backup_critical=True,
        high_availability=True,
        typical_monthly_cost_range="$300-$1500",
        cost_optimization_tips=[
            "Use dedicated instances for compliance",
            "Implement data lifecycle policies",
            "Optimize storage for medical imaging"
        ]
    ),
    
    IndustryType.ECOMMERCE: IndustryProfile(
        name="ecommerce",
        display_name="E-Commerce & Retail",
        description="Online retail platforms requiring scalability and performance",
        icon="🛒",
        recommended_provider="gcp",
        recommended_regions=["us-central1", "europe-west1", "asia-southeast1"],
        min_instances=2,
        recommended_instance_types={
            "aws": "t3.medium",
            "azure": "Standard_B2ms",
            "gcp": "e2-standard-2"
        },
        compliance_requirements=["PCI-DSS", "GDPR"],
        required_features=["CDN integration", "Auto-scaling", "Session management", "Cache layer"],
        backup_critical=True,
        high_availability=True,
        typical_monthly_cost_range="$150-$800",
        cost_optimization_tips=[
            "Use CDN for static assets",
            "Implement aggressive caching",
            "Scale down during off-peak hours",
            "Use spot instances for batch jobs"
        ]
    ),
    
    IndustryType.SAAS: IndustryProfile(
        name="saas",
        display_name="SaaS & B2B Software",
        description="Software-as-a-Service platforms with multi-tenancy support",
        icon="☁️",
        recommended_provider="aws",
        recommended_regions=["us-east-1", "eu-west-1", "ap-northeast-1"],
        min_instances=2,
        recommended_instance_types={
            "aws": "t3.medium",
            "azure": "Standard_B2s",
            "gcp": "e2-standard-2"
        },
        compliance_requirements=["SOC 2", "ISO 27001", "GDPR"],
        required_features=["Multi-tenancy", "API rate limiting", "Usage metering", "Auto-scaling"],
        backup_critical=True,
        high_availability=True,
        typical_monthly_cost_range="$100-$600",
        cost_optimization_tips=[
            "Use containerization for efficiency",
            "Implement tenant-based resource allocation",
            "Optimize database queries",
            "Use serverless for background jobs"
        ]
    ),
    
    IndustryType.EDTECH: IndustryProfile(
        name="edtech",
        display_name="EdTech & E-Learning",
        description="Educational platforms with video streaming and content delivery",
        icon="📚",
        recommended_provider="gcp",
        recommended_regions=["us-central1", "europe-west1", "asia-south1"],
        min_instances=1,
        recommended_instance_types={
            "aws": "t3.medium",
            "azure": "Standard_B2ms",
            "gcp": "e2-medium"
        },
        compliance_requirements=["FERPA", "COPPA", "GDPR"],
        required_features=["Video streaming", "CDN", "Content storage", "User analytics"],
        backup_critical=True,
        high_availability=False,
        typical_monthly_cost_range="$80-$400",
        cost_optimization_tips=[
            "Use CDN for video content",
            "Implement adaptive bitrate streaming",
            "Archive old course materials",
            "Scale based on academic calendar"
        ]
    ),
    
    IndustryType.GAMING: IndustryProfile(
        name="gaming",
        display_name="Gaming & Entertainment",
        description="Gaming platforms requiring low latency and high performance",
        icon="🎮",
        recommended_provider="aws",
        recommended_regions=["us-west-2", "eu-central-1", "ap-northeast-1"],
        min_instances=3,
        recommended_instance_types={
            "aws": "c5.large",
            "azure": "Standard_F2s_v2",
            "gcp": "c2-standard-4"
        },
        compliance_requirements=["GDPR", "Age verification"],
        required_features=["Low latency", "DDoS protection", "Real-time multiplayer", "Leaderboards"],
        backup_critical=True,
        high_availability=True,
        typical_monthly_cost_range="$300-$2000",
        cost_optimization_tips=[
            "Use spot instances for game servers",
            "Implement regional matchmaking",
            "Scale based on player count",
            "Use dedicated gaming instances"
        ]
    ),
    
    IndustryType.MEDIA: IndustryProfile(
        name="media",
        display_name="Media & Streaming",
        description="Media platforms with content delivery and streaming capabilities",
        icon="🎬",
        recommended_provider="gcp",
        recommended_regions=["us-central1", "europe-west1", "asia-east1"],
        min_instances=2,
        recommended_instance_types={
            "aws": "t3.large",
            "azure": "Standard_D4s_v3",
            "gcp": "n2-standard-4"
        },
        compliance_requirements=["DMCA", "GDPR"],
        required_features=["Video transcoding", "CDN", "DRM", "Analytics"],
        backup_critical=True,
        high_availability=True,
        typical_monthly_cost_range="$400-$2500",
        cost_optimization_tips=[
            "Use CDN for content delivery",
            "Implement tiered storage",
            "Optimize video encoding",
            "Use serverless for transcoding"
        ]
    ),
    
    IndustryType.IOT: IndustryProfile(
        name="iot",
        display_name="IoT & Smart Devices",
        description="IoT platforms managing device fleets and telemetry data",
        icon="📡",
        recommended_provider="azure",
        recommended_regions=["eastus", "westeurope", "southeastasia"],
        min_instances=2,
        recommended_instance_types={
            "aws": "t3.medium",
            "azure": "Standard_B2ms",
            "gcp": "e2-standard-2"
        },
        compliance_requirements=["ISO 27001", "GDPR"],
        required_features=["MQTT broker", "Time-series database", "Device management", "Edge computing"],
        backup_critical=True,
        high_availability=True,
        typical_monthly_cost_range="$200-$1000",
        cost_optimization_tips=[
            "Use time-series databases efficiently",
            "Implement data aggregation at edge",
            "Archive historical telemetry",
            "Use serverless for event processing"
        ]
    ),
    
    IndustryType.AI_ML: IndustryProfile(
        name="ai_ml",
        display_name="AI/ML & Data Science",
        description="Machine learning platforms requiring GPU compute and data processing",
        icon="🤖",
        recommended_provider="gcp",
        recommended_regions=["us-central1", "europe-west4", "asia-northeast1"],
        min_instances=1,
        recommended_instance_types={
            "aws": "p3.2xlarge",
            "azure": "Standard_NC6",
            "gcp": "n1-standard-8"
        },
        compliance_requirements=["SOC 2", "ISO 27001"],
        required_features=["GPU support", "Large storage", "Jupyter notebooks", "Model versioning"],
        backup_critical=True,
        high_availability=False,
        typical_monthly_cost_range="$500-$3000",
        cost_optimization_tips=[
            "Use spot instances for training",
            "Implement model caching",
            "Optimize batch sizes",
            "Use preemptible VMs for experiments"
        ]
    ),
    
    IndustryType.LOGISTICS: IndustryProfile(
        name="logistics",
        display_name="Logistics & Supply Chain",
        description="Supply chain platforms with real-time tracking and optimization",
        icon="🚚",
        recommended_provider="aws",
        recommended_regions=["us-east-1", "eu-west-1", "ap-southeast-2"],
        min_instances=2,
        recommended_instance_types={
            "aws": "t3.medium",
            "azure": "Standard_B2s",
            "gcp": "e2-standard-2"
        },
        compliance_requirements=["ISO 27001", "GDPR"],
        required_features=["Real-time tracking", "Route optimization", "Geolocation", "Mobile APIs"],
        backup_critical=True,
        high_availability=True,
        typical_monthly_cost_range="$150-$700",
        cost_optimization_tips=[
            "Use geospatial databases efficiently",
            "Implement caching for routes",
            "Optimize API calls",
            "Use serverless for notifications"
        ]
    )
}


def get_industry_profile(industry: IndustryType) -> IndustryProfile:
    """Get industry profile by type"""
    return INDUSTRY_TEMPLATES[industry]


def get_all_industries() -> List[IndustryProfile]:
    """Get all industry profiles"""
    return list(INDUSTRY_TEMPLATES.values())
