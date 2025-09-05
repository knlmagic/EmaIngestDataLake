#!/usr/bin/env python3
"""
Command-line reset utility for EMA Demo App
Provides advanced reset operations and system management
"""

import argparse
import sys
from pathlib import Path
from pipeline.reset_manager import ResetManager

def main():
    parser = argparse.ArgumentParser(description="EMA Demo Reset Utility")
    parser.add_argument("--db-path", default="ema_demo.sqlite", help="Database path")
    parser.add_argument("--data-path", default="data_lake/raw", help="Data directory path")
    parser.add_argument("--config-path", default="config.json", help="Config file path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Full reset command
    reset_parser = subparsers.add_parser("reset", help="Reset system")
    reset_parser.add_argument("--type", choices=["full", "db", "data", "config"], 
                             default="full", help="Reset type")
    reset_parser.add_argument("--no-backup", action="store_true", 
                             help="Skip creating backup")
    reset_parser.add_argument("--no-regenerate", action="store_true",
                             help="Don't regenerate sample data")
    
    # Backup commands
    backup_parser = subparsers.add_parser("backup", help="Backup management")
    backup_subparsers = backup_parser.add_subparsers(dest="backup_action")
    
    create_parser = backup_subparsers.add_parser("create", help="Create backup")
    create_parser.add_argument("--name", help="Backup name")
    
    list_parser = backup_subparsers.add_parser("list", help="List backups")
    
    restore_parser = backup_subparsers.add_parser("restore", help="Restore backup")
    restore_parser.add_argument("name", help="Backup name to restore")
    
    delete_parser = backup_subparsers.add_parser("delete", help="Delete backup")
    delete_parser.add_argument("name", help="Backup name to delete")
    
    # Status command
    subparsers.add_parser("status", help="Show system status")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean up system")
    clean_parser.add_argument("--keep-backups", action="store_true",
                             help="Keep backup files")
    clean_parser.add_argument("--keep-data", action="store_true",
                             help="Keep sample data files")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize reset manager
    reset_manager = ResetManager(
        Path(args.db_path),
        Path(args.data_path),
        Path(args.config_path)
    )
    
    try:
        if args.command == "reset":
            return handle_reset(reset_manager, args)
        elif args.command == "backup":
            return handle_backup(reset_manager, args)
        elif args.command == "status":
            return handle_status(reset_manager)
        elif args.command == "clean":
            return handle_clean(reset_manager, args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1

def handle_reset(reset_manager, args):
    """Handle reset operations"""
    create_backup = not args.no_backup
    regenerate_data = not args.no_regenerate
    
    print(f"Performing {args.type} reset...")
    
    if args.type == "full":
        results = reset_manager.full_reset(
            create_backup=create_backup,
            regenerate_data=regenerate_data
        )
        
        if results["errors"]:
            print(f"Reset completed with errors: {results['errors']}")
            return 1
        else:
            print("✅ Full system reset completed!")
            if results["backup_created"]:
                print(f"📦 Backup created: {results['backup_created']}")
            return 0
    
    elif args.type == "db":
        tables, records = reset_manager.reset_database()
        print(f"✅ Database reset: {tables} tables, {records} records cleared")
        return 0
    
    elif args.type == "data":
        files_removed = reset_manager.reset_sample_data(regenerate=regenerate_data)
        print(f"✅ Sample data reset: {files_removed} files removed")
        if regenerate_data:
            print("🔄 Sample data regenerated")
        return 0
    
    elif args.type == "config":
        if reset_manager.reset_config():
            print("✅ Config reset to defaults")
            return 0
        else:
            print("❌ Failed to reset config")
            return 1

def handle_backup(reset_manager, args):
    """Handle backup operations"""
    if args.backup_action == "create":
        backup_path = reset_manager.create_backup(args.name)
        print(f"✅ Backup created: {backup_path}")
        return 0
    
    elif args.backup_action == "list":
        backups = reset_manager.list_backups()
        if not backups:
            print("No backups found")
            return 0
        
        print("Available backups:")
        print("-" * 80)
        for backup in backups:
            print(f"Name: {backup['name']}")
            print(f"Created: {backup['created_at']}")
            print(f"Database: {'✅' if backup['db_exists'] else '❌'}")
            print(f"Files: {backup['data_files_count']}")
            print("-" * 80)
        return 0
    
    elif args.backup_action == "restore":
        if reset_manager.restore_backup(args.name):
            print(f"✅ Restored backup: {args.name}")
            return 0
        else:
            print(f"❌ Failed to restore backup: {args.name}")
            return 1
    
    elif args.backup_action == "delete":
        if reset_manager.delete_backup(args.name):
            print(f"✅ Deleted backup: {args.name}")
            return 0
        else:
            print(f"❌ Failed to delete backup: {args.name}")
            return 1
    
    else:
        print("Unknown backup action")
        return 1

def handle_status(reset_manager):
    """Handle status command"""
    status = reset_manager.get_system_status()
    
    print("System Status:")
    print("-" * 40)
    print(f"Database: {'✅ Exists' if status['database_exists'] else '❌ Missing'}")
    print(f"Database Size: {status['database_size'] / 1024:.1f} KB" if status['database_size'] > 0 else "0 KB")
    print(f"Data Files: {status['data_files_count']}")
    print(f"Config: {'✅ Exists' if status['config_exists'] else '❌ Missing'}")
    print(f"Backups: {status['backups_count']}")
    
    if status['last_modified']:
        print(f"Last Modified: {status['last_modified']}")
    
    return 0

def handle_clean(reset_manager, args):
    """Handle clean command"""
    print("Cleaning up system...")
    
    # Clean database
    if not args.keep_data:
        tables, records = reset_manager.reset_database()
        print(f"🗑️ Cleared database: {tables} tables, {records} records")
    
    # Clean sample data
    if not args.keep_data:
        files_removed = reset_manager.reset_sample_data(regenerate=False)
        print(f"🗑️ Removed {files_removed} sample data files")
    
    # Clean backups
    if not args.keep_backups:
        backups = reset_manager.list_backups()
        for backup in backups:
            reset_manager.delete_backup(backup['name'])
        print(f"🗑️ Removed {len(backups)} backup(s)")
    
    print("✅ System cleaned up")
    return 0

if __name__ == "__main__":
    sys.exit(main())
