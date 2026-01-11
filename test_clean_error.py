"""
Test to find why clean pipeline is failing
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("Testing clean pipeline import...")

try:
    from src.clean_extraction_pipeline import extract_citations_clean
    print("✓ Import successful")
    
    print("\nTesting clean pipeline with simple text...")
    test_text = "Doe v. City of New York, 2022 WL 15153410."
    result = extract_citations_clean(test_text)
    print(f"✓ Extraction successful: {len(result)} citations")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\nTesting unified processor...")
try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    processor = UnifiedCitationProcessorV2()
    
    print("Testing extract_citations_unified function...")
    from src.unified_citation_processor_v2 import extract_citations_unified
    result = extract_citations_unified(test_text)
    print(f"✓ Unified extraction successful: {len(result)} citations")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
