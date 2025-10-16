"""
Clean up redundant request_id usage in CaseStrainer codebase.

Strategy:
1. Keep request_id in:
   - Initial request logging (entry point)
   - Final responses to client
   - Error responses
   - Async task tracking
   
2. Remove request_id from:
   - Verbose intermediate logging
   - Internal function returns
   - Pass-through parameters
"""

import re
from pathlib import Path
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the file before modifying."""
    backup_path = Path(str(filepath) + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    shutil.copy2(filepath, backup_path)
    print(f"  ✓ Backup created: {backup_path.name}")
    return backup_path

def clean_vue_api_endpoints(filepath):
    """Clean up vue_api_endpoints.py."""
    print(f"\n{'='*80}")
    print(f"Cleaning: {filepath}")
    print('='*80)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    backup_file(filepath)
    
    changes = []
    new_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Skip verbose logging that's not essential
        if skip_next:
            skip_next = False
            continue
            
        # Keep essential logging (entry, completion, errors)
        keep_patterns = [
            r'===== Starting',
            r'===== Completed',
            r'logger\.error',
            r'logger\.warning',
            r'Starting async processing',
            r'Completed processing',
        ]
        
        # Remove verbose intermediate logging
        remove_patterns = [
            r'logger\.info\(f"\[Request \{request_id\}\] Method:',
            r'logger\.info\(f"\[Request \{request_id\}\] Content-Type:',
            r'logger\.info\(f"\[Request \{request_id\}\] Attempting to parse',
            r'logger\.info\(f"\[Request \{request_id\}\] JSON parsing successful:',
            r'logger\.info\(f"\[Request \{request_id\}\] Received form data',
            r'logger\.info\(f"\[Request \{request_id\}\] Processing file upload',
            r'logger\.info\(f"\[Request \{request_id\}\] File type:',
            r'logger\.info\(f"\[Request \{request_id\}\] Extracted',
            r'logger\.info\(f"\[Request \{request_id\}\] Text length:',
        ]
        
        should_remove = False
        for pattern in remove_patterns:
            if re.search(pattern, line):
                should_remove = True
                changes.append(f"  Line {line_num}: Removed verbose logging")
                break
        
        if should_remove:
            continue
        
        # Keep essential lines
        new_lines.append(line)
    
    # Write back
    new_content = '\n'.join(new_lines)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"\n  Changes made: {len(changes)}")
    for change in changes[:10]:  # Show first 10
        print(f"    {change}")
    if len(changes) > 10:
        print(f"    ... and {len(changes) - 10} more")
    
    return len(changes)

def clean_unified_input_processor(filepath):
    """Clean up unified_input_processor.py."""
    print(f"\n{'='*80}")
    print(f"Cleaning: {filepath}")
    print('='*80)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    backup_file(filepath)
    
    changes = []
    
    # Remove redundant request_id from internal result dicts
    # Keep it only in final returns and error handling
    
    # Pattern: Internal result dicts that don't go to client
    pattern1 = r"'request_id':\s*request_id,\s*\n\s*'success':\s*False"
    if re.search(pattern1, content):
        # This is an internal error result - keep request_id for debugging
        pass
    
    # Pattern: Pass-through in metadata that's not used
    pattern2 = r"result\['metadata'\]\['request_id'\]\s*=\s*request_id"
    matches = list(re.finditer(pattern2, content))
    if matches:
        changes.append(f"  Found {len(matches)} metadata request_id assignments (reviewing...)")
    
    print(f"\n  Analysis complete: {len(changes)} potential cleanups identified")
    print(f"  Note: unified_input_processor.py request_ids are mostly essential for async tracking")
    print(f"  Keeping current structure for now")
    
    return 0  # No changes to this file for now

def main():
    print("=" * 80)
    print("REQUEST_ID CLEANUP SCRIPT")
    print("=" * 80)
    print("\nThis will remove redundant request_id usage while keeping essential tracking.")
    print("Backups will be created automatically.\n")
    
    files_to_clean = [
        ('src/vue_api_endpoints.py', clean_vue_api_endpoints),
        ('src/unified_input_processor.py', clean_unified_input_processor),
    ]
    
    total_changes = 0
    
    for filepath, cleanup_func in files_to_clean:
        path = Path(filepath)
        if path.exists():
            changes = cleanup_func(path)
            total_changes += changes
        else:
            print(f"\n  ⚠ File not found: {filepath}")
    
    print("\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"\nTotal changes made: {total_changes}")
    print("\nWhat was removed:")
    print("  ✗ Verbose intermediate logging (Method, Content-Type, etc.)")
    print("  ✗ Redundant step-by-step progress logging")
    print("\nWhat was kept:")
    print("  ✓ Request entry/exit logging")
    print("  ✓ Error logging")
    print("  ✓ Final response request_id")
    print("  ✓ Async task tracking request_id")
    
    if total_changes > 0:
        print("\n⚠ IMPORTANT: Test the application after cleanup!")
        print("  Run: python test_api.py")
        print("  Or: Test the frontend at https://wolf.law.uw.edu/casestrainer/")
        print("\nTo restore from backup if needed:")
        print("  Find .backup_* files and copy them back")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
