import sys
import os
sys.path.append('src')

def debug_pdf_extraction():
    """Debug the PDF extraction and citation processing pipeline."""
    
    print("🔍 DEBUGGING PDF EXTRACTION PIPELINE")
    print("=" * 60)
    
    # Test URL
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    # Step 1: Test PDF content extraction
    print("Step 1: Testing PDF content extraction...")
    try:
        from src.progress_manager import fetch_url_content
        
        print(f"  Fetching URL: {test_url}")
        content = fetch_url_content(test_url)
        
        if content and len(content.strip()) > 0:
            print(f"  ✅ PDF content extracted: {len(content)} characters")
            
            # Show a sample of the content
            sample = content[:500] if content else "No content"
            print(f"  Sample content: {sample}...")
            
            # Step 2: Test citation extraction from the content
            print("\nStep 2: Testing citation extraction from PDF content...")
            
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            processor = UnifiedCitationProcessorV2()
            
            citations = processor._extract_with_regex(content)
            print(f"  Citations found: {len(citations)}")
            
            if citations:
                print("  ✅ Citation extraction working!")
                for i, citation in enumerate(citations[:5], 1):
                    citation_text = getattr(citation, 'citation', str(citation))
                    case_name = getattr(citation, 'extracted_case_name', 'N/A')
                    print(f"    Citation {i}: {citation_text} - {case_name}")
                
                # Step 3: Test clustering on the extracted citations
                print("\nStep 3: Testing clustering on extracted citations...")
                
                from src.unified_citation_clustering import cluster_citations_unified
                clusters = cluster_citations_unified(citations, content, enable_verification=False)
                
                print(f"  Clusters created: {len(clusters)}")
                
                if clusters:
                    print("  ✅ Clustering working!")
                    for i, cluster in enumerate(clusters[:3], 1):
                        cluster_id = cluster.get('cluster_id', 'N/A')
                        cluster_citations = cluster.get('citations', [])
                        print(f"    Cluster {i}: {cluster_id} - {cluster_citations}")
                else:
                    print("  ❌ No clusters created")
            else:
                print("  ❌ No citations found in PDF content")
                
                # Check if content has citation-like patterns
                import re
                citation_patterns = [
                    r'\d+\s+[A-Z][a-z]*\.?\s*\d*d?\s+\d+',  # Basic citation pattern
                    r'\d+\s+U\.S\.\s+\d+',  # US Reports
                    r'\d+\s+P\.\d*d\s+\d+',  # Pacific Reporter
                    r'\d+\s+Wn\.\d*d\s+\d+'  # Washington Reports
                ]
                
                print("  Checking for citation patterns in content...")
                for pattern in citation_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        print(f"    Found {len(matches)} matches for pattern: {pattern}")
                        print(f"    Examples: {matches[:3]}")
                
        else:
            print("  ❌ Failed to extract PDF content")
            print(f"  Content length: {len(content) if content else 0}")
            print(f"  Content type: {type(content)}")
            
    except Exception as e:
        print(f"  ❌ PDF extraction failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Test the full URL processing pipeline
    print("\nStep 4: Testing full URL processing pipeline...")
    try:
        from src.unified_input_processor import UnifiedInputProcessor
        
        processor = UnifiedInputProcessor()
        result = processor.process_any_input(test_url, 'url', 'debug_test')
        
        print(f"  Full pipeline result: {result.get('success', False)}")
        
        if result.get('success'):
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"  Citations from full pipeline: {len(citations)}")
            print(f"  Clusters from full pipeline: {len(clusters)}")
            
            if len(citations) == 0:
                print("  ❌ Full pipeline also returning 0 citations")
                print("  Issue is in the URL processing pipeline")
            else:
                print("  ✅ Full pipeline working correctly")
        else:
            error = result.get('error', 'Unknown error')
            print(f"  ❌ Full pipeline failed: {error}")
            
    except Exception as e:
        print(f"  ❌ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    debug_pdf_extraction()
