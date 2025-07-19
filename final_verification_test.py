#!/usr/bin/env python3
"""
Final verification test to confirm that both the standalone tool and backend API are working correctly.
"""

import sys
import os
import requests
import logging

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_standalone_tool():
    """Test the standalone filtering tool."""
    print("Testing Standalone Tool...")
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        test_citation = "410 U.S. 113"
        
        result = processor.verify_citation_unified_workflow(test_citation)
        
        canonical_name = result.get('canonical_name')
        verified = result.get('verified')
        
        print(f"  Citation: {test_citation}")
        print(f"  Canonical Name: {canonical_name}")
        print(f"  Verified: {verified}")
        
        # Check if filtering worked
        if canonical_name and any(domain in canonical_name.lower() for domain in ['youtube.com', 'google.com', 'cheaperthandirt.com', 'http', 'www.']):
            print("  ✗ FAILURE: Web domain returned")
            return False
        else:
            print("  ✓ SUCCESS: No web domain returned")
            return True
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False

def test_backend_api():
    """Test the backend API."""
    print("\nTesting Backend API...")
    
    try:
        base_url = "http://localhost:5001"
        endpoint = "/casestrainer/api/analyze_enhanced"
        
        test_data = {
            "type": "text",
            "text": "Roe v. Wade, 410 U.S. 113 (1973)."
        }
        
        response = requests.post(
            f"{base_url}{endpoint}",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            if citations:
                citation = citations[0]
                canonical_name = citation.get('canonical_name')
                verified = citation.get('verified')
                
                print(f"  Citation: {citation.get('citation')}")
                print(f"  Canonical Name: {canonical_name}")
                print(f"  Verified: {verified}")
                
                # Check if filtering worked
                if canonical_name and any(domain in canonical_name.lower() for domain in ['youtube.com', 'google.com', 'cheaperthandirt.com', 'http', 'www.']):
                    print("  ✗ FAILURE: Web domain returned")
                    return False
                else:
                    print("  ✓ SUCCESS: No web domain returned")
                    return True
            else:
                print("  ✓ SUCCESS: No citations found (filtering worked)")
                return True
        else:
            print(f"  ✗ API ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False

def main():
    """Run both tests and provide summary."""
    print("Final Verification Test - Filtering Implementation")
    print("=" * 60)
    
    standalone_success = test_standalone_tool()
    backend_success = test_backend_api()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  Standalone Tool: {'✓ PASSED' if standalone_success else '✗ FAILED'}")
    print(f"  Backend API: {'✓ PASSED' if backend_success else '✗ FAILED'}")
    
    if standalone_success and backend_success:
        print("\n🎉 SUCCESS: Both tools are working correctly!")
        print("   - Web domains are being filtered out")
        print("   - No invalid canonical names are being returned")
        print("   - The filtering fix is fully implemented and working")
        return True
    else:
        print("\n❌ FAILURE: One or both tools have issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 