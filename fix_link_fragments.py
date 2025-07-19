#!/usr/bin/env python3
"""
Fix Link Fragment Issues in Markdown Files
Addresses MD051 markdownlint issues by ensuring table of contents links match actual headings.
"""

import re
import os
from pathlib import Path

def extract_headings(markdown_content):
    """Extract all headings from markdown content."""
    
    headings = []
    lines = markdown_content.split('\n')
    
    for line in lines:
        # Match headings (## Heading Name)
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if match:
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            
            # Create anchor link
            anchor = create_anchor_link(heading_text)
            
            headings.append({
                'level': level,
                'text': heading_text,
                'anchor': anchor,
                'line': line
            })
    
    return headings

def create_anchor_link(text):
    """Create a valid anchor link from heading text."""
    
    # Convert to lowercase
    anchor = text.lower()
    
    # Replace spaces and special characters with hyphens
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = re.sub(r'[-\s]+', '-', anchor)
    
    # Remove leading/trailing hyphens
    anchor = anchor.strip('-')
    
    return anchor

def fix_table_of_contents(markdown_content):
    """Fix table of contents to match actual headings."""
    
    lines = markdown_content.split('\n')
    fixed_lines = []
    in_toc = False
    toc_start = -1
    toc_end = -1
    
    # Find table of contents section
    for i, line in enumerate(lines):
        if re.match(r'^##\s+Table of Contents', line, re.IGNORECASE):
            in_toc = True
            toc_start = i
            fixed_lines.append(line)
            continue
        
        if in_toc:
            # Check if we've reached the end of TOC (empty line or next heading)
            if line.strip() == '' or re.match(r'^##\s+', line):
                toc_end = i
                in_toc = False
                fixed_lines.append(line)
                continue
            
            # Fix TOC links
            if re.match(r'^\d+\.\s*\[', line):
                # Extract link text and fix anchor
                match = re.match(r'^\d+\.\s*\[([^\]]+)\]\(#([^)]+)\)', line)
                if match:
                    link_text = match.group(1)
                    old_anchor = match.group(2)
                    
                    # Create new anchor from link text
                    new_anchor = create_anchor_link(link_text)
                    
                    # Replace the link
                    new_line = re.sub(r'\(#[^)]+\)', f'(#{new_anchor})', line)
                    fixed_lines.append(new_line)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def validate_link_fragments(markdown_content):
    """Validate that all link fragments point to valid headings."""
    
    # Extract all headings
    headings = extract_headings(markdown_content)
    heading_anchors = {h['anchor'] for h in headings}
    
    # Find all link fragments
    link_fragments = re.findall(r'\[([^\]]+)\]\(#([^)]+)\)', markdown_content)
    
    issues = []
    for link_text, fragment in link_fragments:
        if fragment not in heading_anchors:
            issues.append({
                'link_text': link_text,
                'fragment': fragment,
                'suggested': create_anchor_link(link_text)
            })
    
    return issues

def fix_markdown_file(file_path):
    """Fix link fragment issues in a markdown file."""
    
    print(f"📄 Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix table of contents
        content = fix_table_of_contents(content)
        
        # Validate link fragments
        issues = validate_link_fragments(content)
        
        if issues:
            print(f"   ⚠️  Found {len(issues)} link fragment issues:")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"      - '{issue['link_text']}' -> #{issue['fragment']} (suggested: #{issue['suggested']})")
            if len(issues) > 5:
                print(f"      ... and {len(issues) - 5} more")
        else:
            print(f"   ✅ No link fragment issues found")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ Fixed table of contents in {file_path}")
        else:
            print(f"   ℹ️  No changes needed in {file_path}")
            
    except Exception as e:
        print(f"   ❌ Error fixing {file_path}: {e}")

def main():
    """Main function to fix link fragment issues."""
    
    print("🔗 FIXING LINK FRAGMENT ISSUES")
    print("=" * 60)
    
    # Fix the consolidated documentation
    fix_markdown_file("CONSOLIDATED_DOCUMENTATION.md")
    
    # Also check other large documentation files
    large_docs = [
        "README.md",
        "SECURITY_IMPROVEMENTS_SUMMARY.md",
        "DOCUMENTATION_QUALITY_REPORT.md"
    ]
    
    for doc_file in large_docs:
        if os.path.exists(doc_file):
            fix_markdown_file(doc_file)
    
    print(f"\n✅ LINK FRAGMENT FIXES COMPLETE!")
    print("=" * 60)
    print("Next steps:")
    print("1. Review the fixed table of contents")
    print("2. Test link navigation")
    print("3. Commit documentation improvements")

if __name__ == "__main__":
    main() 