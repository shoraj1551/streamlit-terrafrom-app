"""
User Survey System

Collects user profile information for personalized recommendations.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import streamlit as st
from pathlib import Path
import json


class UserSurvey:
    """User profiling survey system"""
    
    COMPANY_TYPES = [
        "Service Provider",
        "Product Company",
        "Startup (Seed/Series A)",
        "Enterprise (500+ employees)",
        "Individual/Freelancer"
    ]
    
    COMPANY_SIZES = [
        "1-10 employees",
        "11-50 employees",
        "51-200 employees",
        "201-500 employees",
        "500+ employees"
    ]
    
    INFRASTRUCTURE_STATUS = [
        "No infrastructure yet",
        "On-premise only",
        "Cloud (AWS)",
        "Cloud (Azure)",
        "Cloud (GCP)",
        "Multi-cloud",
        "Hybrid (on-premise + cloud)"
    ]
    
    BUDGET_RANGES = [
        "Less than $500/month",
        "$500 - $2,000/month",
        "$2,000 - $10,000/month",
        "$10,000 - $50,000/month",
        "$50,000+/month"
    ]
    
    PRIMARY_GOALS = [
        "Cost optimization",
        "Security & compliance",
        "Performance & speed",
        "Scalability",
        "High availability",
        "Developer productivity"
    ]
    
    def __init__(self):
        self.surveys_file = Path("data/surveys.json")
        self.surveys_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.surveys_file.exists():
            self._save_surveys({})
    
    def _load_surveys(self) -> Dict[str, Any]:
        """Load surveys from file"""
        try:
            with open(self.surveys_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_surveys(self, surveys: Dict[str, Any]):
        """Save surveys to file"""
        with open(self.surveys_file, 'w') as f:
            json.dump(surveys, f, indent=2)
    
    def save_survey(self, email: str, survey_data: Dict[str, Any]) -> bool:
        """
        Save user survey data
        
        Args:
            email: User email
            survey_data: Survey responses
            
        Returns:
            Success status
        """
        surveys = self._load_surveys()
        
        surveys[email] = {
            **survey_data,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        self._save_surveys(surveys)
        return True
    
    def get_survey(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user survey data"""
        surveys = self._load_surveys()
        return surveys.get(email)
    
    def has_completed_survey(self, email: str) -> bool:
        """Check if user has completed survey"""
        return self.get_survey(email) is not None


def render_user_survey(user_email: str):
    """
    Render user survey form
    
    Args:
        user_email: User's email address
    """
    st.markdown("## 📋 Quick Profile Setup")
    st.markdown("Help us personalize your experience (takes 2 minutes)")
    
    # Initialize survey system
    if 'survey' not in st.session_state:
        st.session_state.survey = UserSurvey()
    
    # Check if already completed
    if st.session_state.survey.has_completed_survey(user_email):
        st.success("✅ Profile already completed!")
        if st.button("Update Profile"):
            st.session_state.force_survey = True
            st.rerun()
        return True
    
    st.markdown("---")
    
    with st.form("user_survey"):
        # Company Information
        st.markdown("### 🏢 Company Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_type = st.selectbox(
                "Company Type",
                options=UserSurvey.COMPANY_TYPES,
                help="What best describes your organization?"
            )
        
        with col2:
            company_size = st.selectbox(
                "Company Size",
                options=UserSurvey.COMPANY_SIZES,
                help="Number of employees"
            )
        
        # Infrastructure Status
        st.markdown("### ☁️ Current Infrastructure")
        
        infrastructure_status = st.selectbox(
            "Current Infrastructure Status",
            options=UserSurvey.INFRASTRUCTURE_STATUS,
            help="What infrastructure do you currently have?"
        )
        
        # Budget
        st.markdown("### 💰 Budget")
        
        budget_range = st.selectbox(
            "Monthly Infrastructure Budget",
            options=UserSurvey.BUDGET_RANGES,
            help="Approximate monthly budget for cloud infrastructure"
        )
        
        # Primary Goals
        st.markdown("### 🎯 Primary Goals")
        
        primary_goals = st.multiselect(
            "What are your top priorities? (Select up to 3)",
            options=UserSurvey.PRIMARY_GOALS,
            help="Select your main objectives",
            max_selections=3
        )
        
        # Additional Information
        st.markdown("### 📝 Additional Information")
        
        use_case_description = st.text_area(
            "Briefly describe your use case (optional)",
            placeholder="E.g., We're building a SaaS platform for healthcare providers...",
            help="This helps us provide better recommendations"
        )
        
        # Submit
        st.markdown("---")
        submitted = st.form_submit_button("Complete Profile", use_container_width=True)
        
        if submitted:
            if not primary_goals:
                st.error("Please select at least one primary goal")
                return False
            
            # Save survey data
            survey_data = {
                'company_type': company_type,
                'company_size': company_size,
                'infrastructure_status': infrastructure_status,
                'budget_range': budget_range,
                'primary_goals': primary_goals,
                'use_case_description': use_case_description
            }
            
            success = st.session_state.survey.save_survey(user_email, survey_data)
            
            if success:
                # Update user's survey completion status
                if 'auth' in st.session_state:
                    st.session_state.auth.update_user(user_email, {'survey_completed': True})
                
                st.success("✅ Profile completed successfully!")
                st.balloons()
                
                # Update session state
                if 'user' in st.session_state:
                    st.session_state.user['survey_completed'] = True
                
                return True
            else:
                st.error("Failed to save profile. Please try again.")
                return False
    
    return False


def check_survey_completion(user_email: str) -> bool:
    """
    Check if user has completed survey, show if not
    
    Args:
        user_email: User's email
        
    Returns:
        True if completed, False otherwise
    """
    if 'survey' not in st.session_state:
        st.session_state.survey = UserSurvey()
    
    # Check if force survey update
    if st.session_state.get('force_survey', False):
        st.session_state.force_survey = False
        return False
    
    # Check completion
    if not st.session_state.survey.has_completed_survey(user_email):
        render_user_survey(user_email)
        st.stop()
        return False
    
    return True


def get_user_profile(user_email: str) -> Optional[Dict[str, Any]]:
    """Get user's survey profile"""
    if 'survey' not in st.session_state:
        st.session_state.survey = UserSurvey()
    
    return st.session_state.survey.get_survey(user_email)
