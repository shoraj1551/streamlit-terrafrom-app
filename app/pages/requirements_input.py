"""
Requirements Input UI

User interface for inputting infrastructure requirements via:
1. Natural language description
2. Document upload
3. Manual structured input
"""

import streamlit as st
from pathlib import Path
import tempfile
from typing import Dict, Any, Optional

from app.services.ai_requirements_agent import AIRequirementsAgent


def render_requirements_input(user_email: str) -> Optional[Dict[str, Any]]:
    """
    Render requirements input interface
    
    Args:
        user_email: User's email
        
    Returns:
        Extracted requirements or None
    """
    st.markdown("## 📝 Describe Your Infrastructure Needs")
    st.markdown("Choose how you'd like to provide your requirements")
    
    # Initialize AI agent
    if 'ai_agent' not in st.session_state:
        st.session_state.ai_agent = AIRequirementsAgent()
    
    # Input method selection
    input_method = st.radio(
        "Input Method",
        options=[
            "💬 Natural Language Description",
            "📄 Upload Document (PDF/DOCX/TXT)",
            "⚙️ Manual Configuration"
        ],
        label_visibility="collapsed"
    )
    
    requirements = None
    
    if "Natural Language" in input_method:
        requirements = _render_natural_language_input(user_email)
    
    elif "Upload Document" in input_method:
        requirements = _render_document_upload(user_email)
    
    elif "Manual Configuration" in input_method:
        requirements = _render_manual_input(user_email)
    
    return requirements


def _render_natural_language_input(user_email: str) -> Optional[Dict[str, Any]]:
    """Render natural language input"""
    
    st.markdown("### 💬 Describe Your Infrastructure")
    st.markdown("Tell us what you're building in plain English. Our AI will extract the technical requirements.")
    
    # Get industry context if available
    industry = None
    if 'selected_industry' in st.session_state:
        industry = st.session_state.selected_industry.name
    
    # Examples
    with st.expander("💡 See Examples"):
        st.markdown("""
        **Example 1 - E-Commerce**:
        "I'm building an e-commerce platform that needs to handle 10,000 concurrent users. 
        We need auto-scaling, CDN for product images, and PCI-DSS compliance for payments. 
        Database should be highly available with automatic backups."
        
        **Example 2 - SaaS**:
        "We're launching a SaaS product for project management. Need multi-tenant architecture, 
        API rate limiting, and SOC 2 compliance. Expecting 1000 users initially, scaling to 10k."
        
        **Example 3 - AI/ML**:
        "Building a machine learning platform for image recognition. Need GPU instances, 
        large storage for training data (5TB+), and Jupyter notebook environment."
        """)
    
    # Text input
    description = st.text_area(
        "Describe your infrastructure needs:",
        placeholder="E.g., I'm building a healthcare platform that needs HIPAA compliance, handles patient records, requires high availability...",
        height=200,
        help="Be as detailed as possible. Mention: use case, expected users, compliance needs, performance requirements, etc."
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🤖 Extract Requirements with AI", use_container_width=True, type="primary"):
            if not description or len(description) < 50:
                st.error("Please provide a more detailed description (at least 50 characters)")
                return None
            
            with st.spinner("🤖 AI is analyzing your requirements... This may take 30-60 seconds"):
                try:
                    # Extract requirements
                    requirements = st.session_state.ai_agent.extract_from_natural_language(
                        description,
                        industry
                    )
                    
                    # Save requirements
                    req_id = st.session_state.ai_agent.save_requirements(
                        requirements,
                        user_email,
                        description
                    )
                    
                    st.success("✅ Requirements extracted successfully!")
                    
                    # Display extracted requirements
                    _display_requirements(requirements)
                    
                    # Store in session
                    st.session_state.requirements = requirements
                    st.session_state.requirement_id = req_id
                    st.session_state.requirement_description = description
                    
                    return requirements
                
                except Exception as e:
                    st.error(f"Error extracting requirements: {e}")
                    st.info("💡 Try simplifying your description or use the manual configuration option")
                    return None
    
    with col2:
        if st.button("Clear", use_container_width=True):
            st.rerun()
    
    return None


def _render_document_upload(user_email: str) -> Optional[Dict[str, Any]]:
    """Render document upload interface"""
    
    st.markdown("### 📄 Upload Requirements Document")
    st.markdown("Upload a PDF, DOCX, or TXT file containing your infrastructure requirements")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx', 'txt'],
        help="Supported formats: PDF, DOCX, TXT"
    )
    
    if uploaded_file:
        st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        
        if st.button("🤖 Extract Requirements from Document", use_container_width=True, type="primary"):
            with st.spinner("🤖 AI is reading and analyzing your document..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = Path(tmp_file.name)
                    
                    # Extract requirements
                    requirements = st.session_state.ai_agent.extract_from_document(tmp_path)
                    
                    # Clean up temp file
                    tmp_path.unlink()
                    
                    # Save requirements
                    req_id = st.session_state.ai_agent.save_requirements(
                        requirements,
                        user_email,
                        f"Extracted from document: {uploaded_file.name}"
                    )
                    
                    st.success("✅ Requirements extracted from document!")
                    
                    # Display
                    _display_requirements(requirements)
                    
                    # Store in session
                    st.session_state.requirements = requirements
                    st.session_state.requirement_id = req_id
                    
                    return requirements
                
                except Exception as e:
                    st.error(f"Error processing document: {e}")
                    return None
    
    return None


def _render_manual_input(user_email: str) -> Optional[Dict[str, Any]]:
    """Render manual configuration interface"""
    
    st.markdown("### ⚙️ Manual Configuration")
    st.markdown("Specify your infrastructure requirements manually")
    
    with st.form("manual_requirements"):
        # Compute
        st.markdown("#### 💻 Compute")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpu_cores = st.number_input("CPU Cores", min_value=1, max_value=128, value=4)
        with col2:
            ram_gb = st.number_input("RAM (GB)", min_value=1, max_value=1024, value=16)
        with col3:
            gpu_required = st.checkbox("GPU Required")
        
        # Storage
        st.markdown("#### 💾 Storage")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            storage_type = st.selectbox("Storage Type", options=["ssd", "hdd"])
        with col2:
            storage_size = st.number_input("Size (GB)", min_value=10, max_value=10000, value=500)
        with col3:
            iops = st.number_input("IOPS", min_value=100, max_value=50000, value=3000)
        
        # Network
        st.markdown("#### 🌐 Network")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            bandwidth = st.number_input("Bandwidth (Gbps)", min_value=1, max_value=100, value=1)
        with col2:
            static_ip = st.checkbox("Static IP", value=True)
        with col3:
            load_balancer = st.checkbox("Load Balancer")
        
        # Security
        st.markdown("#### 🔒 Security")
        col1, col2 = st.columns(2)
        
        with col1:
            encryption = st.checkbox("Encryption", value=True)
            firewall = st.checkbox("Firewall", value=True)
        with col2:
            ddos_protection = st.checkbox("DDoS Protection")
            compliance = st.multiselect(
                "Compliance Standards",
                options=["HIPAA", "PCI-DSS", "SOC 2", "GDPR", "ISO 27001", "HITECH"]
            )
        
        # Availability
        st.markdown("#### 🎯 Availability")
        col1, col2 = st.columns(2)
        
        with col1:
            uptime_sla = st.selectbox("Uptime SLA", options=[99.0, 99.5, 99.9, 99.95, 99.99], index=2)
        with col2:
            multi_region = st.checkbox("Multi-Region Deployment")
        
        # Scaling
        st.markdown("#### 📈 Scaling")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_instances = st.number_input("Min Instances", min_value=1, max_value=100, value=1)
        with col2:
            max_instances = st.number_input("Max Instances", min_value=1, max_value=100, value=3)
        with col3:
            auto_scaling = st.checkbox("Auto-Scaling")
        
        # Submit
        submitted = st.form_submit_button("Save Configuration", use_container_width=True, type="primary")
        
        if submitted:
            requirements = {
                "compute": {
                    "cpu_cores": cpu_cores,
                    "ram_gb": ram_gb,
                    "gpu_required": gpu_required
                },
                "storage": {
                    "type": storage_type,
                    "size_gb": storage_size,
                    "iops": iops
                },
                "network": {
                    "bandwidth_gbps": bandwidth,
                    "static_ip": static_ip,
                    "load_balancer": load_balancer
                },
                "security": {
                    "encryption": encryption,
                    "firewall": firewall,
                    "ddos_protection": ddos_protection,
                    "compliance": compliance
                },
                "availability": {
                    "uptime_sla": uptime_sla,
                    "multi_region": multi_region
                },
                "scaling": {
                    "min_instances": min_instances,
                    "max_instances": max_instances,
                    "auto_scaling": auto_scaling
                }
            }
            
            # Save
            req_id = st.session_state.ai_agent.save_requirements(
                requirements,
                user_email,
                "Manual configuration"
            )
            
            st.success("✅ Configuration saved!")
            
            # Display
            _display_requirements(requirements)
            
            # Store in session
            st.session_state.requirements = requirements
            st.session_state.requirement_id = req_id
            
            return requirements
    
    return None


def _display_requirements(requirements: Dict[str, Any]):
    """Display extracted requirements in a nice format"""
    
    st.markdown("### 📋 Extracted Requirements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💻 Compute**")
        st.write(f"- CPU: {requirements['compute']['cpu_cores']} cores")
        st.write(f"- RAM: {requirements['compute']['ram_gb']} GB")
        st.write(f"- GPU: {'✅ Required' if requirements['compute']['gpu_required'] else '❌ Not required'}")
        
        st.markdown("**💾 Storage**")
        st.write(f"- Type: {requirements['storage']['type'].upper()}")
        st.write(f"- Size: {requirements['storage']['size_gb']} GB")
        st.write(f"- IOPS: {requirements['storage']['iops']}")
        
        st.markdown("**🌐 Network**")
        st.write(f"- Bandwidth: {requirements['network']['bandwidth_gbps']} Gbps")
        st.write(f"- Static IP: {'✅' if requirements['network']['static_ip'] else '❌'}")
        st.write(f"- Load Balancer: {'✅' if requirements['network']['load_balancer'] else '❌'}")
    
    with col2:
        st.markdown("**🔒 Security**")
        st.write(f"- Encryption: {'✅' if requirements['security']['encryption'] else '❌'}")
        st.write(f"- Firewall: {'✅' if requirements['security']['firewall'] else '❌'}")
        st.write(f"- DDoS Protection: {'✅' if requirements['security']['ddos_protection'] else '❌'}")
        if requirements['security']['compliance']:
            st.write(f"- Compliance: {', '.join(requirements['security']['compliance'])}")
        
        st.markdown("**🎯 Availability**")
        st.write(f"- Uptime SLA: {requirements['availability']['uptime_sla']}%")
        st.write(f"- Multi-Region: {'✅' if requirements['availability']['multi_region'] else '❌'}")
        
        st.markdown("**📈 Scaling**")
        st.write(f"- Instances: {requirements['scaling']['min_instances']}-{requirements['scaling']['max_instances']}")
        st.write(f"- Auto-Scaling: {'✅' if requirements['scaling']['auto_scaling'] else '❌'}")
