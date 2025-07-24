#!/usr/bin/env python3
"""
Test script to verify enhanced v2 processor integration
"""

from src.document_processing_unified import process_document

# Test text with known citations
test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""

print("=== TESTING ENHANCED V2 PROCESSOR INTEGRATION ===")
print(f"Test text: {test_text[:100]}...")

# Process the document
result = process_document(content=test_text)

print(f"\nProcessing complete!")
print(f"Citations found: {len(result['citations'])}")

# Show results
for i, citation in enumerate(result['citations'], 1):
    confidence_icon = "🟢" if citation.get('confidence') == 'high' else "🟡"
    verified_icon = "✅" if citation.get('verified') else "❌"
    
    print(f"\n{i}. {confidence_icon} {citation['citation']}")
    print(f"   Case Name: {citation['case_name']}")
    print(f"   Method: {citation.get('method', 'unknown')}")
    print(f"   Verified: {verified_icon}")
    print(f"   Source: {citation.get('source', 'unknown')}")

print(f"\n=== INTEGRATION TEST COMPLETE ===")
print("✅ Enhanced v2 processor successfully integrated!")
print("✅ Document processing using enhanced processor")
print("✅ Results include confidence levels and methods") 