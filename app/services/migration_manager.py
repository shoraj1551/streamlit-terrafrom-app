"""
Database Migration Management

Alembic migration workflow and utilities.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class MigrationManager:
    """
    Database migration manager
    
    Handles Alembic migrations safely.
    """
    
    def __init__(self, alembic_ini_path: str = "alembic.ini"):
        """
        Initialize migration manager
        
        Args:
            alembic_ini_path: Path to alembic.ini
        """
        self.alembic_ini = alembic_ini_path
        self.migrations_dir = Path("alembic/versions")
    
    def get_current_revision(self) -> Optional[str]:
        """
        Get current database revision
        
        Returns:
            Current revision ID or None
        """
        try:
            result = subprocess.run(
                ["alembic", "current"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse output to get revision
                output = result.stdout.strip()
                if output:
                    # Format: "revision_id (head)"
                    revision = output.split()[0]
                    return revision
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def get_pending_migrations(self) -> List[str]:
        """
        Get list of pending migrations
        
        Returns:
            List of pending migration IDs
        """
        try:
            result = subprocess.run(
                ["alembic", "history"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse to find migrations after current
                # This is simplified - real implementation would parse properly
                return []
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get pending migrations: {e}")
            return []
    
    def create_migration(
        self,
        message: str,
        autogenerate: bool = True
    ) -> Optional[str]:
        """
        Create new migration
        
        Args:
            message: Migration message
            autogenerate: Whether to auto-generate from models
            
        Returns:
            Migration file path or None
        """
        try:
            cmd = ["alembic", "revision"]
            
            if autogenerate:
                cmd.append("--autogenerate")
            
            cmd.extend(["-m", message])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Created migration: {message}")
                return result.stdout.strip()
            else:
                logger.error(f"Failed to create migration: {result.stderr}")
                return None
        
        except Exception as e:
            logger.error(f"Migration creation error: {e}")
            return None
    
    def upgrade(
        self,
        revision: str = "head",
        sql_only: bool = False
    ) -> bool:
        """
        Upgrade database to revision
        
        Args:
            revision: Target revision (default: head)
            sql_only: Only generate SQL, don't execute
            
        Returns:
            True if successful
        """
        try:
            cmd = ["alembic", "upgrade", revision]
            
            if sql_only:
                cmd.append("--sql")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Upgraded to {revision}")
                return True
            else:
                logger.error(f"Upgrade failed: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Upgrade error: {e}")
            return False
    
    def downgrade(
        self,
        revision: str = "-1",
        sql_only: bool = False
    ) -> bool:
        """
        Downgrade database to revision
        
        Args:
            revision: Target revision (default: -1 for one step back)
            sql_only: Only generate SQL, don't execute
            
        Returns:
            True if successful
        """
        try:
            cmd = ["alembic", "downgrade", revision]
            
            if sql_only:
                cmd.append("--sql")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Downgraded to {revision}")
                return True
            else:
                logger.error(f"Downgrade failed: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Downgrade error: {e}")
            return False
    
    def get_migration_status(self) -> dict:
        """
        Get comprehensive migration status
        
        Returns:
            Status dictionary
        """
        return {
            "current_revision": self.get_current_revision(),
            "pending_migrations": self.get_pending_migrations(),
            "migrations_dir": str(self.migrations_dir),
            "alembic_ini": self.alembic_ini
        }


# Global instance
_migration_manager = None


def get_migration_manager() -> MigrationManager:
    """Get global migration manager instance"""
    global _migration_manager
    if _migration_manager is None:
        _migration_manager = MigrationManager()
    return _migration_manager
