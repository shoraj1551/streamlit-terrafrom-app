"""
Environment Selector Page

Select and manage deployment environments (dev/staging/prod).
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.models.environment import EnvironmentType, ENVIRONMENT_TEMPLATES, create_environment_config
from app.services.environment_manager import EnvironmentManager
from app.services.deployment_db import DeploymentDatabase
from app.services.cloud_provider_factory import CloudProviderFactory

# Page configuration
st.set_page_config(
    page_title="Environment Management",
    page_icon="🌍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(-45deg, #0f172a, #1e293b, #334155, #1e293b);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .env-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 1rem 0;
    }
    
    .env-dev { border-left: 4px solid #3b82f6; }
    .env-staging { border-left: 4px solid #fbbf24; }
    .env-prod { border-left: 4px solid #ef4444; }
</style>
""", unsafe_allow_html=True)

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = DeploymentDatabase()

if 'env_manager' not in st.session_state:
    st.session_state.env_manager = EnvironmentManager(st.session_state.db)

# Header
st.title("🌍 Environment Management")
st.markdown("Configure and manage deployment environments")

# Environment selector
st.markdown("### Select Environment")
col1, col2, col3 = st.columns(3)

with col1:
    dev_selected = st.button(
        "🔵 Development",
        use_container_width=True,
        type="primary" if st.session_state.get('selected_env') == 'dev' else "secondary"
    )
    if dev_selected:
        st.session_state.selected_env = 'dev'

with col2:
    staging_selected = st.button(
        "🟡 Staging",
        use_container_width=True,
        type="primary" if st.session_state.get('selected_env') == 'staging' else "secondary"
    )
    if staging_selected:
        st.session_state.selected_env = 'staging'

with col3:
    prod_selected = st.button(
        "🔴 Production",
        use_container_width=True,
        type="primary" if st.session_state.get('selected_env') == 'prod' else "secondary"
    )
    if prod_selected:
        st.session_state.selected_env = 'prod'

st.markdown("---")

# Display environment details
if 'selected_env' in st.session_state:
    env_type = EnvironmentType(st.session_state.selected_env)
    template = ENVIRONMENT_TEMPLATES[env_type]
    
    # Environment header
    env_icons = {'dev': '🔵', 'staging': '🟡', 'prod': '🔴'}
    env_colors = {'dev': 'env-dev', 'staging': 'env-staging', 'prod': 'env-prod'}
    
    st.markdown(f"## {env_icons[st.session_state.selected_env]} {env_type.value.title()} Environment")
    st.caption(template['description'])
    
    # Configuration form
    with st.form("env_config_form"):
        st.markdown("### Configuration")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            cloud_provider = st.selectbox(
                "Cloud Provider",
                options=CloudProviderFactory.get_available_providers(),
                format_func=lambda x: x.upper()
            )
            
            # Get provider to show regions
            provider = CloudProviderFactory.create(cloud_provider)
            region = st.selectbox(
                "Region",
                options=provider.regions[:10]  # Show first 10 regions
            )
        
        with col_b:
            # Get instance types
            instance_types = list(provider.get_instance_types().keys())
            instance_type = st.selectbox(
                "Instance Type",
                options=instance_types[:10]  # Show first 10 types
            )
        
        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            col_adv1, col_adv2 = st.columns(2)
            
            with col_adv1:
                auto_scaling = st.checkbox(
                    "Auto Scaling",
                    value=template['auto_scaling']
                )
                backup_enabled = st.checkbox(
                    "Backup Enabled",
                    value=template['backup_enabled']
                )
                monitoring_enabled = st.checkbox(
                    "Monitoring Enabled",
                    value=template['monitoring_enabled']
                )
            
            with col_adv2:
                min_instances = st.number_input(
                    "Min Instances",
                    min_value=1,
                    max_value=100,
                    value=template['min_instances']
                )
                max_instances = st.number_input(
                    "Max Instances",
                    min_value=1,
                    max_value=100,
                    value=template['max_instances']
                )
                backup_retention = st.number_input(
                    "Backup Retention (days)",
                    min_value=1,
                    max_value=365,
                    value=template['backup_retention_days']
                )
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Configuration", use_container_width=True)
        
        if submitted:
            # Create environment config
            env_config = create_environment_config(
                env_type=env_type,
                cloud_provider=cloud_provider,
                region=region,
                instance_type=instance_type,
                auto_scaling=auto_scaling,
                backup_enabled=backup_enabled,
                monitoring_enabled=monitoring_enabled,
                min_instances=min_instances,
                max_instances=max_instances,
                backup_retention_days=backup_retention
            )
            
            # Estimate cost
            cost_estimate = st.session_state.env_manager.get_environment_cost_estimate(env_config)
            
            st.success(f"✅ {env_type.value.title()} environment configured!")
            
            # Show cost estimate
            st.markdown("### 💰 Cost Estimate")
            col_cost1, col_cost2, col_cost3 = st.columns(3)
            
            with col_cost1:
                st.metric("Monthly Cost", f"${cost_estimate['monthly']}")
            with col_cost2:
                st.metric("Yearly Cost", f"${cost_estimate['yearly']}")
            with col_cost3:
                st.metric("Instances", f"{cost_estimate['instances']}")
            
            st.caption(f"💡 ${cost_estimate['per_instance']}/month per instance")

# Environment comparison
st.markdown("---")
st.markdown("### 📊 Environment Comparison")

comparison_data = []
for env_type in EnvironmentType:
    template = ENVIRONMENT_TEMPLATES[env_type]
    comparison_data.append({
        "Environment": env_type.value.title(),
        "Auto Scaling": "✅" if template['auto_scaling'] else "❌",
        "Backup": "✅" if template['backup_enabled'] else "❌",
        "Min Instances": template['min_instances'],
        "Max Instances": template['max_instances'],
        "Retention": f"{template['backup_retention_days']} days"
    })

st.table(comparison_data)

# Footer
st.markdown("---")
st.caption("💡 Tip: Use dev for testing, staging for pre-production, and prod for live deployments")
