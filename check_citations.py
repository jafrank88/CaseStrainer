#!/usr/bin/env python3
import json

try:
    with open('casehold_citations_1000.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f'Loaded {len(data)} citations')
    print('Sample citations:')
    for i, c in enumerate(data[:5]):
        print(f'  {i+1}. {c["citation"]} - {c.get("case_name", "N/A")}')
        
    # Analyze citation types
    citation_types = {}
    for c in data:
        citation = c["citation"].lower()
        if "f.3d" in citation or "f.supp" in citation or "u.s." in citation:
            citation_types["federal"] = citation_types.get("federal", 0) + 1
        elif "ok" in citation:
            citation_types["oklahoma"] = citation_types.get("oklahoma", 0) + 1
        elif any(state in citation for state in ["cal.", "ny", "tex.", "fla.", "wash."]):
            citation_types["state"] = citation_types.get("state", 0) + 1
        else:
            citation_types["other"] = citation_types.get("other", 0) + 1
    
    print(f'\nCitation type distribution:')
    for ctype, count in citation_types.items():
        print(f'  {ctype}: {count}')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc() 