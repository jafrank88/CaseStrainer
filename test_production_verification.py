#!/usr/bin/env python3
"""
Test the enhanced verification features in production environment
"""

import requests
import json
import sys

def test_production_verification():
    """Test the enhanced verification features in the production environment."""
    
    # Production API endpoint
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    
    # Test text with citations that should trigger enhanced verification
    test_text = """
    The Supreme Court in Garrity v. New Jersey, 385 U.S. 493 (1967), established important precedent.
    See also Davis v. Alaska, 94 S. Ct. 1105, 39 L. Ed. 2d 347 (1974).
    Compare with Terry v. Ohio, 392 U.S. 1, 88 S. Ct. 1868 (1968).
    But see 2021 WL 1234567 (unpublished case).
    """
    
    print("Testing Enhanced Verification in Production Environment")
    print("=" * 60)
    print(f"Production URL: {base_url}")
    print(f"Test text: {test_text.strip()}")
    print("=" * 60)
    
    try:
        # Test 1: Health check
        print("Step 1: Testing API health...")
        health_response = requests.get(f"{base_url}/health", timeout=10, verify=False)
        if health_response.status_code == 200:
            print("[SUCCESS] Production API health check: PASSED")
        else:
            print(f"[FAILED] Production API health check: FAILED (status: {health_response.status_code})")
            return False
        
        # Test 2: Citation processing with enhanced verification
        print("\nStep 2: Testing citation processing with enhanced verification...")
        
        # Prepare the request payload
        payload = {
            "text": test_text,
            "enable_verification": True,
            "debug_mode": True
        }
        
        # Make the request to the enhanced citation processing endpoint
        response = requests.post(
            f"{base_url}/analyze_enhanced", 
            json=payload, 
            timeout=30,
            verify=False,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("[SUCCESS] Production citation processing: PASSED")
            print(f"\nResults summary:")
            print(f"  Citations found: {len(result.get('citations', []))}")
            print(f"  Clusters created: {len(result.get('clusters', []))}")
            
            # Analyze the enhanced verification results
            verified_count = 0
            enhanced_metadata_count = 0
            validation_passed_count = 0
            
            for citation in result.get('citations', []):
                if citation.get('verified'):
                    verified_count += 1
                    
                    # Check for enhanced verification metadata
                    metadata = citation.get('metadata', {})
                    if metadata.get('verification_method') or metadata.get('validation_passed'):
                        enhanced_metadata_count += 1
                    
                    if metadata.get('validation_passed'):
                        validation_passed_count += 1
                    
                    print(f"\n  Citation: {citation.get('citation')}")
                    print(f"    Verified: {citation.get('verified')}")
                    print(f"    Canonical name: {citation.get('canonical_name')}")
                    print(f"    Source: {citation.get('source')}")
                    print(f"    Confidence: {citation.get('confidence')}")
                    if metadata:
                        print(f"    Verification method: {metadata.get('verification_method', 'N/A')}")
                        print(f"    Validation passed: {metadata.get('validation_passed', 'N/A')}")
            
            print(f"\n[SUCCESS] Enhanced Verification Analysis:")
            print(f"  Total verified: {verified_count}")
            print(f"  With enhanced metadata: {enhanced_metadata_count}")
            print(f"  Validation passed: {validation_passed_count}")
            
            # Check if enhanced verification features are working
            if enhanced_metadata_count > 0:
                print("[SUCCESS] Enhanced verification metadata: PRESENT")
            else:
                print("[WARNING] Enhanced verification metadata: MISSING")
            
            if validation_passed_count > 0:
                print("[SUCCESS] Verification validation: WORKING")
            else:
                print("[WARNING] Verification validation: NOT DETECTED")
            
            # Test specific cases
            garrity_found = any(
                'garrity' in citation.get('canonical_name', '').lower() 
                for citation in result.get('citations', [])
                if citation.get('verified')
            )
            
            if garrity_found:
                print("[SUCCESS] Garrity v. New Jersey verification: SUCCESS")
            else:
                print("[WARNING] Garrity v. New Jersey verification: NOT FOUND")
            
            return True
            
        else:
            print(f"[FAILED] Production citation processing: FAILED")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_production_verification()
    if success:
        print("\n[SUCCESS] Production verification test: PASSED")
        print("Enhanced verification features are working in production!")
    else:
        print("\n[FAILED] Production verification test: FAILED")
        print("Enhanced verification features may not be working properly.")
    
    sys.exit(0 if success else 1)
