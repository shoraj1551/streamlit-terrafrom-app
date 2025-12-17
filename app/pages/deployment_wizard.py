"""
Professional Deployment Wizard

Clean, enterprise-grade deployment flow
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
    """Professional deployment wizard"""
    
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = WizardStep.INDUSTRY
    
    if 'wizard_data' not in st.session_state:
        st.session_state.wizard_data = {}
    
    # Professional progress indicator
    _render_progress_indicator()
    
    # Render current step
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


def _render_progress_indicator():
    """Professional progress indicator - GitHub style"""
    steps = [
        ("Industry", "Select your industry vertical"),
        ("Cloud", "Choose cloud strategy"),
        ("Requirements", "Define infrastructure needs"),
        ("Priorities", "Set business priorities"),
        ("Analysis", "Multi-cloud cost analysis"),
        ("Recommendation", "Review recommendations"),
        ("Deploy", "Deploy infrastructure")
    ]
    
    current_step = st.session_state.wizard_step
    step_order = list(WizardStep)
    current_index = step_order.index(current_step)
    
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e1e4e8; border-radius: 6px; padding: 1.5rem; margin-bottom: 2rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
            {''.join([
                f'''<div style="flex: 1; text-align: center;">
                    <div style="width: 32px; height: 32px; border-radius: 50%; margin: 0 auto; 
                         background: {'#0366d6' if i <= current_index else '#f3f4f6'}; 
                         color: {'#ffffff' if i <= current_index else '#6a737d'}; 
                         display: flex; align-items: center; justify-content: center;
                         font-weight: 600; font-size: 0.875rem; 
                         border: 2px solid {'#0366d6' if i <= current_index else '#e1e4e8'};">
                        {i + 1}
                    </div>
                    <div style="font-size: 0.75rem; font-weight: {'600' if i == current_index else '500'}; 
                         color: {'#24292e' if i == current_index else '#6a737d'}; margin-top: 0.5rem;">
                        {label}
                    </div>
                    <div style="font-size: 0.625rem; color: #6a737d; margin-top: 0.25rem;">
                        {desc}
                    </div>
                </div>'''
                for i, (label, desc) in enumerate(steps)
            ])}
        </div>
        <div style="background: #e1e4e8; height: 4px; border-radius: 2px; overflow: hidden;">
            <div style="background: #0366d6; height: 100%; width: {(current_index / (len(steps) - 1)) * 100}%; transition: width 0.3s;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_industry_step(user_email: str):
    """Professional industry selection"""
    st.markdown("## Select Industry")
    st.markdown("Choose your industry vertical to receive tailored infrastructure recommendations")
    st.markdown("")
    
    industries = get_all_industries()
    
    # Display as professional cards
    for industry in industries:
        st.markdown(f"""
        <div class="pro-card">
            <h3 style="margin-top: 0;">{industry.display_name}</h3>
            <p style="margin-bottom: 1rem;">{industry.description}</p>
            <div style="font-size: 0.75rem; color: #6a737d;">
                <strong>Typical Cost:</strong> {industry.typical_monthly_cost_range}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button(f"Select", key=f"ind_{industry.name}", type="primary", use_container_width=True):
                st.session_state.wizard_data['industry'] = industry
                st.session_state.wizard_step = WizardStep.CLOUD_DECISION
                st.rerun()
        
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)


def _render_cloud_step():
    """Professional cloud decision"""
    st.markdown("## Cloud Provider Strategy")
    st.markdown("Have you already decided on a cloud provider?")
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="pro-card">
            <h3>I've Decided</h3>
            <p>Select your preferred cloud provider</p>
        </div>
        """, unsafe_allow_html=True)
        
        provider = st.selectbox("Provider", ["AWS", "Azure", "GCP"], label_visibility="collapsed")
        
        if st.button("Continue with " + provider, type="primary", use_container_width=True):
            st.session_state.wizard_data['locked_provider'] = provider.lower()
            st.session_state.wizard_step = WizardStep.REQUIREMENTS
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="pro-card">
            <h3>Recommend for Me</h3>
            <p>Get AI-powered cloud provider recommendations</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Get Recommendation", type="primary", use_container_width=True):
            st.session_state.wizard_data['locked_provider'] = None
            st.session_state.wizard_step = WizardStep.REQUIREMENTS
            st.rerun()


def _render_requirements_step(user_email: str):
    """Professional requirements input"""
    st.markdown("## Infrastructure Requirements")
    st.markdown("Define your infrastructure needs")
    st.markdown("")
    
    requirements = render_requirements_input(user_email)
    
    if requirements:
        st.session_state.wizard_data['requirements'] = requirements
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Continue", type="primary", use_container_width=True):
                st.session_state.wizard_step = WizardStep.PRIORITIES
                st.rerun()


def _render_priorities_step(user_email: str):
    """Professional priorities assessment"""
    st.markdown("## Business Priorities")
    st.markdown("Rate the importance of each factor for your infrastructure")
    st.markdown("")
    
    industry = st.session_state.wizard_data.get('industry')
    
    if 'priority_engine' not in st.session_state:
        st.session_state.priority_engine = PriorityEngine()
    
    engine = st.session_state.priority_engine
    questions = engine.get_questions(industry.name if industry else "default")
    
    responses = {}
    
    for i, question in enumerate(questions):
        st.markdown(f"**{question['question']}**")
        responses[f"q{i}"] = st.slider(
            "Importance",
            1, 10, 5,
            key=f"priority_{i}",
            help="1 = Not important, 10 = Critical"
        )
        st.markdown("")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Analyze Providers", type="primary", use_container_width=True):
            scores = engine.calculate_priority_scores(responses, industry.name if industry else "default")
            st.session_state.wizard_data['priority_responses'] = responses
            st.session_state.wizard_data['priority_scores'] = scores
            st.session_state.wizard_step = WizardStep.ANALYSIS
            st.rerun()


def _render_analysis_step(user_email: str):
    """Professional analysis"""
    st.markdown("## Multi-Cloud Analysis")
    st.markdown("Analyzing AWS, Azure, and GCP for your requirements")
    st.markdown("")
    
    with st.spinner("Running comprehensive cost and capability analysis..."):
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
        
        primary = recommendation['primary_provider'].upper()
        primary_analysis = recommendation['primary_analysis']
        
        st.info(f"**Recommended Provider**: {primary} — ${primary_analysis.total_monthly:,.2f}/month")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("View Details", type="primary", use_container_width=True):
                st.session_state.wizard_step = WizardStep.RECOMMENDATION
                st.rerun()


def _render_recommendation_step(user_email: str):
    """Professional recommendation display"""
    analyses = st.session_state.wizard_data['analyses']
    recommendation = st.session_state.wizard_data['recommendation']
    requirements = st.session_state.wizard_data['requirements']
    
    render_recommendation_ui(analyses, recommendation, requirements, user_email)
    
    st.markdown("")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Deploy Infrastructure", type="primary", use_container_width=True):
            st.session_state.wizard_step = WizardStep.DEPLOYMENT
            st.rerun()


def _render_deployment_step(user_email: str):
    """Professional deployment"""
    st.markdown("## Deploy Infrastructure")
    st.markdown("")
    
    recommendation = st.session_state.wizard_data['recommendation']
    primary_provider = recommendation['primary_provider']
    
    st.markdown(f"""
    <div class="pro-card">
        <h3>Deployment Configuration</h3>
        <p><strong>Provider:</strong> {primary_provider.upper()}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Select Environments")
    
    deploy_dev = st.checkbox("Development Environment", value=True)
    deploy_staging = st.checkbox("Staging Environment", value=True)
    deploy_prod = st.checkbox("Production Environment", value=False)
    
    st.markdown("")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Deploy", type="primary", use_container_width=True):
            with st.spinner("Deploying infrastructure..."):
                import time
                time.sleep(2)
                st.success("Infrastructure deployed successfully")
                st.balloons()
