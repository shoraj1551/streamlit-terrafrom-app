"""
Cloud Recommendation UI

Beautiful visualization of multi-cloud analysis results with charts and comparisons.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any

from app.services.multi_cloud_analyzer import MultiCloudAnalyzer
from app.services.report_generator import ReportGenerator


def render_recommendation_ui(
    analyses: Dict[str, Any],
    recommendation: Dict[str, Any],
    requirements: Dict[str, Any],
    user_email: str
):
    """
    Render cloud recommendation UI with visualizations
    
    Args:
        analyses: Analysis results for all providers
        recommendation: Recommendation details
        requirements: Infrastructure requirements
        user_email: User's email
    """
    st.markdown("## 🎯 Cloud Provider Recommendation")
    
    # Top Recommendation Banner
    _render_recommendation_banner(recommendation)
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Cost Comparison",
        "⭐ Scoring Analysis",
        "📈 Environment Breakdown",
        "📄 Download Report"
    ])
    
    with tab1:
        _render_cost_comparison(analyses)
    
    with tab2:
        _render_scoring_analysis(analyses)
    
    with tab3:
        _render_environment_breakdown(analyses)
    
    with tab4:
        _render_report_download(analyses, recommendation, requirements, user_email)


def _render_recommendation_banner(recommendation: Dict[str, Any]):
    """Render top recommendation banner"""
    
    primary = recommendation['primary_provider'].upper()
    analysis = recommendation['primary_analysis']
    confidence = recommendation['confidence']
    
    # Color based on confidence
    color = "🟢" if confidence == "high" else "🟡"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 2rem;
    ">
        <h2 style="margin: 0; color: white;">{color} Recommended: {primary}</h2>
        <p style="font-size: 1.1rem; margin: 0.5rem 0;">
            {recommendation['reasoning']}
        </p>
        <div style="display: flex; gap: 2rem; margin-top: 1rem;">
            <div>
                <div style="font-size: 0.9rem; opacity: 0.9;">Monthly Cost</div>
                <div style="font-size: 1.5rem; font-weight: bold;">${analysis.total_monthly:,.2f}</div>
            </div>
            <div>
                <div style="font-size: 0.9rem; opacity: 0.9;">3-Year TCO</div>
                <div style="font-size: 1.5rem; font-weight: bold;">${analysis.three_year_tco:,.2f}</div>
            </div>
            <div>
                <div style="font-size: 0.9rem; opacity: 0.9;">Overall Score</div>
                <div style="font-size: 1.5rem; font-weight: bold;">{analysis.overall_score}/10</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Multi-cloud recommendation if applicable
    if recommendation.get('multi_cloud_recommended'):
        st.info(f"💡 **Multi-Cloud Strategy**: {recommendation['multi_cloud_strategy']}")


def _render_cost_comparison(analyses: Dict[str, Any]):
    """Render cost comparison charts"""
    
    st.markdown("### 💰 Cost Comparison")
    
    # Prepare data
    providers = []
    monthly_costs = []
    yearly_costs = []
    tco_costs = []
    
    for provider, analysis in analyses.items():
        providers.append(provider.upper())
        monthly_costs.append(analysis.total_monthly)
        yearly_costs.append(analysis.total_yearly)
        tco_costs.append(analysis.three_year_tco)
    
    # Monthly Cost Comparison Bar Chart
    col1, col2 = st.columns(2)
    
    with col1:
        fig_monthly = go.Figure(data=[
            go.Bar(
                x=providers,
                y=monthly_costs,
                text=[f'${cost:,.0f}' for cost in monthly_costs],
                textposition='auto',
                marker=dict(
                    color=['#10b981', '#3b82f6', '#f59e0b'],
                    line=dict(color='white', width=2)
                )
            )
        ])
        
        fig_monthly.update_layout(
            title="Monthly Cost Comparison",
            xaxis_title="Provider",
            yaxis_title="Cost (USD)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    with col2:
        # 3-Year TCO Comparison
        fig_tco = go.Figure(data=[
            go.Bar(
                x=providers,
                y=tco_costs,
                text=[f'${cost:,.0f}' for cost in tco_costs],
                textposition='auto',
                marker=dict(
                    color=['#8b5cf6', '#ec4899', '#f97316'],
                    line=dict(color='white', width=2)
                )
            )
        ])
        
        fig_tco.update_layout(
            title="3-Year Total Cost of Ownership",
            xaxis_title="Provider",
            yaxis_title="Cost (USD)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_tco, use_container_width=True)
    
    # Cost Breakdown Table
    st.markdown("#### Detailed Cost Breakdown")
    
    cost_data = []
    for provider, analysis in analyses.items():
        cost_data.append({
            'Provider': provider.upper(),
            'Dev': f"${analysis.dev_cost.monthly_cost:,.2f}",
            'Staging': f"${analysis.staging_cost.monthly_cost:,.2f}",
            'Production': f"${analysis.prod_cost.monthly_cost:,.2f}",
            'Total Monthly': f"${analysis.total_monthly:,.2f}",
            'Total Yearly': f"${analysis.total_yearly:,.2f}",
            '3-Year TCO': f"${analysis.three_year_tco:,.2f}"
        })
    
    df_cost = pd.DataFrame(cost_data)
    st.dataframe(df_cost, use_container_width=True, hide_index=True)
    
    # Cost savings comparison
    min_cost = min(monthly_costs)
    max_cost = max(monthly_costs)
    savings = max_cost - min_cost
    savings_pct = (savings / max_cost) * 100
    
    st.success(f"💡 **Potential Savings**: ${savings:,.2f}/month ({savings_pct:.1f}%) by choosing the most cost-effective option")


def _render_scoring_analysis(analyses: Dict[str, Any]):
    """Render scoring analysis with radar chart"""
    
    st.markdown("### ⭐ Capability Scoring")
    
    # Radar chart for capabilities
    categories = ['Cost', 'Performance', 'Security', 'Scalability', 'Compliance', 'Support']
    
    fig = go.Figure()
    
    colors = {'aws': '#FF9900', 'azure': '#0078D4', 'gcp': '#4285F4'}
    
    for provider, analysis in analyses.items():
        scores = [
            analysis.cost_score,
            analysis.performance_score,
            analysis.security_score,
            analysis.scalability_score,
            analysis.compliance_score,
            analysis.support_score
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            name=provider.upper(),
            line=dict(color=colors.get(provider, '#888888'))
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=True,
        height=500,
        title="Provider Capability Comparison"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Scoring table
    st.markdown("#### Detailed Scores")
    
    score_data = []
    for provider, analysis in analyses.items():
        score_data.append({
            'Provider': provider.upper(),
            'Cost': f"{analysis.cost_score:.1f}/10",
            'Performance': f"{analysis.performance_score:.1f}/10",
            'Security': f"{analysis.security_score:.1f}/10",
            'Scalability': f"{analysis.scalability_score:.1f}/10",
            'Compliance': f"{analysis.compliance_score:.1f}/10",
            'Support': f"{analysis.support_score:.1f}/10",
            'Overall': f"{analysis.overall_score:.1f}/10"
        })
    
    df_scores = pd.DataFrame(score_data)
    st.dataframe(df_scores, use_container_width=True, hide_index=True)
    
    # Provider strengths and weaknesses
    st.markdown("#### Provider Analysis")
    
    cols = st.columns(len(analyses))
    
    for idx, (provider, analysis) in enumerate(analyses.items()):
        with cols[idx]:
            st.markdown(f"**{provider.upper()}**")
            
            with st.expander("✅ Strengths"):
                for strength in analysis.strengths:
                    st.markdown(f"• {strength}")
            
            with st.expander("⚠️ Weaknesses"):
                for weakness in analysis.weaknesses:
                    st.markdown(f"• {weakness}")
            
            with st.expander("🎯 Best For"):
                for best in analysis.best_for:
                    st.markdown(f"• {best}")


def _render_environment_breakdown(analyses: Dict[str, Any]):
    """Render environment-specific breakdown"""
    
    st.markdown("### 📈 Environment Breakdown")
    
    # Environment cost comparison
    environments = ['Development', 'Staging', 'Production']
    
    for env_name, env_key in [('Development', 'dev_cost'), ('Staging', 'staging_cost'), ('Production', 'prod_cost')]:
        st.markdown(f"#### {env_name} Environment")
        
        env_data = []
        for provider, analysis in analyses.items():
            env_cost = getattr(analysis, env_key)
            env_data.append({
                'Provider': provider.upper(),
                'Instances': env_cost.instance_count,
                'Instance Type': env_cost.instance_type,
                'Compute': f"${env_cost.compute_cost:,.2f}",
                'Storage': f"${env_cost.storage_cost:,.2f}",
                'Network': f"${env_cost.network_cost:,.2f}",
                'Additional': f"${env_cost.additional_cost:,.2f}",
                'Total': f"${env_cost.monthly_cost:,.2f}"
            })
        
        df_env = pd.DataFrame(env_data)
        st.dataframe(df_env, use_container_width=True, hide_index=True)
        
        # Cost breakdown chart
        providers_list = [d['Provider'] for d in env_data]
        compute_costs = [getattr(analyses[p.lower()], env_key).compute_cost for p in providers_list]
        storage_costs = [getattr(analyses[p.lower()], env_key).storage_cost for p in providers_list]
        network_costs = [getattr(analyses[p.lower()], env_key).network_cost for p in providers_list]
        
        fig = go.Figure(data=[
            go.Bar(name='Compute', x=providers_list, y=compute_costs),
            go.Bar(name='Storage', x=providers_list, y=storage_costs),
            go.Bar(name='Network', x=providers_list, y=network_costs)
        ])
        
        fig.update_layout(
            barmode='stack',
            title=f"{env_name} Cost Breakdown",
            xaxis_title="Provider",
            yaxis_title="Cost (USD)",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)


def _render_report_download(
    analyses: Dict[str, Any],
    recommendation: Dict[str, Any],
    requirements: Dict[str, Any],
    user_email: str
):
    """Render report download section"""
    
    st.markdown("### 📄 Download Comprehensive Report")
    
    st.info("Generate a detailed PDF report with all analysis results, comparisons, and recommendations.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Report Contents:**")
        st.markdown("""
        - Executive summary with recommendation
        - Complete cost comparison (all environments)
        - Capability scoring analysis
        - Detailed provider breakdowns
        - Strengths, weaknesses, and best-use cases
        - Assumptions and methodology
        """)
    
    with col2:
        if st.button("📥 Generate PDF Report", use_container_width=True, type="primary"):
            with st.spinner("Generating comprehensive report..."):
                try:
                    generator = ReportGenerator()
                    report_path = generator.generate_comparison_report(
                        analyses,
                        recommendation,
                        requirements,
                        user_email
                    )
                    
                    # Read the file
                    with open(report_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    st.success("✅ Report generated successfully!")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_data,
                        file_name=f"cloud_comparison_{user_email.split('@')[0]}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error generating report: {e}")
                    st.info("💡 Try installing reportlab: `pip install reportlab`")
    
    # Summary metrics
    st.markdown("---")
    st.markdown("### 📊 Quick Summary")
    
    # Find best in each category
    best_cost = min(analyses.items(), key=lambda x: x[1].total_monthly)
    best_performance = max(analyses.items(), key=lambda x: x[1].performance_score)
    best_security = max(analyses.items(), key=lambda x: x[1].security_score)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "💰 Best Cost",
            best_cost[0].upper(),
            f"${best_cost[1].total_monthly:,.2f}/mo"
        )
    
    with col2:
        st.metric(
            "⚡ Best Performance",
            best_performance[0].upper(),
            f"{best_performance[1].performance_score}/10"
        )
    
    with col3:
        st.metric(
            "🔒 Best Security",
            best_security[0].upper(),
            f"{best_security[1].security_score}/10"
        )
