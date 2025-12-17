"""
Security Dashboard

Provides real-time security metrics and monitoring dashboard.

Features:
- Security metrics visualization
- Audit log analysis
- Threat detection
- Compliance status
- User activity monitoring
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.services.audit_logger import AuditLogger, AuditEventType, AuditSeverity, get_audit_logger
from app.services.compliance_reporter import ComplianceReporter, ComplianceFramework
from app.middleware.auth_middleware import get_current_user, require_role
from app.auth.auth_provider import UserRole
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SecurityDashboard:
    """
    Security dashboard for monitoring and analytics
    
    Provides real-time security insights and compliance status.
    """
    
    def __init__(self, audit_logger: AuditLogger):
        """
        Initialize security dashboard
        
        Args:
            audit_logger: AuditLogger instance
        """
        self.audit_logger = audit_logger
        self.compliance_reporter = ComplianceReporter(audit_logger)
    
    def get_security_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get security metrics for specified period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary of security metrics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get event counts by type
        total_events = self.audit_logger.get_event_count(
            start_date=start_date,
            end_date=end_date,
        )
        
        # Authentication metrics
        login_success = self.audit_logger.get_event_count(
            event_type=AuditEventType.AUTH_LOGIN,
            start_date=start_date,
            end_date=end_date,
        )
        
        login_failed = self.audit_logger.get_event_count(
            event_type=AuditEventType.AUTH_LOGIN_FAILED,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Deployment metrics
        deployments = self.audit_logger.get_event_count(
            event_type=AuditEventType.DEPLOY_CREATE,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Security events
        rate_limit_hits = self.audit_logger.get_event_count(
            event_type=AuditEventType.SECURITY_RATE_LIMIT,
            start_date=start_date,
            end_date=end_date,
        )
        
        csrf_failures = self.audit_logger.get_event_count(
            event_type=AuditEventType.SECURITY_CSRF_FAIL,
            start_date=start_date,
            end_date=end_date,
        )
        
        unauthorized_attempts = self.audit_logger.get_event_count(
            event_type=AuditEventType.SECURITY_UNAUTHORIZED,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Critical/Error events
        critical_events = self.audit_logger.query_events(
            severity=AuditSeverity.CRITICAL,
            start_date=start_date,
            end_date=end_date,
            limit=10,
        )
        
        error_events = self.audit_logger.query_events(
            severity=AuditSeverity.ERROR,
            start_date=start_date,
            end_date=end_date,
            limit=10,
        )
        
        return {
            "period_days": days,
            "total_events": total_events,
            "authentication": {
                "login_success": login_success,
                "login_failed": login_failed,
                "success_rate": (login_success / (login_success + login_failed) * 100) if (login_success + login_failed) > 0 else 0,
            },
            "deployments": {
                "total": deployments,
                "per_day": deployments / days if days > 0 else 0,
            },
            "security_events": {
                "rate_limit_hits": rate_limit_hits,
                "csrf_failures": csrf_failures,
                "unauthorized_attempts": unauthorized_attempts,
                "total": rate_limit_hits + csrf_failures + unauthorized_attempts,
            },
            "critical_events": len(critical_events),
            "error_events": len(error_events),
        }
    
    def render_dashboard(self):
        """Render security dashboard in Streamlit"""
        st.title("🔒 Security Dashboard")
        
        # Check permissions
        user = get_current_user()
        if not user or user.role not in [UserRole.ADMIN]:
            st.error("⛔ Access Denied: Admin role required")
            return
        
        # Time period selector
        period = st.selectbox(
            "Time Period",
            options=[7, 14, 30, 90],
            format_func=lambda x: f"Last {x} days",
        )
        
        # Get metrics
        metrics = self.get_security_metrics(days=period)
        
        # Display metrics
        st.markdown("## 📊 Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Events", metrics["total_events"])
        
        with col2:
            st.metric(
                "Login Success Rate",
                f"{metrics['authentication']['success_rate']:.1f}%",
            )
        
        with col3:
            st.metric("Deployments", metrics["deployments"]["total"])
        
        with col4:
            security_total = metrics["security_events"]["total"]
            st.metric(
                "Security Events",
                security_total,
                delta=f"⚠️" if security_total > 10 else None,
            )
        
        # Authentication section
        st.markdown("## 🔐 Authentication")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Successful Logins", metrics["authentication"]["login_success"])
        
        with col2:
            st.metric("Failed Logins", metrics["authentication"]["login_failed"])
        
        # Security events section
        st.markdown("## 🛡️ Security Events")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Rate Limit Hits", metrics["security_events"]["rate_limit_hits"])
        
        with col2:
            st.metric("CSRF Failures", metrics["security_events"]["csrf_failures"])
        
        with col3:
            st.metric("Unauthorized Attempts", metrics["security_events"]["unauthorized_attempts"])
        
        # Critical events
        if metrics["critical_events"] > 0:
            st.markdown("## 🚨 Critical Events")
            st.error(f"⚠️ {metrics['critical_events']} critical events in the last {period} days")
            
            # Show recent critical events
            critical_events = self.audit_logger.query_events(
                severity=AuditSeverity.CRITICAL,
                start_date=datetime.now() - timedelta(days=period),
                limit=5,
            )
            
            for event in critical_events:
                with st.expander(f"{event.event_type.value} - {event.timestamp.strftime('%Y-%m-%d %H:%M')}"):
                    st.write(f"**User**: {event.user_email or 'N/A'}")
                    st.write(f"**Status**: {event.status or 'N/A'}")
                    if event.error_message:
                        st.write(f"**Error**: {event.error_message}")
        
        # Compliance section
        st.markdown("## 📋 Compliance Status")
        
        framework = st.selectbox(
            "Framework",
            options=[ComplianceFramework.SOC2, ComplianceFramework.ISO27001, ComplianceFramework.GDPR],
            format_func=lambda x: x.value.upper(),
        )
        
        if st.button("Generate Compliance Report"):
            with st.spinner("Generating report..."):
                report = self.compliance_reporter.generate_report(framework, period_days=period)
                
                # Display compliance percentage
                st.metric(
                    "Compliance Rate",
                    f"{report.compliance_percentage:.1f}%",
                    delta=f"{'✅' if report.compliance_percentage >= 80 else '⚠️'}",
                )
                
                # Display findings
                st.markdown("### Findings")
                
                for finding in report.findings:
                    status_icon = "✅" if finding["compliant"] else "❌"
                    with st.expander(f"{status_icon} {finding['control_id']}: {finding['control_name']}"):
                        st.write(f"**Category**: {finding['category']}")
                        st.write(f"**Evidence**: {finding['evidence_count']} events")
                        
                        if finding["evidence_sample"]:
                            st.write("**Sample Evidence**:")
                            for evidence in finding["evidence_sample"]:
                                st.write(f"- {evidence}")
                
                # Display recommendations
                st.markdown("### Recommendations")
                for i, rec in enumerate(report.recommendations, 1):
                    st.write(f"{i}. {rec}")
                
                # Download report
                report_md = self.compliance_reporter.export_report_markdown(report)
                st.download_button(
                    label="Download Report (Markdown)",
                    data=report_md,
                    file_name=f"compliance_report_{framework.value}_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                )
        
        # Recent activity
        st.markdown("## 📝 Recent Activity")
        
        recent_events = self.audit_logger.query_events(
            start_date=datetime.now() - timedelta(days=1),
            limit=20,
        )
        
        if recent_events:
            for event in recent_events:
                severity_icon = {
                    AuditSeverity.CRITICAL: "🚨",
                    AuditSeverity.ERROR: "❌",
                    AuditSeverity.WARNING: "⚠️",
                    AuditSeverity.INFO: "ℹ️",
                    AuditSeverity.DEBUG: "🔍",
                }.get(event.severity, "ℹ️")
                
                st.text(f"{severity_icon} {event.timestamp.strftime('%H:%M:%S')} - {event.event_type.value} - {event.user_email or 'System'}")
        else:
            st.info("No recent activity")


def show_security_dashboard():
    """Show security dashboard (convenience function)"""
    audit_logger = get_audit_logger()
    dashboard = SecurityDashboard(audit_logger)
    dashboard.render_dashboard()
