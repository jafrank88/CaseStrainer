#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug test for citation extraction functionality.
"""

import sys
import os
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_citation_extraction():
    """Test citation extraction on the problematic PDF."""
    
    print("Citation Extraction Debug Test")
    print("=" * 40)
    
    try:
        # Import the citation extraction modules
        from citation_extractor import CitationExtractor
        from pdf_processor import PyPDF2Processor
        
        print("✅ Successfully imported citation extraction modules")
        
        # Test with a simple text containing known citations
        test_text = """
        This case follows the precedent set in Luis v. United States, 578 U.S. 5 (2016).
        See also Smith v. Jones, 123 F.3d 456 (9th Cir. 2020).
        The court in Brown v. Board, 347 U.S. 483 (1954) established important principles.
        """
        
        print(f"\nTesting with sample text containing known citations...")
        print(f"Text length: {len(test_text)} characters")
        
        # Initialize extractor
        extractor = CitationExtractor()
        
        # Extract citations
        citations = extractor.extract_citations(test_text)
        
        print(f"\nExtracted {len(citations)} citations:")
        for i, citation in enumerate(citations):
            print(f"  {i+1}. {citation.citation}")
            if hasattr(citation, 'extracted_case_name'):
                print(f"      Case name: {citation.extracted_case_name}")
            if hasattr(citation, 'extracted_date'):
                print(f"      Date: {citation.extracted_date}")
        
        if len(citations) > 0:
            print("\n✅ Citation extraction is working correctly!")
            return True
        else:
            print("\n❌ No citations found - extraction may have issues")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This suggests there may be missing modules or path issues")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_processing():
    """Test PDF processing functionality."""
    
    print("\nPDF Processing Test")
    print("=" * 30)
    
    try:
        from pdf_processor import PyPDF2Processor
        
        # Try to download and process the problematic PDF
        pdf_url = "https://www.courts.wa.gov/opinions/pdf/60179-6.25.pdf"
        
        print(f"Attempting to download PDF from: {pdf_url}")
        
        response = requests.get(pdf_url, timeout=30)
        if response.status_code == 200:
            print(f"✅ Successfully downloaded PDF ({len(response.content)} bytes)")
            
            # Process the PDF
            processor = PyPDF2Processor()
            
            # Save temporarily and process
            temp_path = "temp_test.pdf"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            try:
                text = processor.extract_text(temp_path)
                print(f"✅ Successfully extracted text ({len(text)} characters)")
                
                # Look for citation-like patterns in the text
                import re
                citation_patterns = [
                    r'\d+\s+U\.S\.\s+\d+',  # U.S. citations
                    r'\d+\s+F\.\d*d\s+\d+',  # Federal citations
                    r'\d+\s+Wn\.\d*d\s+\d+',  # Washington citations
                    r'\d+\s+P\.\d*d\s+\d+',  # Pacific citations
                ]
                
                found_patterns = []
                for pattern in citation_patterns:
                    matches = re.findall(pattern, text)
                    found_patterns.extend(matches)
                
                print(f"Found {len(found_patterns)} potential citation patterns:")
                for pattern in found_patterns[:10]:  # Show first 10
                    print(f"  - {pattern}")
                
                if len(found_patterns) > 0:
                    print("\n✅ PDF contains citation-like patterns")
                else:
                    print("\n⚠️  No obvious citation patterns found in PDF text")
                
                # Clean up
                os.remove(temp_path)
                return len(found_patterns) > 0
                
            except Exception as e:
                print(f"❌ Failed to process PDF: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return False
        else:
            print(f"❌ Failed to download PDF (status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ PDF processing test failed: {e}")
        return False

if __name__ == '__main__':
    print("Running Citation Extraction Debug Tests")
    print("=" * 50)
    
    extraction_ok = test_citation_extraction()
    pdf_ok = test_pdf_processing()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Citation Extraction: {'✅ WORKING' if extraction_ok else '❌ ISSUES'}")
    print(f"PDF Processing: {'✅ WORKING' if pdf_ok else '❌ ISSUES'}")
    
    if extraction_ok and pdf_ok:
        print("\n🎉 All tests passed - system should be working!")
    else:
        print("\n⚠️  Some issues detected - may need investigation")
