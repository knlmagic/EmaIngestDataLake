# EMA Demo Reset Features

## Overview

The EMA Demo app now includes comprehensive reset functionality to support demo scenarios, testing, and system management. This document outlines the new features and how to use them.

## New Features

### 1. **Multi-Level Reset Options**

#### Full Reset
- Clears database completely
- Regenerates sample data
- Resets configuration to defaults
- Optional backup creation

#### Database Only Reset
- Clears all database tables and records
- Preserves sample data files
- Preserves configuration

#### Sample Data Only Reset
- Removes existing sample data files
- Regenerates fresh sample data
- Preserves database and configuration

#### Config Only Reset
- Resets configuration to default values
- Preserves database and sample data

### 2. **Backup & Restore System**

#### Automatic Backups
- Created before full resets (optional)
- Timestamped backup names
- Includes database, config, and sample data

#### Manual Backups
- Create backups on-demand
- Custom backup names
- Full system state preservation

#### Backup Management
- List all available backups
- Restore from any backup
- Delete old backups
- Backup metadata tracking

### 3. **Enhanced UI Controls**

#### Sidebar Reset Panel
- Reset type selection
- Backup creation option
- System status metrics
- One-click reset execution

#### Backup Management Tab
- Visual backup listing
- Backup actions (restore/delete)
- Manual backup creation
- System information display

### 4. **Command-Line Interface**

#### Reset Operations
```bash
# Full system reset with backup
python reset_demo.py reset --type full

# Database only reset
python reset_demo.py reset --type db

# Sample data reset without regeneration
python reset_demo.py reset --type data --no-regenerate

# Reset without backup
python reset_demo.py reset --type full --no-backup
```

#### Backup Management
```bash
# Create backup
python reset_demo.py backup create --name "demo_state_v1"

# List backups
python reset_demo.py backup list

# Restore backup
python reset_demo.py backup restore backup_20250101_120000

# Delete backup
python reset_demo.py backup delete old_backup
```

#### System Management
```bash
# Show system status
python reset_demo.py status

# Clean up system
python reset_demo.py clean

# Clean but keep backups
python reset_demo.py clean --keep-backups
```

## Demo Scenarios

### Scenario 1: Fresh Demo Start
```bash
# Clean slate for new demo
python reset_demo.py reset --type full
streamlit run app.py
```

### Scenario 2: Reset After Demo
```bash
# Reset for next demo with backup
python reset_demo.py reset --type full
# or use UI: Sidebar → Reset Options → Full Reset → Create backup ✓
```

### Scenario 3: Test Different Configurations
```bash
# Backup current state
python reset_demo.py backup create --name "working_config"

# Test new configuration
python reset_demo.py reset --type config
# Modify config.json
streamlit run app.py

# Restore if needed
python reset_demo.py backup restore working_config
```

### Scenario 4: Clean Development Environment
```bash
# Clean everything for fresh start
python reset_demo.py clean
```

## File Structure

```
├── pipeline/
│   └── reset_manager.py          # Core reset functionality
├── backups/                      # Backup storage directory
│   ├── backup_20250101_120000/   # Timestamped backups
│   │   ├── ema_demo.sqlite
│   │   ├── config.json
│   │   ├── data_lake/
│   │   └── backup_metadata.json
│   └── custom_backup_name/
├── reset_demo.py                 # Command-line utility
└── app.py                        # Enhanced with reset UI
```

## Technical Implementation

### ResetManager Class
- **create_backup()**: Creates timestamped or named backups
- **restore_backup()**: Restores from backup
- **reset_database()**: Clears all database tables
- **reset_sample_data()**: Manages sample data files
- **reset_config()**: Resets configuration
- **full_reset()**: Orchestrates complete system reset
- **get_system_status()**: Provides system information

### Error Handling
- Comprehensive exception handling
- Graceful degradation
- Detailed error messages
- Rollback capabilities

### Logging
- Structured logging for all operations
- Error tracking and debugging
- Operation audit trail

## Best Practices

### For Demo Presentations
1. **Always create backups** before major resets
2. **Test reset functionality** before live demos
3. **Use descriptive backup names** for different demo states
4. **Keep recent backups** for quick recovery

### For Development
1. **Use command-line tools** for automation
2. **Clean environment regularly** to avoid state issues
3. **Document backup purposes** in backup names
4. **Monitor system status** regularly

### For Testing
1. **Test all reset types** before deployment
2. **Verify backup/restore** functionality
3. **Test error scenarios** (missing files, permissions)
4. **Validate data integrity** after resets

## Troubleshooting

### Common Issues

#### Reset Fails
- Check file permissions
- Ensure no processes are using database
- Verify disk space availability

#### Backup/Restore Issues
- Check backup directory permissions
- Verify backup integrity
- Ensure sufficient disk space

#### UI Not Updating
- Refresh browser page
- Check Streamlit logs
- Restart Streamlit server

### Recovery Procedures

#### If Reset Fails Mid-Process
1. Check system status: `python reset_demo.py status`
2. Restore from latest backup if available
3. Manual cleanup if necessary

#### If Database is Corrupted
1. Delete database file
2. Restore from backup
3. Or perform full reset

#### If Sample Data is Missing
1. Use "Sample Data Only" reset
2. Or restore from backup
3. Or manually run sample generation

## Future Enhancements

### Planned Features
- **Selective document type resets** (PO/Invoice/GRN only)
- **Backup compression** for space efficiency
- **Remote backup storage** (S3, etc.)
- **Automated backup scheduling**
- **Reset operation logging** to database
- **Batch operations** for multiple resets

### Integration Opportunities
- **CI/CD pipeline integration** for automated testing
- **Docker container reset** capabilities
- **Cloud deployment reset** automation
- **Multi-environment management**

## Conclusion

The reset functionality transforms the EMA Demo from a static application into a dynamic, demo-ready system that can be quickly reset, backed up, and restored for various presentation and testing scenarios. This makes it ideal for:

- **Live demonstrations** with consistent starting points
- **Development testing** with clean environments
- **Training sessions** with repeatable scenarios
- **System maintenance** with safe backup/restore operations

The combination of UI controls and command-line tools provides flexibility for different use cases while maintaining ease of use for demo scenarios.
