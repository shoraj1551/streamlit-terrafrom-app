"""
Compliance Reporting

Generates compliance reports for various security standards and regulations.

Supports:
- SOC 2 Type II
- ISO 27001
- GDPR
- HIPAA (basic)
- Custom compliance frameworks

Features:
- Automated report generation
- Evidence collection
- Control mapping
- Audit trail analysis
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from app.services.audit_logger import AuditLogger, AuditEventType, AuditSeverity
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks"""
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    CUSTOM = "custom"


@dataclass
class ComplianceControl:
    """Compliance control definition"""
    control_id: str
    framework: ComplianceFramework
    name: str
    description: str
    category: str
    required_evidence: List[str]
    automated_check: Optional[str] = None


@dataclass
class ComplianceReport:
    """Compliance report"""
    report_id: str
    framework: ComplianceFramework
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_controls: int
    compliant_controls: int
    non_compliant_controls: int
    compliance_percentage: float
    findings: List[Dict[str, Any]]
    recommendations: List[str]


class ComplianceReporter:
    """
    Compliance reporting system
    
    Generates compliance reports based on audit logs and system configuration.
    """
    
    # SOC 2 Trust Service Criteria controls
    SOC2_CONTROLS = [
        ComplianceControl(
            control_id="CC6.1",
            framework=ComplianceFramework.SOC2,
            name="Logical Access - Authentication",
            description="System requires authentication for access",
            category="Security",
            required_evidence=["auth.login", "auth.logout"],
        ),
        ComplianceControl(
            control_id="CC6.2",
            framework=ComplianceFramework.SOC2,
            name="Logical Access - Authorization",
            description="System enforces authorization controls",
            category="Security",
            required_evidence=["security.unauthorized"],
        ),
        ComplianceControl(
            control_id="CC6.6",
            framework=ComplianceFramework.SOC2,
            name="Logical Access - Audit Logging",
            description="System logs security-relevant events",
            category="Security",
            required_evidence=["auth.login", "deploy.create", "user.role_change"],
        ),
        ComplianceControl(
            control_id="CC7.2",
            framework=ComplianceFramework.SOC2,
            name="System Monitoring - Security Events",
            description="System monitors and responds to security events",
            category="Monitoring",
            required_evidence=["security.rate_limit", "security.csrf_fail"],
        ),
    ]
    
    # ISO 27001 controls
    ISO27001_CONTROLS = [
        ComplianceControl(
            control_id="A.9.2.1",
            framework=ComplianceFramework.ISO27001,
            name="User Registration and De-registration",
            description="User access is properly managed",
            category="Access Control",
            required_evidence=["user.create", "user.delete"],
        ),
        ComplianceControl(
            control_id="A.9.4.1",
            framework=ComplianceFramework.ISO27001,
            name="Information Access Restriction",
            description="Access to information is restricted",
            category="Access Control",
            required_evidence=["security.unauthorized"],
        ),
        ComplianceControl(
            control_id="A.12.4.1",
            framework=ComplianceFramework.ISO27001,
            name="Event Logging",
            description="Event logs are recorded and retained",
            category="Operations Security",
            required_evidence=["auth.login", "deploy.create"],
        ),
    ]
    
    # GDPR requirements
    GDPR_CONTROLS = [
        ComplianceControl(
            control_id="Art.32",
            framework=ComplianceFramework.GDPR,
            name="Security of Processing",
            description="Appropriate security measures implemented",
            category="Security",
            required_evidence=["auth.login", "security.rate_limit"],
        ),
        ComplianceControl(
            control_id="Art.33",
            framework=ComplianceFramework.GDPR,
            name="Breach Notification",
            description="Security breaches are logged and can be reported",
            category="Incident Response",
            required_evidence=["security.csrf_fail", "security.unauthorized"],
        ),
    ]
    
    def __init__(self, audit_logger: AuditLogger):
        """
        Initialize compliance reporter
        
        Args:
            audit_logger: AuditLogger instance
        """
        self.audit_logger = audit_logger
        
        # Map frameworks to controls
        self.framework_controls = {
            ComplianceFramework.SOC2: self.SOC2_CONTROLS,
            ComplianceFramework.ISO27001: self.ISO27001_CONTROLS,
            ComplianceFramework.GDPR: self.GDPR_CONTROLS,
        }
        
        logger.info("Initialized ComplianceReporter")
    
    def generate_report(
        self,
        framework: ComplianceFramework,
        period_days: int = 30,
    ) -> ComplianceReport:
        """
        Generate compliance report for specified framework
        
        Args:
            framework: Compliance framework
            period_days: Reporting period in days
            
        Returns:
            ComplianceReport object
        """
        import secrets
        
        # Calculate period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Get controls for framework
        controls = self.framework_controls.get(framework, [])
        
        # Check each control
        findings = []
        compliant_count = 0
        
        for control in controls:
            is_compliant, evidence = self._check_control(control, start_date, end_date)
            
            if is_compliant:
                compliant_count += 1
            
            findings.append({
                "control_id": control.control_id,
                "control_name": control.name,
                "category": control.category,
                "compliant": is_compliant,
                "evidence_count": len(evidence),
                "evidence_sample": evidence[:5] if evidence else [],
            })
        
        # Calculate compliance percentage
        total_controls = len(controls)
        compliance_percentage = (compliant_count / total_controls * 100) if total_controls > 0 else 0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(findings)
        
        # Create report
        report = ComplianceReport(
            report_id=f"rpt_{secrets.token_hex(8)}",
            framework=framework,
            generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            total_controls=total_controls,
            compliant_controls=compliant_count,
            non_compliant_controls=total_controls - compliant_count,
            compliance_percentage=compliance_percentage,
            findings=findings,
            recommendations=recommendations,
        )
        
        logger.info(f"Generated {framework.value} compliance report: {compliance_percentage:.1f}% compliant")
        
        return report
    
    def _check_control(
        self,
        control: ComplianceControl,
        start_date: datetime,
        end_date: datetime,
    ) -> tuple[bool, List[str]]:
        """
        Check if control is compliant
        
        Returns:
            Tuple of (is_compliant, evidence_list)
        """
        evidence = []
        
        # Check for required evidence in audit logs
        for event_type_str in control.required_evidence:
            try:
                event_type = AuditEventType(event_type_str)
                count = self.audit_logger.get_event_count(
                    event_type=event_type,
                    start_date=start_date,
                    end_date=end_date,
                )
                
                if count > 0:
                    evidence.append(f"{event_type_str}: {count} events")
            except ValueError:
                # Event type not found
                pass
        
        # Control is compliant if we have evidence for all required event types
        is_compliant = len(evidence) >= len(control.required_evidence)
        
        return is_compliant, evidence
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []
        
        # Check for non-compliant controls
        non_compliant = [f for f in findings if not f["compliant"]]
        
        if non_compliant:
            recommendations.append(
                f"Address {len(non_compliant)} non-compliant controls to improve compliance posture"
            )
        
        # Check for low evidence counts
        low_evidence = [f for f in findings if f["evidence_count"] < 10]
        
        if low_evidence:
            recommendations.append(
                f"Increase activity for {len(low_evidence)} controls with low evidence counts"
            )
        
        # General recommendations
        recommendations.append("Continue monitoring audit logs for compliance evidence")
        recommendations.append("Review and update security policies regularly")
        recommendations.append("Conduct periodic security training for users")
        
        return recommendations
    
    def export_report_markdown(self, report: ComplianceReport) -> str:
        """
        Export report as Markdown
        
        Args:
            report: ComplianceReport object
            
        Returns:
            Markdown formatted report
        """
        md = f"""# Compliance Report - {report.framework.value.upper()}

**Report ID**: {report.report_id}  
**Generated**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Period**: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}

## Summary

- **Total Controls**: {report.total_controls}
- **Compliant**: {report.compliant_controls} ✅
- **Non-Compliant**: {report.non_compliant_controls} ❌
- **Compliance Rate**: {report.compliance_percentage:.1f}%

## Findings

| Control ID | Control Name | Category | Status | Evidence |
|------------|--------------|----------|--------|----------|
"""
        
        for finding in report.findings:
            status = "✅ Compliant" if finding["compliant"] else "❌ Non-Compliant"
            md += f"| {finding['control_id']} | {finding['control_name']} | {finding['category']} | {status} | {finding['evidence_count']} events |\n"
        
        md += "\n## Recommendations\n\n"
        for i, rec in enumerate(report.recommendations, 1):
            md += f"{i}. {rec}\n"
        
        return md
    
    def export_report_json(self, report: ComplianceReport) -> Dict[str, Any]:
        """Export report as JSON"""
        return {
            "report_id": report.report_id,
            "framework": report.framework.value,
            "generated_at": report.generated_at.isoformat(),
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "summary": {
                "total_controls": report.total_controls,
                "compliant_controls": report.compliant_controls,
                "non_compliant_controls": report.non_compliant_controls,
                "compliance_percentage": report.compliance_percentage,
            },
            "findings": report.findings,
            "recommendations": report.recommendations,
        }
