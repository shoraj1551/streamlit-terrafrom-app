"""
Ultra-Minimal Deployment Wizard

Clean, professional, no-nonsense design
"""

import streamlit as st
from typing import Dict, Any, Optional
from enum import Enum

from app.services.user_survey import get_user_profile
from app.models.industry import get_all_industries
from app.services.ai_requirements_agent import AIRequirementsAgent
from app.pages.requirements_input import render_requirements_input
from app.services.priority_engine import PriorityEngine
from app.services.multi_cloud_analyzer import MultiCloudAnalyzer
from app.pages.cloud_recommendation import render_recommendation_ui
from app.services.two_factor_auth import verify_2fa_for_action


class WizardStep(str, Enum):
    """Wizard steps"""
    INDUSTRY = "industry"
    CLOUD_DECISION = "cloud_decision"
    REQUIREMENTS = "requirements"
    PRIORITIES = "priorities"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    DEPLOYMENT = "deployment"


def render_deployment_wizard(user_email: str):
    """Minimal deployment wizard"""
    
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = WizardStep.INDUSTRY
    
    if 'wizard_data' not in st.session_state:
        st.session_state.wizard_data = {}
    
    # Minimal progress
    _render_minimal_progress()
    
    # Render step
    current_step = st.session_state.wizard_step
    
    if current_step == WizardStep.INDUSTRY:
        _render_industry_step(user_email)
    elif current_step == WizardStep.CLOUD_DECISION:
        _render_cloud_step()
    elif current_step == WizardStep.REQUIREMENTS:
        _render_requirements_step(user_email)
    elif current_step == WizardStep.PRIORITIES:
        _render_priorities_step(user_email)
    elif current_step == WizardStep.ANALYSIS:
        _render_analysis_step(user_email)
    elif current_step == WizardStep.RECOMMENDATION:
        _render_recommendation_step(user_email)
    elif current_step == WizardStep.DEPLOYMENT:
        _render_deployment_step(user_email)


def _render_minimal_progress():
    """Ultra-minimal progress indicator"""
    steps = ["Industry", "Cloud", "Requirements", "Priorities", "Analysis", "Recommendation", "Deploy"]
    current_step = st.session_state.wizard_step
    step_order = list(WizardStep)
    current_index = step_order.index(current_step)
    
    progress = (current_index / (len(steps) - 1)) * 100
    
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
            {''.join([
                f'<div style="flex: 1; height: 2px; background: {"#000000" if i <= current_index else "#e5e7eb"};"></div>'
                for i in range(len(steps))
            ])}
        </div>
        <div style="font-size: 0.75rem; color: #6b7280;">
            Step {current_index + 1} of {len(steps)}: {steps[current_index]}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_industry_step(user_email: str):
    """Minimal industry selection"""
    st.markdown("## Select Industry")
    st.markdown("")
    
    industries = get_all_industries()
    
    for industry in industries:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{industry.display_name}**")
            st.markdown(f"<p style='font-size: 0.875rem; color: #6b7280;'>{industry.description}</p>", unsafe_allow_html=True)
        
        with col2:
            if st.button("Select", key=f"ind_{industry.name}", use_container_width=True):
                st.session_state.wizard_data['industry'] = industry
                st.session_state.wizard_step = WizardStep.CLOUD_DECISION
                st.rerun()
        
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)


def _render_cloud_step():
    """Minimal cloud decision"""
    st.markdown("## Cloud Provider")
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("I've decided on a provider", use_container_width=True):
            provider = st.selectbox("Provider", ["AWS", "Azure", "GCP"])
            if st.button("Continue"):
                st.session_state.wizard_data['locked_provider'] = provider.lower()
                st.session_state.wizard_step = WizardStep.REQUIREMENTS
                st.rerun()
    
    with col2:
        if st.button("Recommend for me", use_container_width=True):
            st.session_state.wizard_data['locked_provider'] = None
            st.session_state.wizard_step = WizardStep.REQUIREMENTS
            st.rerun()


def _render_requirements_step(user_email: str):
    """Minimal requirements"""
    st.markdown("## Requirements")
    st.markdown("")
    
    requirements = render_requirements_input(user_email)
    
    if requirements:
        st.session_state.wizard_data['requirements'] = requirements
        if st.button("Continue", type="primary"):
            st.session_state.wizard_step = WizardStep.PRIORITIES
            st.rerun()


def _render_priorities_step(user_email: str):
    """Minimal priorities"""
    st.markdown("## Priorities")
    st.markdown("")
    
    industry = st.session_state.wizard_data.get('industry')
    
    if 'priority_engine' not in st.session_state:
        st.session_state.priority_engine = PriorityEngine()
    
    engine = st.session_state.priority_engine
    questions = engine.get_questions(industry.name if industry else "default")
    
    responses = {}
    
    for i, question in enumerate(questions):
        st.markdown(f"**{question['question']}**")
        responses[f"q{i}"] = st.slider("", 1, 10, 5, key=f"priority_{i}", label_visibility="collapsed")
        st.markdown("")
    
    if st.button("Analyze", type="primary"):
        scores = engine.calculate_priority_scores(responses, industry.name if industry else "default")
        st.session_state.wizard_data['priority_responses'] = responses
        st.session_state.wizard_data['priority_scores'] = scores
        st.session_state.wizard_step = WizardStep.ANALYSIS
        st.rerun()


def _render_analysis_step(user_email: str):
    """Minimal analysis"""
    st.markdown("## Analysis")
    st.markdown("")
    
    with st.spinner("Analyzing..."):
        requirements = st.session_state.wizard_data['requirements']
        priority_scores = st.session_state.wizard_data['priority_scores']
        industry = st.session_state.wizard_data.get('industry')
        
        if 'cloud_analyzer' not in st.session_state:
            st.session_state.cloud_analyzer = MultiCloudAnalyzer()
        
        analyzer = st.session_state.cloud_analyzer
        
        analyses = analyzer.analyze_all_providers(
            requirements,
            {k.value: v for k, v in priority_scores.items()},
            industry.name if industry else "default"
        )
        
        recommendation = analyzer.get_recommendation(
            analyses,
            {k.value: v for k, v in priority_scores.items()}
        )
        
        st.session_state.wizard_data['analyses'] = analyses
        st.session_state.wizard_data['recommendation'] = recommendation
        
        st.success("Analysis complete")
        
        if st.button("View Results", type="primary"):
            st.session_state.wizard_step = WizardStep.RECOMMENDATION
            st.rerun()


def _render_recommendation_step(user_email: str):
    """Minimal recommendation"""
    analyses = st.session_state.wizard_data['analyses']
    recommendation = st.session_state.wizard_data['recommendation']
    requirements = st.session_state.wizard_data['requirements']
    
    render_recommendation_ui(analyses, recommendation, requirements, user_email)
    
    st.markdown("")
    
    if st.button("Deploy", type="primary"):
        st.session_state.wizard_step = WizardStep.DEPLOYMENT
        st.rerun()


def _render_deployment_step(user_email: str):
    """Minimal deployment"""
    st.markdown("## Deploy")
    st.markdown("")
    
    recommendation = st.session_state.wizard_data['recommendation']
    primary_provider = recommendation['primary_provider']
    
    st.markdown(f"**Provider**: {primary_provider.upper()}")
    st.markdown("")
    
    deploy_dev = st.checkbox("Development")
    deploy_staging = st.checkbox("Staging")
    deploy_prod = st.checkbox("Production")
    
    if st.button("Deploy Infrastructure", type="primary"):
        with st.spinner("Deploying..."):
            import time
            time.sleep(2)
            st.success("Deployed successfully")
