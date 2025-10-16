#!/usr/bin/env python3
"""
Document vs Network Response Analysis
===================================

Analysis of whether extracted case names from the network response
actually appear in the original document (1033940.pdf).
"""

def analyze_document_vs_network():
    """Analyze the findings from document search"""
    
    print("🔍 DOCUMENT vs NETWORK RESPONSE ANALYSIS")
    print("=" * 60)
    print()
    
    # Network response extractions vs what's actually in the document
    analysis_results = [
        {
            "citation": "578 U.S. 330",
            "extracted_name": "Inc. v. Robins", 
            "canonical_name": "Spokeo, Inc. v. Robins",
            "in_document": True,
            "document_context": "Spokeo, Inc. v. Robins, 578 U.S. 330, 339, 136 S. Ct. 1540, 194 L. Ed. 2d 635 (2016)",
            "issue": "EXTRACTION LOGIC - Corporate name truncation",
            "analysis": "✅ FOUND: Full case name exists in document, extraction truncated 'Spokeo, Inc.' to 'Inc.'"
        },
        {
            "citation": "9 P.3d 655", 
            "extracted_name": "N/A",
            "canonical_name": "People Ex rel Bryant v. Holladay",
            "in_document": False,
            "document_context": "59 P.3d 655 (2002) - Fraternal Ord. of Eagles case",
            "issue": "WRONG CANONICAL DATA",
            "analysis": "❌ MISMATCH: 9 P.3d 655 doesn't exist, but 59 P.3d 655 does (different case entirely)"
        },
        {
            "citation": "268 P.3d 892",
            "extracted_name": "Green v. Pi", 
            "canonical_name": "Five Corners Family Farmers v. State",
            "in_document": True,
            "document_context": "Five Corners Fam. Farmers v. State, 173 Wn.2d 296, 306, 268 P.3d 892 (2011)",
            "issue": "EXTRACTION LOGIC - Wrong case extracted",
            "analysis": "✅ FOUND: Correct case name exists, but extraction picked up wrong text"
        },
        {
            "citation": "101 Wn.2d 270",
            "extracted_name": "rn v. Se",
            "canonical_name": "Coburn v. Seda",
            "in_document": True, 
            "document_context": "Coburn v. Seda, 101 Wn.2d 270, 279, 677 P.2d 173 (1984)",
            "issue": "EXTRACTION LOGIC - Severe truncation",
            "analysis": "✅ FOUND: Full case name exists, extraction severely truncated 'Coburn' to 'rn'"
        },
        {
            "citation": "183 Wn.2d 674",
            "extracted_name": "Carlsen v. Global Client Solutions",
            "canonical_name": "Carlsen v. Global Client Solutions, LLC", 
            "in_document": True,
            "document_context": "Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 495 n.2, 256 P.3d 321 (2011)",
            "issue": "CITATION MISMATCH",
            "analysis": "🔶 PARTIAL: Case exists but with different citation (171 Wn.2d 486, not 183 Wn.2d 674)"
        },
        {
            "citation": "521 U.S. 811",
            "extracted_name": "Spokeo, Inc. v. Robins",
            "canonical_name": "Raines v. Byrd",
            "in_document": True,
            "document_context": "Raines v. Byrd, 521 U.S. 811, 820 n.3, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997)",
            "issue": "EXTRACTION LOGIC - Wrong case extracted", 
            "analysis": "✅ FOUND: Correct case name (Raines v. Byrd) exists, but extraction picked up nearby Spokeo text"
        }
    ]
    
    print("📋 DETAILED ANALYSIS:")
    print()
    
    for i, result in enumerate(analysis_results, 1):
        print(f"{i}. Citation: {result['citation']}")
        print(f"   📤 Network Extracted: '{result['extracted_name']}'")
        print(f"   📋 Network Canonical: '{result['canonical_name']}'")
        print(f"   📄 In Document: {'✅ YES' if result['in_document'] else '❌ NO'}")
        print(f"   📝 Document Context: {result['document_context']}")
        print(f"   🎯 Issue Type: {result['issue']}")
        print(f"   🔍 Analysis: {result['analysis']}")
        print()
    
    # Summary statistics
    print("=" * 60)
    print("📊 SUMMARY STATISTICS")
    print("=" * 60)
    
    total_cases = len(analysis_results)
    found_in_doc = sum(1 for r in analysis_results if r['in_document'])
    extraction_logic_issues = sum(1 for r in analysis_results if 'EXTRACTION LOGIC' in r['issue'])
    canonical_data_issues = sum(1 for r in analysis_results if 'CANONICAL' in r['issue'] or 'MISMATCH' in r['issue'])
    
    print(f"Total cases analyzed: {total_cases}")
    print(f"Cases found in document: {found_in_doc}/{total_cases} ({found_in_doc/total_cases*100:.1f}%)")
    print(f"Extraction logic issues: {extraction_logic_issues}/{total_cases} ({extraction_logic_issues/total_cases*100:.1f}%)")
    print(f"Canonical data issues: {canonical_data_issues}/{total_cases} ({canonical_data_issues/total_cases*100:.1f}%)")
    
    print()
    print("🎯 KEY FINDINGS:")
    print()
    print("1. ✅ MOST CASE NAMES EXIST IN DOCUMENT")
    print("   - 5/6 cases (83%) have the correct case names in the source document")
    print("   - This proves the document contains the right information")
    print()
    print("2. 🔧 EXTRACTION LOGIC IS THE PRIMARY ISSUE")
    print("   - 4/6 cases (67%) have pure extraction logic problems")
    print("   - Corporate name truncation: 'Spokeo, Inc.' → 'Inc.'")
    print("   - Severe truncation: 'Coburn' → 'rn'") 
    print("   - Wrong text extraction: picking up nearby text instead of correct case name")
    print()
    print("3. 📋 SOME CANONICAL DATA ISSUES")
    print("   - 1 case has wrong canonical citation (9 P.3d vs 59 P.3d)")
    print("   - 1 case has citation mismatch (183 Wn.2d vs 171 Wn.2d)")
    print()
    print("4. 🎉 OUR FIXES SHOULD WORK")
    print("   - Since the correct case names exist in the document,")
    print("   - Our enhanced extraction patterns should capture them correctly")
    print("   - The 62.5% → 85%+ improvement target is achievable")
    
    print()
    print("=" * 60)
    print("🚀 CONCLUSION")
    print("=" * 60)
    print()
    print("The network response extraction failures are primarily due to")
    print("EXTRACTION LOGIC ISSUES, not missing data in the source document.")
    print()
    print("Our enhanced regex patterns and extraction logic should resolve")
    print("most of these issues and significantly improve the success rate.")
    print()
    print("The fixes we implemented directly address:")
    print("✅ Corporate name truncation prevention")
    print("✅ Better context window extraction") 
    print("✅ Enhanced signal word cleaning")
    print("✅ Improved validation and fallback logic")

if __name__ == "__main__":
    analyze_document_vs_network()
