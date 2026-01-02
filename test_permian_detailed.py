#!/usr/bin/env python3
"""
Detailed test of Permian Basin case to see which verification path is used
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_input_processor import UnifiedInputProcessor
import logging

# Configure detailed logging to see verification paths
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_permian_verification_paths():
    """Test Permian Basin case to identify verification path usage."""
    
    print("=" * 80)
    print("🔍 DETAILED PERMIAN BASIN VERIFICATION PATH ANALYSIS")
    print("=" * 80)
    
    url = "https://www.courtlistener.com/opinion/107672/permian-basin-area-rate-cases/"
    
    try:
        # Initialize the processor
        processor = UnifiedInputProcessor(verbose=True)
        
        print("🚀 Processing Permian Basin URL...")
        print("Watching for verification path usage...")
        print()
        
        # Track timing
        start_time = time.time()
        
        # Process the URL
        result = processor.process_any_input(url, input_type='url', request_id='permian-detailed-test')
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print("=" * 80)
        print("📈 PROCESSING RESULTS")
        print("=" * 80)
        print(f"⏱️  Total processing time: {processing_time:.2f} seconds")
        print(f"📊 Success: {result.get('success', False)}")
        print(f"📚 Citations found: {len(result.get('citations', []))}")
        
        if result.get('success') and result.get('citations'):
            citations = result.get('citations', [])
            
            # Analyze verification sources
            sources = {}
            verified_count = 0
            
            for citation in citations:
                source = citation.get('source', 'Unknown')
                if source not in sources:
                    sources[source] = 0
                sources[source] += 1
                
                if citation.get('verified', False):
                    verified_count += 1
            
            print(f"✅ Verified citations: {verified_count}/{len(citations)}")
            print()
            
            print("🔍 VERIFICATION SOURCES USED:")
            for source, count in sorted(sources.items()):
                print(f"  {source}: {count} citations")
            
            print()
            print("🎯 VERIFICATION PATH ANALYSIS:")
            
            # Check which verification path was used
            if 'courtlistener_lookup_batch' in sources:
                print("✅ Step 1 (Batch Lookup): Used - CourtListener citation-lookup batch API")
            else:
                print("❌ Step 1 (Batch Lookup): NOT USED - Problem!")
            
            if 'courtlistener_search' in sources:
                print("✅ Step 2 (Search API): Used - CourtListener search API")
            else:
                print("⚠️  Step 2 (Search API): Not needed or not used")
            
            # Check for external fallback sources
            external_sources = ['casemine', 'leagle', 'justia', 'openjurist', 'google_scholar']
            external_used = any(src in sources for src in external_sources)
            
            if external_used:
                print("✅ Step 3 (External Fallback): Used - External sources")
                for src in external_sources:
                    if src in sources:
                        print(f"    - {src}: {sources[src]} citations")
            else:
                print("⚠️  Step 3 (External Fallback): Not needed")
            
            print()
            print("📊 PERFORMANCE ANALYSIS:")
            if processing_time < 30:
                print(f"✅ Fast processing: {processing_time:.2f}s < 30s")
            elif processing_time < 60:
                print(f"⚠️  Moderate processing: {processing_time:.2f}s < 60s")
            else:
                print(f"❌ Slow processing: {processing_time:.2f}s > 60s")
                print("   This suggests the optimized three-step process is not being used!")
            
            # Check for specific issues
            if processing_time > 300:
                print("🚨 CRITICAL: Processing took over 5 minutes!")
                print("   Likely causes:")
                print("   - Fallback verification path used instead of optimized batch")
                print("   - External sources being used for all citations")
                print("   - Timeout issues causing delays")
            
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ Processing failed: {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception during processing: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_permian_verification_paths()
    sys.exit(0 if success else 1)
