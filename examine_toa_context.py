#!/usr/bin/env python3
"""
Examine ToA context to understand case name extraction issues from a real brief.
"""

import re
from pathlib import Path
from typing import List, Set

# Use pdfminer.six for PDF extraction
from io import StringIO
from pdfminer.high_level import extract_text

def extract_toa_section(text):
    """
    Extract the Table of Authorities section from the text.
    """
    toa_pattern = r'TABLE OF AUTHORITIES'
    toa_match = re.search(toa_pattern, text, re.IGNORECASE)
    if not toa_match:
        return None
    toa_start = toa_match.start()
    section_patterns = [
        r'\n\s*I\.\s*[A-Z\s]+\n',
        r'\n\s*II\.\s*[A-Z\s]+\n',
        r'\n\s*III\.\s*[A-Z\s]+\n',
        r'\n\s*IV\.\s*[A-Z\s]+\n',
        r'\n\s*V\.\s*[A-Z\s]+\n',
        r'\n\s*VI\.\s*[A-Z\s]+\n',
        r'\n\s*VII\.\s*[A-Z\s]+\n',
        r'\n\s*VIII\.\s*[A-Z\s]+\n',
        r'\n\s*IX\.\s*[A-Z\s]+\n',
        r'\n\s*X\.\s*[A-Z\s]+\n',
        r'\n\s*CONCLUSION\s*\n',
        r'\n\s*ARGUMENT\s*\n',
        r'\n\s*INTRODUCTION\s*\n',
    ]
    toa_end = len(text)
    for pattern in section_patterns:
        match = re.search(pattern, text[toa_start:])
        if match:
            potential_end = toa_start + match.start()
            if potential_end > toa_start:
                toa_end = potential_end
                break
    return text[toa_start:toa_end]

def extract_case_names(text: str) -> Set[str]:
    # Remove headers/footers and blank lines
    lines = [line for line in text.split('\n') if line.strip()]
    # Remove lines that are section headers
    skip_headers = [
        'TABLE OF AUTHORITIES', 'State Cases', 'Federal Cases', 'Statutes', 'Other Authorities',
        'Cases', 'Authorities', 'Constitution', 'Rules', 'Regulations', 'Treatises', 'Secondary Sources'
    ]
    filtered_lines = [line for line in lines if not any(h in line for h in skip_headers)]
    # Regex for case names: e.g., State v. Blake
    case_v_pattern = r'([A-Z][A-Za-z\s&,\.]+)\s+v\.\s+([A-Z][A-Za-z\s&,\.]+)'
    names = set()
    for line in filtered_lines:
        for match in re.finditer(case_v_pattern, line):
            first_party = match.group(1).strip()
            second_party = match.group(2).strip().rstrip(',')
            case_name = f"{first_party} v. {second_party}"
            names.add(case_name)
    return names

def main():
    briefs_dir = Path("wa_briefs_text")
    if not briefs_dir.exists():
        print("wa_briefs_text directory not found!")
        return
    brief_files = sorted(list(briefs_dir.glob("*.txt")))[:10]
    if not brief_files:
        print("No .txt brief files found in wa_briefs_text directory!")
        return
    for brief_file in brief_files:
        print(f"\n=== Analyzing: {brief_file.name} ===")
        text = brief_file.read_text(encoding="utf-8")
        toa_section = extract_toa_section(text)
        if not toa_section:
            print("No ToA section found in this brief.")
            continue
        # ToA case names
        toa_names = extract_case_names(toa_section)
        # Non-ToA (body) case names
        body_start = toa_section and text.find(toa_section) + len(toa_section) or 0
        body_text = text[body_start:]
        body_names = extract_case_names(body_text)
        # Only show ToA names not found in body
        mismatches = [name for name in toa_names if name not in body_names]
        if not mismatches:
            print("All ToA case names found in body.")
            continue
        print(f"ToA case names NOT found in body ({len(mismatches)}):")
        for name in mismatches:
            print(f"  {name}")
            # Show context: find the line in ToA section
            for line in toa_section.split('\n'):
                if name in line:
                    print(f"    Context: {line.strip()}")
                    break

if __name__ == "__main__":
    main() 