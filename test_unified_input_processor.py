#!/usr/bin/env python3
"""
Test using UnifiedInputProcessor like the Permian test but with smaller sample
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_input_processor import UnifiedInputProcessor

def test_unified_input_processor():
    """Test source preservation using UnifiedInputProcessor."""
    
    print("=" * 60)
    print("TESTING UNIFIED INPUT PROCESSOR SOURCE PRESERVATION")
    print("=" * 60)
    
    # Use the same text as our working test
    text = """
    In the case of Permian Basin Area Rate Cases v. FPC, 377 U.S. 33 (1964), the court 
    considered the regulatory authority. This was followed by Seaboard Air Line Railroad 
    Co. v. United States, 382 U.S. 154 (1965), which established important precedent.
    Another relevant case is United Gas Pipe Line Co. v. Federal Power Commission, 
    385 U.S. 83 (1966).
    """
    
    print("Testing with UnifiedInputProcessor...")
    print()
    
    try:
        # Initialize the processor (like the Permian test does)
        processor = UnifiedInputProcessor(verbose=True)
        
        print("🔥 Processing text with UnifiedInputProcessor...")
        start_time = time.time()
        
        # Process the text (like the Permian test does)
        result = processor.process_any_input(text, input_type='text', request_id='source-preservation-test')
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print("=" * 60)
        print("UNIFIED INPUT PROCESSOR RESULTS")
        print("=" * 60)
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Success: {result.get('success', False)}")
        print(f"Citations found: {len(result.get('citations', []))}")
        print()
        
        if result.get('citations'):
            citations = result.get('citations', [])
            
            print("CITATION DETAILS:")
            sources = {}
            verified_count = 0
            
            for i, citation in enumerate(citations):
                citation_text = citation.get('citation', 'Unknown')
                verified = citation.get('verified', False)
                source = citation.get('source', 'Unknown')
                canonical_name = citation.get('canonical_name', 'Not set')
                
                print(f"Citation {i+1}: {citation_text}")
                print(f"  verified: {verified}")
                print(f"  source: {source}")
                print(f"  canonical_name: {canonical_name}")
                print()
                
                if source not in sources:
                    sources[source] = 0
                sources[source] += 1
                
                if verified:
                    verified_count += 1
            
            print("VERIFICATION SUMMARY:")
            print(f"Total verified: {verified_count}/{len(citations)}")
            print()
            
            print("SOURCES USED:")
            for source, count in sorted(sources.items()):
                print(f"  {source}: {count} citations")
            
            print()
            print("SOURCE PRESERVATION ANALYSIS:")
            
            # Check if sources are preserved correctly
            if 'courtlistener_lookup_batch' in sources:
                courtlistener_count = sources['courtlistener_lookup_batch']
                print(f"✅ CourtListener batch lookup sources preserved: {courtlistener_count} citations")
                
                if courtlistener_count == verified_count:
                    print("✅ ALL VERIFIED CITATIONS HAVE CORRECT SOURCES")
                    return True
                else:
                    print("⚠️  Some verified citations are missing correct sources")
                    return False
            elif 'Unknown' in sources and sources['Unknown'] == len(citations):
                print("❌ ALL SOURCES SHOW AS 'UNKNOWN' - Preservation failed")
                return False
            else:
                print("⚠️  Unexpected source pattern")
                return False
        else:
            print("❌ No citations found")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_unified_input_processor()
    print()
    if success:
        print("🎉 UNIFIED INPUT PROCESSOR SOURCE PRESERVATION SUCCESSFUL!")
    else:
        print("❌ UNIFIED INPUT PROCESSOR SOURCE PRESERVATION FAILED!")
    sys.exit(0 if success else 1)
