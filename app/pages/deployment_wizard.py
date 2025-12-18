"""
Deployment Wizard - Updated with Service Layer Integration

Uses DeploymentService for all deployment operations.
"""

import streamlit as st
from typing import Dict, Any
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.deployment_service import get_deployment_service
from app.services.config_service import get_config_service
from app.core.rbac import get_rbac_manager, Permission
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def render_deployment_wizard(user_email: str):
    """
    Render deployment wizard with service layer integration
    
    Args:
        user_email: Current user's email
    """
    try:
        # Get services
        deployment_service = get_deployment_service()
        rbac = get_rbac_manager()
        
        # Check permission
        if not rbac.has_permission(user_email, Permission.DEPLOY_CREATE):
            st.error("⛔ You don't have permission to create deployments")
            st.info("Contact your administrator to request deployment access")
            return
        
        st.markdown("## Deploy Infrastructure")
        st.markdown("Create and manage cloud infrastructure deployments")
        st.markdown("")
        
        # Deployment form
        with st.form("deployment_form"):
            st.markdown("### Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                provider = st.selectbox(
                    "Cloud Provider",
                    ["aws", "azure", "gcp"],
                    help="Select your cloud provider"
                )
                
                region = st.text_input(
                    "Region",
                    value="us-east-1" if provider == "aws" else "eastus",
                    help="Deployment region"
                )
            
            with col2:
                instance_type = st.selectbox(
                    "Instance Type",
                    ["t2.micro", "t2.small", "t2.medium", "t2.large"],
                    help="Select instance size"
                )
                
                priority = st.selectbox(
                    "Priority",
                    ["normal", "high", "urgent"],
                    help="Deployment priority in queue"
                )
            
            # Advanced options
            with st.expander("Advanced Options"):
                variables = {}
                
                st.markdown("#### Terraform Variables")
                var_count = st.number_input("Number of variables", 0, 10, 0)
                
                for i in range(int(var_count)):
                    col_key, col_value = st.columns(2)
                    with col_key:
                        key = st.text_input(f"Variable {i+1} Name", key=f"var_key_{i}")
                    with col_value:
                        value = st.text_input(f"Variable {i+1} Value", key=f"var_val_{i}")
                    
                    if key:
                        variables[key] = value
            
            # Submit button
            st.markdown("")
            col_submit, col_cancel = st.columns([1, 3])
            
            with col_submit:
                submitted = st.form_submit_button(
                    "🚀 Deploy",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted:
                # Validate inputs
                if not region:
                    st.error("❌ Region is required")
                    return
                
                # Create deployment using service
                with st.spinner("Creating deployment..."):
                    try:
                        deployment_id = deployment_service.create_deployment(
                            user_email=user_email,
                            provider=provider,
                            region=region,
                            instance_type=instance_type,
                            variables=variables,
                            priority=priority
                        )
                        
                        st.success(f"✅ Deployment created successfully!")
                        st.info(f"Deployment ID: `{deployment_id}`")
                        st.info("Your deployment has been added to the queue")
                        
                        # Show queue position
                        from app.services.deployment_queue import get_queue_manager
                        queue = get_queue_manager()
                        status = queue.get_queue_status()
                        st.metric("Queue Position", f"#{status['queue_size']}")
                        
                    except ValueError as e:
                        st.error(f"❌ Validation Error: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Failed to create deployment: {str(e)}")
                        logger.error(f"Deployment creation error: {e}", exc_info=True)
        
        # Show recent deployments
        st.markdown("---")
        st.markdown("### Your Recent Deployments")
        
        try:
            deployments = deployment_service.get_user_deployments(
                user_email=user_email,
                limit=10
            )
            
            if deployments:
                for deployment in deployments:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{deployment.get('deployment_id', 'N/A')[:8]}...**")
                            st.caption(f"{deployment.get('provider', 'N/A')} • {deployment.get('region', 'N/A')}")
                        
                        with col2:
                            status = deployment.get('status', 'unknown')
                            if status == 'completed':
                                st.success(status.upper())
                            elif status == 'failed':
                                st.error(status.upper())
                            elif status == 'running':
                                st.info(status.upper())
                            else:
                                st.warning(status.upper())
                        
                        with col3:
                            created_at = deployment.get('created_at', 'N/A')
                            if created_at != 'N/A':
                                # Show relative time
                                from datetime import datetime
                                try:
                                    dt = datetime.fromisoformat(created_at)
                                    st.caption(dt.strftime("%Y-%m-%d %H:%M"))
                                except:
                                    st.caption(created_at)
                            else:
                                st.caption(created_at)
                        
                        with col4:
                            # Actions
                            if rbac.has_permission(user_email, Permission.DEPLOY_CANCEL):
                                if deployment.get('status') in ['queued', 'running']:
                                    if st.button("Cancel", key=f"cancel_{deployment.get('deployment_id')}"):
                                        try:
                                            deployment_service.cancel_deployment(
                                                deployment_id=deployment.get('deployment_id'),
                                                user_email=user_email,
                                                reason="User cancelled"
                                            )
                                            st.success("Deployment cancelled")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Failed to cancel: {str(e)}")
                        
                        st.markdown("---")
            else:
                st.info("📭 No deployments yet. Create your first deployment above!")
        
        except Exception as e:
            st.error(f"⚠️ Could not load deployments: {str(e)}")
            logger.error(f"Failed to load deployments: {e}", exc_info=True)
    
    except Exception as e:
        st.error("⚠️ An error occurred in the deployment wizard")
        st.error(f"Error: {str(e)}")
        logger.error(f"Deployment wizard error: {e}", exc_info=True)
