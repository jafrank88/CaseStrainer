#!/usr/bin/env python3
"""
Clean citations for web search by:
1. Removing all ShortCaseCitations
2. Extracting citation text from FullCaseCitations (text between first single quotes)
3. Normalizing "Wn." to "Wash."
4. Deduplicating results
"""

import re
from typing import List, Set

def extract_citation_from_fullcase(fullcase_line: str) -> str:
    """Extract citation text from FullCaseCitation line (text between first single quotes)"""
    # Find text between first set of single quotes
    match = re.search(r"'([^']+)'", fullcase_line)
    if match:
        return match.group(1)
    return ""

def normalize_citation(citation: str) -> str:
    """Normalize citation by converting 'Wn.' to 'Wash.'"""
    return citation.replace("Wn.", "Wash.")

def clean_citations_for_websearch(input_file: str, output_file: str):
    """Clean citations for web search"""
    citations: Set[str] = set()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Skip ShortCaseCitations
            if line.startswith("ShortCaseCitation"):
                continue
                
            # Process FullCaseCitations
            if line.startswith("FullCaseCitation"):
                citation = extract_citation_from_fullcase(line)
                if citation:
                    normalized = normalize_citation(citation)
                    citations.add(normalized)
    
    # Write cleaned citations to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for citation in sorted(citations):
            f.write(f"{citation}\n")
    
    print(f"Cleaned citations saved to {output_file}")
    print(f"Total unique citations: {len(citations)}")
    
    # Show first few citations as preview
    print("\nFirst 10 citations:")
    for i, citation in enumerate(sorted(citations)[:10]):
        print(f"{i+1}. {citation}")

if __name__ == "__main__":
    input_file = "citations_for_websearch.txt"
    output_file = "cleaned_citations_for_websearch.txt"
    
    clean_citations_for_websearch(input_file, output_file) 