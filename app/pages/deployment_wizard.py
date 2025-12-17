"""
Enhanced Deployment Wizard

Step-by-step wizard for complete infrastructure deployment journey.
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
    """
    Render complete deployment wizard
    
    Args:
        user_email: User's email
    """
    
    # Initialize wizard state
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = WizardStep.INDUSTRY
    
    if 'wizard_data' not in st.session_state:
        st.session_state.wizard_data = {}
    
    # Progress bar
    _render_progress_bar()
    
    st.markdown("---")
    
    # Render current step
    current_step = st.session_state.wizard_step
    
    if current_step == WizardStep.INDUSTRY:
        _render_industry_step(user_email)
    
    elif current_step == WizardStep.CLOUD_DECISION:
        _render_cloud_decision_step()
    
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


def _render_progress_bar():
    """Render professional progress indicator"""
    
    steps = [
        ("Industry", "Select your industry vertical"),
        ("Cloud", "Choose cloud provider strategy"),
        ("Requirements", "Define infrastructure needs"),
        ("Priorities", "Set business priorities"),
        ("Analysis", "Multi-cloud cost analysis"),
        ("Recommendation", "Review recommendations"),
        ("Deploy", "Deploy infrastructure")
    ]
    
    current_step = st.session_state.wizard_step
    step_order = list(WizardStep)
    current_index = step_order.index(current_step)
    
    # Progress percentage
    progress = (current_index / (len(steps) - 1)) * 100
    
    st.markdown(f"""
    <div style="margin-bottom: 2rem; background: white; padding: 1.5rem; border-radius: 0.5rem; border: 1px solid #e5e7eb;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
            {''.join([
                f'''<div style="flex: 1; text-align: center; position: relative;">
                    <div style="width: 32px; height: 32px; border-radius: 50%; margin: 0 auto; 
                         background: {'#2563eb' if i <= current_index else '#e5e7eb'}; 
                         color: {'white' if i <= current_index else '#9ca3af'}; 
                         display: flex; align-items: center; justify-content: center;
                         font-weight: 600; font-size: 0.875rem; border: 2px solid {'#2563eb' if i <= current_index else '#e5e7eb'};">
                        {i + 1}
                    </div>
                    <div style="font-size: 0.75rem; font-weight: {'600' if i == current_index else '500'}; 
                         color: {'#111827' if i == current_index else '#6b7280'}; margin-top: 0.5rem;">
                        {label}
                    </div>
                    <div style="font-size: 0.625rem; color: #9ca3af; margin-top: 0.125rem;">
                        {desc}
                    </div>
                </div>'''
                for i, (label, desc) in enumerate(steps)
            ])}
        </div>
        <div style="background: #e5e7eb; height: 4px; border-radius: 2px; overflow: hidden; margin-top: 1rem;">
            <div style="background: linear-gradient(90deg, #2563eb, #1d4ed8); height: 100%; width: {progress}%; transition: width 0.3s;"></div>
        </div>
        <div style="text-align: center; margin-top: 0.75rem; font-size: 0.875rem; color: #6b7280;">
            Step {current_index + 1} of {len(steps)} • {progress:.0f}% Complete
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_industry_step(user_email: str):
    """Step 1: Industry Selection - Professional Design"""
    
    st.markdown("### Select Your Industry")
    st.markdown("Choose your industry vertical to receive tailored infrastructure recommendations")
    
    st.markdown("")
    
    industries = get_all_industries()
    
    # Display as professional cards in grid
    cols = st.columns(2)
    
    for idx, industry in enumerate(industries):
        with cols[idx % 2]:
            # Professional card design
            st.markdown(f"""
            <div style="background: white; padding: 1.25rem; border-radius: 0.5rem; border: 1px solid #e5e7eb; margin-bottom: 1rem; cursor: pointer; transition: all 0.2s;">
                <div style="font-size: 1.125rem; font-weight: 600; color: #111827; margin-bottom: 0.5rem;">
                    {industry.display_name}
                </div>
                <div style="font-size: 0.875rem; color: #6b7280; margin-bottom: 0.75rem;">
                    {industry.description}
                </div>
                <div style="font-size: 0.75rem; color: #9ca3af;">
                    <span style="font-weight: 500;">Typical Cost:</span> {industry.typical_monthly_cost_range}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(
                f"Select {industry.display_name}",
                key=f"ind_{industry.name}",
                use_container_width=True,
                type="secondary"
            ):
                st.session_state.wizard_data['industry'] = industry
                st.session_state.wizard_step = WizardStep.CLOUD_DECISION
                st.rerun()


def _render_cloud_decision_step():
    """Step 2: Cloud Provider Decision"""
    
    st.markdown("## ☁️ Cloud Provider Decision")
    st.markdown("Have you already decided on a cloud provider?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Yes, I've decided", use_container_width=True, type="primary"):
            st.session_state.wizard_data['cloud_decided'] = True
            
            # Show provider selection
            provider = st.selectbox(
                "Select your cloud provider:",
                options=["AWS", "Azure", "GCP"]
            )
            
            if st.button("Continue", use_container_width=True):
                st.session_state.wizard_data['locked_provider'] = provider.lower()
                st.session_state.wizard_step = WizardStep.REQUIREMENTS
                st.rerun()
    
    with col2:
        if st.button("❓ No, recommend for me", use_container_width=True):
            st.session_state.wizard_data['cloud_decided'] = False
            st.session_state.wizard_data['locked_provider'] = None
            st.session_state.wizard_step = WizardStep.REQUIREMENTS
            st.rerun()
    
    # Back button
    if st.button("← Back"):
        st.session_state.wizard_step = WizardStep.INDUSTRY
        st.rerun()


def _render_requirements_step(user_email: str):
    """Step 3: Requirements Input"""
    
    st.markdown("## 📝 Infrastructure Requirements")
    
    requirements = render_requirements_input(user_email)
    
    if requirements:
        st.session_state.wizard_data['requirements'] = requirements
        
        if st.button("Continue to Priorities →", type="primary", use_container_width=True):
            st.session_state.wizard_step = WizardStep.PRIORITIES
            st.rerun()
    
    # Back button
    if st.button("← Back"):
        st.session_state.wizard_step = WizardStep.CLOUD_DECISION
        st.rerun()


def _render_priorities_step(user_email: str):
    """Step 4: Priority Assessment"""
    
    st.markdown("## 🎯 Priority Assessment")
    st.markdown("Rate the importance of each factor (1-10)")
    
    industry = st.session_state.wizard_data.get('industry')
    
    if 'priority_engine' not in st.session_state:
        st.session_state.priority_engine = PriorityEngine()
    
    engine = st.session_state.priority_engine
    questions = engine.get_questions(industry.name if industry else "default")
    
    responses = {}
    
    for i, question in enumerate(questions):
        st.markdown(f"**{i+1}. {question['question']}**")
        
        responses[f"q{i}"] = st.slider(
            "Importance",
            min_value=1,
            max_value=10,
            value=5,
            key=f"priority_{i}",
            label_visibility="collapsed"
        )
        
        st.markdown("---")
    
    if st.button("Analyze Cloud Providers →", type="primary", use_container_width=True):
        # Calculate scores
        scores = engine.calculate_priority_scores(
            responses,
            industry.name if industry else "default"
        )
        
        st.session_state.wizard_data['priority_responses'] = responses
        st.session_state.wizard_data['priority_scores'] = scores
        
        st.session_state.wizard_step = WizardStep.ANALYSIS
        st.rerun()
    
    # Back button
    if st.button("← Back"):
        st.session_state.wizard_step = WizardStep.REQUIREMENTS
        st.rerun()


def _render_analysis_step(user_email: str):
    """Step 5: Multi-Cloud Analysis"""
    
    st.markdown("## 📊 Analyzing Cloud Providers...")
    
    with st.spinner("Running comprehensive analysis across AWS, Azure, and GCP..."):
        requirements = st.session_state.wizard_data['requirements']
        priority_scores = st.session_state.wizard_data['priority_scores']
        industry = st.session_state.wizard_data.get('industry')
        
        # Initialize analyzer
        if 'cloud_analyzer' not in st.session_state:
            st.session_state.cloud_analyzer = MultiCloudAnalyzer()
        
        analyzer = st.session_state.cloud_analyzer
        
        # Run analysis
        analyses = analyzer.analyze_all_providers(
            requirements,
            {k.value: v for k, v in priority_scores.items()},
            industry.name if industry else "default"
        )
        
        # Get recommendation
        recommendation = analyzer.get_recommendation(
            analyses,
            {k.value: v for k, v in priority_scores.items()}
        )
        
        # Save results
        st.session_state.wizard_data['analyses'] = analyses
        st.session_state.wizard_data['recommendation'] = recommendation
        
        st.success("✅ Analysis complete!")
        
        # Show quick summary
        primary = recommendation['primary_provider'].upper()
        primary_analysis = recommendation['primary_analysis']
        
        st.info(f"**Recommended**: {primary} (${primary_analysis.total_monthly:,.2f}/month)")
        
        if st.button("View Detailed Recommendation →", type="primary", use_container_width=True):
            st.session_state.wizard_step = WizardStep.RECOMMENDATION
            st.rerun()


def _render_recommendation_step(user_email: str):
    """Step 6: Recommendation Display"""
    
    analyses = st.session_state.wizard_data['analyses']
    recommendation = st.session_state.wizard_data['recommendation']
    requirements = st.session_state.wizard_data['requirements']
    
    # Render recommendation UI
    render_recommendation_ui(analyses, recommendation, requirements, user_email)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Back to Analysis"):
            st.session_state.wizard_step = WizardStep.ANALYSIS
            st.rerun()
    
    with col2:
        if st.button("Proceed to Deployment →", type="primary", use_container_width=True):
            st.session_state.wizard_step = WizardStep.DEPLOYMENT
            st.rerun()


def _render_deployment_step(user_email: str):
    """Step 7: Deployment"""
    
    st.markdown("## 🚀 Deploy Infrastructure")
    
    recommendation = st.session_state.wizard_data['recommendation']
    primary_provider = recommendation['primary_provider']
    
    st.info(f"Deploying to **{primary_provider.upper()}**")
    
    # Environment selection
    st.markdown("### Select Environments to Deploy")
    
    deploy_dev = st.checkbox("Development Environment", value=True)
    deploy_staging = st.checkbox("Staging Environment", value=True)
    deploy_prod = st.checkbox("Production Environment", value=False)
    
    if deploy_dev or deploy_staging or deploy_prod:
        if st.button("🚀 Start Deployment", type="primary", use_container_width=True):
            with st.spinner("Deploying infrastructure..."):
                # Simulate deployment
                import time
                
                if deploy_dev:
                    st.info("Deploying Development environment...")
                    time.sleep(1)
                    st.success("✅ Development deployed")
                
                if deploy_staging:
                    st.info("Deploying Staging environment...")
                    time.sleep(1)
                    st.success("✅ Staging deployed")
                
                if deploy_prod:
                    st.info("Deploying Production environment...")
                    time.sleep(1)
                    st.success("✅ Production deployed")
                
                st.balloons()
                st.success("🎉 All environments deployed successfully!")
    
    # Destroy functionality
    st.markdown("---")
    st.markdown("### 🗑️ Destroy Infrastructure")
    
    st.warning("⚠️ This action requires 2FA verification")
    
    destroy_env = st.selectbox(
        "Select environment to destroy:",
        options=["Development", "Staging", "Production (Disabled)"]
    )
    
    if "Production" not in destroy_env:
        if st.button("🗑️ Destroy Environment", type="secondary"):
            # Verify 2FA
            if verify_2fa_for_action(user_email, f"Destroy {destroy_env}"):
                with st.spinner(f"Destroying {destroy_env}..."):
                    import time
                    time.sleep(2)
                    st.success(f"✅ {destroy_env} destroyed")
    else:
        st.error("❌ Production environment cannot be destroyed for safety")
    
    # Back button
    if st.button("← Back to Recommendation"):
        st.session_state.wizard_step = WizardStep.RECOMMENDATION
        st.rerun()
