#!/usr/bin/env python3
"""
Test script for new file type support and case name extraction.
Tests RTF, HTML, HTM, and ODT file processing with case name extraction.
"""

import os
import tempfile
import requests
import json
from pathlib import Path

def create_test_files():
    """Create test files for different formats."""
    test_files = {}
    
    # Test HTML file
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Legal Document</title></head>
    <body>
        <h1>Sample Legal Document</h1>
        <p>This document contains citations like <em>Brown v. Board of Education</em>, 347 U.S. 483 (1954).</p>
        <p>Another citation: <em>Roe v. Wade</em>, 410 U.S. 113 (1973).</p>
        <p>Washington case: <em>State v. Smith</em>, 123 Wn.2d 456 (1994).</p>
    </body>
    </html>
    """
    
    # Test RTF file
    rtf_content = r"""{\rtf1\ansi\deff0 {\fonttbl {\f0 Times New Roman;}}
\f0\fs24 Sample Legal Document\par
\par
This document contains citations like {\i Brown v. Board of Education}, 347 U.S. 483 (1954).\par
\par
Another citation: {\i Roe v. Wade}, 410 U.S. 113 (1973).\par
\par
Washington case: {\i State v. Smith}, 123 Wn.2d 456 (1994).\par
}"""
    
    # Test text file with case names
    text_content = """
    Sample Legal Document
    
    This document contains citations like Brown v. Board of Education, 347 U.S. 483 (1954).
    Another citation: Roe v. Wade, 410 U.S. 113 (1973).
    Washington case: State v. Smith, 123 Wn.2d 456 (1994).
    
    Additional cases:
    Miranda v. Arizona, 384 U.S. 436 (1966)
    Gideon v. Wainwright, 372 U.S. 335 (1963)
    """
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        test_files['html'] = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rtf', delete=False, encoding='utf-8') as f:
        f.write(rtf_content)
        test_files['rtf'] = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(text_content)
        test_files['txt'] = f.name
    
    return test_files

def test_document_processing():
    """Test the new document processing functionality."""
    print("Testing New File Type Support and Case Name Extraction")
    print("=" * 60)
    
    # Create test files
    test_files = create_test_files()
    
    try:
        # Import the document processing module
        from src.document_processing_unified import process_document
        
        # Test each file type
        for file_type, file_path in test_files.items():
            print(f"\nTesting {file_type.upper()} file processing:")
            print("-" * 40)
            
            try:
                # Process the document
                result = process_document(file_path=file_path, extract_case_names=True)
                
                if result.get('success'):
                    print(f"✅ {file_type.upper()} processing successful")
                    print(f"   Text length: {result.get('text_length', 0)} characters")
                    print(f"   Citations found: {len(result.get('citations', []))}")
                    print(f"   Case names found: {len(result.get('case_names', []))}")
                    
                    # Show some citations
                    citations = result.get('citations', [])
                    if citations:
                        print(f"   Sample citations:")
                        for i, citation in enumerate(citations[:3]):
                            print(f"     {i+1}. {citation.get('citation', 'N/A')}")
                    
                    # Show case names
                    case_names = result.get('case_names', [])
                    if case_names:
                        print(f"   Extracted case names:")
                        for i, case_name in enumerate(case_names[:3]):
                            print(f"     {i+1}. {case_name}")
                    
                else:
                    print(f"❌ {file_type.upper()} processing failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error testing {file_type.upper()} file: {str(e)}")
        
        # Test direct text processing
        print(f"\nTesting direct text processing:")
        print("-" * 40)
        
        sample_text = """
        This is a sample legal document with citations.
        Brown v. Board of Education, 347 U.S. 483 (1954)
        Roe v. Wade, 410 U.S. 113 (1973)
        State v. Smith, 123 Wn.2d 456 (1994)
        """
        
        result = process_document(content=sample_text, extract_case_names=True)
        
        if result.get('success'):
            print("✅ Direct text processing successful")
            print(f"   Citations found: {len(result.get('citations', []))}")
            print(f"   Case names found: {len(result.get('case_names', []))}")
        else:
            print(f"❌ Direct text processing failed: {result.get('error', 'Unknown error')}")
        
        # Test URL processing
        print(f"\nTesting URL processing:")
        print("-" * 40)
        
        test_url = "https://www.law.cornell.edu/supct/html/02-102.ZS.html"
        
        try:
            result = process_document(url=test_url, extract_case_names=True)
            
            if result.get('success'):
                print("✅ URL processing successful")
                print(f"   Text length: {result.get('text_length', 0)} characters")
                print(f"   Citations found: {len(result.get('citations', []))}")
                print(f"   Case names found: {len(result.get('case_names', []))}")
            else:
                print(f"❌ URL processing failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error testing URL processing: {str(e)}")
    
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure all required dependencies are installed:")
        print("  pip install beautifulsoup4 striprtf")
    
    finally:
        # Clean up test files
        for file_path in test_files.values():
            try:
                os.unlink(file_path)
            except:
                pass

def test_backend_api():
    """Test the backend API with new file types."""
    print(f"\nTesting Backend API with New File Types")
    print("=" * 60)
    
    # Create test files
    test_files = create_test_files()
    
    try:
        base_url = "http://localhost:5000/casestrainer/api"
        
        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
        
        # Test file uploads
        for file_type, file_path in test_files.items():
            print(f"\nTesting {file_type.upper()} file upload:")
            print("-" * 40)
            
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (f'test.{file_type}', f, 'application/octet-stream')}
                    data = {'type': 'file'}
                    
                    response = requests.post(f"{base_url}/analyze", files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get('task_id')
                    print(f"✅ {file_type.upper()} upload accepted, task ID: {task_id}")
                    
                    # Check task status
                    if task_id:
                        status_response = requests.get(f"{base_url}/task_status/{task_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print(f"   Status: {status_data.get('status', 'unknown')}")
                            if status_data.get('status') == 'completed':
                                citations = status_data.get('citations', [])
                                case_names = status_data.get('case_names', [])
                                print(f"   Citations found: {len(citations)}")
                                print(f"   Case names found: {len(case_names)}")
                else:
                    print(f"❌ {file_type.upper()} upload failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error testing {file_type.upper()} upload: {str(e)}")
    
    except Exception as e:
        print(f"❌ Error testing backend API: {str(e)}")
    
    finally:
        # Clean up test files
        for file_path in test_files.values():
            try:
                os.unlink(file_path)
            except:
                pass

if __name__ == "__main__":
    print("CaseStrainer New File Type Support Test")
    print("=" * 60)
    
    # Test document processing
    test_document_processing()
    
    # Test backend API
    test_backend_api()
    
    print("\n" + "=" * 60)
    print("Test completed!") 