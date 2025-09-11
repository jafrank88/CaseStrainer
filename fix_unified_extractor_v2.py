#!/usr/bin/env python3
"""
Script to fix the indentation issue in unified_case_name_extractor.py
"""

def fix_unified_extractor():
    """Fix the indentation issue in the unified case name extractor"""
    
    # Read the file
    with open('src/unified_case_name_extractor.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and fix the problematic lines
    for i, line in enumerate(lines):
        if '🚨 FIX: Use much larger context window' in line:
            print(f"Found problematic line {i+1}: {line.strip()}")
            # Fix the indentation
            lines[i] = '        # 🚨 FIX: Use much larger context window to ensure we capture full case names\n'
            print(f"Fixed line {i+1}")
        elif 'Previous: base_window = 300, max_window = 500' in line:
            print(f"Found problematic line {i+1}: {line.strip()}")
            # Fix the indentation
            lines[i] = '        # Previous: base_window = 300, max_window = 500 (too small!)\n'
            print(f"Fixed line {i+1}")
        elif 'New: base_window = 800, max_window = 1000' in line:
            print(f"Found problematic line {i+1}: {line.strip()}")
            # Fix the indentation
            lines[i] = '        # New: base_window = 800, max_window = 1000 (much better!)\n'
            print(f"Fixed line {i+1}")
        elif 'base_window = 800' in line and '          ' in line:
            print(f"Found problematic line {i+1}: {line.strip()}")
            # Fix the indentation
            lines[i] = '        base_window = 800\n'
            print(f"Fixed line {i+1}")
        elif 'max_window = 1000' in line and '          ' in line:
            print(f"Found problematic line {i+1}: {line.strip()}")
            # Fix the indentation
            lines[i] = '        max_window = 1000\n'
            print(f"Fixed line {i+1}")
    
    # Write the fixed content back
    with open('src/unified_case_name_extractor.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ File has been fixed")

if __name__ == "__main__":
    fix_unified_extractor()

