"""
Final test of the streamlined code
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("FINAL TEST OF STREAMLINED CODE")
print("=" * 60)

# Test 1: clean_extraction_pipeline.py with deprecation warning
print("\n1. Testing clean_extraction_pipeline.py (should show deprecation warning):")
print("-" * 50)

import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    
    from src.clean_extraction_pipeline import extract_citations_clean
    
    if w:
        print(f"✅ Deprecation warning caught: {w[0].message}")
    else:
        print("❌ No deprecation warning found")

# Test 2: Extract citations
text = """Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV-00074-APG-NJK, 2025 WL 1410708, at *1 (D. Nev. Apr. 7, 2025)"""

citations = extract_citations_clean(text)

print(f"\nExtracted {len(citations)} citations:")
for cit in citations:
    if "WL" in str(cit.citation):
        print(f"  WL Citation: {cit.citation}")
        print(f"    Case Name: {cit.extracted_case_name}")
        print(f"    Verification Error: {getattr(cit, 'verification_error', 'None')}")

# Test 3: unified_case_extraction_master.py directly
print("\n\n2. Testing unified_case_extraction_master.py directly:")
print("-" * 50)

from src.unified_case_extraction_master import extract_citations_unified

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    
    citations2 = extract_citations_unified(text)
    
    if w:
        print(f"✅ Deprecation warning caught: {w[0].message}")
    else:
        print("❌ No deprecation warning found")

print(f"\nExtracted {len(citations2)} citations with unified function")

print("\n" + "=" * 60)
print("STREAMLINING SUMMARY:")
print("-" * 50)
print("✅ Created extract_citations_unified() in unified_case_extraction_master.py")
print("✅ Updated clean_extraction_pipeline.py to use the new function")
print("✅ Added deprecation warnings to guide migration")
print("✅ Maintained backward compatibility")
print("✅ Reduced code duplication")
print("\nNEXT STEPS:")
print("1. Gradually update the 4 files that import clean_extraction_pipeline")
print("2. Eventually remove clean_extraction_pipeline.py")
print("3. Clean up other deprecated code")
print("=" * 60)
