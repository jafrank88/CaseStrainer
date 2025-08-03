#!/usr/bin/env python3
"""
Test File Safeguard Script
Moves test files to a safe location to prevent them from running in production
"""

import os
import shutil
import glob
from datetime import datetime

def safeguard_test_files():
    """Move test files to a safe location"""
    
    # Create backup directory
    backup_dir = "archived_test_files"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_dir}_{timestamp}"
    
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    
    print(f"🔒 Moving test files to: {backup_path}")
    
    # Test file patterns to move
    test_patterns = [
        "test_*.py",
        "*_test.py",
        "test_*_production*.py",
        "*_production_test*.py"
    ]
    
    moved_files = []
    
    for pattern in test_patterns:
        files = glob.glob(pattern)
        for file_path in files:
            if os.path.isfile(file_path):
                try:
                    # Create subdirectory structure
                    file_dir = os.path.dirname(file_path)
                    if file_dir:
                        backup_subdir = os.path.join(backup_path, file_dir)
                        if not os.path.exists(backup_subdir):
                            os.makedirs(backup_subdir)
                        dest_path = os.path.join(backup_subdir, os.path.basename(file_path))
                    else:
                        dest_path = os.path.join(backup_path, os.path.basename(file_path))
                    
                    # Move the file
                    shutil.move(file_path, dest_path)
                    moved_files.append((file_path, dest_path))
                    print(f"  📁 Moved: {file_path} -> {dest_path}")
                    
                except Exception as e:
                    print(f"  ❌ Failed to move {file_path}: {e}")
    
    # Create a README in the backup directory
    readme_content = f"""# Test Files Archive

This directory contains test files that were moved to prevent them from running in production.

Moved on: {datetime.now().isoformat()}
Total files moved: {len(moved_files)}

## Files moved:
"""
    
    for src, dest in moved_files:
        readme_content += f"- {src} -> {dest}\n"
    
    readme_path = os.path.join(backup_path, "README.md")
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"\n✅ Safeguard complete!")
    print(f"   Files moved: {len(moved_files)}")
    print(f"   Backup location: {backup_path}")
    print(f"   README created: {readme_path}")
    
    return moved_files

def create_test_file_guard():
    """Create a guard file to prevent test execution"""
    
    guard_content = """#!/usr/bin/env python3
\"\"\"
Test Execution Guard
This file prevents test files from being executed in production
\"\"\"

import sys
import os

def block_test_execution():
    \"\"\"Block test execution in production\"\"\"
    print("Test execution blocked in production environment")
    print("   Please run tests in a development environment")
    sys.exit(1)

# Check if we're in production
if os.getenv('FLASK_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production':
    block_test_execution()

# Check for test files in current directory
test_files = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]
if test_files:
    print(f"Test files detected: {test_files}")
    print("   Consider moving them to a test directory")
"""
    
    guard_path = "test_execution_guard.py"
    with open(guard_path, 'w') as f:
        f.write(guard_content)
    
    print(f"🛡️  Created test execution guard: {guard_path}")
    return guard_path

if __name__ == "__main__":
    print("🔒 CaseStrainer Test File Safeguard")
    print("=" * 50)
    
    # Move test files
    moved_files = safeguard_test_files()
    
    print("\n" + "=" * 50)
    
    # Create guard file
    guard_path = create_test_file_guard()
    
    print("\n" + "=" * 50)
    print("✅ Safeguard setup complete!")
    print("   Test files have been moved to prevent production interference")
    print("   Test execution guard has been created")
    print("\n   To restore test files for development:")
    print(f"   - Check the backup directory: {moved_files[0][1].split('_')[0]}_*")
    print("   - Move files back to their original locations") 