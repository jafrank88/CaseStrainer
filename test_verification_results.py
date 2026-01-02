#!/usr/bin/env python3
"""
Test and display verification results for the Permian Basin URL
"""

import sys
import os
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_input_processor import UnifiedInputProcessor
import logging

# Configure logging to show only important messages
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_permian_verification_results():
    """Test the Permian Basin URL and display verification results."""
    url = "https://www.courtlistener.com/opinion/107672/permian-basin-area-rate-cases/"

    print("=" * 80)
    print("🔍 TESTING PERMIAN BASIN VERIFICATION FIXES")
    print("=" * 80)
    print(f"URL: {url}")
    print()

    try:
        # Initialize the processor
        processor = UnifiedInputProcessor(verbose=False)

        # Process the URL
        print("🚀 Processing URL...")
        start_time = time.time()
        result = processor.process_any_input(url, input_type='url', request_id='test-verification-fixes')
        end_time = time.time()

        processing_time = end_time - start_time
        
        if result.get('success') and result.get('citations'):
            citations = result.get('citations', [])
            
            print(f"✅ SUCCESS: Processing completed in {processing_time:.2f} seconds")
            print(f"📊 Text length: {len(result.get('text', ''))} characters")
            print(f"📚 Citations found: {len(citations)}")
            print()
            
            # Analyze verification results
            verified_count = sum(1 for c in citations if c.get('verified', False))
            possible_match_count = sum(1 for c in citations if c.get('possible_match', False))
            total_count = len(citations)
            
            print("=" * 80)
            print("📈 VERIFICATION RESULTS SUMMARY")
            print("=" * 80)
            print(f"Total citations: {total_count}")
            print(f"✅ Verified: {verified_count} ({verified_count/total_count*100:.1f}%)")
            print(f"⚠️  Possible matches: {possible_match_count} ({possible_match_count/total_count*100:.1f}%)")
            print(f"❌ Unverified: {total_count - verified_count - possible_match_count} ({(total_count - verified_count - possible_match_count)/total_count*100:.1f}%)")
            print()
            
            # Check verification sources
            sources = {}
            for citation in citations:
                source = citation.get('source', 'Unknown')
                if source not in sources:
                    sources[source] = {'verified': 0, 'possible': 0, 'unverified': 0}
                
                if citation.get('verified', False):
                    sources[source]['verified'] += 1
                elif citation.get('possible_match', False):
                    sources[source]['possible'] += 1
                else:
                    sources[source]['unverified'] += 1
            
            print("=" * 80)
            print("🔍 VERIFICATION SOURCES BREAKDOWN")
            print("=" * 80)
            for source, counts in sorted(sources.items()):
                total = counts['verified'] + counts['possible'] + counts['unverified']
                print(f"{source}:")
                print(f"  ✅ Verified: {counts['verified']}")
                print(f"  ⚠️  Possible: {counts['possible']}")
                print(f"  ❌ Unverified: {counts['unverified']}")
                print(f"  📊 Total: {total}")
                print()
            
            # Show specific improvements
            print("=" * 80)
            print("🎯 VERIFICATION FIXES ANALYSIS")
            print("=" * 80)
            
            # OpenJurist improvements
            openjurist_total = sources.get('OpenJurist', {'verified': 0, 'possible': 0, 'unverified': 0})
            openjurist_success = openjurist_total['verified'] + openjurist_total['possible']
            print(f"🔹 OpenJurist (timeout fix):")
            print(f"   Success rate: {openjurist_success}/{openjurist_total['verified'] + openjurist_total['possible'] + openjurist_total['unverified'] if openjurist_total else 0} citations")
            print(f"   Status: {'✅ IMPROVED' if openjurist_success > 0 else '❌ Still failing'}")
            print()
            
            # Google Scholar improvements
            google_scholar_total = sources.get('Google Scholar', {'verified': 0, 'possible': 0, 'unverified': 0})
            google_scholar_success = google_scholar_total['verified'] + google_scholar_total['possible']
            print(f"🔹 Google Scholar (rate limit fix):")
            print(f"   Success rate: {google_scholar_success}/{google_scholar_total['verified'] + google_scholar_total['possible'] + google_scholar_total['unverified'] if google_scholar_total else 0} citations")
            print(f"   Status: {'✅ IMPROVED' if google_scholar_success > 0 else '❌ Still failing'}")
            print()
            
            # Timeout improvements
            print(f"🔹 Overall timeout (30s→60s):")
            if processing_time < 60:
                print(f"   Processing time: {processing_time:.2f}s ✅ Under 60s")
            else:
                print(f"   Processing time: {processing_time:.2f}s ⚠️  Still over 60s")
            print()
            
            # Show example verified citations
            print("=" * 80)
            print("📋 EXAMPLE VERIFIED CITATIONS")
            print("=" * 80)
            verified_examples = [c for c in citations if c.get('verified', False)][:5]
            for i, citation in enumerate(verified_examples, 1):
                print(f"{i}. {citation.get('citation', 'N/A')}")
                print(f"   Source: {citation.get('source', 'Unknown')}")
                print(f"   Case name: {citation.get('canonical_name', 'N/A')}")
                print()
            
            # Calculate overall success
            overall_success_rate = (verified_count + possible_match_count) / total_count * 100
            print("=" * 80)
            print("🏆 OVERALL SUCCESS METRICS")
            print("=" * 80)
            print(f"Target success rate: 80%+")
            print(f"Actual success rate: {overall_success_rate:.1f}%")
            print(f"Status: {'✅ TARGET MET' if overall_success_rate >= 80 else '⚠️  BELOW TARGET'}")
            print()
            
            print(f"Target processing time: <45s")
            print(f"Actual processing time: {processing_time:.2f}s")
            print(f"Status: {'✅ TARGET MET' if processing_time < 45 else '⚠️  ABOVE TARGET'}")
            print()
            
            return True
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ FAILED: {error}")
            return False

    except Exception as e:
        print(f"❌ Exception during processing: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_permian_verification_results()
    sys.exit(0 if success else 1)
