#!/usr/bin/env python3
"""
Debug fallback verification process for non-WL, non-CourtListener citations
"""

import json
import requests
from datetime import datetime

def debug_fallback_verification():
    """Extract and test non-WL, non-CL citations to debug fallback verification"""
    
    print("DEBUGGING FALLBACK VERIFICATION PROCESS")
    print("=" * 60)
    
    # Load the comprehensive analysis results
    try:
        with open('comprehensive_all_citations_analysis_20250730_120812.json', 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading analysis results: {e}")
        return
    
    # Extract unverified citations (excluding WL)
    unverified_citations = analysis_data.get('unverified_citations', [])
    non_wl_unverified = [
        citation for citation in unverified_citations 
        if not ('WL' in citation['citation'] or 'WESTLAW' in citation['citation'].upper())
    ]
    
    print(f"Total unverified citations: {len(unverified_citations)}")
    print(f"Non-WL unverified citations: {len(non_wl_unverified)}")
    
    if not non_wl_unverified:
        print("✅ No non-WL unverified citations found - all failures are WL citations")
        return
    
    # Show examples of non-WL unverified citations
    print(f"\nExamples of non-WL unverified citations:")
    print("-" * 50)
    for i, citation_data in enumerate(non_wl_unverified[:10]):
        print(f"{i+1}. {citation_data['citation']}")
        print(f"   Expected: {citation_data.get('expected_case', 'N/A')}")
        print(f"   Source: {citation_data.get('source_attempted', 'N/A')}")
        print(f"   File: {citation_data.get('file_name', 'N/A')}")
        print()
    
    # Test a sample of these citations to see if fallback is being called
    print(f"Testing sample of non-WL unverified citations to debug fallback...")
    print("-" * 60)
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    test_sample = non_wl_unverified[:5]  # Test first 5
    
    fallback_debug_results = []
    
    for i, citation_data in enumerate(test_sample):
        citation = citation_data['citation']
        case_name = citation_data.get('expected_case', '')
        
        print(f"\n[{i+1}/{len(test_sample)}] DEBUGGING: {citation}")
        print(f"Expected case: {case_name}")
        
        # Create test input
        if case_name and case_name != 'N/A':
            test_text = f"In {case_name}, the court cited {citation}."
        else:
            test_text = f"This case cites {citation}."
        
        try:
            # Make API call with detailed response
            response = requests.post(
                endpoint,
                json={"text": test_text, "type": "text"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                citations_found = result.get('citations', [])
                
                if citations_found:
                    citation_result = citations_found[0]
                    verified = citation_result.get('verified', False)
                    source = citation_result.get('source', 'unknown')
                    canonical_name = citation_result.get('canonical_name', '')
                    
                    print(f"  Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
                    print(f"  Source: {source}")
                    print(f"  Canonical Name: {canonical_name}")
                    
                    # Check if fallback was attempted
                    if 'fallback' in source.lower() or 'cornell' in source.lower() or 'justia' in source.lower():
                        print(f"  ✅ Fallback verification was attempted")
                    elif source == 'regex':
                        print(f"  ❌ Only regex extraction - fallback NOT attempted")
                    elif 'CourtListener' in source:
                        print(f"  ℹ️  CourtListener verification (not fallback)")
                    else:
                        print(f"  ❓ Unknown source - fallback status unclear")
                    
                    fallback_debug_results.append({
                        'citation': citation,
                        'verified': verified,
                        'source': source,
                        'canonical_name': canonical_name,
                        'fallback_attempted': 'fallback' in source.lower() or 'cornell' in source.lower() or 'justia' in source.lower()
                    })
                    
                else:
                    print(f"  ❌ No citations extracted from text")
                    fallback_debug_results.append({
                        'citation': citation,
                        'verified': False,
                        'source': 'no_extraction',
                        'canonical_name': '',
                        'fallback_attempted': False
                    })
            else:
                print(f"  ❌ API error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
    
    # Analyze fallback results
    print(f"\n{'='*60}")
    print("FALLBACK VERIFICATION ANALYSIS")
    print(f"{'='*60}")
    
    fallback_attempted_count = sum(1 for r in fallback_debug_results if r['fallback_attempted'])
    fallback_not_attempted_count = len(fallback_debug_results) - fallback_attempted_count
    
    print(f"Citations tested: {len(fallback_debug_results)}")
    print(f"Fallback attempted: {fallback_attempted_count}")
    print(f"Fallback NOT attempted: {fallback_not_attempted_count}")
    
    if fallback_not_attempted_count == len(fallback_debug_results):
        print(f"\n❌ CRITICAL ISSUE: Fallback verification is NOT being called")
        print(f"All non-WL unverified citations show source 'regex' - fallback pipeline is broken")
        print(f"\nPossible causes:")
        print(f"1. Fallback verifier not imported or configured")
        print(f"2. Fallback logic not triggered in verification pipeline")
        print(f"3. Fallback verifier failing silently")
        print(f"4. Environment configuration missing for fallback services")
        
        # Check if fallback verifier exists
        print(f"\n🔍 CHECKING FALLBACK VERIFIER CONFIGURATION...")
        check_fallback_configuration()
        
    elif fallback_attempted_count > 0:
        print(f"\n✅ Fallback verification is being called for some citations")
        print(f"May need to investigate why it's not working for all unverified citations")
    else:
        print(f"\n❓ Mixed results - need further investigation")
    
    return fallback_debug_results

def check_fallback_configuration():
    """Check if fallback verifier is properly configured"""
    
    print("Checking fallback verifier configuration...")
    
    # Check if fallback verifier file exists
    import os
    fallback_file = "src/fallback_verifier.py"
    
    if os.path.exists(fallback_file):
        print(f"✅ Fallback verifier file exists: {fallback_file}")
        
        # Check if it's being imported in the main pipeline
        pipeline_files = [
            "src/unified_citation_processor_v2.py",
            "src/vue_api_endpoints.py",
            "src/app_final_vue.py"
        ]
        
        for pipeline_file in pipeline_files:
            if os.path.exists(pipeline_file):
                try:
                    with open(pipeline_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'fallback_verifier' in content.lower() or 'FallbackVerifier' in content:
                            print(f"✅ Fallback verifier imported in: {pipeline_file}")
                        else:
                            print(f"❌ Fallback verifier NOT imported in: {pipeline_file}")
                except Exception as e:
                    print(f"❌ Error reading {pipeline_file}: {e}")
            else:
                print(f"❌ Pipeline file not found: {pipeline_file}")
    else:
        print(f"❌ Fallback verifier file NOT found: {fallback_file}")
        print(f"This explains why fallback verification is not working")

def test_fallback_verifier_directly():
    """Test the fallback verifier directly to see if it works"""
    
    print(f"\n🧪 TESTING FALLBACK VERIFIER DIRECTLY...")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from src.fallback_verifier import FallbackVerifier
        
        verifier = FallbackVerifier()
        
        # Test with a known citation
        test_citation = "194 Wn. 2d 784"
        test_case_name = "State v. Arndt"
        test_date = "2019"
        
        print(f"Testing fallback verifier with: {test_citation}")
        
        result = verifier.verify_citation(test_citation, test_case_name, test_date)
        
        print(f"Fallback result:")
        print(f"  Verified: {result.get('verified', False)}")
        print(f"  Source: {result.get('source', 'unknown')}")
        print(f"  Canonical Name: {result.get('canonical_name', '')}")
        
        if result.get('verified'):
            print(f"✅ Fallback verifier is working correctly")
        else:
            print(f"❌ Fallback verifier failed to verify known citation")
            
    except ImportError as e:
        print(f"❌ Cannot import fallback verifier: {e}")
        print(f"This confirms fallback verification is not available")
    except Exception as e:
        print(f"❌ Error testing fallback verifier: {e}")

if __name__ == "__main__":
    debug_results = debug_fallback_verification()
    test_fallback_verifier_directly()
