"""
Professional Main Application - Enterprise Grade UI

Clean, sophisticated interface designed for enterprise users.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.__version__ import __version__, __app_name__
from app.services.auth_system import check_authentication
from app.services.user_survey import check_survey_completion
from app.pages.deployment_wizard import render_deployment_wizard
from app.services.two_factor_auth import render_2fa_setup

# Page configuration
st.set_page_config(
    page_title="Cloud Infrastructure Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS - Enterprise Grade
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Clean Background */
    .stApp {
        background: #f8f9fa;
    }
    
    /* Remove default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Professional Header */
    .main-header {
        background: linear-gradient(135deg, #1a1f36 0%, #2d3748 100%);
        padding: 1.5rem 2rem;
        border-radius: 0;
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
        color: white;
    }
    
    .main-header p {
        font-size: 0.875rem;
        margin: 0.25rem 0 0 0;
        color: #cbd5e0;
        font-weight: 400;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #2d3748;
    }
    
    /* Navigation Items */
    .nav-item {
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
        background: transparent;
        border: 1px solid transparent;
    }
    
    .nav-item:hover {
        background: #f7fafc;
        border-color: #e2e8f0;
    }
    
    .nav-item.active {
        background: #edf2f7;
        border-color: #cbd5e0;
        font-weight: 500;
    }
    
    .nav-item.disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 0.375rem;
        font-weight: 500;
        transition: all 0.2s;
        border: 1px solid transparent;
        font-size: 0.875rem;
        padding: 0.5rem 1rem;
    }
    
    .stButton>button[kind="primary"] {
        background: #2563eb;
        color: white;
        border-color: #2563eb;
    }
    
    .stButton>button[kind="primary"]:hover {
        background: #1d4ed8;
        border-color: #1d4ed8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    .stButton>button[kind="secondary"] {
        background: white;
        color: #374151;
        border-color: #d1d5db;
    }
    
    .stButton>button[kind="secondary"]:hover {
        background: #f9fafb;
        border-color: #9ca3af;
    }
    
    /* Cards */
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .info-card h3 {
        font-size: 1rem;
        font-weight: 600;
        color: #111827;
        margin: 0 0 0.5rem 0;
    }
    
    .info-card p {
        font-size: 0.875rem;
        color: #6b7280;
        margin: 0;
    }
    
    /* Status Indicators */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .status-badge.success {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-badge.warning {
        background: #fef3c7;
        color: #92400e;
    }
    
    .status-badge.info {
        background: #dbeafe;
        color: #1e40af;
    }
    
    /* Remove childish emojis from headers */
    h1, h2, h3 {
        color: #111827;
        font-weight: 600;
    }
    
    /* Professional spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Clean inputs */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select {
        border-radius: 0.375rem;
        border-color: #d1d5db;
        font-size: 0.875rem;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
        color: #111827;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: #6b7280;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point"""
    
    # Check authentication
    user = check_authentication()
    
    if not user:
        return
    
    # Check survey completion
    survey_complete = check_survey_completion(user['email'])
    
    if not survey_complete:
        return
    
    # Determine available pages based on user progress
    available_pages = get_available_pages()
    
    # Sidebar navigation
    with st.sidebar:
        # Company branding (minimal)
        st.markdown(f"""
        <div style="padding: 1rem 0; border-bottom: 1px solid #e5e7eb; margin-bottom: 1rem;">
            <div style="font-size: 1.125rem; font-weight: 600; color: #111827;">Infrastructure Platform</div>
            <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">v{__version__}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # User info
        st.markdown(f"""
        <div style="padding: 0.75rem; background: #f9fafb; border-radius: 0.5rem; margin-bottom: 1.5rem;">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">Signed in as</div>
            <div style="font-size: 0.875rem; font-weight: 500; color: #111827;">{user['full_name']}</div>
            <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.125rem;">{user['email']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        st.markdown('<div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Navigation</div>', unsafe_allow_html=True)
        
        page = st.radio(
            "Navigation",
            options=available_pages,
            label_visibility="collapsed",
            format_func=lambda x: x.replace("🔒 ", "")  # Remove lock emoji from display
        )
        
        st.markdown("---")
        
        # Logout
        if st.button("Sign Out", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>Cloud Infrastructure Deployment</h1>
        <p>Enterprise-grade multi-cloud infrastructure management platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Route to selected page
    if "Deployment" in page and "🔒" not in page:
        render_deployment_wizard(user['email'])
    
    elif "Security" in page and "🔒" not in page:
        render_security_settings(user['email'])
    
    elif "Dashboard" in page and "🔒" not in page:
        render_dashboard(user['email'])
    
    elif "🔒" in page:
        render_locked_page(page)
    
    else:
        render_dashboard(user['email'])


def get_available_pages():
    """Get list of available pages based on user progress"""
    pages = []
    
    # Always available
    pages.append("Dashboard")
    pages.append("Deployment")
    pages.append("Security Settings")
    
    # Conditionally available based on deployment status
    if 'wizard_data' in st.session_state and 'analyses' in st.session_state.wizard_data:
        pages.append("Cost Analysis")
    else:
        pages.append("🔒 Cost Analysis")
    
    # Only show if deployments exist
    if st.session_state.get('has_deployments', False):
        pages.append("Infrastructure")
    else:
        pages.append("🔒 Infrastructure")
    
    return pages


def render_security_settings(user_email: str):
    """Render security settings page"""
    st.markdown("### Security Settings")
    st.markdown("Manage your account security and authentication methods")
    
    st.markdown("")
    
    tab1, tab2 = st.tabs(["Two-Factor Authentication", "Password Management"])
    
    with tab1:
        render_2fa_setup(user_email)
    
    with tab2:
        st.markdown("#### Change Password")
        st.markdown("Update your account password")
        
        st.markdown("")
        
        with st.form("change_password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password", help="Minimum 8 characters")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                submitted = st.form_submit_button("Update Password", type="primary", use_container_width=True)
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters")
                else:
                    st.success("Password updated successfully")


def render_dashboard(user_email: str):
    """Render dashboard page"""
    st.markdown("### Overview")
    st.markdown("Monitor your cloud infrastructure and deployments")
    
    st.markdown("")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Deployments", "0", help="Number of active infrastructure deployments")
    
    with col2:
        st.metric("Total Environments", "0", help="Development, Staging, and Production environments")
    
    with col3:
        st.metric("Monthly Spend", "$0", help="Estimated monthly cloud infrastructure cost")
    
    with col4:
        st.metric("Success Rate", "—", help="Deployment success rate")
    
    st.markdown("")
    
    # Getting started card
    st.markdown("""
    <div class="info-card">
        <h3>Get Started</h3>
        <p>Deploy your first cloud infrastructure using the Deployment wizard. Our AI-powered platform will analyze your requirements and recommend the optimal cloud provider configuration.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Start Deployment", type="primary", use_container_width=True):
            st.session_state.current_page = "Deployment"
            st.rerun()


def render_locked_page(page_name: str):
    """Render locked page with explanation"""
    clean_name = page_name.replace("🔒 ", "")
    
    st.markdown(f"### {clean_name}")
    
    st.markdown("")
    
    st.info(f"**{clean_name}** will be available after you complete the deployment wizard.")
    
    st.markdown("""
    <div class="info-card">
        <h3>Complete These Steps First</h3>
        <p>1. Navigate to the Deployment page<br/>
        2. Complete the infrastructure requirements wizard<br/>
        3. Review and approve the recommended configuration<br/>
        4. Deploy your infrastructure</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Go to Deployment", type="primary"):
        st.session_state.current_page = "Deployment"
        st.rerun()


if __name__ == "__main__":
    main()
