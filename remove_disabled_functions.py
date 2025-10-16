"""
Remove DISABLED functions from progress_manager.py
"""

from pathlib import Path
import shutil
from datetime import datetime

def remove_disabled_functions():
    """Remove create_progress_routes_DISABLED and related code."""
    
    filepath = Path('src/progress_manager.py')
    
    # Create backup
    backup_path = Path(str(filepath) + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    shutil.copy2(filepath, backup_path)
    print(f"✓ Backup created: {backup_path}")
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the start of create_progress_routes_DISABLED (line 912, 0-indexed: 911)
    # Find the line before process_citation_task_direct (line 1520, so 1519 is blank, remove through 1518)
    
    start_line = None
    end_line = None
    
    for i, line in enumerate(lines):
        if 'def create_progress_routes_DISABLED' in line:
            start_line = i
            print(f"Found start at line {i+1}: {line[:50]}...")
        if start_line is not None and end_line is None and 'def process_citation_task_direct' in line:
            end_line = i - 1  # Line before this function
            print(f"Found end before line {i+1}")
            break
    
    if start_line is None or end_line is None:
        print("Error: Could not find DISABLED function boundaries")
        return False
    
    # Calculate lines to remove
    lines_to_remove = end_line - start_line + 1
    print(f"\nRemoving lines {start_line+1} to {end_line+1} ({lines_to_remove} lines)")
    
    # Remove the lines
    new_lines = lines[:start_line] + lines[end_line+1:]
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✓ Removed {lines_to_remove} lines")
    print(f"✓ File updated: {filepath}")
    print(f"\nOriginal lines: {len(lines)}")
    print(f"New lines: {len(new_lines)}")
    print(f"Removed: {len(lines) - len(new_lines)}")
    
    return True

if __name__ == '__main__':
    print("="*80)
    print("REMOVING DISABLED FUNCTIONS FROM PROGRESS_MANAGER.PY")
    print("="*80)
    print()
    
    success = remove_disabled_functions()
    
    if success:
        print("\n" + "="*80)
        print("SUCCESS - DISABLED functions removed")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("FAILED - Could not remove DISABLED functions")
        print("="*80)
