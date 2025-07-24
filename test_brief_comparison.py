import os
import glob
import random
import re
import sys
from src.toa_parser import ImprovedToAParser
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from a_plus_citation_processor import extract_citations_with_custom_logic

# Suppress debug output
import logging
logging.getLogger().setLevel(logging.ERROR)

def normalize_name(name):
    if not name:
        return ''
    # Remove punctuation and extra spaces, convert to lowercase
    normalized = name.lower()
    # Remove common punctuation that might interfere with matching
    normalized = re.sub(r'[.,;:!?()[\]{}"\']', '', normalized)
    # Remove extra spaces and normalize
    normalized = ' '.join(normalized.split())
    return normalized

def fuzzy_match_name(name1, name2, threshold=0.8):
    """Simple fuzzy matching for case names"""
    if not name1 or not name2:
        return False
    
    # Exact match after normalization
    if normalize_name(name1) == normalize_name(name2):
        return True
    
    # Check if one is contained in the other (for partial matches)
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # Check for key parts (before and after "v.")
    parts1 = norm1.split(' v ')
    parts2 = norm2.split(' v ')
    
    if len(parts1) == 2 and len(parts2) == 2:
        # Check if either plaintiff or defendant matches
        if parts1[0] == parts2[0] or parts1[1] == parts2[1]:
            return True
    
    return False

def normalize_year(year):
    if not year:
        return ''
    return ''.join(filter(str.isdigit, year))

def get_toa_entries(toa_entries):
    # Returns list of (name, year) tuples
    result = []
    for entry in toa_entries:
        name = entry.case_name
        year = entry.years[0] if entry.years else ''
        if name:
            result.append((name, year))
    return result

def get_processor_entries(citations):
    # Returns list of (name, year) tuples
    result = []
    for c in citations:
        name = getattr(c, 'extracted_case_name', None) or getattr(c, 'case_name', None)
        year = getattr(c, 'extracted_date', None) or getattr(c, 'year', None)
        if name:
            result.append((name, year))
    return result

def get_aplus_entries(citations):
    # Returns list of (name, year) tuples
    result = []
    for c in citations:
        name = c.get('case_name') or c.get('extracted_case_name')
        year = c.get('year') or c.get('extracted_date')
        if name:
            result.append((name, year))
    return result

def print_all_entries(v2_entries, aplus_entries, toa_entries, brief_name):
    print(f"\n=== {brief_name} ===")
    
    print(f"\n--- ToA Entries ({len(toa_entries)}) ---")
    for i, (name, year) in enumerate(toa_entries):
        print(f"  {i+1}. {name} ({year})")
    
    print(f"\n--- v2 Entries ({len(v2_entries)}) ---")
    for i, (name, year) in enumerate(v2_entries):
        print(f"  {i+1}. {name} ({year})")
    
    print(f"\n--- A+ Entries ({len(aplus_entries)}) ---")
    for i, (name, year) in enumerate(aplus_entries):
        print(f"  {i+1}. {name} ({year})")
    
    # Find matches between ToA and v2
    print(f"\n--- ToA <-> v2 Matches ---")
    toa_v2_matches = 0
    for toa_name, toa_year in toa_entries:
        for v2_name, v2_year in v2_entries:
            if fuzzy_match_name(toa_name, v2_name):
                print(f"  [MATCH] {toa_name} ({toa_year}) <-> {v2_name} ({v2_year})")
                toa_v2_matches += 1
                break
    
    # Find matches between ToA and A+
    print(f"\n--- ToA <-> A+ Matches ---")
    toa_aplus_matches = 0
    for toa_name, toa_year in toa_entries:
        for aplus_name, aplus_year in aplus_entries:
            if fuzzy_match_name(toa_name, aplus_name):
                print(f"  [MATCH] {toa_name} ({toa_year}) <-> {aplus_name} ({aplus_year})")
                toa_aplus_matches += 1
                break
    
    # Calculate accuracy
    toa_v2_accuracy = (toa_v2_matches / len(toa_entries)) * 100 if toa_entries else 0
    toa_aplus_accuracy = (toa_aplus_matches / len(toa_entries)) * 100 if toa_entries else 0
    
    print(f"\n--- Summary ---")
    print(f"ToA entries: {len(toa_entries)}")
    print(f"v2 entries: {len(v2_entries)}")
    print(f"A+ entries: {len(aplus_entries)}")
    print(f"ToA <-> v2 matches: {toa_v2_matches}")
    print(f"ToA <-> A+ matches: {toa_aplus_matches}")
    print(f"ToA <-> v2 accuracy: {toa_v2_accuracy:.1f}%")
    print(f"ToA <-> A+ accuracy: {toa_aplus_accuracy:.1f}%")

def main():
    # Use a specific brief that has a proper ToA section
    fname = 'wa_briefs_text/020_Appellants Brief.txt'
    
    print(f"=== Processing: {os.path.basename(fname)} ===")
    
    toa_parser = ImprovedToAParser()
    v2 = UnifiedCitationProcessorV2()
    
    with open(fname, encoding='utf-8') as f:
        text = f.read()
    
    toa_entries = toa_parser.parse_toa_section_simple(text)
    toa_list = get_toa_entries(toa_entries)
    v2_citations = v2.process_text(text)
    v2_list = get_processor_entries(v2_citations)
    aplus_citations = extract_citations_with_custom_logic(text)
    aplus_list = get_aplus_entries(aplus_citations)
    
    print(f"\nToA entries found: {len(toa_list)}")
    print(f"v2 entries found: {len(v2_list)}")
    print(f"A+ entries found: {len(aplus_list)}")
    
    print_all_entries(v2_list, aplus_list, toa_list, os.path.basename(fname))

if __name__ == "__main__":
    main() 