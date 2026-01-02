#!/usr/bin/env python3
"""
Quick Diagnostic Script for Extraction Pipeline Investigation

Run this INSIDE a worker container to test extraction in isolation:
    docker exec -it casestrainer-rqworker1-prod python /app/diagnostic_extraction_test.py

This bypasses the full pipeline and tests extraction directly.
"""

import sys
import logging

# Configure logging to see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

print("=" * 80)
print("DIAGNOSTIC: Testing Citation Extraction in Isolation")
print("=" * 80)

# Test cases that consistently fail
TEST_CASES = [
    {
        'citation': '548 P.3d 226',
        'context': 'See Erickson v. Pharmacia LLC, 548 P.3d 226 (2024).',
        'expected': 'Erickson v. Pharmacia LLC'
    },
    {
        'citation': '831 F.2d 508',
        'context': 'See United States v. Smith, 831 F.2d 508 (1987).',
        'expected': 'Goad v. Celotex Corp.'
    },
    {
        'citation': '2019 WL 2066127',
        'context': 'Nazar v. Harbor Freight Tools USA Inc., 2019 WL 2066127.',
        'expected': 'Nazar v. Harbor Freight Tools USA Inc.'
    }
]

print("\n1. Testing Import of Clean Extraction Pipeline...")
try:
    from src.clean_extraction_pipeline import extract_citations_clean
    print("   ✅ Import successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

print("\n2. Testing Extraction Function with Test Cases...")
for i, test in enumerate(TEST_CASES, 1):
    print(f"\n   Test {i}: {test['citation']}")
    print(f"   Context: {test['context']}")
    print(f"   Expected: {test['expected']}")
    
    try:
        results = extract_citations_clean(test['context'])
        
        if not results:
            print(f"   ❌ No citations extracted!")
            continue
        
        print(f"   Found {len(results)} citation(s):")
        for j, citation in enumerate(results, 1):
            extracted_name = citation.extracted_case_name if hasattr(citation, 'extracted_case_name') else 'N/A'
            citation_text = citation.citation if hasattr(citation, 'citation') else 'Unknown'
            start_index = citation.start_index if hasattr(citation, 'start_index') else None
            
            print(f"      Citation {j}:")
            print(f"         Text: {citation_text}")
            print(f"         Extracted Name: {extracted_name}")
            print(f"         Start Index: {start_index}")
            
            if extracted_name == test['expected']:
                print(f"      ✅ PASS - Extracted correctly!")
            elif extracted_name == 'N/A':
                print(f"      ❌ FAIL - Extracted as N/A")
            else:
                print(f"      ⚠️  PARTIAL - Extracted different name")
    
    except Exception as e:
        print(f"   ❌ Extraction failed with error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("3. Testing Special Format Extraction Directly...")
try:
    from src.clean_extraction_pipeline import _extract_special_citation_formats
    
    test_text = "See United States v. Smith, 831 F.2d 508 (1987)."
    test_citation = "831 F.2d 508"
    test_start = test_text.find(test_citation)
    
    print(f"   Text: {test_text}")
    print(f"   Citation: {test_citation}")
    print(f"   Start Index: {test_start}")
    
    result = _extract_special_citation_formats(test_text, test_citation, test_start)
    
    if result:
        print(f"   ✅ Special format extraction returned: '{result}'")
    else:
        print(f"   ❌ Special format extraction returned None")
        
except ImportError:
    print("   ⚠️  Cannot import _extract_special_citation_formats (private function)")
except Exception as e:
    print(f"   ❌ Special format test failed: {e}")

print("\n" + "=" * 80)
print("4. Checking Citation Object Structure...")
try:
    from src.models import CitationResult
    import inspect
    
    fields = [m for m in dir(CitationResult) if not m.startswith('_')]
    print(f"   CitationResult fields: {', '.join(fields)}")
    
    # Check if it's a dataclass
    if hasattr(CitationResult, '__dataclass_fields__'):
        print(f"   ✅ Is a dataclass")
        for field_name, field in CitationResult.__dataclass_fields__.items():
            print(f"      - {field_name}: {field.type}")
    else:
        print(f"   ⚠️  Not a dataclass")
        
except Exception as e:
    print(f"   ❌ Failed to inspect CitationResult: {e}")

print("\n" + "=" * 80)
print("5. Testing Eyecite Integration...")
try:
    import eyecite
    
    test_text = "See United States v. Smith, 831 F.2d 508 (1987)."
    citations = eyecite.get_citations(test_text)
    
    print(f"   Eyecite found {len(citations)} citation(s):")
    for cit in citations:
        print(f"      - {cit}")
        print(f"        Type: {type(cit).__name__}")
        if hasattr(cit, 'span'):
            print(f"        Span: {cit.span()}")
        if hasattr(cit, 'metadata'):
            print(f"        Metadata: {cit.metadata}")
            
except Exception as e:
    print(f"   ❌ Eyecite test failed: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\nNEXT STEPS:")
print("1. If extraction works here but not in production → Pipeline integration issue")
print("2. If extraction fails here → Logic issue in extraction code")
print("3. If start_index is None → Eyecite not providing positions")
print("4. Review logs above to identify which component is failing")
print("=" * 80)
