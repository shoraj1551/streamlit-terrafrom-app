"""
Professional Infrastructure Platform

Enterprise-grade design based on GitHub/Stripe aesthetic
"""

import streamlit as st
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.__version__ import __version__
from app.services.auth0_integration import check_authentication, render_login_page
from app.services.user_survey import check_survey_completion
from app.pages.deployment_wizard import render_deployment_wizard
from app.services.two_factor_auth import render_2fa_setup

st.set_page_config(
    page_title="Infrastructure Platform",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional CSS - GitHub/Stripe inspired
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Base colors */
    .stApp {
        background: #f7f8fa;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Professional header */
    .pro-header {
        background: #ffffff;
        padding: 1rem 2rem;
        border-bottom: 1px solid #e1e4e8;
        margin: -1rem -1rem 0 -1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .pro-header h1 {
        font-size: 1.25rem;
        font-weight: 600;
        color: #24292e;
        margin: 0;
    }
    
    .pro-header .user-info {
        font-size: 0.875rem;
        color: #586069;
    }
    
    /* Typography scale */
    h1 {
        font-size: 1.75rem;
        font-weight: 600;
        color: #24292e;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        font-size: 1.25rem;
        font-weight: 600;
        color: #24292e;
        margin-bottom: 0.5rem;
    }
    
    h3 {
        font-size: 1rem;
        font-weight: 600;
        color: #24292e;
        margin-bottom: 0.5rem;
    }
    
    p {
        color: #586069;
        font-size: 0.875rem;
        line-height: 1.6;
    }
    
    /* Primary buttons - GitHub blue */
    .stButton>button[kind="primary"] {
        background: #0366d6;
        color: #ffffff;
        border: 1px solid #0366d6;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
        font-weight: 500;
        transition: background 0.2s;
    }
    
    .stButton>button[kind="primary"]:hover {
        background: #0256c7;
        border-color: #0256c7;
    }
    
    /* Secondary buttons */
    .stButton>button {
        background: #ffffff;
        color: #24292e;
        border: 1px solid #e1e4e8;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        background: #f3f4f6;
        border-color: #d1d5db;
    }
    
    /* Cards */
    .pro-card {
        background: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 6px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    .pro-card h3 {
        margin-top: 0;
    }
    
    /* Inputs */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select {
        border: 1px solid #e1e4e8;
        border-radius: 6px;
        font-size: 0.875rem;
        background: #ffffff;
        padding: 0.5rem 0.75rem;
    }
    
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>select:focus {
        border-color: #0366d6;
        box-shadow: 0 0 0 3px rgba(3, 102, 214, 0.1);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid #e1e4e8;
        background: #ffffff;
        padding: 0 2rem;
        margin: 0 -2rem 2rem -2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 0;
        color: #586069;
        font-weight: 500;
        font-size: 0.875rem;
        border: none;
        background: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        color: #24292e;
        border-bottom: 3px solid #0366d6;
    }
    
    /* Container */
    .block-container {
        padding: 2rem 4rem;
        max-width: 1280px;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        color: #24292e;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        color: #6a737d;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }
    
    /* Status badges */
    .status-success {
        background: #dcfce7;
        color: #166534;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .status-warning {
        background: #fef3c7;
        color: #92400e;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .status-info {
        background: #dbeafe;
        color: #1e40af;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    /* Info boxes */
    .stInfo {
        background: #f1f8ff;
        border-left: 3px solid #0366d6;
    }
    
    .stSuccess {
        background: #dcfce7;
        border-left: 3px solid #28a745;
    }
    
    .stWarning {
        background: #fef3c7;
        border-left: 3px solid #ffd33d;
    }
    
    .stError {
        background: #fee;
        border-left: 3px solid #d73a49;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application"""
    
    user = check_authentication()
    if not user:
        return
    
    survey_complete = check_survey_completion(user['email'])
    if not survey_complete:
        return
    
    # Professional header
    st.markdown(f"""
    <div class="pro-header">
        <h1>Infrastructure Platform</h1>
        <div class="user-info">{user['full_name']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["Deploy", "Security", "Settings"])
    
    with tab1:
        render_deployment_wizard(user['email'])
    
    with tab2:
        render_security_page(user['email'])
    
    with tab3:
        render_settings_page(user['email'])
    
    # Sign out in sidebar (minimal)
    with st.sidebar:
        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def render_security_page(user_email: str):
    """Security settings page"""
    st.markdown("## Security")
    st.markdown("Manage authentication and access control")
    st.markdown("")
    
    render_2fa_setup(user_email)


def render_settings_page(user_email: str):
    """Settings page"""
    st.markdown("## Settings")
    st.markdown("Account preferences and configuration")
    st.markdown("")
    
    st.markdown("### Change Password")
    
    with st.form("password_form"):
        st.text_input("Current Password", type="password")
        st.text_input("New Password", type="password", help="Minimum 8 characters")
        st.text_input("Confirm New Password", type="password")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("Update Password", type="primary")
        
        if submitted:
            st.success("Password updated successfully")


if __name__ == "__main__":
    main()
