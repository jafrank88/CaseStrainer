#!/usr/bin/env python3
"""
Debug the case name extraction issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_case_name_extraction():
    """Test case name extraction step by step."""
    
    test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023). State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010)."""
    
    print("=== Testing Case Name Extraction ===")
    print(f"Test text: {test_text}")
    print()
    
    # Test 1: Direct CitationParser extraction
    try:
        from src.standalone_citation_parser import CitationParser
        parser = CitationParser()
        
        print("🔍 TEST 1: Direct CitationParser extraction")
        print("Testing citation: '2 Wn. 3d 329'")
        
        result = parser.extract_from_text(test_text, "2 Wn. 3d 329")
        print(f"  Result: {result}")
        print(f"  Case name: {result.get('case_name')}")
        print(f"  Year: {result.get('year')}")
        print()
        
        print("Testing citation: '169 Wn.2d 815'")
        result2 = parser.extract_from_text(test_text, "169 Wn.2d 815")
        print(f"  Result: {result2}")
        print(f"  Case name: {result2.get('case_name')}")
        print(f"  Year: {result2.get('year')}")
        print()
        
    except Exception as e:
        print(f"❌ CitationParser test failed: {e}")
        print()
    
    # Test 2: Enhanced clustering case name extraction
    try:
        from src.enhanced_clustering import EnhancedCitationClusterer, ClusteringConfig
        
        config = ClusteringConfig(debug_mode=True)
        clusterer = EnhancedCitationClusterer(config)
        
        print("🔍 TEST 2: Enhanced clustering case name extraction")
        
        # Mock citation objects
        mock_citations = [
            {'citation': '2 Wn. 3d 329', 'extracted_case_name': None, 'extracted_date': None},
            {'citation': '169 Wn.2d 815', 'extracted_case_name': None, 'extracted_date': None}
        ]
        
        for citation in mock_citations:
            case_name = clusterer._extract_case_name(citation, test_text)
            year = clusterer._extract_year(citation, test_text)
            print(f"  Citation: '{citation['citation']}'")
            print(f"    Case name: {case_name}")
            print(f"    Year: {year}")
            print()
            
    except Exception as e:
        print(f"❌ Enhanced clustering test failed: {e}")
        print()
    
    # Test 3: Check the _improve_case_name_extraction method
    try:
        from src.enhanced_sync_processor import EnhancedSyncProcessor
        
        processor = EnhancedSyncProcessor()
        
        print("🔍 TEST 3: _improve_case_name_extraction method")
        
        # Mock citations
        mock_citations = [
            {'citation': '2 Wn. 3d 329', 'extracted_case_name': None, 'extracted_date': '2023'},
            {'citation': '169 Wn.2d 815', 'extracted_case_name': None, 'extracted_date': '2010'}
        ]
        
        print("Before improvement:")
        for citation in mock_citations:
            print(f"  '{citation['citation']}' → case_name: {citation['extracted_case_name']}")
        
        # Apply improvement
        processor._improve_case_name_extraction(mock_citations, test_text)
        
        print("After improvement:")
        for citation in mock_citations:
            print(f"  '{citation['citation']}' → case_name: {citation['extracted_case_name']}")
        
    except Exception as e:
        print(f"❌ _improve_case_name_extraction test failed: {e}")
        print()

if __name__ == "__main__":
    test_case_name_extraction()
