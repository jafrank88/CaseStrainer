#!/usr/bin/env python3
"""
Fix Markdown Linting Issues
Automatically fixes common markdownlint issues in documentation files.
"""

import re
import os
from pathlib import Path

def fix_markdown_linting(file_path):
    """Fix common markdownlint issues in a markdown file."""
    
    print(f"📄 Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            current_line = line
            
            # Fix MD009: Remove trailing spaces (except for intentional 2-space line breaks)
            if current_line.endswith(' ') and not current_line.endswith('  '):
                current_line = current_line.rstrip()
            
            # Fix MD022: Add blank lines around headings
            if re.match(r'^#{1,6}\s+', current_line):
                # Add blank line before heading if not at start and previous line is not blank
                if i > 0 and lines[i-1].strip() != '':
                    fixed_lines.append('')
                fixed_lines.append(current_line)
                # Add blank line after heading if not at end and next line is not blank
                if i < len(lines) - 1 and lines[i+1].strip() != '':
                    fixed_lines.append('')
            else:
                fixed_lines.append(current_line)
        
        # Fix MD032: Add blank lines around lists
        final_lines = []
        for i, line in enumerate(fixed_lines):
            current_line = line
            
            # Check if this is a list item
            if re.match(r'^[\s]*[-*+]\s+', current_line) or re.match(r'^[\s]*\d+\.\s+', current_line):
                # Add blank line before list if previous line is not blank and not a list item
                if i > 0 and not re.match(r'^[\s]*[-*+]\s+', fixed_lines[i-1]) and not re.match(r'^[\s]*\d+\.\s+', fixed_lines[i-1]) and fixed_lines[i-1].strip() != '':
                    final_lines.append('')
                final_lines.append(current_line)
                # Add blank line after list if next line is not blank and not a list item
                if i < len(fixed_lines) - 1 and not re.match(r'^[\s]*[-*+]\s+', fixed_lines[i+1]) and not re.match(r'^[\s]*\d+\.\s+', fixed_lines[i+1]) and fixed_lines[i+1].strip() != '':
                    final_lines.append('')
            else:
                final_lines.append(current_line)
        
        # Fix MD031: Add blank lines around fenced code blocks
        content = '\n'.join(final_lines)
        content = re.sub(r'([^\n])\n```', r'\1\n\n```', content)
        content = re.sub(r'```\n([^\n])', r'```\n\n\1', content)
        
        # Fix MD040: Add language specification to fenced code blocks
        content = re.sub(r'```\n', r'```text\n', content)
        
        # Fix MD024: Resolve duplicate headings by adding numbers
        heading_counts = {}
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if re.match(r'^#{1,6}\s+', line):
                heading_text = re.sub(r'^#{1,6}\s+', '', line)
                if heading_text in heading_counts:
                    heading_counts[heading_text] += 1
                    # Add number to duplicate heading
                    level = len(re.match(r'^(#{1,6})', line).group(1))
                    line = '#' * level + ' ' + heading_text + f' ({heading_counts[heading_text]})'
                else:
                    heading_counts[heading_text] = 1
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Fix MD047: Ensure file ends with single newline
        content = content.rstrip() + '\n'
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ Fixed markdownlint issues in {file_path}")
            
            # Count the types of fixes made
            fixes_made = []
            if content != original_content:
                fixes_made.append("formatting")
            if re.search(r'```text\n', content):
                fixes_made.append("code block language")
            if re.search(r'\(\d+\)', content):
                fixes_made.append("duplicate headings")
            
            print(f"   📊 Fixes applied: {', '.join(fixes_made)}")
        else:
            print(f"   ℹ️  No markdownlint issues found in {file_path}")
            
    except Exception as e:
        print(f"   ❌ Error fixing {file_path}: {e}")

def run_markdownlint_check(file_path):
    """Run markdownlint to check for remaining issues."""
    
    try:
        import subprocess
        
        # Run markdownlint
        result = subprocess.run([
            "markdownlint", file_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ No markdownlint issues found!")
        else:
            print(f"   ⚠️  Remaining issues:")
            print(result.stdout)
            
    except FileNotFoundError:
        print(f"   ℹ️  markdownlint not found, skipping check")
    except Exception as e:
        print(f"   ❌ Error running markdownlint: {e}")

def find_markdown_files():
    """Find all markdown files in the project."""
    
    markdown_files = []
    
    # Get all .md files in current directory
    for file in Path('.').glob('*.md'):
        if file.name not in ['CONSOLIDATED_DOCUMENTATION.md']:  # Skip the large consolidated file
            markdown_files.append(str(file))
    
    # Get all .md files in docs directory if it exists
    docs_dir = Path('docs')
    if docs_dir.exists():
        for file in docs_dir.glob('**/*.md'):
            markdown_files.append(str(file))
    
    return markdown_files

def main():
    """Main function to fix markdownlint issues."""
    
    print("📝 MARKDOWN LINTING FIXES")
    print("=" * 60)
    
    # Find all markdown files
    markdown_files = find_markdown_files()
    
    print(f"🔧 FIXING MARKDOWN LINTING ISSUES")
    print("=" * 50)
    print(f"Found {len(markdown_files)} markdown files to process")
    
    # Fix each markdown file
    for file_path in markdown_files:
        fix_markdown_linting(file_path)
    
    # Check for remaining issues
    print(f"\n🔍 RUNNING MARKDOWNLINT CHECK")
    print("=" * 50)
    
    for file_path in markdown_files:
        print(f"\nChecking: {file_path}")
        run_markdownlint_check(file_path)
    
    print(f"\n✅ MARKDOWN LINTING FIXES COMPLETE!")
    print("=" * 60)
    print("Next steps:")
    print("1. Review the fixed documentation")
    print("2. Test markdown rendering")
    print("3. Commit documentation improvements")

if __name__ == "__main__":
    main() 