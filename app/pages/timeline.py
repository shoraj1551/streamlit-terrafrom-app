"""
Deployment Timeline Page

Visual timeline of all deployments with filtering and details.
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.deployment_db import DeploymentDatabase
from app.services.health_check import HealthCheckSystem
from app.services.alerting_system import AlertingSystem

# Page configuration
st.set_page_config(
    page_title="Deployment Timeline",
    page_icon="📅",
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
    
    .timeline-item {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .timeline-item:hover {
        transform: translateX(5px);
        border-left-width: 6px;
    }
    
    .timeline-success { border-left-color: #10b981; }
    .timeline-failed { border-left-color: #ef4444; }
    .timeline-pending { border-left-color: #fbbf24; }
    
    .health-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .health-healthy { background-color: #10b981; }
    .health-degraded { background-color: #fbbf24; }
    .health-unhealthy { background-color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = DeploymentDatabase()

if 'health_check' not in st.session_state:
    st.session_state.health_check = HealthCheckSystem()

if 'alerting' not in st.session_state:
    st.session_state.alerting = AlertingSystem()

# Header
st.title("📅 Deployment Timeline")
st.markdown("Track all deployments across time with detailed insights")

# System Health Status
col_health1, col_health2 = st.columns([3, 1])

with col_health1:
    st.markdown("### 🏥 System Health")

with col_health2:
    if st.button("🔄 Check Health", use_container_width=True):
        st.rerun()

# Get health status
health = st.session_state.health_check.check_all()

col_h1, col_h2, col_h3, col_h4 = st.columns(4)

status_colors = {
    'healthy': 'health-healthy',
    'degraded': 'health-degraded',
    'unhealthy': 'health-unhealthy'
}

with col_h1:
    overall_color = status_colors.get(health['overall_status'], 'health-healthy')
    st.markdown(f"""
    <div style="text-align: center;">
        <span class="health-indicator {overall_color}"></span>
        <strong>Overall: {health['overall_status'].title()}</strong>
    </div>
    """, unsafe_allow_html=True)

# Show component health
for idx, component in enumerate(health['components'][:3]):
    col = [col_h2, col_h3, col_h4][idx]
    with col:
        comp_color = status_colors.get(component['status'], 'health-healthy')
        st.markdown(f"""
        <div style="text-align: center;">
            <span class="health-indicator {comp_color}"></span>
            <strong>{component['name'].replace('_', ' ').title()}</strong><br>
            <small>{component['response_time_ms']:.1f}ms</small>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Recent Alerts
st.markdown("### 🔔 Recent Alerts")

recent_alerts = st.session_state.alerting.get_recent_alerts(5)

if recent_alerts:
    for alert in recent_alerts:
        severity_colors = {
            'info': '🔵',
            'warning': '🟡',
            'error': '🔴',
            'critical': '🔴'
        }
        icon = severity_colors.get(alert.severity.value, '⚪')
        
        st.markdown(f"""
        <div class="timeline-item">
            {icon} <strong>{alert.title}</strong><br>
            <small>{alert.message}</small><br>
            <small style="color: #94a3b8;">{alert.timestamp}</small>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("📭 No recent alerts")

st.markdown("---")

# Deployment Timeline
st.markdown("### 📅 Deployment Timeline")

# Filters
col_filter1, col_filter2, col_filter3 = st.columns(3)

with col_filter1:
    provider_filter = st.selectbox(
        "Cloud Provider",
        options=["All", "AWS", "Azure", "GCP"]
    )

with col_filter2:
    env_filter = st.selectbox(
        "Environment",
        options=["All", "Dev", "Staging", "Production"]
    )

with col_filter3:
    time_filter = st.selectbox(
        "Time Range",
        options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"]
    )

# Mock deployment timeline data
deployments = [
    {
        'id': 'deploy-125',
        'timestamp': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
        'provider': 'AWS',
        'environment': 'Production',
        'region': 'us-east-1',
        'status': 'success',
        'duration': '245s',
        'cost': '$45.20'
    },
    {
        'id': 'deploy-124',
        'timestamp': (datetime.now() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'),
        'provider': 'Azure',
        'environment': 'Staging',
        'region': 'eastus',
        'status': 'success',
        'duration': '198s',
        'cost': '$30.50'
    },
    {
        'id': 'deploy-123',
        'timestamp': (datetime.now() - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
        'provider': 'GCP',
        'environment': 'Dev',
        'region': 'us-central1',
        'status': 'failed',
        'duration': '67s',
        'cost': '$0.00'
    },
    {
        'id': 'deploy-122',
        'timestamp': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
        'provider': 'AWS',
        'environment': 'Dev',
        'region': 'us-west-2',
        'status': 'success',
        'duration': '212s',
        'cost': '$8.50'
    },
    {
        'id': 'deploy-121',
        'timestamp': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
        'provider': 'Azure',
        'environment': 'Production',
        'region': 'westeurope',
        'status': 'success',
        'duration': '267s',
        'cost': '$60.75'
    }
]

# Display timeline
for deployment in deployments:
    status_class = f"timeline-{deployment['status']}"
    status_icon = '✅' if deployment['status'] == 'success' else '❌'
    provider_icons = {'AWS': '☁️', 'Azure': '🔷', 'GCP': '🔶'}
    
    st.markdown(f"""
    <div class="timeline-item {status_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                {status_icon} <strong>{deployment['id']}</strong> - 
                {provider_icons.get(deployment['provider'], '')} {deployment['provider']} - 
                <span style="color: #94a3b8;">{deployment['environment']}</span>
            </div>
            <div style="text-align: right;">
                <strong>{deployment['cost']}</strong><br>
                <small style="color: #94a3b8;">{deployment['duration']}</small>
            </div>
        </div>
        <div style="margin-top: 0.5rem; color: #94a3b8; font-size: 0.9rem;">
            📍 {deployment['region']} | 🕐 {deployment['timestamp']}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
