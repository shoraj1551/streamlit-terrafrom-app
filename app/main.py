import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_parser import ConfigParser
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Cloud Infrastructure Deployment",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("1️⃣ Select Cloud Provider")
    cloud_provider = st.selectbox(
        "Choose your cloud provider:",
        options=["AWS", "Azure", "GCP"],
        help="Select the cloud platform where you want to deploy"
    )
    
    st.header("2️⃣ Upload Configuration")
    uploaded_file = st.file_uploader(
        "Upload your infrastructure configuration file",
        type=["json", "yaml", "yml"],
        help="Supported formats: JSON, YAML"
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
                    if config.tags:
                        st.write("**Tags:**")
                        st.json(config.tags)
            
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

# Deployment section
st.header("3️⃣ Deploy Infrastructure")

deploy_button_disabled = not (uploaded_file and st.session_state.get("config_valid", False))

if st.button("🚀 Deploy Infrastructure", type="primary", disabled=deploy_button_disabled):
    if st.session_state.get("config_valid", False):
        with st.spinner(f"Deploying infrastructure on {cloud_provider}..."):
            try:
                # TODO: Implement actual Terraform execution
                st.warning("⚠️ Terraform execution not yet implemented")
                logger.info(f"Deployment initiated for provider: {cloud_provider}")
                
                # Placeholder for deployment logic
                st.info("""
                **Next Steps (Not Yet Implemented)**:
                1. Generate Terraform configuration from uploaded config
                2. Run `terraform plan` to preview changes
                3. Execute `terraform apply` to deploy infrastructure
                4. Display deployment status and outputs
                """)
                
                # Show what would be deployed
                with st.expander("📝 Deployment Preview"):
                    config = st.session_state.config
                    st.code(f"""
# Terraform Configuration Preview
provider "{config.provider}" {{
  region = "{config.region}"
}}

resource "{config.provider}_instance" "web" {{
  instance_type = "{config.instance_type}"
  {f'ami = "{config.ami_id}"' if config.ami_id else '# AMI will be auto-selected'}
  
  tags = {{
    {chr(10).join([f'    {k} = "{v}"' for k, v in config.tags.items()]) if config.tags else '    # No tags specified'}
  }}
}}
                    """, language="hcl")
                
            except Exception as e:
                st.error(f"❌ Deployment failed: {str(e)}")
                logger.exception("Deployment error")
    else:
        st.error("Please upload and validate a configuration file first")

# Footer
st.markdown("---")
st.markdown("**Streamlit Terraform Deployer** | Environment: development | Phase 1 Implementation")
