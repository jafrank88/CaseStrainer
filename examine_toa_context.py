#!/usr/bin/env python3
"""
Examine ToA context to understand case name extraction issues from a real brief.
"""

import re
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import json

def extract_citation_contexts(pdf_path: str, window_size: int = 200) -> List[Dict]:
    """Extract text around citations with context.
    
    Args:
        pdf_path: Path to the PDF file
        window_size: Number of characters to include before and after citation
        
    Returns:
        List of dicts with citation and its context
    """
    doc = fitz.open(pdf_path)
    results = []
    
    # Common citation patterns
    citation_patterns = [
        r'\b\d+\s+Wn\.?\s*\d+[a-z]?\b',  # Washington Reports
        r'\b\d+\s+Wn\.?\s*2d\s+\d+\b',  # Washington Reports 2d
        r'\b\d+\s+Wash\.?\s*\d+\b',     # Washington Reports (alternate)
        r'\b\d+\s+Wash\.?\s*App\.?\s*\d+\b',  # Washington Appellate Reports
        r'\b\d+\s+U\.?\s*S\.?\s*\d+\b',  # US Reports
        r'\b\d+\s+S\.?\s*Ct\.?\s*\d+\b',  # Supreme Court Reporter
    ]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        for pattern in citation_patterns:
            for match in re.finditer(pattern, text):
                start = max(0, match.start() - window_size)
                end = min(len(text), match.end() + window_size)
                context = text[start:end]
                
                # Try to find the case name before the citation
                preceding_text = text[max(0, match.start() - 300):match.start()]
                case_name = extract_case_name(preceding_text, match.group(0))
                
                results.append({
                    'citation': match.group(0),
                    'page': page_num + 1,
                    'context': context,
                    'case_name': case_name,
                    'preceding_text': preceding_text[-100:],  # Last 100 chars before citation
                })
    
    doc.close()
    return results

def extract_case_name(text: str, citation: str) -> str:
    """Extract case name from text preceding a citation."""
    # Look for patterns like "State v. Smith, 123 Wn.2d 456"
    patterns = [
        r'([A-Z][A-Za-z0-9&.,\'\- ]+?\sv\.\s+[A-Z][A-Za-z0-9&.,\'\- ]+?)\s*,\s*' + re.escape(citation),
        r'(In\s+re\s+[A-Z][A-Za-z0-9&.,\'\- ]+?)\s*,\s*' + re.escape(citation),
        r'([A-Z][A-Za-z0-9&.,\'\- ]+?\sv\.\s+[A-Z][A-Za-z0-9&.,\'\- ]+?)\s+' + re.escape(citation),
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    
    return ""

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