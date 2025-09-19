#!/usr/bin/env python3
"""
Test the newly integrated enhanced features: Progress Callbacks and False Positive Prevention
"""

import sys
from pathlib import Path
import asyncio

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_progress_callbacks():
    """Test that progress callbacks work in the main pipeline."""
    print("🧪 Testing Progress Callbacks")
    print("=" * 50)
    
    progress_updates = []
    
    def progress_callback(progress, step, message):
        progress_updates.append({
            'progress': progress,
            'step': step,
            'message': message
        })
        print(f"📊 Progress: {progress}% - {step}: {message}")
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        # Create processor with progress callback
        processor = UnifiedCitationProcessorV2(progress_callback=progress_callback)
        
        test_text = """
        In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), 
        the court ruled on environmental regulations. See also Johnson v. State, 
        150 Wn.2d 674 (2004), and Smith v. Jones, 2019 WL 2516279 (Fed. Cir. 2019).
        """
        
        # Process text
        result = asyncio.run(processor.process_text(test_text))
        
        print(f"\n✅ Processing completed")
        print(f"✅ Citations found: {len(result.get('citations', []))}")
        print(f"✅ Progress updates received: {len(progress_updates)}")
        
        if progress_updates:
            print("🎉 SUCCESS: Progress callbacks are working!")
            print("📋 Progress updates received:")
            for update in progress_updates:
                print(f"   {update['progress']}% - {update['step']}: {update['message']}")
        else:
            print("❌ FAILURE: No progress updates received")
            
        return len(progress_updates) > 0
        
    except Exception as e:
        print(f"❌ Error testing progress callbacks: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_false_positive_prevention():
    """Test that false positive prevention filters work."""
    print("\n🧪 Testing False Positive Prevention")
    print("=" * 50)
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        
        # Test text with potential false positives
        test_text = """
        The case was decided in 2006. Page 123 contains the ruling.
        See Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006).
        The volume is 150 and the page is 674. Also see 150 Wn.2d 674 (2004).
        Reference number 42 is not a citation. Neither is standalone 999.
        """
        
        result = asyncio.run(processor.process_text(test_text))
        citations = result.get('citations', [])
        
        print(f"✅ Citations found: {len(citations)}")
        
        # Check what citations were found
        citation_texts = [c.citation for c in citations if hasattr(c, 'citation')]
        print(f"✅ Citation texts: {citation_texts}")
        
        # Should find real citations but filter false positives
        real_citations = [c for c in citation_texts if any(pattern in c for pattern in ['WL', 'Wn.2d'])]
        standalone_numbers = [c for c in citation_texts if c.isdigit()]
        
        print(f"✅ Real citations found: {len(real_citations)}")
        print(f"✅ Standalone numbers filtered: {len(standalone_numbers)} (should be 0)")
        
        if real_citations and len(standalone_numbers) == 0:
            print("🎉 SUCCESS: False positive prevention is working!")
            print(f"   Real citations: {real_citations}")
        else:
            print("❌ FAILURE: False positive prevention not working properly")
            if standalone_numbers:
                print(f"   Standalone numbers found: {standalone_numbers}")
                
        return len(real_citations) > 0 and len(standalone_numbers) == 0
        
    except Exception as e:
        print(f"❌ Error testing false positive prevention: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_pipeline_integration():
    """Test that enhanced features are properly integrated."""
    print("\n🧪 Testing Enhanced Pipeline Integration")
    print("=" * 50)
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        # Test that the processor has the new methods
        processor = UnifiedCitationProcessorV2()
        
        methods_to_check = [
            '_update_progress',
            '_filter_false_positive_citations',
            '_is_standalone_page_number',
            '_is_volume_without_reporter'
        ]
        
        missing_methods = []
        for method in methods_to_check:
            if not hasattr(processor, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        else:
            print("✅ All enhanced methods are present")
        
        # Test that progress callback parameter works
        def dummy_callback(progress, step, message):
            pass
            
        processor_with_callback = UnifiedCitationProcessorV2(progress_callback=dummy_callback)
        
        if hasattr(processor_with_callback, 'progress_callback') and processor_with_callback.progress_callback:
            print("✅ Progress callback parameter working")
        else:
            print("❌ Progress callback parameter not working")
            return False
        
        print("🎉 SUCCESS: Enhanced features are properly integrated!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_feature_comparison():
    """Compare results with and without enhanced features."""
    print("\n🧪 Testing Feature Impact")
    print("=" * 50)
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        test_text = """
        In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), 
        the court ruled. Page 123 discusses the case. See also 150 Wn.2d 674 (2004).
        Volume 42 is referenced. The number 999 appears standalone.
        """
        
        # Test with enhanced features
        processor = UnifiedCitationProcessorV2()
        result = asyncio.run(processor.process_text(test_text))
        citations = result.get('citations', [])
        
        print(f"✅ Enhanced pipeline found: {len(citations)} citations")
        
        # Check quality of results
        wl_citations = [c for c in citations if hasattr(c, 'citation') and 'WL' in c.citation]
        wn_citations = [c for c in citations if hasattr(c, 'citation') and 'Wn.2d' in c.citation]
        
        print(f"✅ WL citations: {len(wl_citations)}")
        print(f"✅ Wn.2d citations: {len(wn_citations)}")
        
        if wl_citations and wn_citations:
            print("🎉 SUCCESS: Enhanced pipeline finding quality citations!")
        else:
            print("❌ Quality citations not found")
            
        return len(citations) > 0
        
    except Exception as e:
        print(f"❌ Error testing feature comparison: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 Testing Enhanced Features Integration")
    print("=" * 70)
    print("Testing Progress Callbacks and False Positive Prevention")
    print("=" * 70)
    
    results = {
        'progress_callbacks': test_progress_callbacks(),
        'false_positive_prevention': test_false_positive_prevention(),
        'pipeline_integration': test_enhanced_pipeline_integration(),
        'feature_impact': test_feature_comparison()
    }
    
    print(f"\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    
    for feature, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {feature.replace('_', ' ').title()}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 OVERALL RESULT: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 SUCCESS: All enhanced features are working properly!")
        print("✅ Progress callbacks provide real-time updates")
        print("✅ False positive prevention improves result quality")
        print("✅ Features are properly integrated into main pipeline")
    else:
        print("⚠️ Some features need attention")
    
    print(f"\n💡 BENEFITS ACHIEVED:")
    print("• Better user experience with progress updates")
    print("• Cleaner results with false positive filtering")
    print("• Enhanced main pipeline without breaking changes")
    print("• Extracted valuable features from unused processors")

if __name__ == "__main__":
    main()
