"""
Logs Viewer Page

View, search, and filter deployment logs with configurable retention.
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.deployment_db import DeploymentDatabase
from app.services.logging import LogRetentionPeriod

# Page configuration
st.set_page_config(
    page_title="Deployment Logs",
    page_icon="📋",
    layout="wide"
)

# Custom CSS for logs viewer
st.markdown("""
<style>
    /* Animated Gradient Background */
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
    
    /* Log Entry Styles */
    .log-entry {
        font-family: 'Fira Code', monospace;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }
    
    .log-entry:hover {
        transform: translateX(5px);
    }
    
    .log-info {
        background: rgba(59, 130, 246, 0.15);
        border-left: 4px solid #3b82f6;
    }
    
    .log-warning {
        background: rgba(251, 191, 36, 0.15);
        border-left: 4px solid #fbbf24;
    }
    
    .log-error {
        background: rgba(239, 68, 68, 0.15);
        border-left: 4px solid #ef4444;
    }
    
    .log-debug {
        background: rgba(107, 114, 128, 0.15);
        border-left: 4px solid #6b7280;
    }
    
    .log-timestamp {
        color: #94a3b8;
        font-weight: 600;
    }
    
    .log-level {
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    
    .level-info { background: #3b82f6; color: white; }
    .level-warning { background: #fbbf24; color: #1e293b; }
    .level-error { background: #ef4444; color: white; }
    .level-debug { background: #6b7280; color: white; }
</style>
""", unsafe_allow_html=True)

# Initialize database
if 'db' not in st.session_state:
    st.session_state.db = DeploymentDatabase()

# Header
st.title("📋 Deployment Logs")
st.markdown("View and analyze deployment logs with advanced filtering")

# Filters Section
st.markdown("### 🔍 Filters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Get recent deployments for filter
    stats = st.session_state.db.get_statistics()
    deployment_filter = st.selectbox(
        "Deployment",
        options=["All Deployments"],
        key="deployment_filter"
    )

with col2:
    level_filter = st.selectbox(
        "Log Level",
        options=["All Levels", "INFO", "WARNING", "ERROR", "DEBUG"],
        key="level_filter"
    )

with col3:
    time_range = st.selectbox(
        "Time Range",
        options=["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom"],
        key="time_range"
    )

with col4:
    retention_period = st.selectbox(
        "Retention Period",
        options=["1 Month", "6 Months (Default)", "1 Year", "2 Years"],
        key="retention_period"
    )

# Search bar
search_query = st.text_input(
    "🔍 Search logs",
    placeholder="Search by message, deployment ID, or any text...",
    key="search_query"
)

# Calculate time range
def get_time_range():
    if time_range == "Last Hour":
        return datetime.now() - timedelta(hours=1)
    elif time_range == "Last 24 Hours":
        return datetime.now() - timedelta(days=1)
    elif time_range == "Last 7 Days":
        return datetime.now() - timedelta(days=7)
    elif time_range == "Last 30 Days":
        return datetime.now() - timedelta(days=30)
    return None

# Mock logs for demonstration (replace with actual database query)
def get_mock_logs():
    """Generate mock logs for demonstration"""
    logs = []
    levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
    messages = [
        "Starting deployment to AWS us-east-1",
        "Terraform initialization completed",
        "Planning infrastructure changes",
        "Applying Terraform configuration",
        "Deployment completed successfully",
        "Cost estimate: $45.50/month",
        "Warning: High cost deployment detected",
        "Error: Failed to connect to Azure",
        "Retrying deployment...",
        "GCP instance created successfully"
    ]
    
    for i in range(20):
        logs.append({
            'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
            'level': levels[i % len(levels)],
            'logger': 'deployment',
            'message': messages[i % len(messages)],
            'deployment_id': f'deploy-{1000 + i}',
            'cloud_provider': ['aws', 'azure', 'gcp'][i % 3],
            'environment': ['dev', 'staging', 'prod'][i % 3]
        })
    
    return logs

# Get logs (using mock data for now)
logs = get_mock_logs()

# Apply filters
if level_filter != "All Levels":
    logs = [log for log in logs if log['level'] == level_filter]

if search_query:
    logs = [log for log in logs if search_query.lower() in log['message'].lower()]

# Display log count and actions
col_actions1, col_actions2, col_actions3 = st.columns([2, 1, 1])

with col_actions1:
    st.markdown(f"### Showing {len(logs)} log entries")

with col_actions2:
    if st.button("🔄 Refresh Logs"):
        st.rerun()

with col_actions3:
    if st.button("📥 Export CSV"):
        st.success("Logs exported to logs_export.csv")

st.markdown("---")

# Display logs
if logs:
    for log in logs:
        level_class = f"log-{log['level'].lower()}"
        level_badge_class = f"level-{log['level'].lower()}"
        timestamp = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        
        # Provider icon
        provider_icons = {'aws': '☁️', 'azure': '🔷', 'gcp': '🔶'}
        provider_icon = provider_icons.get(log.get('cloud_provider', ''), '')
        
        st.markdown(f"""
        <div class="log-entry {level_class}">
            <span class="log-timestamp">{timestamp}</span> | 
            <span class="log-level {level_badge_class}">{log['level']}</span> | 
            {provider_icon} <strong>{log.get('cloud_provider', 'N/A').upper()}</strong> | 
            <span style="color: #94a3b8">{log.get('environment', 'N/A')}</span> | 
            {log['message']}
            <br>
            <small style="color: #64748b">Deployment: {log.get('deployment_id', 'N/A')}</small>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("📭 No logs found matching your filters")

# Footer with retention info
st.markdown("---")
col_footer1, col_footer2 = st.columns(2)

with col_footer1:
    st.caption(f"📊 Total deployments: {stats['total_deployments']}")

with col_footer2:
    retention_days = {
        "1 Month": 30,
        "6 Months (Default)": 180,
        "1 Year": 365,
        "2 Years": 730
    }
    days = retention_days[retention_period]
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    st.caption(f"🗑️ Logs before {cutoff_date} will be automatically deleted")
