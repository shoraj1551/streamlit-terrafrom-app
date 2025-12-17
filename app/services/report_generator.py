"""
Report Generator

Generates downloadable PDF reports for cloud provider analysis.
"""

from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
import io

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("ReportLab not installed. PDF generation will be limited.")


class ReportGenerator:
    """Generate PDF reports for cloud analysis"""
    
    def __init__(self):
        self.reports_dir = Path("data/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_comparison_report(
        self,
        analyses: Dict[str, Any],
        recommendation: Dict[str, Any],
        requirements: Dict[str, Any],
        user_email: str
    ) -> str:
        """
        Generate comprehensive comparison report
        
        Returns:
            Path to generated PDF
        """
        if not REPORTLAB_AVAILABLE:
            return self._generate_text_report(analyses, recommendation, requirements, user_email)
        
        # Create PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cloud_comparison_{timestamp}.pdf"
        filepath = self.reports_dir / filename
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        elements.append(Paragraph("Multi-Cloud Infrastructure Analysis Report", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Metadata
        meta_data = [
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['User:', user_email],
            ['Providers Analyzed:', 'AWS, Azure, GCP']
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        elements.append(Paragraph("Executive Summary", heading_style))
        
        primary = recommendation['primary_provider'].upper()
        primary_analysis = recommendation['primary_analysis']
        
        summary_text = f"""
        Based on your requirements and priorities, we recommend <b>{primary}</b> as your primary cloud provider.
        <br/><br/>
        <b>Total Monthly Cost:</b> ${primary_analysis.total_monthly:,.2f}<br/>
        <b>Total Yearly Cost:</b> ${primary_analysis.total_yearly:,.2f}<br/>
        <b>3-Year TCO:</b> ${primary_analysis.three_year_tco:,.2f}<br/>
        <b>Overall Score:</b> {primary_analysis.overall_score}/10<br/>
        <b>Confidence:</b> {recommendation['confidence'].title()}<br/>
        <br/>
        <b>Reasoning:</b> {recommendation['reasoning']}
        """
        
        elements.append(Paragraph(summary_text, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Cost Comparison Table
        elements.append(Paragraph("Cost Comparison", heading_style))
        
        cost_data = [
            ['Provider', 'Dev', 'Staging', 'Production', 'Total Monthly', '3-Year TCO'],
        ]
        
        for provider, analysis in analyses.items():
            cost_data.append([
                provider.upper(),
                f"${analysis.dev_cost.monthly_cost:,.2f}",
                f"${analysis.staging_cost.monthly_cost:,.2f}",
                f"${analysis.prod_cost.monthly_cost:,.2f}",
                f"${analysis.total_monthly:,.2f}",
                f"${analysis.three_year_tco:,.2f}"
            ])
        
        cost_table = Table(cost_data, colWidths=[1*inch, 1*inch, 1*inch, 1.2*inch, 1.3*inch, 1.3*inch])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(cost_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Scoring Comparison
        elements.append(Paragraph("Capability Scores", heading_style))
        
        score_data = [
            ['Provider', 'Cost', 'Performance', 'Security', 'Scalability', 'Overall'],
        ]
        
        for provider, analysis in analyses.items():
            score_data.append([
                provider.upper(),
                f"{analysis.cost_score:.1f}/10",
                f"{analysis.performance_score:.1f}/10",
                f"{analysis.security_score:.1f}/10",
                f"{analysis.scalability_score:.1f}/10",
                f"{analysis.overall_score:.1f}/10"
            ])
        
        score_table = Table(score_data, colWidths=[1.2*inch, 1*inch, 1.2*inch, 1*inch, 1.2*inch, 1*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(score_table)
        elements.append(PageBreak())
        
        # Detailed Analysis for Each Provider
        for provider, analysis in analyses.items():
            elements.append(Paragraph(f"{provider.upper()} - Detailed Analysis", heading_style))
            
            # Strengths
            strengths_text = "<b>Strengths:</b><br/>" + "<br/>".join([f"• {s}" for s in analysis.strengths])
            elements.append(Paragraph(strengths_text, styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
            
            # Weaknesses
            weaknesses_text = "<b>Weaknesses:</b><br/>" + "<br/>".join([f"• {w}" for w in analysis.weaknesses])
            elements.append(Paragraph(weaknesses_text, styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
            
            # Best For
            best_for_text = "<b>Best For:</b><br/>" + "<br/>".join([f"• {b}" for b in analysis.best_for])
            elements.append(Paragraph(best_for_text, styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Environment Breakdown
            env_data = [
                ['Environment', 'Instances', 'Instance Type', 'Monthly Cost'],
                ['Development', str(analysis.dev_cost.instance_count), analysis.dev_cost.instance_type, f"${analysis.dev_cost.monthly_cost:,.2f}"],
                ['Staging', str(analysis.staging_cost.instance_count), analysis.staging_cost.instance_type, f"${analysis.staging_cost.monthly_cost:,.2f}"],
                ['Production', str(analysis.prod_cost.instance_count), analysis.prod_cost.instance_type, f"${analysis.prod_cost.monthly_cost:,.2f}"],
            ]
            
            env_table = Table(env_data, colWidths=[1.5*inch, 1.2*inch, 1.8*inch, 1.5*inch])
            env_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(env_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Assumptions
        elements.append(PageBreak())
        elements.append(Paragraph("Assumptions & Methodology", heading_style))
        
        assumptions_text = """
        <b>Cost Calculations:</b><br/>
        • Pricing based on on-demand rates as of December 2024<br/>
        • 3-year TCO includes 10% discount for reserved instances<br/>
        • Network costs estimated based on typical usage patterns<br/>
        • Storage costs calculated per GB per month<br/>
        <br/>
        <b>Environment Sizing:</b><br/>
        • Development: 1 instance at 50% of production size<br/>
        • Staging: Minimum instances at 75% of production size<br/>
        • Production: Maximum instances at full size with auto-scaling<br/>
        <br/>
        <b>Scoring Methodology:</b><br/>
        • Scores weighted based on your stated priorities<br/>
        • Provider capabilities rated on industry benchmarks<br/>
        • Cost score inversely proportional to total cost<br/>
        • Overall score is priority-weighted average<br/>
        """
        
        elements.append(Paragraph(assumptions_text, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        return str(filepath)
    
    def _generate_text_report(
        self,
        analyses: Dict[str, Any],
        recommendation: Dict[str, Any],
        requirements: Dict[str, Any],
        user_email: str
    ) -> str:
        """Generate simple text report if ReportLab not available"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cloud_comparison_{timestamp}.txt"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("MULTI-CLOUD INFRASTRUCTURE ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"User: {user_email}\n\n")
            
            f.write("RECOMMENDATION\n")
            f.write("-" * 80 + "\n")
            primary = recommendation['primary_provider'].upper()
            f.write(f"Primary Provider: {primary}\n")
            f.write(f"Reasoning: {recommendation['reasoning']}\n\n")
            
            f.write("COST COMPARISON\n")
            f.write("-" * 80 + "\n")
            for provider, analysis in analyses.items():
                f.write(f"\n{provider.upper()}:\n")
                f.write(f"  Total Monthly: ${analysis.total_monthly:,.2f}\n")
                f.write(f"  Total Yearly: ${analysis.total_yearly:,.2f}\n")
                f.write(f"  3-Year TCO: ${analysis.three_year_tco:,.2f}\n")
                f.write(f"  Overall Score: {analysis.overall_score}/10\n")
        
        return str(filepath)
