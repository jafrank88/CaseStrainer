#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

from unified_extraction_architecture import extract_case_name_and_year_unified

# Test context
text = """Certified questions are questions of law that this court reviews de novo and in light
of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430
P.3d 655 (2018)."""

citation = '192 Wn.2d 453'
citation_pos = text.find(citation)

print(f"Testing extraction with debug=False")
print(f"Citation: '{citation}'")
print(f"Position: {citation_pos}")
print("=" * 50)

try:
    result = extract_case_name_and_year_unified(
        text=text,
        citation=citation,
        start_index=citation_pos,
        end_index=citation_pos + len(citation),
        debug=False
    )
    
    print(f"Result: {result}")
    print(f"Case name: '{result.get('case_name', 'N/A')}'")
    print(f"Year: '{result.get('year', 'N/A')}'")
    print(f"Confidence: {result.get('confidence', 'N/A')}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()



