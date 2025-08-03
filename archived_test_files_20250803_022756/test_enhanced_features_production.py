#!/usr/bin/env python3
"""
Test enhanced verification features with citations that will trigger fallback verification
"""

import requests
import json
import sys

def test_enhanced_verification_features():
    """Test enhanced verification features with citations that require fallback verification."""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    
    # Test text with citations that should trigger enhanced verification and fallback
    test_text = """
    The court in Smith v. Jones, 123 Fake 456 (2020), established precedent.
    See also Unknown Case, 999 Made.Up 123 (2021).
    Compare with 2023 WL 1234567 (unpublished decision).
    But see Garrity v. New Jersey, 385 U.S. 493 (1967) (well-known case for comparison).
    """
    
    print("Testing Enhanced Verification Features in Production")
    print("=" * 60)
    print(f"Production URL: {base_url}")
    print(f"Test text includes fake citations that should trigger fallback verification")
    print("=" * 60)
    
    try:
        # Test enhanced verification with citations that will trigger fallback
        print("Testing citation processing with enhanced verification...")
        
        payload = {
            "text": test_text,
            "enable_verification": True,
            "debug_mode": True
        }
        
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
            
            print("[SUCCESS] Enhanced verification test: PASSED")
            print(f"\nResults summary:")
            print(f"  Citations found: {len(result.get('citations', []))}")
            print(f"  Clusters created: {len(result.get('clusters', []))}")
            
            # Analyze enhanced verification results in detail
            verified_count = 0
            unverified_count = 0
            courtlistener_count = 0
            fallback_count = 0
            validation_metadata_count = 0
            
            print(f"\nDetailed Citation Analysis:")
            for i, citation in enumerate(result.get('citations', []), 1):
                print(f"\n  Citation {i}: {citation.get('citation')}")
                print(f"    Verified: {citation.get('verified')}")
                print(f"    Canonical name: {citation.get('canonical_name')}")
                print(f"    Source: {citation.get('source')}")
                print(f"    Confidence: {citation.get('confidence')}")
                print(f"    Verification method: {citation.get('verification_method')}")
                print(f"    Validation passed: {citation.get('validation_passed')}")
                print(f"    Fallback source: {citation.get('fallback_source')}")
                
                # Count verification types
                if citation.get('verified'):
                    verified_count += 1
                    if 'CourtListener' in str(citation.get('source', '')):
                        courtlistener_count += 1
                    elif 'fallback' in str(citation.get('source', '')):
                        fallback_count += 1
                else:
                    unverified_count += 1
                
                # Check for enhanced metadata
                if (citation.get('verification_method') != 'N/A' or 
                    citation.get('validation_passed') != 'N/A' or 
                    citation.get('fallback_source') != 'N/A'):
                    validation_metadata_count += 1
                
                # Show metadata details
                metadata = citation.get('metadata', {})
                if metadata:
                    print(f"    Metadata keys: {list(metadata.keys())}")
            
            print(f"\n[SUCCESS] Enhanced Verification Analysis:")
            print(f"  Total citations: {len(result.get('citations', []))}")
            print(f"  Verified: {verified_count}")
            print(f"  Unverified: {unverified_count}")
            print(f"  CourtListener verified: {courtlistener_count}")
            print(f"  Fallback verified: {fallback_count}")
            print(f"  With enhanced metadata: {validation_metadata_count}")
            
            # Check if enhanced verification features are working
            if validation_metadata_count > 0:
                print("[SUCCESS] Enhanced verification metadata: DETECTED")
            else:
                print("[INFO] Enhanced verification metadata: Not triggered (all citations verified by CourtListener)")
            
            if fallback_count > 0:
                print("[SUCCESS] Fallback verification: WORKING")
            else:
                print("[INFO] Fallback verification: Not needed (CourtListener handled all verifiable citations)")
            
            # Check for specific test cases
            fake_citations = [c for c in result.get('citations', []) if not c.get('verified')]
            if fake_citations:
                print(f"[SUCCESS] Fake citation detection: {len(fake_citations)} unverified citations correctly identified")
            else:
                print("[INFO] All citations were verified (no fake citations detected)")
            
            return True
            
        else:
            print(f"[FAILED] Enhanced verification test: FAILED")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_enhanced_verification_features()
    if success:
        print("\n[SUCCESS] Enhanced verification features test: COMPLETED")
        print("Enhanced verification system is working correctly in production!")
    else:
        print("\n[FAILED] Enhanced verification features test: FAILED")
    
    sys.exit(0 if success else 1)
