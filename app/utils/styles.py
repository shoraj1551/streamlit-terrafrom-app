"""
Professional Styling System for Streamlit Terraform Platform
Enterprise-grade design inspired by GitHub, Stripe, and Linear
"""

import streamlit as st


class DesignSystem:
    """Centralized design system for consistent UI/UX"""
    
    # Color Palette - Professional and accessible
    COLORS = {
        # Primary
        'primary': '#0366d6',
        'primary_hover': '#0256c7',
        'primary_light': '#e6f2ff',
        
        # Neutrals
        'text_primary': '#24292e',
        'text_secondary': '#586069',
        'text_tertiary': '#6a737d',
        'border': '#e1e4e8',
        'background': '#ffffff',
        'background_secondary': '#f6f8fa',
        
        # Status colors
        'success': '#28a745',
        'success_bg': '#dcfce7',
        'success_text': '#166534',
        
        'warning': '#ffd33d',
        'warning_bg': '#fef3c7',
        'warning_text': '#92400e',
        
        'error': '#d73a49',
        'error_bg': '#fee',
        'error_text': '#991b1b',
        
        'info': '#0366d6',
        'info_bg': '#dbeafe',
        'info_text': '#1e40af',
    }
    
    # Typography Scale
    TYPOGRAPHY = {
        'h1': '2rem',      # 32px
        'h2': '1.5rem',    # 24px
        'h3': '1.25rem',   # 20px
        'h4': '1rem',      # 16px
        'body': '0.875rem', # 14px
        'small': '0.75rem', # 12px
    }
    
    # Spacing Scale (4px grid)
    SPACING = {
        'xs': '0.25rem',   # 4px
        'sm': '0.5rem',    # 8px
        'md': '1rem',      # 16px
        'lg': '1.5rem',    # 24px
        'xl': '2rem',      # 32px
        'xxl': '3rem',     # 48px
    }
    
    @staticmethod
    def inject_custom_css():
        """Inject professional CSS into Streamlit app"""
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            /* Global Styles */
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }
            
            .stApp {
                background: #ffffff;
            }
            
            /* Remove default Streamlit padding for full control */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 100%;
            }
            
            /* Typography */
            h1 {
                font-size: 2rem;
                font-weight: 700;
                color: #24292e;
                margin-bottom: 1rem;
                line-height: 1.2;
            }
            
            h2 {
                font-size: 1.5rem;
                font-weight: 600;
                color: #24292e;
                margin-bottom: 0.75rem;
                line-height: 1.3;
            }
            
            h3 {
                font-size: 1.25rem;
                font-weight: 600;
                color: #24292e;
                margin-bottom: 0.5rem;
                line-height: 1.4;
            }
            
            p, .stMarkdown {
                color: #586069;
                font-size: 0.875rem;
                line-height: 1.6;
            }
            
            /* Buttons */
            .stButton>button {
                background: #0366d6;
                color: #ffffff;
                border: 1px solid #0366d6;
                border-radius: 6px;
                padding: 0.5rem 1rem;
                font-size: 0.875rem;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            
            .stButton>button:hover {
                background: #0256c7;
                border-color: #0256c7;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            }
            
            /* Metrics - Fix truncation */
            [data-testid="stMetricValue"] {
                font-size: 1.75rem !important;
                font-weight: 700 !important;
                color: #24292e !important;
                white-space: nowrap !important;
                overflow: visible !important;
            }
            
            [data-testid="stMetricLabel"] {
                font-size: 0.875rem !important;
                font-weight: 500 !important;
                color: #586069 !important;
                white-space: nowrap !important;
                overflow: visible !important;
                text-overflow: clip !important;
            }
            
            [data-testid="stMetricDelta"] {
                font-size: 0.75rem !important;
            }
            
            /* Fix column widths to prevent truncation */
            [data-testid="column"] {
                min-width: 200px !important;
                flex: 1 1 auto !important;
            }
            
            /* Ensure metric containers don't constrain content */
            [data-testid="metric-container"] {
                width: 100% !important;
                min-width: fit-content !important;
            }
            
            /* Cards */
            .card {
                background: #ffffff;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            }
            
            /* Forms */
            .stTextInput>div>div>input,
            .stSelectbox>div>div>select,
            .stTextArea>div>div>textarea {
                border: 1px solid #e1e4e8;
                border-radius: 6px;
                font-size: 0.875rem;
                background: #ffffff;
                padding: 0.5rem 0.75rem;
            }
            
            .stTextInput>div>div>input:focus,
            .stSelectbox>div>div>select:focus,
            .stTextArea>div>div>textarea:focus {
                border-color: #0366d6;
                box-shadow: 0 0 0 3px rgba(3, 102, 214, 0.1);
                outline: none;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2rem;
                border-bottom: 1px solid #e1e4e8;
            }
            
            .stTabs [data-baseweb="tab"] {
                font-size: 0.875rem;
                font-weight: 500;
                color: #586069;
                padding: 0.75rem 0;
                border-bottom: 2px solid transparent;
            }
            
            .stTabs [aria-selected="true"] {
                color: #24292e;
                border-bottom-color: #0366d6;
            }
            
            /* Sidebar */
            [data-testid="stSidebar"] {
                background: #f6f8fa;
                border-right: 1px solid #e1e4e8;
            }
            
            [data-testid="stSidebar"] .stRadio > label {
                font-size: 0.875rem;
                font-weight: 500;
                color: #24292e;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                transition: background 0.2s ease;
            }
            
            [data-testid="stSidebar"] .stRadio > label:hover {
                background: #e1e4e8;
            }
            
            /* Status Badges */
            .status-badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 500;
            }
            
            .status-success {
                background: #dcfce7;
                color: #166534;
            }
            
            .status-warning {
                background: #fef3c7;
                color: #92400e;
            }
            
            .status-error {
                background: #fee;
                color: #991b1b;
            }
            
            .status-info {
                background: #dbeafe;
                color: #1e40af;
            }
            
            /* Alerts */
            .stSuccess {
                background: #dcfce7;
                border-left: 3px solid #28a745;
                padding: 1rem;
                border-radius: 6px;
            }
            
            .stWarning {
                background: #fef3c7;
                border-left: 3px solid #ffd33d;
                padding: 1rem;
                border-radius: 6px;
            }
            
            .stError {
                background: #fee;
                border-left: 3px solid #d73a49;
                padding: 1rem;
                border-radius: 6px;
            }
            
            .stInfo {
                background: #dbeafe;
                border-left: 3px solid #0366d6;
                padding: 1rem;
                border-radius: 6px;
            }
            
            /* Dataframes */
            .stDataFrame {
                border: 1px solid #e1e4e8;
                border-radius: 6px;
                overflow: hidden;
            }
            
            /* Fix column widths to prevent truncation */
            .element-container {
                width: 100% !important;
            }
            
            /* Ensure proper grid layout */
            [data-testid="column"] {
                padding: 0 0.5rem;
            }
            
            /* Remove excessive emoji spacing */
            .emoji {
                margin-right: 0.5rem;
            }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def status_badge(text: str, status: str = 'info') -> str:
        """Create a status badge"""
        return f'<span class="status-badge status-{status}">{text}</span>'
    
    @staticmethod
    def card(content: str, title: str = None) -> str:
        """Create a card component"""
        title_html = f'<h3>{title}</h3>' if title else ''
        return f'<div class="card">{title_html}{content}</div>'
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency properly to avoid truncation"""
        return f"${amount:,.2f}"
    
    @staticmethod
    def format_number(number: int) -> str:
        """Format large numbers with commas"""
        return f"{number:,}"


def apply_professional_theme():
    """Apply the professional theme to the Streamlit app"""
    DesignSystem.inject_custom_css()
