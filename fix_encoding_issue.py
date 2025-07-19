#!/usr/bin/env python3
"""
Fix Encoding Issues in Markdown Files
"""

import os

def fix_encoding_issue(file_path):
    """Fix encoding issues in a markdown file."""
    
    print(f"🔧 FIXING ENCODING ISSUE")
    print("=" * 50)
    print(f"📄 Processing: {file_path}")
    
    try:
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        content = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                used_encoding = encoding
                print(f"   ✅ Successfully read with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print(f"   ❌ Could not read file with any encoding")
            return False
        
        # Write back with UTF-8 encoding
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Fixed encoding and saved as UTF-8")
        return True
        
    except Exception as e:
        print(f"   ❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Main function to fix encoding issues."""
    
    print("🔧 ENCODING ISSUE FIXES")
    print("=" * 60)
    
    # Fix the problematic file
    success = fix_encoding_issue("docs/CITATION_PROCESSING_FLOWCHART.md")
    
    if success:
        print(f"\n✅ ENCODING FIX COMPLETE!")
        print("=" * 60)
        print("Next steps:")
        print("1. Run markdown linting fix again")
        print("2. Verify all files are processed")
        print("3. Commit fixes")
    else:
        print(f"\n❌ ENCODING FIX FAILED!")
        print("=" * 60)
        print("Manual intervention may be required")

if __name__ == "__main__":
    main() 