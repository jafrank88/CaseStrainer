#!/usr/bin/env python3
"""
Simple test to check if the backend is running
"""

import requests
import os

print("Starting simple test...")

try:
    print("Step 1: Basic import test")
    import sys
    from pathlib import Path
    
    print("Step 2: Adding path")
    project_root = Path(__file__).parent.resolve()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    print("Step 3: Importing function")
    from src.case_name_extraction_core import extract_case_name_triple
    
    print("Step 4: Testing function")
    result = extract_case_name_triple("test text", "test citation")
    
    print("Step 5: Displaying result")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    if result:
        print(f"Keys: {list(result.keys())}")
        for key, value in result.items():
            print(f"  {key}: '{value}'")
    else:
        print("Result is None or False")
        
    print("Test completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

def test_backend():
    """Test if the backend is running"""
    
    try:
        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get("http://localhost:5000/health", timeout=5)
        print(f"Health check status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Backend is running!")
            return True
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def test_file_exists():
    """Test if the PDF file exists"""
    
    pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if os.path.exists(pdf_path):
        print(f"✅ File exists: {pdf_path}")
        print(f"📁 File size: {os.path.getsize(pdf_path)} bytes")
        return True
    else:
        print(f"❌ File not found: {pdf_path}")
        return False

from src.standalone_citation_parser import CitationParser

parser = CitationParser()
result = parser.extract_from_text("Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1", "146 Wn.2d 1")
print("Result:", result)

if __name__ == "__main__":
    print("🧪 Simple backend test")
    print("=" * 30)
    
    # Test if file exists
    file_exists = test_file_exists()
    
    # Test if backend is running
    backend_running = test_backend()
    
    if file_exists and backend_running:
        print("\n✅ Ready to test PDF upload!")
    else:
        print("\n❌ Cannot proceed with test")
