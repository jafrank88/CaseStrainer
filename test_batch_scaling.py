#!/usr/bin/env python3
"""
Test batch verification scaling with more citations
"""

import sys
import os
import time
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_verification_master import get_master_verifier

def test_batch_scaling():
    """Test batch verification with 50 citations like Permian case."""
    
    print("=" * 60)
    print("TESTING BATCH VERIFICATION SCALING (50 Citations)")
    print("=" * 60)
    
    # Create 50 test citations (mix of real and test)
    citation_texts = []
    case_names = []
    case_dates = []
    
    # Add real Supreme Court citations
    real_citations = [
        ("378 U.S. 33", "Permian Basin Area Rate Cases v. FPC", "1974"),
        ("377 U.S. 33", "Permian Basin Area Rate Cases v. FPC", "1974"),
        ("382 U.S. 154", "Seaboard Air Line Railroad Co. v. United States", "1945"),
        ("385 U.S. 83", "United Gas Pipe Line Co. v. Federal Power Commission", "1966"),
        ("376 U.S. 515", "United States v. E. I. du Pont de Nemours & Co.", "1964"),
        ("374 U.S. 203", "Heart of Atlanta Motel, Inc. v. United States", "1964"),
        ("381 U.S. 479", "United States v. Butler", "1936"),
        ("384 U.S. 316", "Katzenbach v. McClung", "1964"),
        ("383 U.S. 663", "United States v. Darby", "1941"),
        ("386 U.S. 738", "South Carolina v. Katzenbach", "1966")
    ]
    
    # Add real citations
    for citation, name, date in real_citations:
        citation_texts.append(citation)
        case_names.append(name)
        case_dates.append(date)
    
    # Add test citations to make 50 total
    for i in range(40):
        citation_texts.append(f"{380+i} U.S. {100+i}")
        case_names.append(f"Test Case v. Test Defendant {i}")
        case_dates.append(["1960", "1970", "1980", "1990", "2000"][i % 5])
    
    print(f"Testing {len(citation_texts)} citations...")
    print(f"Real citations: {len(real_citations)}")
    print(f"Test citations: {len(citation_texts) - len(real_citations)}")
    print()
    
    async def run_verification():
        try:
            # Get the verifier
            verifier = get_master_verifier()
            
            # Track timing
            start_time = time.time()
            
            # Run verification
            results = await verifier.verify_citations_batch(citation_texts, case_names, case_dates)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print("=" * 60)
            print("RESULTS")
            print("=" * 60)
            print(f"Processing time: {processing_time:.2f} seconds")
            print(f"Total citations: {len(results)}")
            
            # Analyze results
            verified_count = 0
            sources = {}
            real_verified = 0
            
            for i, result in enumerate(results):
                if result and result.verified:
                    verified_count += 1
                    source = result.source or 'Unknown'
                    if source not in sources:
                        sources[source] = 0
                    sources[source] += 1
                    
                    # Check if it's a real citation
                    if i < len(real_citations):
                        real_verified += 1
                        print(f"✅ REAL {result.citation} -> {result.canonical_name} (source: {result.source})")
                    else:
                        print(f"✅ TEST {result.citation} -> {result.canonical_name} (source: {result.source})")
                else:
                    if i < len(real_citations):
                        print(f"❌ REAL {result.citation} -> NOT FOUND")
                    else:
                        print(f"❌ TEST {result.citation} -> NOT FOUND")
            
            print()
            print("VERIFICATION SUMMARY:")
            print(f"Total verified: {verified_count}/{len(results)} ({verified_count/len(results)*100:.1f}%)")
            print(f"Real citations verified: {real_verified}/{len(real_citations)} ({real_verified/len(real_citations)*100:.1f}%)")
            print()
            
            if sources:
                print("SOURCES USED:")
                for source, count in sorted(sources.items()):
                    print(f"  {source}: {count} citations")
            else:
                print("NO SOURCES RECORDED")
            
            print()
            print("THREE-STEP ANALYSIS:")
            if 'courtlistener_lookup_batch' in sources:
                print("✅ Step 1 (Batch Lookup): USED")
            else:
                print("❌ Step 1 (Batch Lookup): NOT USED")
                
            if 'courtlistener_search' in sources:
                print("✅ Step 2 (Search API): USED")
            else:
                print("❌ Step 2 (Search API): NOT USED")
                
            external_sources = ['casemine', 'leagle', 'justia', 'openjurist']
            if any(src in sources for src in external_sources):
                print("✅ Step 3 (External Fallback): USED")
            else:
                print("❌ Step 3 (External Fallback): NOT USED")
            
            print()
            print("PERFORMANCE ANALYSIS:")
            print(f"Time per citation: {processing_time/len(results):.2f} seconds")
            
            if processing_time < 60:
                print("✅ FAST: Processing completed within 1 minute")
            elif processing_time < 180:
                print("⚠️  MODERATE: Processing took 1-3 minutes")
            elif processing_time < 300:
                print("⚠️  SLOW: Processing took 3-5 minutes")
            else:
                print("❌ VERY SLOW: Processing took over 5 minutes")
            
            return processing_time < 300  # Success if under 5 minutes
            
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False
    
    # Run the async function
    return asyncio.run(run_verification())

if __name__ == "__main__":
    success = test_batch_scaling()
    sys.exit(0 if success else 1)
