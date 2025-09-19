#!/usr/bin/env python3
"""
Step 2: Debug citation processing pipeline step by step
"""

import sys
from pathlib import Path
import re
import asyncio

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_individual_extraction_methods():
    """Test each citation extraction method individually."""
    
    # Sample text with WL citations from the actual PDF
    test_text = """
    In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), the court ruled that evidence 
    regarding the defendant's prior bad acts was inadmissible. See also Johnson v. State, 2018 WL 3037217 
    (Wyo. 2018), where the court held that motions in limine are proper procedural tools.
    The plaintiff also cites Brown v. Smith, 2020 WL 1234567 (10th Cir. 2020).
    """
    
    print("🔬 Step 2: Individual Extraction Method Testing")
    print("=" * 60)
    print(f"Test text contains 3 WL citations:")
    print("  - 2006 WL 3801910")
    print("  - 2018 WL 3037217") 
    print("  - 2020 WL 1234567")
    print()
    
    # Manual regex test
    wl_pattern = r'\b\d{4}\s+WL\s+\d+\b'
    manual_matches = re.findall(wl_pattern, test_text, re.IGNORECASE)
    print(f"📊 Manual regex: {len(manual_matches)} WL citations found")
    for match in manual_matches:
        print(f"    - {match}")
    print()
    
    # Test UnifiedCitationProcessorV2 methods individually
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        print("🧪 Testing UnifiedCitationProcessorV2 methods:")
        
        # Test enhanced regex extraction
        try:
            enhanced_citations = processor._extract_with_enhanced_regex(test_text)
            enhanced_wl = [c for c in enhanced_citations if 'WL' in c.citation]
            print(f"  Enhanced regex: {len(enhanced_wl)} WL citations")
            for c in enhanced_wl:
                print(f"    - {c.citation} (confidence: {c.confidence})")
        except Exception as e:
            print(f"  ❌ Enhanced regex error: {e}")
        
        # Test eyecite extraction
        try:
            eyecite_citations = processor._extract_with_eyecite(test_text)
            eyecite_wl = [c for c in eyecite_citations if 'WL' in c.citation]
            print(f"  Eyecite: {len(eyecite_wl)} WL citations")
            for c in eyecite_wl:
                print(f"    - {c.citation} (confidence: {c.confidence})")
        except Exception as e:
            print(f"  ❌ Eyecite error: {e}")
        
        # Test full pipeline
        try:
            print(f"\n🔄 Testing full pipeline...")
            result = asyncio.run(processor.process_text(test_text))
            
            wl_citations = [c for c in result if 'WL' in c.citation]
            print(f"  Full pipeline: {len(wl_citations)} WL citations")
            for c in wl_citations:
                print(f"    - {c.citation} (source: {c.source}, confidence: {c.confidence})")
                
            if len(manual_matches) > len(wl_citations):
                print(f"  ⚠️  PIPELINE ISSUE: Manual found {len(manual_matches)}, pipeline found {len(wl_citations)}")
            else:
                print(f"  ✅ Pipeline working correctly")
                
        except Exception as e:
            print(f"  ❌ Full pipeline error: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error importing UnifiedCitationProcessorV2: {e}")

def test_sync_vs_async_processing():
    """Test sync vs async processing paths."""
    
    print(f"\n🔄 Step 3: Sync vs Async Processing Comparison")
    print("=" * 60)
    
    test_text = """
    In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), the court ruled.
    See also Johnson v. State, 2018 WL 3037217 (Wyo. 2018).
    """
    
    # Test sync processing
    print("📝 Testing Sync Processing (UnifiedSyncProcessor):")
    try:
        from unified_sync_processor import UnifiedSyncProcessor
        
        sync_processor = UnifiedSyncProcessor()
        sync_result = sync_processor.process_text(test_text)
        
        sync_citations = sync_result.get('citations', [])
        sync_wl = [c for c in sync_citations if 'WL' in c.get('citation', '')]
        
        print(f"  Total citations: {len(sync_citations)}")
        print(f"  WL citations: {len(sync_wl)}")
        
        if sync_wl:
            print("  WL Citations found:")
            for citation in sync_wl:
                print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
        else:
            print("  ❌ No WL citations found in sync processing")
            
    except Exception as e:
        print(f"  ❌ Sync processing error: {e}")
    
    print()
    
    # Test async processing simulation
    print("⚡ Testing Async Processing (process_citation_task_direct):")
    try:
        from rq_worker import process_citation_task_direct
        
        # Simulate async processing
        async_result = process_citation_task_direct('test_task', test_text, 'text')
        
        if async_result and 'citations' in async_result:
            async_citations = async_result.get('citations', [])
            async_wl = [c for c in async_citations if 'WL' in c.get('citation', '')]
            
            print(f"  Total citations: {len(async_citations)}")
            print(f"  WL citations: {len(async_wl)}")
            
            if async_wl:
                print("  WL Citations found:")
                for citation in async_wl:
                    print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
            else:
                print("  ❌ No WL citations found in async processing")
        else:
            print("  ❌ Async processing returned no results")
            
    except Exception as e:
        print(f"  ❌ Async processing error: {e}")

def check_recent_changes():
    """Check for recent changes that might have broken WL detection."""
    
    print(f"\n🔍 Step 4: Checking Recent Changes")
    print("=" * 60)
    
    # Check if verification is disabled (from memory)
    print("📋 Checking known issues from memories:")
    print("  1. ✅ Major bug was fixed in unified_citation_processor_v2.py")
    print("  2. ⚠️  Verification may be disabled around lines 2454-2461")
    print("  3. ⚠️  Deduplication issues in sync/async pipelines")
    print("  4. ✅ PDF extraction bug was fixed")
    print()
    
    # Check current verification status
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        # Read the file to check if verification is disabled
        processor_file = Path(__file__).parent / 'src' / 'unified_citation_processor_v2.py'
        if processor_file.exists():
            with open(processor_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for disabled verification around line 2454-2461
            lines = content.splitlines()
            verification_area = lines[2450:2465] if len(lines) > 2465 else []
            
            print("🔍 Checking verification status around lines 2454-2461:")
            for i, line in enumerate(verification_area, 2451):
                if 'verify' in line.lower() and ('#' in line or 'disabled' in line.lower()):
                    print(f"  ⚠️  Line {i}: {line.strip()}")
                elif 'verify' in line.lower():
                    print(f"  ✅ Line {i}: {line.strip()}")
                    
    except Exception as e:
        print(f"❌ Error checking recent changes: {e}")

def main():
    """Main function for Steps 2-4."""
    
    # Step 2: Test individual extraction methods
    test_individual_extraction_methods()
    
    # Step 3: Compare sync vs async
    test_sync_vs_async_processing()
    
    # Step 4: Check recent changes
    check_recent_changes()
    
    print(f"\n" + "=" * 60)
    print("📋 Steps 2-4 Summary:")
    print("=" * 60)
    print("Based on the testing above:")
    print("1. If individual methods find WL citations but full pipeline doesn't:")
    print("   → Issue is in pipeline integration")
    print("2. If sync works but async doesn't (or vice versa):")
    print("   → Issue is in specific processing path")
    print("3. If verification is disabled:")
    print("   → Need to re-enable verification")
    print("4. If deduplication is broken:")
    print("   → Citations might be getting filtered out incorrectly")

if __name__ == "__main__":
    main()
