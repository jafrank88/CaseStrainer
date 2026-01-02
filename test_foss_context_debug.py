#!/usr/bin/env python3
"""
Debug the case name extraction context for FOSS citation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.strict_context_isolator import get_strict_context_for_citation, extract_case_name_from_strict_context

def debug_foss_extraction():
    """Debug what context is being extracted for FOSS citation"""
    
    print("🔍 DEBUGGING FOSS CASE NAME EXTRACTION")
    print("=" * 50)
    
    # The exact text from our test
    text = "This case involves FOSS v. NATIONAL MARINE FISHERIES SERVICE, 161 F.3d 584 (9th Cir. 1998)."
    citation = "161 F.3d 584"
    
    # Find citation position
    citation_pos = text.find(citation)
    print(f"📍 Citation position: {citation_pos}")
    print(f"📄 Full text: '{text}'")
    print(f"🎯 Citation: '{citation}'")
    
    # Get all citation positions
    from src.utils.strict_context_isolator import find_all_citation_positions
    all_positions = find_all_citation_positions(text)
    print(f"🔍 All citation positions: {all_positions}")
    
    # Get strict context
    strict_context = get_strict_context_for_citation(
        text, citation_pos, citation_pos + len(citation), all_positions, max_lookback=100
    )
    
    print(f"\n📝 Strict context extracted: '{strict_context}'")
    print(f"📏 Context length: {len(strict_context)}")
    
    # Try to extract case name from this context
    case_name = extract_case_name_from_strict_context(strict_context, citation)
    print(f"⚖️  Extracted case name: '{case_name}'")
    
    # Analyze the issue
    print(f"\n🔍 ANALYSIS:")
    if case_name and "This case involves" in case_name:
        print("❌ PROBLEM: Context includes 'This case involves' prefix")
        print("   The extraction is getting too much preceding text")
        print("   Need to improve context isolation")
    elif case_name and "FOSS v. NATIONAL MARINE FISHERIES SERVICE" in case_name:
        print("✅ GOOD: Case name extracted correctly")
    else:
        print("⚠️  UNEXPECTED: Case name extraction failed or got unexpected result")

if __name__ == "__main__":
    debug_foss_extraction()
