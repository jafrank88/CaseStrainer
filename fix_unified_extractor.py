#!/usr/bin/env python3
"""
Script to fix the indentation issue in unified_case_name_extractor.py
"""

def fix_unified_extractor():
    """Fix the indentation issue in the unified case name extractor"""
    
    # Read the file
    with open('src/unified_case_name_extractor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the problematic section
    old_section = '''        """
        Get optimized context for extraction using best practices from all systems
        """
                  # 🚨 FIX: Use much larger context window to ensure we capture full case names          # Previous: base_window = 300, max_window = 500 (too small!)                           
          # New: base_window = 800, max_window = 1000 (much better!)
          base_window = 800
          max_window = 1000'''
    
    new_section = '''        """
        Get optimized context for extraction using best practices from all systems
        """
        # 🚨 FIX: Use much larger context window to ensure we capture full case names
        # Previous: base_window = 300, max_window = 500 (too small!)
        # New: base_window = 800, max_window = 1000 (much better!)
        base_window = 800
        max_window = 1000'''
    
    # Replace the problematic section
    if old_section in content:
        content = content.replace(old_section, new_section)
        print("✅ Fixed the indentation issue")
    else:
        print("❌ Could not find the problematic section")
        return
    
    # Write the fixed content back
    with open('src/unified_case_name_extractor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ File has been fixed")

if __name__ == "__main__":
    fix_unified_extractor()
