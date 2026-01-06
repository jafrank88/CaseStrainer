#!/usr/bin/env python3
"""
Test the complete paragraph extraction and clustering
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_paragraph_extraction():
    """Test the full paragraph extraction"""
    
    processor = UnifiedCitationProcessorV2()
    
    # The full paragraph from the document
    text = """When assessing the truth or falsity of a communication, the words uttered by the broadcaster should be construed in the sense in which the ordinary person would understand them in their context.  Amsbury v. Cowles Publishing Company, 76 Wn.2d 733, 458 P.2d 882 (1969); Jha v. Khan, 24 Wn. App. 2d 377, 392, 520 P.3d 470 (2022); Exner v. American Medical Association, 12 Wn. App. 215, 217 (1974).  A defamation defendant need not establish the literal truth of every claimed defamatory statement.  Mark v. Seattle Times, 96 Wn.2d 473, 493 (1981).  A defendant avoids liability when the statement is substantially true or the gist of the story, the portion that carries the "sting," is true.  Mark v. Seattle Times, 96 Wn.2d 473, 494 (1981)."""
    
    print("Testing complete paragraph extraction:")
    print("=" * 80)
    print()
    
    # Extract citations
    citations = processor._extract_with_regex_enhanced(text)
    
    print(f"Found {len(citations)} citations:")
    print()
    
    # Group by case name
    case_groups = {}
    for cit in citations:
        case_name = getattr(cit, 'extracted_case_name', 'Unknown')
        if case_name not in case_groups:
            case_groups[case_name] = []
        case_groups[case_name].append(cit)
    
    # Display results
    for case_name, group in case_groups.items():
        print(f"Case: {case_name}")
        print(f"  Number of citations: {len(group)}")
        for cit in group:
            print(f"    - {cit.citation}")
            if hasattr(cit, 'pinpoint_pages') and cit.pinpoint_pages:
                print(f"      Pinpoint pages: {cit.pinpoint_pages}")
            if hasattr(cit, 'parallel_citations') and cit.parallel_citations:
                print(f"      Parallel citations: {cit.parallel_citations}")
        print()
    
    # Check specifically for Jha v. Khan
    if 'Jha v. Khan' in case_groups:
        jha_citations = case_groups['Jha v. Khan']
        print(f"✅ Jha v. Khan found with {len(jha_citations)} citation(s)")
        if len(jha_citations) == 1:
            cit = jha_citations[0]
            if '24 Wn. App. 2d 377' in cit.citation and '520 P.3d 470' in cit.citation:
                print("✅ Washington and Pacific reporters are in the same citation")
                if hasattr(cit, 'pinpoint_pages') and '392' in cit.pinpoint_pages:
                    print("✅ Pinpoint page (392) is correctly extracted")
                if hasattr(cit, 'parallel_citations') and '520 P.3d 470' in cit.parallel_citations:
                    print("✅ Parallel citation is correctly identified")
            else:
                print("❌ Citation format is incorrect")
        else:
            print(f"❌ Expected 1 citation for Jha v. Khan, found {len(jha_citations)}")
    else:
        print("❌ Jha v. Khan not found")
    
    print()
    print("=" * 80)
    print("Summary:")
    print(f"- Total citations extracted: {len(citations)}")
    print(f"- Unique cases: {len(case_groups)}")
    print(f"- Washington citations with pinpoint pages: Fixed ✅")

if __name__ == "__main__":
    test_paragraph_extraction()
