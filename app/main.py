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

logger = setup_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Cloud Infrastructure Deployment",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'deployment_state' not in st.session_state:
    st.session_state.deployment_state = None
if 'deployment_running' not in st.session_state:
    st.session_state.deployment_running = False

# Title and description
st.title("☁️ Cloud Infrastructure Deployment")
st.markdown("""
Deploy cloud infrastructure with Terraform through an intuitive interface.
Upload your configuration file and deploy with a single click.
""")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    st.info(f"Environment: **development**")
    st.info(f"Max Upload Size: **10MB**")
    
    st.markdown("---")
    st.markdown("### 📚 Supported Formats")
    st.markdown("- JSON (.json)")
    st.markdown("- YAML (.yaml, .yml)")
    
    # Deployment status in sidebar
    if st.session_state.deployment_state:
        st.markdown("---")
        st.markdown("### 📜 Current Deployment")
        status = st.session_state.deployment_state.status
        
        # Color-code status
        if status == DeploymentStatus.COMPLETED:
            st.success(f"Status: {status.value}")
        elif status == DeploymentStatus.FAILED:
            st.error(f"Status: {status.value}")
        elif status in [DeploymentStatus.INITIALIZING, DeploymentStatus.PLANNING, DeploymentStatus.APPLYING]:
            st.warning(f"Status: {status.value}")
        else:
            st.info(f"Status: {status.value}")
        
        st.metric("Progress", f"{st.session_state.deployment_state.progress_percentage}%")
        st.caption(st.session_state.deployment_state.current_step)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("1️⃣ Select Cloud Provider")
    cloud_provider = st.selectbox(
        "Choose your cloud provider:",
        options=["AWS", "Azure", "GCP"],
        help="Select the cloud platform where you want to deploy",
        disabled=st.session_state.deployment_running
    )
    
    # Show warning for non-AWS providers
    if cloud_provider != "AWS":
        st.warning(f"⚠️ {cloud_provider} support coming in Phase 3. Currently only AWS is supported.")
    
    st.header("2️⃣ Upload Configuration")
    uploaded_file = st.file_uploader(
        "Upload your infrastructure configuration file",
        type=["json", "yaml", "yml"],
        help="Supported formats: JSON, YAML",
        disabled=st.session_state.deployment_running
    )
    
    # Configuration preview
    if uploaded_file:
        try:
            # Parse and validate configuration
            config = ConfigParser.parse_uploaded_file(uploaded_file)
            
            st.success("✅ Configuration file validated successfully!")
            
            # Display configuration details
            with st.expander("📋 Configuration Details", expanded=True):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.metric("Provider", config.provider.upper())
                    st.metric("Region", config.region)
                    st.metric("Instance Type", config.instance_type)
                
                with col_b:
                    if config.ami_id:
                        st.metric("AMI ID", config.ami_id)
                    else:
                        st.info("AMI: Latest Amazon Linux 2 (auto-selected)")
                    if config.tags:
                        st.write("**Tags:**")
                        st.json(config.tags)
            
            # Show generated Terraform preview
            with st.expander("🔍 Terraform Configuration Preview"):
                try:
                    tf_preview = TerraformGenerator.preview_config(config)
                    st.code(tf_preview, language="hcl")
                except NotImplementedError as e:
                    st.warning(f"⚠️ {str(e)}")
            
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

with col2:
    st.header("📊 Status")
    
    # Status indicators
    if uploaded_file and st.session_state.get("config_valid", False):
        st.metric("Configuration", "Valid ✅")
        st.metric("Provider", cloud_provider)
        st.metric("Ready to Deploy", "Yes ✅")
    else:
        st.metric("Configuration", "Pending ⏳")
        st.metric("Ready to Deploy", "No ❌")
    
    # Show deployment info if exists
    if st.session_state.deployment_state:
        st.markdown("---")
        st.markdown("### 🚀 Deployment Info")
        st.caption(f"ID: {st.session_state.deployment_state.deployment_id[:8]}...")

# Deployment section
st.header("3️⃣ Deploy Infrastructure")

# Warning about AWS costs
if st.session_state.get("config_valid", False) and not st.session_state.deployment_running:
    st.warning("""
    ⚠️ **Important**: This will create REAL AWS resources that may incur costs!
    - Make sure you have AWS credentials configured
    - Use t2.micro instances (free tier eligible)
    - Remember to destroy resources after testing
    """)

deploy_button_disabled = (
    not (uploaded_file and st.session_state.get("config_valid", False)) 
    or st.session_state.deployment_running
    or (st.session_state.get("config") and st.session_state.config.provider != "aws")
)

if st.button("🚀 Deploy Infrastructure", type="primary", disabled=deploy_button_disabled):
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
            
            # Display results
            progress_placeholder.empty()
            
            if deployment_state.status == DeploymentStatus.COMPLETED:
                st.success("🎉 Deployment completed successfully!")
                
                # Show outputs if available
                if deployment_state.result:
                    with st.expander("📊 Deployment Outputs", expanded=True):
                        outputs = executor.parse_outputs(deployment_state.result)
                        if outputs:
                            for key, value in outputs.items():
                                st.metric(key, value)
                        else:
                            st.info("No outputs available")
            else:
                st.error(f"❌ Deployment failed: {deployment_state.error}")
            
            # Show logs
            with st.expander("📋 Deployment Logs", expanded=True):
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
    st.markdown("**Streamlit Terraform Deployer**")
with col_footer2:
    st.markdown("Environment: development")
with col_footer3:
    st.markdown("Phase 2: Core Functionality ✨")
