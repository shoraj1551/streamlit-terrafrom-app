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

# Page configuration
st.set_page_config(
    page_title="Monitoring Dashboard",
    page_icon="📊",
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
    
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = DeploymentDatabase()

if 'metrics_collector' not in st.session_state:
    st.session_state.metrics_collector = MetricsCollector(st.session_state.db)

# Header
st.title("📊 Monitoring Dashboard")
st.markdown("Real-time deployment metrics and performance monitoring")

# Time period selector
col_period1, col_period2 = st.columns([3, 1])

with col_period1:
    period = st.selectbox(
        "Time Period",
        options=["Last 7 Days", "Last 30 Days", "Last 90 Days"],
        key="period_selector"
    )

with col_period2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# Map period to days
period_map = {
    "Last 7 Days": "7d",
    "Last 30 Days": "30d",
    "Last 90 Days": "90d"
}
period_key = period_map[period]

# Get aggregated metrics (mock data for now)
stats = st.session_state.db.get_statistics()

# Mock aggregated metrics
aggregated = {
    'total_deployments': stats['total_deployments'],
    'successful_deployments': stats['successful'],
    'failed_deployments': stats['failed'],
    'success_rate': stats['success_rate'],
    'avg_deployment_time': 245.5,  # seconds
    'total_cost': 1247.80,
    'avg_cost_per_deployment': 31.20,
    'by_provider': {'aws': 15, 'azure': 8, 'gcp': 12},
    'by_environment': {'dev': 20, 'staging': 10, 'prod': 5}
}

st.markdown("---")

# Key Metrics
st.markdown("### 📈 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Deployments",
        aggregated['total_deployments'],
        delta=f"+{aggregated['total_deployments'] - aggregated['failed_deployments']}" if aggregated['total_deployments'] > 0 else None
    )

with col2:
    st.metric(
        "Success Rate",
        f"{aggregated['success_rate']}%",
        delta=f"{aggregated['success_rate'] - 85}%" if aggregated['success_rate'] > 0 else None
    )

with col3:
    st.metric(
        "Avg Deploy Time",
        f"{aggregated['avg_deployment_time']}s",
        delta="-15s" if aggregated['avg_deployment_time'] > 0 else None,
        delta_color="inverse"
    )

with col4:
    st.metric(
        "Total Cost",
        f"${aggregated['total_cost']}",
        delta=f"+${aggregated['total_cost'] * 0.1:.2f}"
    )

st.markdown("---")

# Charts Section
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("### 🌐 Deployments by Cloud Provider")
    
    if aggregated['by_provider']:
        provider_data = pd.DataFrame([
            {'Provider': k.upper(), 'Deployments': v}
            for k, v in aggregated['by_provider'].items()
        ])
        st.bar_chart(provider_data.set_index('Provider'))
    else:
        st.info("No deployment data available")

with col_chart2:
    st.markdown("### 🌍 Deployments by Environment")
    
    if aggregated['by_environment']:
        env_data = pd.DataFrame([
            {'Environment': k.title(), 'Deployments': v}
            for k, v in aggregated['by_environment'].items()
        ])
        st.bar_chart(env_data.set_index('Environment'))
    else:
        st.info("No deployment data available")

st.markdown("---")

# Cost Trend
st.markdown("### 💰 Cost Trend")

# Mock cost trend data
dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
costs = [25 + (i % 10) * 5 + (i % 3) * 3 for i in range(30)]

cost_df = pd.DataFrame({
    'Date': dates,
    'Cost ($)': costs
})

st.line_chart(cost_df.set_index('Date'))

st.markdown("---")

# Performance Metrics
st.markdown("### ⚡ Performance Metrics")

col_perf1, col_perf2, col_perf3 = st.columns(3)

with col_perf1:
    st.markdown("**Terraform Init**")
    st.metric("Avg Duration", "45.2s", delta="-5s", delta_color="inverse")

with col_perf2:
    st.markdown("**Terraform Plan**")
    st.metric("Avg Duration", "78.5s", delta="-8s", delta_color="inverse")

with col_perf3:
    st.markdown("**Terraform Apply**")
    st.metric("Avg Duration", "121.8s", delta="-12s", delta_color="inverse")

st.markdown("---")

# Recent Deployments Table
st.markdown("### 📋 Recent Deployments")

# Mock recent deployments
recent_deployments = [
    {
        'ID': 'deploy-123',
        'Provider': 'AWS',
        'Environment': 'prod',
        'Region': 'us-east-1',
        'Status': '✅ Success',
        'Duration': '245s',
        'Cost': '$45.20'
    },
    {
        'ID': 'deploy-122',
        'Provider': 'Azure',
        'Environment': 'staging',
        'Region': 'eastus',
        'Status': '✅ Success',
        'Duration': '198s',
        'Cost': '$30.50'
    },
    {
        'ID': 'deploy-121',
        'Provider': 'GCP',
        'Environment': 'dev',
        'Region': 'us-central1',
        'Status': '❌ Failed',
        'Duration': '67s',
        'Cost': '$0.00'
    },
    {
        'ID': 'deploy-120',
        'Provider': 'AWS',
        'Environment': 'dev',
        'Region': 'us-west-2',
        'Status': '✅ Success',
        'Duration': '212s',
        'Cost': '$8.50'
    }
]

st.table(recent_deployments)

# Footer
st.markdown("---")
col_footer1, col_footer2 = st.columns(2)

with col_footer1:
    st.caption(f"📊 Showing data for {period.lower()}")

with col_footer2:
    st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
