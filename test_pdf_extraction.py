#!/usr/bin/env python3
"""
Test PDF extraction directly without server
Tests the PDF file extraction and citation detection functionality
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

def test_file_exists():
    """Test if the PDF file exists"""
    pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if os.path.exists(pdf_path):
        print(f"✅ File exists: {pdf_path}")
        print(f"📁 File size: {os.path.getsize(pdf_path)} bytes")
        return True, pdf_path
    else:
        print(f"❌ File not found: {pdf_path}")
        return False, None

def test_pdf_extraction(file_path):
    """Test PDF text extraction"""
    try:
        print(f"\n📖 Testing PDF text extraction...")
        
        # Import the file extraction module
        from file_utils import extract_text_from_file
        
        # Extract text from the PDF
        start_time = time.time()
        extracted_text = extract_text_from_file(file_path)
        extraction_time = time.time() - start_time
        
        if extracted_text:
            print(f"✅ Text extraction successful!")
            print(f"⏱️  Extraction time: {extraction_time:.2f} seconds")
            print(f"📝 Text length: {len(extracted_text)} characters")
            print(f"📄 First 500 characters:")
            print("-" * 50)
            print(extracted_text[:500])
            print("-" * 50)
            
            return True, extracted_text
        else:
            print(f"❌ No text extracted from PDF")
            return False, None
            
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_citation_extraction(text):
    """Test citation extraction from text"""
    try:
        print(f"\n🔍 Testing citation extraction...")
        
        # Import the citation extraction module
        from citation_utils import extract_all_citations
        
        # Extract citations from the text
        start_time = time.time()
        citations = extract_all_citations(text)
        extraction_time = time.time() - start_time
        
        print(f"✅ Citation extraction successful!")
        print(f"⏱️  Extraction time: {extraction_time:.2f} seconds")
        print(f"📚 Found {len(citations)} citations")
        
        if citations:
            print(f"\n📋 Citations found:")
            for i, citation in enumerate(citations, 1):
                print(f"  {i}. {citation}")
        else:
            print(f"\n📚 No citations found in the document")
        
        return True, citations
        
    except Exception as e:
        print(f"❌ Citation extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_citation_verification(citations):
    """Test citation verification (if backend is available)"""
    try:
        print(f"\n🔍 Testing citation verification...")
        
        # Check if backend is available
        import requests
        try:
            response = requests.get("http://localhost:5000/casestrainer/api/health", timeout=5)
            if response.status_code != 200:
                print("⚠️  Backend not available, skipping verification")
                return False, None
        except:
            print("⚠️  Backend not available, skipping verification")
            return False, None
        
        # Import the verification module
        from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        verifier = EnhancedMultiSourceVerifier()
        
        print(f"🔍 Verifying {len(citations)} citations...")
        verified_citations = []
        
        for i, citation in enumerate(citations, 1):
            print(f"  Verifying {i}/{len(citations)}: {citation}")
            try:
                result = verifier.verify_citation(citation)
                verified_citations.append(result)
                print(f"    ✅ Verified: {result.get('verified', 'Unknown')}")
                if result.get('case_name'):
                    print(f"    📄 Case: {result.get('case_name')}")
            except Exception as e:
                print(f"    ❌ Verification failed: {e}")
                verified_citations.append({'citation': citation, 'verified': 'false', 'error': str(e)})
        
        print(f"\n📊 Verification summary:")
        print(f"  Total citations: {len(citations)}")
        print(f"  Verified: {len([c for c in verified_citations if c.get('verified') == 'true'])}")
        print(f"  Unverified: {len([c for c in verified_citations if c.get('verified') != 'true'])}")
        
        return True, verified_citations
        
    except Exception as e:
        print(f"❌ Citation verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """Main test function"""
    print("🧪 Testing PDF extraction and citation detection")
    print("=" * 60)
    
    # Step 1: Check if file exists
    file_exists, file_path = test_file_exists()
    if not file_exists:
        print("\n❌ Cannot proceed without the PDF file")
        return False
    
    # Step 2: Test PDF text extraction
    extraction_success, extracted_text = test_pdf_extraction(file_path)
    if not extraction_success:
        print("\n❌ PDF extraction failed")
        return False
    
    # Step 3: Test citation extraction
    citation_success, citations = test_citation_extraction(extracted_text)
    if not citation_success:
        print("\n❌ Citation extraction failed")
        return False
    
    # Step 4: Test citation verification (optional)
    if citations:
        verification_success, verified_citations = test_citation_verification(citations)
        if verification_success:
            print("\n✅ All tests completed successfully!")
        else:
            print("\n⚠️  Citation verification skipped (backend not available)")
            print("💡 To test verification, start the backend server first:")
            print("   - Run: python start_backend.py")
    else:
        print("\n⚠️  No citations found to verify")
    
    print("\n✅ PDF extraction and citation detection test completed!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 