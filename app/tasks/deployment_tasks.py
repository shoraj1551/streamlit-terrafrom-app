"""
Celery Tasks for Terraform Deployments

Background tasks for running Terraform deployments asynchronously.
"""

from app.celery_app import celery_app
from app.services.terraform_executor import TerraformExecutor, DeploymentState, DeploymentStatus
from app.services.deployment_db import DeploymentDatabase
from app.services.audit_logger import AuditLogger
from app.utils.logger import setup_logger
import asyncio
from typing import Dict, Optional

logger = setup_logger(__name__)


@celery_app.task(bind=True, name='deploy_infrastructure')
def deploy_infrastructure(
    self,
    deployment_id: str,
    working_dir: str,
    user_email: str,
    provider: str,
    region: str,
    instance_type: str,
    variables: Optional[Dict[str, str]] = None,
    cost_estimate: Optional[float] = None
):
    """
    Background task for Terraform deployment
    
    Args:
        self: Celery task instance
        deployment_id: Unique deployment ID
        working_dir: Terraform working directory
        user_email: Email of user who initiated deployment
        provider: Cloud provider
        region: Deployment region
        instance_type: Instance type
        variables: Terraform variables
        cost_estimate: Estimated monthly cost
        
    Returns:
        Dictionary with deployment results
    """
    audit_logger = AuditLogger()
    db = DeploymentDatabase()
    
    # Update task state
    self.update_state(
        state='STARTED',
        meta={'deployment_id': deployment_id, 'status': 'initializing'}
    )
    
    # Log deployment start
    audit_logger.log_event(
        event_type="deployment.started",
        user_id=user_email,
        resource_type="deployment",
        resource_id=deployment_id,
        details={
            'provider': provider,
            'region': region,
            'instance_type': instance_type
        },
        severity="info"
    )
    
    try:
        # Create deployment state
        deployment_state = DeploymentState(
            deployment_id=deployment_id,
            status=DeploymentStatus.PENDING,
            current_step="Initializing",
            progress_percentage=0
        )
        
        # Save initial deployment
        db.save_deployment(
            deployment_state=deployment_state,
            user_email=user_email,
            provider=provider,
            region=region,
            instance_type=instance_type,
            deployment_dir=working_dir,
            cost_estimate=cost_estimate
        )
        
        # Execute deployment
        executor = TerraformExecutor(working_dir)
        
        # Run async deployment in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Update state: Init
            deployment_state.status = DeploymentStatus.RUNNING
            deployment_state.current_step = "Initializing Terraform"
            deployment_state.progress_percentage = 10
            db.update_deployment_status(
                deployment_id, 
                deployment_state.status.value,
                deployment_state.current_step,
                deployment_state.progress_percentage
            )
            
            # Terraform init
            init_result = loop.run_until_complete(executor.init())
            if not init_result.success:
                raise Exception(f"Terraform init failed: {init_result.error}")
            
            # Update state: Validate
            deployment_state.current_step = "Validating configuration"
            deployment_state.progress_percentage = 30
            db.update_deployment_status(
                deployment_id,
                deployment_state.status.value,
                deployment_state.current_step,
                deployment_state.progress_percentage
            )
            
            # Terraform validate
            validate_result = loop.run_until_complete(executor.validate())
            if not validate_result.success:
                raise Exception(f"Terraform validate failed: {validate_result.error}")
            
            # Update state: Plan
            deployment_state.current_step = "Creating execution plan"
            deployment_state.progress_percentage = 50
            db.update_deployment_status(
                deployment_id,
                deployment_state.status.value,
                deployment_state.current_step,
                deployment_state.progress_percentage
            )
            
            # Terraform plan
            plan_result = loop.run_until_complete(executor.plan(variables=variables))
            if not plan_result.success:
                raise Exception(f"Terraform plan failed: {plan_result.error}")
            
            # Update state: Apply
            deployment_state.current_step = "Applying infrastructure changes"
            deployment_state.progress_percentage = 70
            db.update_deployment_status(
                deployment_id,
                deployment_state.status.value,
                deployment_state.current_step,
                deployment_state.progress_percentage
            )
            
            # Terraform apply
            apply_result = loop.run_until_complete(
                executor.apply(variables=variables, auto_approve=True)
            )
            if not apply_result.success:
                raise Exception(f"Terraform apply failed: {apply_result.error}")
            
            # Success
            deployment_state.status = DeploymentStatus.COMPLETED
            deployment_state.current_step = "Deployment completed successfully"
            deployment_state.progress_percentage = 100
            deployment_state.result = apply_result
            
            db.update_deployment_status(
                deployment_id,
                deployment_state.status.value,
                deployment_state.current_step,
                deployment_state.progress_percentage
            )
            
            # Log success
            audit_logger.log_event(
                event_type="deployment.completed",
                user_id=user_email,
                resource_type="deployment",
                resource_id=deployment_id,
                status="success",
                details={'duration': apply_result.duration_seconds},
                severity="info"
            )
            
            return {
                'deployment_id': deployment_id,
                'status': 'completed',
                'message': 'Deployment completed successfully'
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        error_message = str(e)
        logger.error(f"Deployment {deployment_id} failed: {error_message}")
        
        # Update deployment status
        db.update_deployment_status(
            deployment_id,
            'failed',
            'Deployment failed',
            error_message=error_message
        )
        
        # Log failure
        audit_logger.log_event(
            event_type="deployment.failed",
            user_id=user_email,
            resource_type="deployment",
            resource_id=deployment_id,
            status="failure",
            error_message=error_message,
            severity="error"
        )
        
        # Re-raise for Celery
        raise


@celery_app.task(name='destroy_infrastructure')
def destroy_infrastructure(
    deployment_id: str,
    working_dir: str,
    user_email: str,
    variables: Optional[Dict[str, str]] = None
):
    """
    Background task for destroying Terraform infrastructure
    
    Args:
        deployment_id: Deployment ID to destroy
        working_dir: Terraform working directory
        user_email: User email
        variables: Terraform variables
        
    Returns:
        Dictionary with results
    """
    audit_logger = AuditLogger()
    
    # Log destruction start
    audit_logger.log_event(
        event_type="deployment.destroy_started",
        user_id=user_email,
        resource_type="deployment",
        resource_id=deployment_id,
        severity="warning"
    )
    
    try:
        executor = TerraformExecutor(working_dir)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            destroy_result = loop.run_until_complete(
                executor.destroy(variables=variables, auto_approve=True)
            )
            
            if destroy_result.success:
                audit_logger.log_event(
                    event_type="deployment.destroyed",
                    user_id=user_email,
                    resource_type="deployment",
                    resource_id=deployment_id,
                    status="success",
                    severity="warning"
                )
                
                return {
                    'deployment_id': deployment_id,
                    'status': 'destroyed',
                    'message': 'Infrastructure destroyed successfully'
                }
            else:
                raise Exception(f"Destroy failed: {destroy_result.error}")
                
        finally:
            loop.close()
            
    except Exception as e:
        error_message = str(e)
        logger.error(f"Destroy {deployment_id} failed: {error_message}")
        
        audit_logger.log_event(
            event_type="deployment.destroy_failed",
            user_id=user_email,
            resource_type="deployment",
            resource_id=deployment_id,
            status="failure",
            error_message=error_message,
            severity="error"
        )
        
        raise
