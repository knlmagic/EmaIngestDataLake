"""
Reset Manager for EMA Demo App
Provides comprehensive reset functionality for demo environments
"""

import os
import json
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ResetManager:
    """Manages reset operations for the EMA demo app"""
    
    def __init__(self, db_path: Path, data_raw_path: Path, config_path: Path):
        self.db_path = db_path
        self.data_raw_path = data_raw_path
        self.config_path = config_path
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of current system state
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Backup directory path
        """
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        try:
            # Backup database
            if self.db_path.exists():
                shutil.copy2(self.db_path, backup_path / "ema_demo.sqlite")
            
            # Backup config
            if self.config_path.exists():
                shutil.copy2(self.config_path, backup_path / "config.json")
            
            # Backup sample data
            if self.data_raw_path.exists():
                shutil.copytree(self.data_raw_path, backup_path / "data_lake", dirs_exist_ok=True)
            
            # Create backup metadata
            metadata = {
                "created_at": datetime.now().isoformat(),
                "backup_name": backup_name,
                "db_exists": self.db_path.exists(),
                "data_files_count": len(list(self.data_raw_path.glob("*"))) if self.data_raw_path.exists() else 0,
                "config_exists": self.config_path.exists()
            }
            
            with open(backup_path / "backup_metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / "backup_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                        backups.append({
                            "name": backup_dir.name,
                            "path": str(backup_dir),
                            **metadata
                        })
                    except Exception as e:
                        logger.warning(f"Failed to read backup metadata for {backup_dir}: {e}")
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore from a backup
        
        Args:
            backup_name: Name of backup to restore
            
        Returns:
            True if successful, False otherwise
        """
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_name}")
            return False
        
        try:
            # Restore database
            backup_db = backup_path / "ema_demo.sqlite"
            if backup_db.exists():
                shutil.copy2(backup_db, self.db_path)
            
            # Restore config
            backup_config = backup_path / "config.json"
            if backup_config.exists():
                shutil.copy2(backup_config, self.config_path)
            
            # Restore data files
            backup_data = backup_path / "data_lake"
            if backup_data.exists():
                if self.data_raw_path.exists():
                    shutil.rmtree(self.data_raw_path)
                shutil.copytree(backup_data, self.data_raw_path)
            
            logger.info(f"Restored from backup: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_name}: {e}")
            return False
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup"""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            return False
        
        try:
            shutil.rmtree(backup_path)
            logger.info(f"Deleted backup: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_name}: {e}")
            return False
    
    def reset_database(self) -> Tuple[int, int]:
        """
        Reset database only (clear all data)
        
        Returns:
            Tuple of (tables_cleared, records_deleted)
        """
        if not self.db_path.exists():
            return 0, 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            total_deleted = 0
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                total_deleted += cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database reset: {len(tables)} tables cleared, {total_deleted} records deleted")
            return len(tables), total_deleted
            
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            raise
    
    def reset_sample_data(self, regenerate: bool = True) -> int:
        """
        Reset sample data files
        
        Args:
            regenerate: Whether to regenerate sample data after clearing
            
        Returns:
            Number of files processed
        """
        files_removed = 0
        
        try:
            # Remove existing sample files
            if self.data_raw_path.exists():
                for file_path in self.data_raw_path.glob("*"):
                    if file_path.is_file():
                        file_path.unlink()
                        files_removed += 1
            
            # Regenerate if requested
            if regenerate:
                from .sample_data import generate
                generate(self.data_raw_path, n_sets=15)
                logger.info("Sample data regenerated")
            
            logger.info(f"Sample data reset: {files_removed} files removed")
            return files_removed
            
        except Exception as e:
            logger.error(f"Failed to reset sample data: {e}")
            raise
    
    def reset_config(self) -> bool:
        """Reset config to defaults"""
        default_config = {
            "qty_tolerance_units": 1,
            "price_tolerance_pct": 2.0,
            "fx_rates": {
                "USD": 1.0,
                "GBP": 1.3,
                "INR": 0.012
            }
        }
        
        try:
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            
            logger.info("Config reset to defaults")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset config: {e}")
            return False
    
    def full_reset(self, create_backup: bool = True, regenerate_data: bool = True) -> Dict:
        """
        Perform full system reset
        
        Args:
            create_backup: Whether to create backup before reset
            regenerate_data: Whether to regenerate sample data
            
        Returns:
            Dictionary with reset results
        """
        results = {
            "backup_created": None,
            "database_reset": False,
            "sample_data_reset": False,
            "config_reset": False,
            "errors": []
        }
        
        try:
            # Create backup if requested
            if create_backup:
                backup_path = self.create_backup("pre_reset_backup")
                results["backup_created"] = backup_path
            
            # Reset database
            tables_cleared, records_deleted = self.reset_database()
            results["database_reset"] = True
            results["tables_cleared"] = tables_cleared
            results["records_deleted"] = records_deleted
            
            # Reset sample data
            files_removed = self.reset_sample_data(regenerate=regenerate_data)
            results["sample_data_reset"] = True
            results["files_removed"] = files_removed
            
            # Reset config
            results["config_reset"] = self.reset_config()
            
            logger.info("Full system reset completed successfully")
            
        except Exception as e:
            error_msg = f"Full reset failed: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        status = {
            "database_exists": self.db_path.exists(),
            "database_size": 0,
            "data_files_count": 0,
            "config_exists": self.config_path.exists(),
            "backups_count": len(self.list_backups()),
            "last_modified": None
        }
        
        try:
            if self.db_path.exists():
                status["database_size"] = self.db_path.stat().st_size
                status["last_modified"] = datetime.fromtimestamp(
                    self.db_path.stat().st_mtime
                ).isoformat()
            
            if self.data_raw_path.exists():
                status["data_files_count"] = len(list(self.data_raw_path.glob("*")))
            
        except Exception as e:
            logger.warning(f"Failed to get system status: {e}")
        
        return status
