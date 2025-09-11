#!/usr/bin/env python3
"""
Script to fix the context window logic for case name extraction
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_improved_context_logic():
    """Test improved context window logic"""
    
    # The exact text from the user's test paragraph
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""
    
    # The problematic citation
    problematic_citation = "392 P.3d 1041"
    
    print("=== Testing Improved Context Logic ===")
    print(f"Citation: {problematic_citation}")
    print()
    
    # Find the citation position
    citation_pos = test_text.find(problematic_citation)
    if citation_pos == -1:
        print("❌ Citation not found in text!")
        return
    
    print(f"Citation found at position: {citation_pos}")
    print()
    
    # IMPROVED CONTEXT WINDOW LOGIC
    # Instead of using a fixed or percentage-based window, use a larger window
    # and prioritize case names closer to the citation
    
    # Test different context window strategies
    strategies = [
        {
            'name': 'Current Logic (200-500 chars)',
            'window': min(500, max(200, len(test_text[:citation_pos]) // 2))
        },
        {
            'name': 'Fixed Large Window (800 chars)',
            'window': 800
        },
        {
            'name': 'Percentage-based (80% of available)',
            'window': int(len(test_text[:citation_pos]) * 0.8)
        },
        {
            'name': 'Full Context (all available)',
            'window': len(test_text[:citation_pos])
        }
    ]
    
    for strategy in strategies:
        window_size = strategy['window']
        start_pos = max(0, citation_pos - window_size)
        context_window = test_text[start_pos:citation_pos]
        
        print(f"=== {strategy['name']} ===")
        print(f"Window size: {window_size} chars")
        print(f"Context: '{context_window}'")
        
        # Look for case name patterns in this context
        import re
        
        # Pattern for "In re" cases
        in_re_pattern = r'In re [^,]+'
        in_re_matches = re.findall(in_re_pattern, context_window)
        
        # Pattern for "v." cases
        v_pattern = r'[^,]+ v\. [^,]+'
        v_matches = re.findall(v_pattern, context_window)
        
        print(f"  'In re' matches: {in_re_matches}")
        print(f"  'v.' matches: {v_matches}")
        
        # IMPROVED CASE NAME SELECTION LOGIC
        # Prioritize case names that are closer to the citation
        if in_re_matches:
            # Find the position of each case name relative to the citation
            case_name_positions = []
            for case_name in in_re_matches:
                case_pos = context_window.rfind(case_name)
                if case_pos != -1:
                    # Calculate distance from citation (closer = better)
                    distance = len(context_window) - case_pos
                    case_name_positions.append((case_name, distance))
            
            # Sort by distance (closest first)
            case_name_positions.sort(key=lambda x: x[1])
            
            if case_name_positions:
                best_case_name = case_name_positions[0][0]
                print(f"  🎯 BEST CASE NAME (closest): '{best_case_name}' (distance: {case_name_positions[0][1]})")
            else:
                print(f"  ❌ No case names found in context")
        else:
            print(f"  ❌ No 'In re' case names found")
        
        print()
    
    print("=== RECOMMENDATION ===")
    print("The 'Fixed Large Window (800 chars)' or 'Full Context' strategy")
    print("should be used to ensure 'In re Marriage of Black' is captured")
    print("for the citation '392 P.3d 1041'.")

if __name__ == "__main__":
    test_improved_context_logic()
