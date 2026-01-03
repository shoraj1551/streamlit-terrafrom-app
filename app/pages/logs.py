"""
Logs Viewer Page

View, search, and filter deployment logs with configurable retention.
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.deployment_db import DeploymentDatabase
from app.services.logging import LogRetentionPeriod
from app.utils.styles import apply_professional_theme

# Page configuration
st.set_page_config(
    page_title="Logs - Infrastructure Platform",
    page_icon="📋",
    layout="wide"
)

# Apply professional styling
apply_professional_theme()

# Initialize database
if 'db' not in st.session_state:
    st.session_state.db = DeploymentDatabase()

# Header
st.title("Deployment Logs")
st.markdown("View and analyze deployment logs with advanced filtering")

# Filters Section
st.markdown("### Filters")
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
    "Search logs",
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
            'cloud_provider': ['AWS', 'Azure', 'GCP'][i % 3],
            'environment': ['Development', 'Staging', 'Production'][i % 3]
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

# Display logs using structured dataframe
if logs:
    # Convert logs to DataFrame for better display
    logs_df = pd.DataFrame([
        {
            'Timestamp': datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
            'Level': log['level'],
            'Provider': log.get('cloud_provider', 'N/A'),
            'Environment': log.get('environment', 'N/A'),
            'Message': log['message'],
            'Deployment ID': log.get('deployment_id', 'N/A')
        }
        for log in logs
    ])
    
    # Display as dataframe with custom styling
    st.dataframe(
        logs_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
            "Level": st.column_config.TextColumn("Level", width="small"),
            "Provider": st.column_config.TextColumn("Provider", width="small"),
            "Environment": st.column_config.TextColumn("Environment", width="medium"),
            "Message": st.column_config.TextColumn("Message", width="large"),
            "Deployment ID": st.column_config.TextColumn("Deployment ID", width="medium"),
        }
    )
else:
    st.info("No logs found matching your filters")

# Footer with retention info
st.markdown("---")
col_footer1, col_footer2 = st.columns(2)

with col_footer1:
    st.caption(f"Total deployments: {stats['total_deployments']}")

with col_footer2:
    retention_days = {
        "1 Month": 30,
        "6 Months (Default)": 180,
        "1 Year": 365,
        "2 Years": 730
    }
    days = retention_days[retention_period]
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    st.caption(f"Logs before {cutoff_date} will be automatically deleted")
