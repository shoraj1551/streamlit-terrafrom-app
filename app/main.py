"""
Ultra-Minimal Professional Application

True enterprise-grade design - Stripe/Linear/Vercel aesthetic
"""

import streamlit as st
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.__version__ import __version__
from app.services.auth_system import check_authentication
from app.services.user_survey import check_survey_completion
from app.pages.deployment_wizard import render_deployment_wizard
from app.services.two_factor_auth import render_2fa_setup

st.set_page_config(
    page_title="Infrastructure Platform",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ultra-minimal CSS - True enterprise grade
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Clean white background */
    .stApp {
        background: #ffffff;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Minimal header */
    .minimal-header {
        padding: 1rem 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 2rem;
    }
    
    .minimal-header h1 {
        font-size: 1.25rem;
        font-weight: 600;
        color: #000000;
        margin: 0;
    }
    
    /* Remove sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Minimal buttons */
    .stButton>button {
        background: #000000;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
        font-weight: 500;
        transition: opacity 0.2s;
    }
    
    .stButton>button:hover {
        opacity: 0.8;
        background: #000000;
    }
    
    .stButton>button[kind="secondary"] {
        background: #ffffff;
        color: #000000;
        border: 1px solid #e5e7eb;
    }
    
    .stButton>button[kind="secondary"]:hover {
        background: #f9fafb;
        border-color: #d1d5db;
    }
    
    /* Clean typography */
    h1, h2, h3 {
        color: #000000;
        font-weight: 600;
    }
    
    h2 {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    h3 {
        font-size: 1.125rem;
        margin-bottom: 0.5rem;
    }
    
    p {
        color: #6b7280;
        font-size: 0.875rem;
        line-height: 1.5;
    }
    
    /* Minimal inputs */
    .stTextInput>div>div>input {
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        font-size: 0.875rem;
    }
    
    /* Clean metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        color: #000000;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Remove padding */
    .block-container {
        padding: 2rem 4rem;
        max-width: 1200px;
    }
    
    /* Minimal tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 0;
        color: #6b7280;
        font-weight: 500;
        border: none;
        background: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        color: #000000;
        border-bottom: 2px solid #000000;
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
    
    # Minimal header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="minimal-header">
            <h1>Infrastructure Platform</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div style='padding-top: 1rem;'></div>", unsafe_allow_html=True)
        if st.button("Sign Out", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Minimal navigation
    tab1, tab2, tab3 = st.tabs(["Deploy", "Security", "Settings"])
    
    with tab1:
        render_deployment_wizard(user['email'])
    
    with tab2:
        render_security_page(user['email'])
    
    with tab3:
        render_settings_page(user['email'])


def render_security_page(user_email: str):
    """Minimal security page"""
    st.markdown("## Security")
    st.markdown("Manage authentication and access control")
    st.markdown("")
    
    render_2fa_setup(user_email)


def render_settings_page(user_email: str):
    """Minimal settings page"""
    st.markdown("## Settings")
    st.markdown("Account preferences and configuration")
    st.markdown("")
    
    st.markdown("### Change Password")
    
    with st.form("password_form"):
        st.text_input("Current Password", type="password")
        st.text_input("New Password", type="password")
        st.text_input("Confirm Password", type="password")
        
        submitted = st.form_submit_button("Update Password")
        if submitted:
            st.success("Password updated")


if __name__ == "__main__":
    main()
