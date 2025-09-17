#!/usr/bin/env python3

# Debug the actual extraction context being used
import sys
sys.path.append('/app/src')  # Add the src directory to Python path

from src.unified_extraction_architecture import extract_case_name_and_year_unified

# Test text
text = """Certified questions are questions of law that this court reviews de novo and in light
of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430
P.3d 655 (2018)."""

# Test both citations
citations = [
    {'citation': '192 Wn.2d 453', 'start': 323, 'end': 336},
    {'citation': '430 P.3d 655', 'start': 343, 'end': 355}
]

print("Testing extraction with actual context windows:")
print("=" * 60)

for cite_info in citations:
    citation = cite_info['citation']
    start_index = cite_info['start']
    end_index = cite_info['end']
    
    print(f"\nCitation: {citation}")
    print(f"Position: {start_index}-{end_index}")
    
    # Test the extraction
    result = extract_case_name_and_year_unified(
        text=text,
        citation=citation,
        start_index=start_index,
        end_index=end_index,
        debug=True
    )
    
    print(f"Result: {result}")
    print(f"Case name: '{result.get('case_name', 'N/A')}'")
    print(f"Year: '{result.get('year', 'N/A')}'")
    
    # Check the context window
    context_start = max(0, start_index - 500)
    context_end = min(len(text), end_index + 100)
    context = text[context_start:context_end]
    
    print(f"Context window ({context_start}:{context_end}):")
    print(f"'{context}'")
    print("-" * 40)



