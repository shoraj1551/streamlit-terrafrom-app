"""
Models package initialization
"""

from app.models.environment import (
    EnvironmentType,
    EnvironmentConfig,
    ENVIRONMENT_TEMPLATES,
    get_environment_template,
    create_environment_config
)

from app.models.industry import (
    IndustryType,
    IndustryProfile,
    INDUSTRY_TEMPLATES,
    get_industry_profile,
    get_all_industries
)

__all__ = [
    'EnvironmentType',
    'EnvironmentConfig',
    'ENVIRONMENT_TEMPLATES',
    'get_environment_template',
    'create_environment_config',
    'IndustryType',
    'IndustryProfile',
    'INDUSTRY_TEMPLATES',
    'get_industry_profile',
    'get_all_industries'
]
