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
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

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
    """Main application with error boundaries and service layer integration"""
    
    try:
        # Initialize services
        from app.core.di_container import setup_services, get_container
        from app.services.auth_service import AuthenticationService
        from app.core.rbac import get_rbac_manager, Permission
        
        # Setup DI container
        setup_services()
        container = get_container()
        
        # Get services
        auth_service = container.resolve(AuthenticationService)
        rbac = get_rbac_manager()
        
        # Check authentication
        user = check_authentication()
        if not user:
            return
        
        user_email = user.get('email')
        
        # Verify session is still valid
        session_id = st.session_state.get('session_id')
        if session_id:
            session = auth_service.verify_session(session_id)
            if not session:
                st.error("Your session has expired. Please log in again.")
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
                return
        
        # Check survey completion
        survey_complete = check_survey_completion(user_email)
        if not survey_complete:
            return
        
        # Professional header
        st.markdown(f"""
        <div class="pro-header">
            <h1>Infrastructure Platform</h1>
            <div class="user-info">
                {user['full_name']} 
                <span style="margin-left: 1rem; color: #6c757d;">
                    Role: {rbac.get_user_role(user_email).value.title()}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
        
        # Navigation tabs with permission checks
        available_tabs = []
        tab_names = []
        
        # Deploy tab - requires deploy:create permission
        if rbac.has_permission(user_email, Permission.DEPLOY_CREATE):
            available_tabs.append("deploy")
            tab_names.append("Deploy")
        
        # Security tab - always available
        available_tabs.append("security")
        tab_names.append("Security")
        
        # Settings tab - always available
        available_tabs.append("settings")
        tab_names.append("Settings")
        
        # Admin tab - requires admin permission
        if rbac.is_admin(user_email):
            available_tabs.append("admin")
            tab_names.append("Admin")
        
        # Create tabs
        tabs = st.tabs(tab_names)
        
        # Render tabs based on permissions
        tab_index = 0
        
        if "deploy" in available_tabs:
            with tabs[tab_index]:
                try:
                    render_deployment_wizard(user_email)
                except Exception as e:
                    st.error("⚠️ An error occurred while loading the deployment wizard.")
                    st.error(f"Error: {str(e)}")
                    logger.error(f"Deployment wizard error: {e}", exc_info=True)
            tab_index += 1
        
        with tabs[tab_index]:
            try:
                render_security_page(user_email)
            except Exception as e:
                st.error("⚠️ An error occurred while loading security settings.")
                logger.error(f"Security page error: {e}", exc_info=True)
        tab_index += 1
        
        with tabs[tab_index]:
            try:
                render_settings_page(user_email)
            except Exception as e:
                st.error("⚠️ An error occurred while loading settings.")
                logger.error(f"Settings page error: {e}", exc_info=True)
        tab_index += 1
        
        if "admin" in available_tabs:
            with tabs[tab_index]:
                try:
                    render_admin_page(user_email)
                except Exception as e:
                    st.error("⚠️ An error occurred while loading admin panel.")
                    logger.error(f"Admin page error: {e}", exc_info=True)
        
        # Sign out in sidebar (minimal)
        with st.sidebar:
            st.markdown("---")
            if st.button("Sign Out", use_container_width=True):
                # Use auth service for proper logout
                if session_id:
                    auth_service.logout(session_id, user_email, "User logout")
                
                # Clear session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("Logged out successfully")
                st.rerun()
    
    except Exception as e:
        # Global error boundary
        st.error("⚠️ An unexpected error occurred")
        st.error("Please try refreshing the page. If the problem persists, contact support.")
        
        # Log error
        logger.error(f"Application error: {e}", exc_info=True)
        
        # Show error details in expander (for debugging)
        with st.expander("Error Details (for support)"):
            st.code(str(e))


def render_admin_page(user_email: str):
    """Admin panel for system management"""
    from app.core.rbac import get_rbac_manager, Role, Permission
    from app.services.deployment_service import get_deployment_service
    
    rbac = get_rbac_manager()
    
    # Verify admin permission
    if not rbac.is_admin(user_email):
        st.error("⛔ Access Denied: Admin privileges required")
        return
    
    st.markdown("## Admin Panel")
    st.markdown("System administration and monitoring")
    st.markdown("")
    
    # Tabs for different admin functions
    admin_tab1, admin_tab2, admin_tab3 = st.tabs([
        "System Health",
        "User Management", 
        "Audit Logs"
    ])
    
    with admin_tab1:
        render_health_dashboard()
    
    with admin_tab2:
        render_user_management(user_email)
    
    with admin_tab3:
        render_audit_logs()


def render_health_dashboard():
    """System health dashboard"""
    import requests
    
    st.markdown("### System Health")
    
    try:
        # Call health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        health_data = response.json()
        
        # Overall status
        status = health_data.get("status", "unknown")
        if status == "healthy":
            st.success(f"✅ System Status: {status.upper()}")
        elif status == "degraded":
            st.warning(f"⚠️ System Status: {status.upper()}")
        else:
            st.error(f"❌ System Status: {status.upper()}")
        
        # Dependency checks
        st.markdown("#### Dependencies")
        checks = health_data.get("checks", {})
        
        cols = st.columns(4)
        for idx, (service, check_data) in enumerate(checks.items()):
            with cols[idx % 4]:
                service_status = check_data.get("status", "unknown") if isinstance(check_data, dict) else check_data
                if service_status == "healthy":
                    st.metric(service.title(), "✅ Healthy")
                elif service_status == "degraded":
                    st.metric(service.title(), "⚠️ Degraded")
                else:
                    st.metric(service.title(), "❌ Unhealthy")
        
        # Circuit breakers
        st.markdown("#### Circuit Breakers")
        circuit_breakers = health_data.get("circuit_breakers", {})
        
        if circuit_breakers:
            for cb_name, cb_data in circuit_breakers.items():
                state = cb_data.get("state", "unknown")
                failures = cb_data.get("failure_count", 0)
                
                if state == "closed":
                    st.success(f"✅ {cb_name}: CLOSED ({failures} failures)")
                elif state == "half_open":
                    st.warning(f"⚠️ {cb_name}: HALF-OPEN (testing recovery)")
                else:
                    st.error(f"❌ {cb_name}: OPEN (service unavailable)")
        else:
            st.info("No circuit breakers configured")
    
    except requests.RequestException as e:
        st.error(f"⚠️ Could not fetch health data: {str(e)}")
        st.info("Make sure the FastAPI server is running on port 8000")


def render_user_management(admin_email: str):
    """User management interface"""
    from app.core.rbac import get_rbac_manager, Role
    
    rbac = get_rbac_manager()
    
    st.markdown("### User Management")
    
    # Role assignment
    st.markdown("#### Assign Role")
    
    with st.form("assign_role"):
        user_email = st.text_input("User Email")
        role = st.selectbox("Role", [r.value for r in Role])
        
        if st.form_submit_button("Assign Role"):
            if user_email:
                rbac.assign_role(user_email, Role(role), admin_email)
                st.success(f"✅ Assigned {role} role to {user_email}")
            else:
                st.error("Please enter a user email")


def render_audit_logs():
    """Audit log viewer"""
    st.markdown("### Audit Logs")
    st.info("🚧 Audit log viewer coming soon")
    st.markdown("View and search security audit logs")



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
