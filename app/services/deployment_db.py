import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.utils.logger import setup_logger
from app.services.terraform_executor import DeploymentState, DeploymentStatus

logger = setup_logger(__name__)


class DeploymentDatabase:
    """SQLite database for tracking deployment history"""
    
    def __init__(self, db_path: str = "./data/deployments.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        self._create_tables()
        logger.info(f"Initialized DeploymentDatabase at: {db_path}")
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Deployments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deployment_id TEXT UNIQUE NOT NULL,
                provider TEXT NOT NULL,
                region TEXT NOT NULL,
                instance_type TEXT,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                outputs TEXT,
                cost_estimate REAL,
                deployment_dir TEXT
            )
        """)
        
        # Deployment logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployment_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deployment_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                log_level TEXT,
                message TEXT,
                FOREIGN KEY (deployment_id) REFERENCES deployments(deployment_id)
            )
        """)
        
        self.conn.commit()
        logger.info("Database tables created/verified")
    
    def save_deployment(
        self,
        deployment_state: DeploymentState,
        provider: str,
        region: str,
        instance_type: str,
        deployment_dir: str,
        cost_estimate: Optional[float] = None
    ) -> int:
        """
        Save deployment to database
        
        Args:
            deployment_state: Deployment state object
            provider: Cloud provider
            region: Deployment region
            instance_type: Instance type
            deployment_dir: Deployment directory path
            cost_estimate: Estimated monthly cost
            
        Returns:
            Database row ID
        """
        cursor = self.conn.cursor()
        
        # Prepare outputs as JSON
        outputs_json = None
        if deployment_state.result:
            outputs_json = json.dumps({
                "output": deployment_state.result.output,
                "duration": deployment_state.result.duration_seconds
            })
        
        # Determine completed_at
        completed_at = None
        if deployment_state.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED]:
            completed_at = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO deployments (
                deployment_id, provider, region, instance_type, status,
                completed_at, error_message, outputs, cost_estimate, deployment_dir
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            deployment_state.deployment_id,
            provider,
            region,
            instance_type,
            deployment_state.status.value,
            completed_at,
            deployment_state.error,
            outputs_json,
            cost_estimate,
            deployment_dir
        ))
        
        row_id = cursor.lastrowid
        
        # Save logs
        for log in deployment_state.logs:
            self.save_log(deployment_state.deployment_id, "INFO", log)
        
        self.conn.commit()
        logger.info(f"Saved deployment: {deployment_state.deployment_id}")
        
        return row_id
    
    def save_log(
        self,
        deployment_id: str,
        log_level: str,
        message: str
    ):
        """
        Save a log entry
        
        Args:
            deployment_id: Deployment ID
            log_level: Log level (INFO, WARNING, ERROR)
            message: Log message
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO deployment_logs (deployment_id, log_level, message)
            VALUES (?, ?, ?)
        """, (deployment_id, log_level, message))
        
        self.conn.commit()
    
    def get_deployment(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get deployment by ID
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            Deployment dictionary or None
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM deployments WHERE deployment_id = ?
        """, (deployment_id,))
        
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_all_deployments(
        self,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all deployments
        
        Args:
            limit: Maximum number of results
            status: Filter by status (optional)
            
        Returns:
            List of deployment dictionaries
        """
        cursor = self.conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM deployments
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT * FROM deployments
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_deployment_logs(self, deployment_id: str) -> List[Dict[str, Any]]:
        """
        Get logs for a deployment
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            List of log dictionaries
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM deployment_logs
            WHERE deployment_id = ?
            ORDER BY timestamp ASC
        """, (deployment_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get deployment statistics
        
        Returns:
            Statistics dictionary
        """
        cursor = self.conn.cursor()
        
        # Total deployments
        cursor.execute("SELECT COUNT(*) as total FROM deployments")
        total = cursor.fetchone()["total"]
        
        # Successful deployments
        cursor.execute("""
            SELECT COUNT(*) as successful FROM deployments
            WHERE status = 'completed'
        """)
        successful = cursor.fetchone()["successful"]
        
        # Failed deployments
        cursor.execute("""
            SELECT COUNT(*) as failed FROM deployments
            WHERE status = 'failed'
        """)
        failed = cursor.fetchone()["failed"]
        
        # Total estimated cost
        cursor.execute("""
            SELECT SUM(cost_estimate) as total_cost FROM deployments
            WHERE status = 'completed'
        """)
        total_cost = cursor.fetchone()["total_cost"] or 0.0
        
        # Success rate
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        return {
            "total_deployments": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(success_rate, 2),
            "total_estimated_cost": round(total_cost, 2)
        }
    
    def delete_deployment(self, deployment_id: str) -> bool:
        """
        Delete a deployment and its logs
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            True if deleted, False otherwise
        """
        cursor = self.conn.cursor()
        
        # Delete logs first (foreign key constraint)
        cursor.execute("""
            DELETE FROM deployment_logs WHERE deployment_id = ?
        """, (deployment_id,))
        
        # Delete deployment
        cursor.execute("""
            DELETE FROM deployments WHERE deployment_id = ?
        """, (deployment_id,))
        
        self.conn.commit()
        
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted deployment: {deployment_id}")
        
        return deleted
    
    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("Database connection closed")
