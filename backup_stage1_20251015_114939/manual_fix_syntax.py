"""
Manual fix for syntax errors in unified_citation_processor_v2.py
"""

import shutil
import os

file_path = r'src\unified_citation_processor_v2.py'
backup_path = r'src\unified_citation_processor_v2.py.backup'

# Create backup
shutil.copy2(file_path, backup_path)
print(f"✓ Created backup: {backup_path}")

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Fix 1: Remove incomplete if statement at line 2603 (index 2602)
# The if statement has no body, so we need to either add a pass or remove it
# Looking at the context, it seems like dead code that should be removed

# Fix 2: Remove orphaned code starting around line 2626

# Let's identify the exact lines to fix
print("\nLine 2603:", lines[2602].rstrip() if len(lines) > 2602 else "N/A")
print("Line 2604:", lines[2603].rstrip() if len(lines) > 2603 else "N/A")
print("Line 2625:", lines[2624].rstrip() if len(lines) > 2624 else "N/A")
print("Line 2626:", lines[2625].rstrip() if len(lines) > 2625 else "N/A")

# Strategy: Remove lines 2603 and 2626 onwards (the orphaned code)
new_lines = []
skip_mode = False

for i, line in enumerate(lines):
    line_num = i + 1
    
    # Skip line 2603 (the incomplete if statement)
    if line_num == 2603:
        print(f"Removing line {line_num}: {line.rstrip()}")
        continue
    
    # Start skipping at line 2626 (orphaned code after return)
    if line_num == 2626:
        skip_mode = True
        print(f"Starting skip at line {line_num}")
    
    # Stop skipping when we hit a line with proper indentation (function/class def)
    if skip_mode:
        # Check if this line starts a new function or has minimal indentation
        stripped = line.lstrip()
        indent_len = len(line) - len(stripped)
        
        # If we hit a line with 4 or fewer spaces (or a def/class), stop skipping
        if indent_len <= 4 and stripped and not stripped.startswith('#'):
            print(f"Ending skip at line {line_num}: {line.rstrip()}")
            skip_mode = False
        else:
            if line.strip():  # Only log non-empty lines
                print(f"Skipping line {line_num}: {line.rstrip()}")
            continue
    
    new_lines.append(line)

# Write fixed file
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✓ Fixed! Removed {len(lines) - len(new_lines)} lines")
print(f"Original: {len(lines)} lines")
print(f"New: {len(new_lines)} lines")
print(f"\nBackup saved to: {backup_path}")
