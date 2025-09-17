import sys
import os
sys.path.append('src')

def test_enhanced_processor_debug():
    """Debug the EnhancedSyncProcessor directly."""
    
    print("🔍 TESTING ENHANCED SYNC PROCESSOR DIRECTLY")
    print("=" * 60)
    
    try:
        # Step 1: Get PDF content
        from src.progress_manager import fetch_url_content
        
        test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
        print(f"📄 Extracting content from: {test_url}")
        
        text = fetch_url_content(test_url)
        
        if text and len(text.strip()) > 0:
            print(f"  ✅ PDF content: {len(text)} characters")
            
            # Step 2: Test EnhancedSyncProcessor directly
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            from src.config import get_config_value
            
            print("\nStep 2: Testing EnhancedSyncProcessor...")
            
            courtlistener_key = get_config_value("COURTLISTENER_API_KEY")
            
            options = ProcessingOptions(
                enable_enhanced_verification=True,
                enable_cross_validation=True,
                enable_false_positive_prevention=True,
                enable_confidence_scoring=True,
                courtlistener_api_key=courtlistener_key
            )
            
            processor = EnhancedSyncProcessor(options=options)
            
            print(f"  Processing {len(text)} characters...")
            
            result = processor.process_any_input_enhanced(text, 'text', {})
            
            print(f"  EnhancedSyncProcessor result type: {type(result)}")
            
            if isinstance(result, dict):
                print(f"  Result keys: {list(result.keys())}")
                
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                success = result.get('success', False)
                processing_strategy = result.get('processing_strategy', 'N/A')
                
                print(f"  Success: {success}")
                print(f"  Citations: {len(citations)}")
                print(f"  Clusters: {len(clusters)}")
                print(f"  Processing strategy: {processing_strategy}")
                
                if len(citations) > 0:
                    print("  ✅ EnhancedSyncProcessor found citations!")
                    
                    # Show some examples
                    for i, citation in enumerate(citations[:5], 1):
                        if isinstance(citation, dict):
                            citation_text = citation.get('citation', 'N/A')
                            case_name = citation.get('extracted_case_name', 'N/A')
                        else:
                            citation_text = str(citation)
                            case_name = 'N/A'
                        print(f"    Citation {i}: {citation_text} - {case_name}")
                    
                    if len(clusters) > 0:
                        print(f"  ✅ Clustering working! {len(clusters)} clusters")
                    else:
                        print("  ❌ No clusters found")
                else:
                    print("  ❌ EnhancedSyncProcessor found no citations")
                    
                    # Check for error messages
                    error = result.get('error')
                    if error:
                        print(f"  Error: {error}")
                    
                    # Check if processing was skipped due to thresholds
                    text_length = len(text)
                    print(f"  Text length: {text_length} characters")
                    
                    # Check processor thresholds
                    print(f"  Processor thresholds:")
                    print(f"    enhanced_sync_threshold: {getattr(processor.options, 'enhanced_sync_threshold', 'N/A')}")
                    print(f"    ultra_fast_threshold: {getattr(processor.options, 'ultra_fast_threshold', 'N/A')}")
                    print(f"    clustering_threshold: {getattr(processor.options, 'clustering_threshold', 'N/A')}")
                    
            else:
                print(f"  ❌ Unexpected result type: {type(result)}")
                print(f"  Result: {result}")
                
        else:
            print("  ❌ No PDF content extracted")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_enhanced_processor_debug()
