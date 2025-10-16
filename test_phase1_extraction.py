"""
Phase 1 Consolidation Test Script
==================================

This script tests the Phase 1 citation pattern consolidation to ensure:
1. Shared patterns work correctly
2. Neutral citations are extracted
3. Case names are clean (no citation bleeding)
4. Clustering works properly
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 70)
print("PHASE 1 CONSOLIDATION - TEST SUITE")
print("=" * 70)
print()

# Test 1: Import shared patterns
print("TEST 1: Import Shared Citation Patterns")
print("-" * 70)
try:
    from src.citation_patterns import CitationPatterns
    patterns = CitationPatterns.get_compiled_patterns()
    print(f"✅ Successfully imported CitationPatterns")
    print(f"✅ Total patterns available: {len(patterns)}")
    
    # Check for neutral patterns
    neutral_patterns = [k for k in patterns.keys() if 'neutral' in k]
    print(f"✅ Neutral citation patterns: {len(neutral_patterns)}")
    print(f"   {', '.join(neutral_patterns)}")
    print()
except Exception as e:
    print(f"❌ FAILED: {e}")
    print()
    sys.exit(1)

# Test 2: Test pattern matching
print("TEST 2: Pattern Matching")
print("-" * 70)
test_cases = [
    ("2017-NM-007", "neutral_nm", "New Mexico neutral"),
    ("388 P.3d 977", "p_3d", "Pacific Reporter 3d"),
    ("159 Wn.2d 700", "wn_2d", "Washington Reports 2d"),
    ("2020 ND 45", "neutral_nd", "North Dakota neutral"),
    ("572 U.S. 782", "us_supreme", "U.S. Reports"),
]

all_passed = True
for citation_text, pattern_name, description in test_cases:
    pattern = patterns.get(pattern_name)
    if pattern:
        match = pattern.search(citation_text)
        if match:
            print(f"✅ {description:30s} | '{citation_text}' | Pattern: {pattern_name}")
        else:
            print(f"❌ {description:30s} | '{citation_text}' | Pattern: {pattern_name} | NO MATCH")
            all_passed = False
    else:
        print(f"❌ {description:30s} | Pattern '{pattern_name}' not found")
        all_passed = False

if not all_passed:
    print("\n❌ Pattern matching FAILED")
    sys.exit(1)
print()

# Test 3: Import clean_extraction_pipeline
print("TEST 3: Import Clean Extraction Pipeline")
print("-" * 70)
try:
    from src.clean_extraction_pipeline import CleanExtractionPipeline
    pipeline = CleanExtractionPipeline()
    print(f"✅ Successfully imported CleanExtractionPipeline")
    print(f"✅ Pipeline initialized with {len(pipeline.citation_patterns)} patterns")
    print()
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    print()
    sys.exit(1)

# Test 4: Extract from test document
print("TEST 4: Extract Citations from Test Document")
print("-" * 70)
try:
    with open('test_neutral_citation.txt', 'r', encoding='utf-8') as f:
        test_text = f.read()
    
    print(f"✅ Loaded test document ({len(test_text)} chars)")
    
    citations = pipeline.extract_citations(test_text)
    print(f"✅ Extracted {len(citations)} citations")
    print()
    
    # Analyze results
    print("Extracted Citations:")
    print("-" * 70)
    
    neutral_found = []
    for i, cit in enumerate(citations, 1):
        cit_text = cit.citation if hasattr(cit, 'citation') else str(cit)
        case_name = cit.extracted_case_name if hasattr(cit, 'extracted_case_name') else 'N/A'
        
        # Check if it's a neutral citation
        is_neutral = any(pattern.search(cit_text) for pattern in [
            patterns['neutral_nm'],
            patterns['neutral_nd'],
            patterns['neutral_ok'],
            patterns['neutral_sd'],
            patterns['neutral_ut'],
            patterns['neutral_wi'],
            patterns['neutral_wy'],
            patterns['neutral_mt'],
        ])
        
        if is_neutral:
            neutral_found.append(cit_text)
        
        marker = "🌟" if is_neutral else "📄"
        print(f"{marker} {i:2d}. {cit_text:30s} | Case: {case_name[:50]}")
    
    print()
    print(f"Neutral citations found: {len(neutral_found)}")
    for nc in neutral_found:
        print(f"  ✅ {nc}")
    print()
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    print()
    sys.exit(1)

# Test 5: Check for case name bleeding
print("TEST 5: Case Name Bleeding Check")
print("-" * 70)
issues = []
for cit in citations:
    cit_text = cit.citation if hasattr(cit, 'citation') else str(cit)
    case_name = cit.extracted_case_name if hasattr(cit, 'extracted_case_name') else ''
    
    # Check if any OTHER citation text appears in this case name
    for other_cit in citations:
        other_text = other_cit.citation if hasattr(other_cit, 'citation') else str(other_cit)
        if other_text != cit_text and other_text in case_name:
            issues.append(f"{cit_text}: contains '{other_text}' in case name")

if issues:
    print(f"❌ Found {len(issues)} case name bleeding issues:")
    for issue in issues:
        print(f"  ❌ {issue}")
    print()
else:
    print(f"✅ No case name bleeding detected - all case names are clean!")
    print()

# Test 6: Specific neutral citation test (PRIMARY TEST)
print("TEST 6: Hamaatsa Neutral Citation (PRIMARY TEST)")
print("-" * 70)
hamaatsa_nm = None
hamaatsa_p3d = None

for cit in citations:
    cit_text = cit.citation if hasattr(cit, 'citation') else str(cit)
    case_name = cit.extracted_case_name if hasattr(cit, 'extracted_case_name') else ''
    
    if '2017-NM-007' in cit_text:
        hamaatsa_nm = cit
    elif '388 P.3d 977' in cit_text:
        hamaatsa_p3d = cit

# Check if both were extracted
if hamaatsa_nm:
    print(f"✅ Extracted 2017-NM-007")
    nm_case_name = hamaatsa_nm.extracted_case_name if hasattr(hamaatsa_nm, 'extracted_case_name') else ''
    print(f"   Case name: {nm_case_name}")
    if '2017-NM-007' in nm_case_name:
        print(f"   ⚠️  WARNING: Citation appears in case name (should not!)")
    else:
        print(f"   ✅ Case name is clean (no citation)")
else:
    print(f"❌ Did NOT extract 2017-NM-007")

if hamaatsa_p3d:
    print(f"✅ Extracted 388 P.3d 977")
    p3d_case_name = hamaatsa_p3d.extracted_case_name if hasattr(hamaatsa_p3d, 'extracted_case_name') else ''
    print(f"   Case name: {p3d_case_name}")
    if '2017-NM-007' in p3d_case_name:
        print(f"   ❌ FAIL: Neutral citation in case name (case name bleeding!)")
    else:
        print(f"   ✅ Case name is clean")
else:
    print(f"❌ Did NOT extract 388 P.3d 977")

# Check if they should cluster
if hamaatsa_nm and hamaatsa_p3d:
    nm_name = hamaatsa_nm.extracted_case_name if hasattr(hamaatsa_nm, 'extracted_case_name') else ''
    p3d_name = hamaatsa_p3d.extracted_case_name if hasattr(hamaatsa_p3d, 'extracted_case_name') else ''
    
    # Normalize for comparison
    nm_name_clean = nm_name.lower().strip()
    p3d_name_clean = p3d_name.lower().strip()
    
    if nm_name_clean == p3d_name_clean:
        print(f"✅ Both have matching case names - should cluster together")
    else:
        print(f"⚠️  Case names don't match exactly:")
        print(f"   NM:  '{nm_name}'")
        print(f"   P3d: '{p3d_name}'")

print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total citations extracted: {len(citations)}")
print(f"Neutral citations found: {len(neutral_found)}")
print(f"Case name bleeding issues: {len(issues)}")
print()

if hamaatsa_nm and hamaatsa_p3d and len(issues) == 0:
    print("✅✅✅ PHASE 1 TESTS PASSED ✅✅✅")
    print()
    print("Key successes:")
    print("  ✅ Shared patterns working")
    print("  ✅ Neutral citations extracted")
    print("  ✅ Case names clean (no bleeding)")
    print("  ✅ Ready for clustering")
    print()
    sys.exit(0)
else:
    print("❌❌❌ PHASE 1 TESTS FAILED ❌❌❌")
    print()
    print("Issues found:")
    if not hamaatsa_nm:
        print("  ❌ 2017-NM-007 not extracted")
    if not hamaatsa_p3d:
        print("  ❌ 388 P.3d 977 not extracted")
    if len(issues) > 0:
        print(f"  ❌ {len(issues)} case name bleeding issues")
    print()
    sys.exit(1)
