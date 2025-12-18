"""
Updated Deployment Database using SQLAlchemy and PostgreSQL

Replaces the old SQLite-based deployment_db.py with PostgreSQL support.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.database import (
    Database, get_database,
    Deployment, DeploymentLog, AuditLog
)
from app.services.encryption import EncryptionService
from app.services.terraform_executor import DeploymentState, DeploymentStatus
from app.utils.logger import setup_logger
import json

logger = setup_logger(__name__)


class DeploymentDatabase:
    """
    PostgreSQL-based deployment tracking database
    
    Provides methods for storing and retrieving deployment information
    with encryption for sensitive data.
    """
    
    def __init__(self, db_url: str = None):
        """
        Initialize deployment database
        
        Args:
            db_url: PostgreSQL connection URL (optional, reads from env if not provided)
        """
        self.db = Database(db_url)
        self.db.create_tables()
        
        # Initialize encryption service for sensitive data
        try:
            self.encryption = EncryptionService()
        except ValueError:
            logger.warning("Encryption not configured - sensitive data will not be encrypted")
            self.encryption = None
        
        logger.info("Initialized DeploymentDatabase with PostgreSQL")
    
    def save_deployment(
        self,
        deployment_state: DeploymentState,
        user_email: str,
        provider: str,
        region: str,
        instance_type: str,
        deployment_dir: str,
        cost_estimate: Optional[float] = None,
        config_file: Optional[str] = None
    ) -> int:
        """
        Save deployment to database
        
        Args:
            deployment_state: Deployment state object
            user_email: Email of user who initiated deployment
            provider: Cloud provider
            region: Deployment region
            instance_type: Instance type
            deployment_dir: Deployment directory path
            cost_estimate: Estimated monthly cost
            config_file: Path to configuration file
            
        Returns:
            Database row ID
        """
        session = self.db.get_session()
        
        try:
            # Prepare outputs as JSON
            outputs_json = None
            if deployment_state.result:
                outputs_dict = {
                    "output": deployment_state.result.output,
                    "duration": deployment_state.result.duration_seconds,
                    "return_code": deployment_state.result.return_code
                }
                outputs_json = json.dumps(outputs_dict)
                
                # Encrypt outputs if encryption is available
                if self.encryption:
                    outputs_json = self.encryption.encrypt(outputs_json)
            
            # Determine timestamps
            completed_at = None
            if deployment_state.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED]:
                completed_at = datetime.utcnow()
            
            # Create deployment record
            deployment = Deployment(
                deployment_id=deployment_state.deployment_id,
                user_email=user_email,
                provider=provider,
                region=region,
                instance_type=instance_type,
                status=deployment_state.status.value,
                current_step=deployment_state.current_step,
                progress_percentage=deployment_state.progress_percentage,
                created_at=datetime.utcnow(),
                completed_at=completed_at,
                error_message=deployment_state.error,
                outputs=outputs_json,
                cost_estimate=cost_estimate,
                deployment_dir=deployment_dir,
                config_file=config_file
            )
            
            session.add(deployment)
            session.flush()  # Get the ID
            
            # Save logs
            for log_message in deployment_state.logs:
                log_entry = DeploymentLog(
                    deployment_id=deployment_state.deployment_id,
                    timestamp=datetime.utcnow(),
                    log_level="INFO",
                    message=log_message
                )
                session.add(log_entry)
            
            session.commit()
            
            logger.info(f"Saved deployment: {deployment_state.deployment_id}")
            return deployment.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save deployment: {e}")
            raise
        finally:
            session.close()
    
    def update_deployment_status(
        self,
        deployment_id: str,
        status: str,
        current_step: str = None,
        progress_percentage: int = None,
        error_message: str = None
    ) -> bool:
        """
        Update deployment status
        
        Args:
            deployment_id: Deployment ID
            status: New status
            current_step: Current step description
            progress_percentage: Progress percentage
            error_message: Error message if failed
            
        Returns:
            True if updated successfully
        """
        session = self.db.get_session()
        
        try:
            deployment = session.query(Deployment).filter_by(
                deployment_id=deployment_id
            ).first()
            
            if not deployment:
                logger.warning(f"Deployment not found: {deployment_id}")
                return False
            
            deployment.status = status
            if current_step:
                deployment.current_step = current_step
            if progress_percentage is not None:
                deployment.progress_percentage = progress_percentage
            if error_message:
                deployment.error_message = error_message
            
            # Set completed_at if final status
            if status in ['completed', 'failed', 'cancelled']:
                deployment.completed_at = datetime.utcnow()
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update deployment status: {e}")
            return False
        finally:
            session.close()
    
    def get_deployment(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get deployment by ID
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            Deployment dictionary or None
        """
        session = self.db.get_session()
        
        try:
            deployment = session.query(Deployment).filter_by(
                deployment_id=deployment_id
            ).first()
            
            if not deployment:
                return None
            
            # Convert to dictionary
            result = {
                'id': deployment.id,
                'deployment_id': deployment.deployment_id,
                'user_email': deployment.user_email,
                'provider': deployment.provider,
                'region': deployment.region,
                'instance_type': deployment.instance_type,
                'status': deployment.status,
                'current_step': deployment.current_step,
                'progress_percentage': deployment.progress_percentage,
                'created_at': deployment.created_at.isoformat() if deployment.created_at else None,
                'completed_at': deployment.completed_at.isoformat() if deployment.completed_at else None,
                'error_message': deployment.error_message,
                'cost_estimate': deployment.cost_estimate,
                'deployment_dir': deployment.deployment_dir
            }
            
            # Decrypt outputs if encrypted
            if deployment.outputs and self.encryption:
                try:
                    decrypted = self.encryption.decrypt(deployment.outputs)
                    result['outputs'] = json.loads(decrypted)
                except Exception as e:
                    logger.warning(f"Failed to decrypt outputs: {e}")
                    result['outputs'] = None
            else:
                result['outputs'] = deployment.outputs
            
            return result
            
        finally:
            session.close()
    
    def get_deployments_by_user(
        self,
        user_email: str,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get deployments for a specific user
        
        Args:
            user_email: User email
            limit: Maximum number of results
            status: Filter by status (optional)
            
        Returns:
            List of deployment dictionaries
        """
        session = self.db.get_session()
        
        try:
            query = session.query(Deployment).filter_by(user_email=user_email)
            
            if status:
                query = query.filter_by(status=status)
            
            query = query.order_by(desc(Deployment.created_at)).limit(limit)
            
            deployments = query.all()
            
            return [
                {
                    'deployment_id': d.deployment_id,
                    'status': d.status,
                    'provider': d.provider,
                    'region': d.region,
                    'created_at': d.created_at.isoformat() if d.created_at else None,
                    'cost_estimate': d.cost_estimate
                }
                for d in deployments
            ]
            
        finally:
            session.close()
    
    def get_deployment_logs(self, deployment_id: str) -> List[Dict[str, Any]]:
        """
        Get logs for a deployment
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            List of log dictionaries
        """
        session = self.db.get_session()
        
        try:
            logs = session.query(DeploymentLog).filter_by(
                deployment_id=deployment_id
            ).order_by(DeploymentLog.timestamp).all()
            
            return [
                {
                    'timestamp': log.timestamp.isoformat(),
                    'log_level': log.log_level,
                    'message': log.message
                }
                for log in logs
            ]
            
        finally:
            session.close()
    
    def get_statistics(self, user_email: str = None) -> Dict[str, Any]:
        """
        Get deployment statistics
        
        Args:
            user_email: Optional user email to filter by
            
        Returns:
            Statistics dictionary
        """
        session = self.db.get_session()
        
        try:
            query = session.query(Deployment)
            
            if user_email:
                query = query.filter_by(user_email=user_email)
            
            total = query.count()
            successful = query.filter_by(status='completed').count()
            failed = query.filter_by(status='failed').count()
            
            # Calculate total cost
            total_cost = session.query(
                Deployment.cost_estimate
            ).filter(
                and_(
                    Deployment.status == 'completed',
                    Deployment.cost_estimate.isnot(None)
                )
            )
            
            if user_email:
                total_cost = total_cost.filter_by(user_email=user_email)
            
            cost_sum = sum([c[0] for c in total_cost.all() if c[0]])
            
            success_rate = (successful / total * 100) if total > 0 else 0.0
            
            return {
                'total_deployments': total,
                'successful': successful,
                'failed': failed,
                'success_rate': round(success_rate, 2),
                'total_estimated_cost': round(cost_sum, 2)
            }
            
        finally:
            session.close()
    
    def delete_deployment(self, deployment_id: str) -> bool:
        """
        Delete a deployment and its logs
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            True if deleted, False otherwise
        """
        session = self.db.get_session()
        
        try:
            deployment = session.query(Deployment).filter_by(
                deployment_id=deployment_id
            ).first()
            
            if not deployment:
                return False
            
            # Logs will be deleted automatically due to cascade
            session.delete(deployment)
            session.commit()
            
            logger.info(f"Deleted deployment: {deployment_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete deployment: {e}")
            return False
        finally:
            session.close()
    
    def close(self):
        """Close database connection"""
        # SQLAlchemy handles connection pooling, no explicit close needed
        logger.info("Database connection pool will be managed by SQLAlchemy")
