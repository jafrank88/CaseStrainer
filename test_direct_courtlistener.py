#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct test of CourtListener API with City of Seattle v. Ratliff citation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_direct_courtlistener():
    """Test CourtListener API directly with the configured API key."""
    
    print("Direct CourtListener API Test")
    print("=" * 35)
    
    try:
        # Import the configuration system
        from config import get_config_value
        
        # Get the API key
        api_key = get_config_value("COURTLISTENER_API_KEY")
        
        if not api_key:
            print("❌ No API key found in configuration")
            return False
        
        print(f"✅ API key found: {api_key[:8]}...")
        
        # Import the verification function
        from courtlistener_verification import verify_with_courtlistener
        
        print("✅ Successfully imported verification function")
        
        # Test citations from City of Seattle v. Ratliff
        test_cases = [
            {
                "citation": "100 Wn.2d 212",
                "extracted_case_name": "City of Seattle v. Ratliff",
                "expected_canonical_name": "City of Seattle v. Ratliff",
                "expected_year": "1983"
            },
            {
                "citation": "667 P.2d 630", 
                "extracted_case_name": "City of Seattle v. Ratliff",
                "expected_canonical_name": "City of Seattle v. Ratliff",
                "expected_year": "1983"
            }
        ]
        
        print(f"\nTesting {len(test_cases)} citations...")
        
        for i, test_case in enumerate(test_cases):
            print(f"\n--- Test {i+1}: {test_case['citation']} ---")
            print(f"Citation: {test_case['citation']}")
            print(f"Extracted case name: {test_case['extracted_case_name']}")
            
            try:
                # Call the verification function
                result = verify_with_courtlistener(
                    api_key,
                    test_case['citation'],
                    test_case['extracted_case_name']
                )
                
                print(f"API call successful: {result is not None}")
                
                if result:
                    print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    
                    if isinstance(result, dict):
                        verified = result.get('verified', False)
                        canonical_name = result.get('canonical_name')
                        canonical_date = result.get('canonical_date')
                        
                        print(f"Verified: {verified}")
                        print(f"Canonical name: {canonical_name}")
                        print(f"Canonical date: {canonical_date}")
                        
                        if verified and canonical_name and canonical_date:
                            print("✅ SUCCESS: Got canonical data!")
                            
                            # Check if it matches expected values
                            if test_case['expected_year'] in str(canonical_date):
                                print("✅ Date matches expected year")
                            else:
                                print(f"⚠️  Date doesn't match expected ({test_case['expected_year']})")
                                
                        else:
                            print("❌ No canonical data returned")
                    else:
                        print(f"❌ Unexpected result format: {result}")
                else:
                    print("❌ No result returned from API")
                    
            except Exception as e:
                print(f"❌ API call failed: {e}")
                import traceback
                traceback.print_exc()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing CourtListener API with City of Seattle v. Ratliff")
    print("=" * 55)
    
    success = test_direct_courtlistener()
    
    print("\n" + "=" * 55)
    if success:
        print("🎉 Direct API test completed!")
    else:
        print("❌ Direct API test failed")
    
    print("\nThis test checks:")
    print("1. API key configuration")
    print("2. Direct CourtListener API calls")
    print("3. Canonical name and date retrieval")
    print("4. Expected vs actual results")
