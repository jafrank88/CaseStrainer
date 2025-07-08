#!/usr/bin/env python3
"""
Test script to verify case name and date extraction from user documents.
"""

import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor import UnifiedCitationProcessor, DateExtractor, CaseNameExtractor

def test_document_extraction():
    """Test case name and date extraction from various document formats."""
    print("Testing Document Extraction Capabilities")
    print("=" * 60)
    
    processor = UnifiedCitationProcessor()
    date_extractor = DateExtractor()
    case_extractor = CaseNameExtractor()
    
    # Test documents with different formats
    test_documents = [
        {
            "name": "Legal Brief with Standard Citations",
            "content": """
            In the case of Roe v. Wade, 410 U.S. 113 (1973), the Supreme Court held that 
            the right to privacy encompasses a woman's decision to terminate her pregnancy. 
            This decision was later reaffirmed in Planned Parenthood v. Casey, 505 U.S. 833 (1992).
            
            The Washington Supreme Court in State v. Smith, 200 Wash. 2d 72, 514 P.3d 643 (2023), 
            addressed similar constitutional issues. The court decided this case on June 6, 2023.
            """
        },
        {
            "name": "Academic Paper with Complex Citations",
            "content": """
            Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873 (1954), 
            marked a turning point in American constitutional law. The case was argued on 
            December 9, 1952, and decided on May 17, 1954.
            
            Subsequent cases like Loving v. Virginia, 388 U.S. 1 (1967), and Obergefell v. Hodges, 
            576 U.S. 644 (2015), built upon this foundation.
            """
        },
        {
            "name": "Legal Memorandum with Multiple Formats",
            "content": """
            MEMORANDUM
            
            Re: Citation Analysis
            
            The following cases are relevant:
            
            1. Miranda v. Arizona, 384 U.S. 436, decided June 13, 1966
            2. In re Gault, 387 U.S. 1 (1967) - juvenile rights case
            3. State v. Johnson, 200 Wash. 2d 123, filed January 15, 2024
            4. Ex parte Milligan, 71 U.S. 2 (1866)
            
            Additional authorities:
            - Terry v. Ohio, 392 U.S. 1, 88 S. Ct. 1868 (1968)
            - Mapp v. Ohio, 367 U.S. 643 (1961)
            """
        },
        {
            "name": "Document with Parallel Citations",
            "content": """
            The landmark case of Gideon v. Wainwright, 372 U.S. 335, 83 S. Ct. 792, 
            9 L. Ed. 2d 799 (1963), established the right to counsel in criminal cases.
            
            This was followed by Argersinger v. Hamlin, 407 U.S. 25, 92 S. Ct. 2006, 
            32 L. Ed. 2d 530 (1972), which extended this right to misdemeanor cases.
            """
        },
        {
            "name": "Document with Date Variations",
            "content": """
            Recent developments in Washington law:
            
            - State v. Davis, 200 Wash. 2d 45, decided on 12/15/2023
            - In re Smith, 200 Wash. App. 123, filed January 22, 2024
            - Johnson v. State, 200 Wash. 2d 89, issued on March 8, 2024
            
            Historical context:
            - Marbury v. Madison, 5 U.S. 137 (1803)
            - McCulloch v. Maryland, 17 U.S. 316 (1819)
            """
        }
    ]
    
    for doc in test_documents:
        print(f"\n{'='*60}")
        print(f"Testing: {doc['name']}")
        print(f"{'='*60}")
        
        # Test case name extraction
        print("\n--- Case Name Extraction ---")
        citations = processor.extract_citations(doc['content'])
        
        for citation in citations:
            print(f"\nCitation: {citation.citation}")
            
            # Extract case name from context
            extracted_name = case_extractor.extract_case_name(doc['content'], citation.citation)
            print(f"Extracted case name: {extracted_name}")
            
            # Extract date from context
            if citation.start_index is not None and citation.end_index is not None:
                extracted_date = date_extractor.extract_date_from_context(
                    doc['content'], citation.start_index, citation.end_index
                )
                print(f"Extracted date: {extracted_date}")
            
            # Check if citation was found in context
            context = citation.context if citation.context else "No context"
            print(f"Context: {context[:100]}...")
        
        # Test full document processing
        print(f"\n--- Full Document Processing ---")
        result = processor.process_text(doc['content'], {'extract_case_names': True})
        
        print(f"Total citations found: {result.get('total_citations', 0)}")
        print(f"Verified citations: {result.get('verified_citations', 0)}")
        
        # Show extracted case names and dates
        if 'citations' in result:
            for citation_data in result['citations']:
                print(f"\nCitation: {citation_data.get('citation', 'N/A')}")
                print(f"Case name: {citation_data.get('case_name', 'N/A')}")
                print(f"Extracted case name: {citation_data.get('extracted_case_name', 'N/A')}")
                print(f"Canonical date: {citation_data.get('canonical_date', 'N/A')}")
                print(f"Extracted date: {citation_data.get('extracted_date', 'N/A')}")
                print(f"Verified: {citation_data.get('verified', False)}")

def test_date_extraction_patterns():
    """Test various date extraction patterns."""
    print(f"\n{'='*60}")
    print("Testing Date Extraction Patterns")
    print(f"{'='*60}")
    
    date_extractor = DateExtractor()
    
    test_cases = [
        {
            "text": "Roe v. Wade, 410 U.S. 113 (1973)",
            "citation": "410 U.S. 113",
            "expected": "1973-01-01"
        },
        {
            "text": "Brown v. Board of Education, 347 U.S. 483, decided May 17, 1954",
            "citation": "347 U.S. 483",
            "expected": "1954-05-17"
        },
        {
            "text": "State v. Smith, 200 Wash. 2d 72, filed on January 15, 2024",
            "citation": "200 Wash. 2d 72",
            "expected": "2024-01-15"
        },
        {
            "text": "Case decided on 12/15/2023, Johnson v. State, 200 Wash. 2d 89",
            "citation": "200 Wash. 2d 89",
            "expected": "2023-12-15"
        },
        {
            "text": "In re Gault, 387 U.S. 1, issued on March 8, 1967",
            "citation": "387 U.S. 1",
            "expected": "1967-03-08"
        }
    ]
    
    for test_case in test_cases:
        text = test_case["text"]
        citation = test_case["citation"]
        expected = test_case["expected"]
        
        # Find citation position
        citation_start = text.find(citation)
        citation_end = citation_start + len(citation)
        
        if citation_start != -1:
            extracted_date = date_extractor.extract_date_from_context(
                text, citation_start, citation_end
            )
            
            print(f"\nText: {text}")
            print(f"Citation: {citation}")
            print(f"Expected: {expected}")
            print(f"Extracted: {extracted_date}")
            print(f"Match: {extracted_date == expected}")

def test_case_name_extraction_patterns():
    """Test various case name extraction patterns."""
    print(f"\n{'='*60}")
    print("Testing Case Name Extraction Patterns")
    print(f"{'='*60}")
    
    case_extractor = CaseNameExtractor()
    
    test_cases = [
        {
            "text": "Roe v. Wade, 410 U.S. 113 (1973)",
            "citation": "410 U.S. 113",
            "expected": "Roe v. Wade"
        },
        {
            "text": "Brown v. Board of Education, 347 U.S. 483",
            "citation": "347 U.S. 483",
            "expected": "Brown v. Board of Education"
        },
        {
            "text": "In re Gault, 387 U.S. 1 (1967)",
            "citation": "387 U.S. 1",
            "expected": "In re Gault"
        },
        {
            "text": "Ex parte Milligan, 71 U.S. 2 (1866)",
            "citation": "71 U.S. 2",
            "expected": "Ex parte Milligan"
        },
        {
            "text": "State v. Smith, 200 Wash. 2d 72",
            "citation": "200 Wash. 2d 72",
            "expected": "State v. Smith"
        },
        {
            "text": "Johnson and Smith v. State, 200 Wash. 2d 89",
            "citation": "200 Wash. 2d 89",
            "expected": "Johnson and Smith v. State"
        }
    ]
    
    for test_case in test_cases:
        text = test_case["text"]
        citation = test_case["citation"]
        expected = test_case["expected"]
        
        extracted_name = case_extractor.extract_case_name(text, citation)
        
        print(f"\nText: {text}")
        print(f"Citation: {citation}")
        print(f"Expected: {expected}")
        print(f"Extracted: {extracted_name}")
        print(f"Match: {extracted_name == expected}")

if __name__ == "__main__":
    print("Document Extraction Test Suite")
    print("=" * 60)
    
    # Test document extraction
    test_document_extraction()
    
    # Test date extraction patterns
    test_date_extraction_patterns()
    
    # Test case name extraction patterns
    test_case_name_extraction_patterns()
    
    print(f"\n{'='*60}")
    print("Test suite completed!") 