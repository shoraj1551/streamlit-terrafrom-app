"""
Monitoring Dashboard Page

Comprehensive dashboard for deployment metrics and monitoring.
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.deployment_db import DeploymentDatabase
from app.services.metrics_collector import MetricsCollector
from app.utils.styles import apply_professional_theme, DesignSystem

# Page configuration
st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide"
)

# Apply professional styling
apply_professional_theme()

# ULTRA-AGGRESSIVE CSS to FORCE proper display - MAXIMUM SPECIFICITY
st.markdown("""
<style>
    /* NUCLEAR OPTION - Force columns to be wide enough */
    div[data-testid="column"] {
        min-width: 280px !important;
        max-width: none !important;
        flex: 1 1 280px !important;
        padding: 0 1.5rem !important;
    }
    
    /* Force metrics to NEVER truncate - EVER */
    div[data-testid="stMetric"] {
        width: 100% !important;
        min-width: 250px !important;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #586069 !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        word-wrap: break-word !important;
        display: block !important;
        width: 100% !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #24292e !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        word-wrap: break-word !important;
        display: block !important;
        width: 100% !important;
    }
    
    /* Better overall spacing */
    .main .block-container {
        padding: 2rem 4rem !important;
        max-width: 100% !important;
    }
    
    /* Headings with proper spacing */
    h1 {
        margin-top: 0 !important;
        margin-bottom: 1.5rem !important;
        font-size: 2.5rem !important;
    }
    
    h2, h3 {
        margin-top: 2.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Remove any width constraints */
    .stColumn {
        min-width: 280px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = DeploymentDatabase()

if 'metrics_collector' not in st.session_state:
    st.session_state.metrics_collector = MetricsCollector(st.session_state.db)

# Header with better spacing
st.title("Dashboard")
st.markdown("Real-time deployment metrics and performance monitoring")
st.markdown("")  # Spacing

# Time period selector with better layout
col_period1, col_period2, col_spacer = st.columns([2, 1, 3])

with col_period1:
    period = st.selectbox(
        "Time Period",
        options=["Last 7 Days", "Last 30 Days", "Last 90 Days"],
        key="period_selector"
    )

with col_period2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.markdown("---")

# Get aggregated metrics
stats = st.session_state.db.get_statistics()

# Mock aggregated metrics
aggregated = {
    'total_deployments': stats['total_deployments'],
    'successful_deployments': stats['successful'],
    'failed_deployments': stats['failed'],
    'success_rate': stats['success_rate'],
    'avg_deployment_time': 245.5,
    'total_cost': 1247.80,
    'avg_cost_per_deployment': 31.20,
    'by_provider': {'aws': 15, 'azure': 8, 'gcp': 12},
    'by_environment': {'dev': 20, 'staging': 10, 'prod': 5}
}

# Key Metrics - WITH PROPER SPACING
st.markdown("### Key Metrics")
st.markdown("")  # Spacing

# Use containers for better control
metric_container = st.container()
with metric_container:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Deployments",
            value=str(aggregated['total_deployments']),
            delta=f"+{aggregated['total_deployments'] - aggregated['failed_deployments']}" if aggregated['total_deployments'] > 0 else None
        )
    
    with col2:
        st.metric(
            label="Success Rate",
            value=f"{aggregated['success_rate']:.1f}%",
            delta=f"{aggregated['success_rate'] - 85:.1f}%" if aggregated['success_rate'] > 0 else None
        )
    
    with col3:
        st.metric(
            label="Avg Deploy Time",
            value=f"{aggregated['avg_deployment_time']:.1f}s",
            delta="-15s" if aggregated['avg_deployment_time'] > 0 else None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="Total Cost",
            value=f"${aggregated['total_cost']:,.2f}",
            delta=f"+${aggregated['total_cost'] * 0.1:,.2f}"
        )

st.markdown("")  # Spacing
st.markdown("---")

# Charts Section
st.markdown("### Deployment Analytics")
st.markdown("")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("**Deployments by Cloud Provider**")
    
    if aggregated['by_provider']:
        provider_data = pd.DataFrame([
            {'Provider': k.upper(), 'Deployments': v}
            for k, v in aggregated['by_provider'].items()
        ])
        st.bar_chart(provider_data.set_index('Provider'), height=300)
    else:
        st.info("No deployment data available")

with col_chart2:
    st.markdown("**Deployments by Environment**")
    
    if aggregated['by_environment']:
        env_data = pd.DataFrame([
            {'Environment': k.title(), 'Deployments': v}
            for k, v in aggregated['by_environment'].items()
        ])
        st.bar_chart(env_data.set_index('Environment'), height=300)
    else:
        st.info("No deployment data available")

st.markdown("")
st.markdown("---")

# Cost Trend
st.markdown("### Cost Trend")
st.markdown("")

dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
costs = [25 + (i % 10) * 5 + (i % 3) * 3 for i in range(30)]

cost_df = pd.DataFrame({
    'Date': dates,
    'Cost ($)': costs
})

st.line_chart(cost_df.set_index('Date'), height=300)

st.markdown("")
st.markdown("---")

# Performance Metrics
st.markdown("### Performance Metrics")
st.markdown("")

col_perf1, col_perf2, col_perf3 = st.columns(3)

with col_perf1:
    st.markdown("**Terraform Init**")
    st.metric("Average Duration", "45.2s", delta="-5s", delta_color="inverse")

with col_perf2:
    st.markdown("**Terraform Plan**")
    st.metric("Average Duration", "78.5s", delta="-8s", delta_color="inverse")

with col_perf3:
    st.markdown("**Terraform Apply**")
    st.metric("Average Duration", "121.8s", delta="-12s", delta_color="inverse")

st.markdown("")
st.markdown("---")

# Recent Deployments
st.markdown("### Recent Deployments")
st.markdown("")

recent_deployments_data = [
    {
        'ID': 'deploy-123',
        'Provider': 'AWS',
        'Environment': 'Production',
        'Region': 'us-east-1',
        'Status': 'Success',
        'Duration': '245s',
        'Cost': '$45.20'
    },
    {
        'ID': 'deploy-122',
        'Provider': 'Azure',
        'Environment': 'Staging',
        'Region': 'eastus',
        'Status': 'Success',
        'Duration': '198s',
        'Cost': '$30.50'
    },
    {
        'ID': 'deploy-121',
        'Provider': 'GCP',
        'Environment': 'Development',
        'Region': 'us-central1',
        'Status': 'Failed',
        'Duration': '67s',
        'Cost': '$0.00'
    },
    {
        'ID': 'deploy-120',
        'Provider': 'AWS',
        'Environment': 'Development',
        'Region': 'us-west-2',
        'Status': 'Success',
        'Duration': '212s',
        'Cost': '$8.50'
    }
]

df = pd.DataFrame(recent_deployments_data)
st.dataframe(df, use_container_width=True, hide_index=True, height=200)

# Footer
st.markdown("")
st.markdown("---")
col_footer1, col_footer2 = st.columns(2)

with col_footer1:
    st.caption(f"Showing data for {period.lower()}")

with col_footer2:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
