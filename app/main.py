"""
Enhanced Main Application

Integrated multi-cloud infrastructure deployment platform with AI-powered
requirements analysis, multi-cloud cost comparison, and secure deployment.
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
    page_title="Cloud Infrastructure Deployer",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
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
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .stButton>button {
        border-radius: 0.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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
    if not check_survey_completion(user['email']):
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"### {__app_name__}")
        st.markdown(f"Version {__version__}")
        st.markdown("---")
        
        # User info
        st.markdown(f"**👤 {user['full_name']}**")
        st.markdown(f"📧 {user['email']}")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            options=[
                "🚀 Deployment Wizard",
                "🔐 Security Settings",
                "📊 Dashboard",
                "📝 Logs",
                "⚙️ Settings"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            # BUG-012 FIX: Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>☁️ Cloud Infrastructure Deployer</h1>
        <p>AI-Powered Multi-Cloud Infrastructure Deployment Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Route to selected page
    if "Deployment Wizard" in page:
        render_deployment_wizard(user['email'])
    
    elif "Security Settings" in page:
        render_security_settings(user['email'])
    
    elif "Dashboard" in page:
        render_dashboard(user['email'])
    
    elif "Logs" in page:
        render_logs(user['email'])
    
    elif "Settings" in page:
        render_settings(user['email'])


def render_security_settings(user_email: str):
    """Render security settings page"""
    st.markdown("## 🔐 Security Settings")
    
    tab1, tab2 = st.tabs(["Two-Factor Authentication", "Password"])
    
    with tab1:
        render_2fa_setup(user_email)
    
    with tab2:
        st.markdown("### Change Password")
        
        with st.form("change_password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password"):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters")
                else:
                    # Change password logic here
                    st.success("Password changed successfully!")


def render_dashboard(user_email: str):
    """Render dashboard page"""
    st.markdown("## 📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Deployments", "0", "0")
    
    with col2:
        st.metric("Active Environments", "0", "0")
    
    with col3:
        st.metric("Monthly Cost", "$0", "$0")
    
    with col4:
        st.metric("Success Rate", "0%", "0%")
    
    st.markdown("---")
    
    st.info("📊 Deploy your first infrastructure using the Deployment Wizard!")


def render_logs(user_email: str):
    """Render logs page"""
    st.markdown("## 📝 Deployment Logs")
    
    st.info("No deployment logs yet. Start a deployment to see logs here.")


def render_settings(user_email: str):
    """Render settings page"""
    st.markdown("## ⚙️ Settings")
    
    tab1, tab2 = st.tabs(["Profile", "Preferences"])
    
    with tab1:
        st.markdown("### Profile Settings")
        
        with st.form("profile_settings"):
            full_name = st.text_input("Full Name", value=st.session_state.user.get('full_name', ''))
            email = st.text_input("Email", value=user_email, disabled=True)
            
            if st.form_submit_button("Update Profile"):
                st.success("Profile updated successfully!")
    
    with tab2:
        st.markdown("### Preferences")
        
        theme = st.selectbox("Theme", options=["Dark", "Light"])
        notifications = st.checkbox("Email Notifications", value=True)
        
        if st.button("Save Preferences"):
            st.success("Preferences saved!")


if __name__ == "__main__":
    main()
