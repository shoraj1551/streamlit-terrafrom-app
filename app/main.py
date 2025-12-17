import streamlit as st
import sys
import os
import asyncio
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_parser import ConfigParser
from app.utils.logger import setup_logger
from app.services.terraform_executor import TerraformExecutor, DeploymentStatus
from app.services.terraform_generator import TerraformGenerator
from app.services.cost_estimator import AWSCostEstimator
from app.services.deployment_db import DeploymentDatabase
from app.__version__ import __version__, __app_name__

logger = setup_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Terraform Cloud Deployer",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional UI with animations
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Animated Gradient Background */
    .stApp {
        background: linear-gradient(-45deg, #0f172a, #1e293b, #334155, #1e293b);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Hero Section */
    .hero-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
        animation: fadeInDown 0.8s ease-out;
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        color: white;
        margin: 0;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.9);
        margin-top: 0.5rem;
    }
    
    .version-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        color: white;
        margin-top: 1rem;
        backdrop-filter: blur(10px);
    }
    
    /* Card Styles with Glassmorphism */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        animation: fadeIn 0.6s ease-out;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.7;
        }
    }
    
    @keyframes glow {
        0%, 100% {
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
        }
        50% {
            box-shadow: 0 0 40px rgba(102, 126, 234, 0.8);
        }
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
        animation: glow 2s ease-in-out infinite;
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        animation: glow 2s ease-in-out infinite;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stSidebar"] .element-container {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        padding: 1rem;
        border: 2px dashed rgba(102, 126, 234, 0.5);
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.1);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.7);
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(102, 126, 234, 0.2);
    }
    
    /* Success/Warning/Error Messages */
    .stSuccess, .stWarning, .stError, .stInfo {
        border-radius: 12px;
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Code Blocks */
    code {
        font-family: 'Fira Code', monospace;
        background: rgba(30, 41, 59, 0.8);
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px 12px 0 0;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(102, 126, 234, 0.2);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Loading Animation */
    .loading-pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Floating Animation for Icons */
    .float-icon {
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% {
            transform: translateY(0px);
        }
        50% {
            transform: translateY(-10px);
        }
    }
    
    /* Step Numbers */
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50%;
        color: white;
        font-weight: 700;
        margin-right: 1rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'deployment_state' not in st.session_state:
    st.session_state.deployment_state = None
if 'deployment_running' not in st.session_state:
    st.session_state.deployment_running = False
if 'db' not in st.session_state:
    st.session_state.db = DeploymentDatabase()
if 'cost_estimator' not in st.session_state:
    st.session_state.cost_estimator = AWSCostEstimator()

# Hero Section
st.markdown(f"""
<div class="hero-container">
    <h1 class="hero-title">☁️ {__app_name__}</h1>
    <p class="hero-subtitle">Deploy cloud infrastructure with Terraform through a professional interface</p>
    <span class="version-badge">v{__version__} - Enterprise Grade</span>
</div>
""", unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    col_env1, col_env2 = st.columns(2)
    with col_env1:
        st.metric("Environment", "Dev", delta="Active")
    with col_env2:
        st.metric("Max Size", "10MB")
    
    st.markdown("---")
    st.markdown("### 📚 Supported Formats")
    st.markdown("""
    - 📄 JSON (.json)
    - 📝 YAML (.yaml, .yml)
    """)
    
    # Deployment status in sidebar
    if st.session_state.deployment_state:
        st.markdown("---")
        st.markdown("### 📜 Current Deployment")
        status = st.session_state.deployment_state.status
        
        # Color-code status
        if status == DeploymentStatus.COMPLETED:
            st.success(f"✅ {status.value}")
        elif status == DeploymentStatus.FAILED:
            st.error(f"❌ {status.value}")
        elif status in [DeploymentStatus.INITIALIZING, DeploymentStatus.PLANNING, DeploymentStatus.APPLYING]:
            st.warning(f"⚡ {status.value}")
        else:
            st.info(f"ℹ️ {status.value}")
        
        st.progress(st.session_state.deployment_state.progress_percentage / 100)
        st.caption(st.session_state.deployment_state.current_step)
    
    # Deployment statistics
    st.markdown("---")
    st.markdown("### 📊 Statistics")
    stats = st.session_state.db.get_statistics()
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("Total", stats["total_deployments"], delta=None)
        st.metric("Success", stats["successful"], delta=f"{stats['success_rate']}%")
    with col_s2:
        st.metric("Failed", stats["failed"])
        if stats["total_deployments"] > 0:
            st.metric("Rate", f"{stats['success_rate']}%")

# Main content
st.markdown("## 🚀 Deployment Workflow")

# Step 1: Cloud Provider Selection
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### <span class='step-number'>1</span> Select Cloud Provider", unsafe_allow_html=True)
    cloud_provider = st.selectbox(
        "Choose your cloud platform:",
        options=["AWS", "Azure", "GCP"],
        help="Select the cloud platform where you want to deploy",
        disabled=st.session_state.deployment_running,
        label_visibility="collapsed"
    )
    
    # Show warning for non-AWS providers
    if cloud_provider != "AWS":
        st.warning(f"⚠️ {cloud_provider} support coming soon. Currently only AWS is supported.")

with col2:
    st.markdown("### 📊 Status")
    if cloud_provider == "AWS":
        st.success("✅ Ready")
    else:
        st.error("❌ Unavailable")

st.markdown("---")

# Step 2: Configuration Upload
st.markdown("### <span class='step-number'>2</span> Upload Configuration", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop your infrastructure configuration file here",
    type=["json", "yaml", "yml"],
    help="Supported formats: JSON, YAML",
    disabled=st.session_state.deployment_running,
    label_visibility="collapsed"
)

# Configuration preview
if uploaded_file:
    try:
        # Parse and validate configuration
        config = ConfigParser.parse_uploaded_file(uploaded_file)
        
        st.success("✅ Configuration validated successfully!")
        
        # Display configuration details in tabs
        tab1, tab2, tab3 = st.tabs(["📋 Details", "🔍 Terraform Preview", "💰 Cost Estimate"])
        
        with tab1:
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric("Provider", config.provider.upper(), delta="Supported")
                st.metric("Region", config.region)
            
            with col_b:
                st.metric("Instance Type", config.instance_type)
                if config.ami_id:
                    st.metric("AMI ID", config.ami_id[:12] + "...")
            
            with col_c:
                if config.tags:
                    st.markdown("**Tags:**")
                    for key, value in config.tags.items():
                        st.code(f"{key}: {value}")
        
        with tab2:
            try:
                tf_preview = TerraformGenerator.preview_config(config)
                st.code(tf_preview, language="hcl")
            except NotImplementedError as e:
                st.warning(f"⚠️ {str(e)}")
        
        with tab3:
            if config.provider == "aws":
                cost_estimate = st.session_state.cost_estimator.estimate_ec2_cost(
                    config.instance_type
                )
                free_tier = st.session_state.cost_estimator.get_free_tier_info(
                    config.instance_type
                )
                
                # Free tier badge
                if free_tier["eligible"]:
                    st.success("✅ Free Tier Eligible (750 hours/month for 12 months)")
                else:
                    st.info("ℹ️ Not eligible for AWS Free Tier")
                
                # Cost breakdown
                col_cost1, col_cost2, col_cost3 = st.columns(3)
                with col_cost1:
                    st.metric("Hourly Cost", f"${cost_estimate['compute']['hourly']}")
                with col_cost2:
                    st.metric("Monthly Cost", f"${cost_estimate['total']['monthly']}")
                with col_cost3:
                    st.metric("Yearly Cost", f"${cost_estimate['total']['yearly']}")
                
                st.caption(f"💡 Assumes {cost_estimate['assumptions']['uptime_percentage']}% uptime")
                
                # Store cost estimate
                st.session_state.cost_estimate = cost_estimate['total']['monthly']
        
        # Store config in session state
        st.session_state.config = config
        st.session_state.config_valid = True
        
    except ValueError as e:
        st.error(f"❌ Configuration validation failed: {str(e)}")
        logger.error(f"Configuration validation error: {e}")
        st.session_state.config = None
        st.session_state.config_valid = False
        
        # Show helpful hints
        with st.expander("💡 Configuration Help"):
            st.markdown("""
            **Required fields:**
            - `provider`: Must be one of: aws, azure, gcp
            - `region`: Deployment region (e.g., us-east-1)
            - `instance_type`: Instance type (e.g., t2.micro)
            
            **Optional fields:**
            - `ami_id`: AMI ID for AWS instances
            - `tags`: Key-value pairs for resource tagging
            
            **Example JSON:**
            ```json
            {
                "provider": "aws",
                "region": "us-east-1",
                "instance_type": "t2.micro",
                "tags": {
                    "Environment": "dev",
                    "Project": "test"
                }
            }
            ```
            """)
            
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        logger.exception("Unexpected error during file parsing")
        st.session_state.config = None
        st.session_state.config_valid = False

st.markdown("---")

# Step 3: Deployment
st.markdown("### <span class='step-number'>3</span> Deploy Infrastructure", unsafe_allow_html=True)

# Safety confirmation
if st.session_state.get("config_valid", False) and not st.session_state.deployment_running:
    with st.expander("⚠️ Pre-Deployment Safety Checklist", expanded=True):
        st.markdown("""
        **Before deploying, please confirm:**
        
        - ✓ I have reviewed the configuration details above
        - ✓ I have checked the cost estimate
        - ✓ I understand this will create REAL AWS resources
        - ✓ I have AWS credentials properly configured
        - ✓ I will destroy resources after testing
        - ✓ I accept responsibility for any AWS charges
        """)
        
        # Cost warning
        if st.session_state.get('cost_estimate'):
            monthly_cost = st.session_state.cost_estimate
            yearly_cost = monthly_cost * 12
            
            if monthly_cost > 10:
                st.warning(f"💰 **Cost Alert**: This deployment costs ~${monthly_cost}/month (${yearly_cost}/year)")
        
        # Confirmation checkbox
        safety_confirmed = st.checkbox(
            "✅ I have read and confirmed the above checklist",
            key="safety_confirmation"
        )
        
        if not safety_confirmed:
            st.info("👆 Please confirm the safety checklist to enable deployment")

deploy_button_disabled = (
    not (uploaded_file and st.session_state.get("config_valid", False)) 
    or st.session_state.deployment_running
    or (st.session_state.get("config") and st.session_state.config.provider != "aws")
    or not st.session_state.get("safety_confirmation", False)
)

if st.button("🚀 Deploy Infrastructure", type="primary", disabled=deploy_button_disabled, use_container_width=True):
    if st.session_state.get("config_valid", False):
        st.session_state.deployment_running = True
        
        # Create deployment directory
        deployment_dir = Path("./deployments") / f"deploy_{int(time.time())}"
        deployment_dir.mkdir(parents=True, exist_ok=True)
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        logs_placeholder = st.empty()
        
        try:
            config = st.session_state.config
            
            # Generate Terraform configuration
            with progress_placeholder.container():
                st.info("📝 Generating Terraform configuration...")
            
            TerraformGenerator.write_config_to_file(config, deployment_dir)
            
            with progress_placeholder.container():
                st.success("✅ Terraform configuration generated")
            
            # Execute deployment
            with progress_placeholder.container():
                st.info("🚀 Starting deployment...")
            
            # Create executor
            executor = TerraformExecutor(str(deployment_dir))
            
            # Run deployment in async
            async def run_deployment():
                return await executor.full_deployment()
            
            # Execute
            deployment_state = asyncio.run(run_deployment())
            st.session_state.deployment_state = deployment_state
            
            # Save to database
            try:
                st.session_state.db.save_deployment(
                    deployment_state=deployment_state,
                    provider=config.provider,
                    region=config.region,
                    instance_type=config.instance_type,
                    deployment_dir=str(deployment_dir),
                    cost_estimate=st.session_state.get('cost_estimate')
                )
                logger.info(f"Deployment saved to database: {deployment_state.deployment_id}")
            except Exception as e:
                logger.error(f"Failed to save deployment to database: {e}")
            
            # Display results
            progress_placeholder.empty()
            
            if deployment_state.status == DeploymentStatus.COMPLETED:
                st.success("🎉 Deployment completed successfully!")
                
                # Show outputs if available
                if deployment_state.result:
                    with st.expander("📊 Deployment Outputs", expanded=True):
                        outputs = executor.parse_outputs(deployment_state.result)
                        if outputs:
                            cols = st.columns(len(outputs))
                            for idx, (key, value) in enumerate(outputs.items()):
                                with cols[idx]:
                                    st.metric(key, value)
                        else:
                            st.info("No outputs available")
            else:
                st.error(f"❌ Deployment failed: {deployment_state.error}")
            
            # Show logs
            with st.expander("📋 Deployment Logs", expanded=False):
                for log in deployment_state.logs:
                    st.text(log)
            
            # Show cleanup instructions
            if deployment_state.status == DeploymentStatus.COMPLETED:
                st.info(f"""
                **Next Steps:**
                - Check your AWS console to verify resources
                - To destroy resources, run: `cd {deployment_dir} && terraform destroy`
                """)
            
        except Exception as e:
            progress_placeholder.empty()
            st.error(f"❌ Deployment failed: {str(e)}")
            logger.exception("Deployment error")
        finally:
            st.session_state.deployment_running = False
            
            # Add rerun button
            if st.button("🔄 Deploy Another Configuration"):
                st.session_state.deployment_state = None
                st.rerun()
    else:
        st.error("Please upload and validate a configuration file first")

# Footer
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)
with col_footer1:
    st.markdown(f"**{__app_name__}** v{__version__}")
with col_footer2:
    st.markdown("🔒 Enterprise Security Enabled")
with col_footer3:
    st.markdown("Made with ❤️ by Shoraj Tomer")
