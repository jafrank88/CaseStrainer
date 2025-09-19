#!/usr/bin/env python3
"""
Test UnifiedCitationProcessorV2 directly with large documents to isolate the issue.
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_processor_v2_directly():
    """Test UnifiedCitationProcessorV2 directly with different document sizes."""
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        
        # Test cases with increasing sizes
        base_citations = """
        State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
        City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
        Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
        """
        
        test_cases = [
            ("Small", base_citations, 1),
            ("Medium", base_citations + "\nAdditional content. " * 100, 100),
            ("Large", base_citations + "\nAdditional content. " * 500, 500),
            ("Very Large", base_citations + "\nAdditional content. " * 1000, 1000),
            ("Huge", base_citations + "\nAdditional content. " * 2000, 2000)
        ]
        
        print("🧪 Testing UnifiedCitationProcessorV2 Directly")
        print("=" * 60)
        
        for name, text, multiplier in test_cases:
            size_kb = len(text) / 1024
            print(f"\n📄 {name} Document ({size_kb:.1f} KB, {multiplier}x padding):")
            
            try:
                # Time the processing
                import time
                start_time = time.time()
                
                result = await processor.process_text(text)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                print(f"  ✅ Processed in {processing_time:.2f}s")
                print(f"  📊 Citations: {len(citations)}")
                print(f"  🔗 Clusters: {len(clusters)}")
                
                if len(citations) > 0:
                    print(f"  📋 Sample citations:")
                    for i, citation in enumerate(citations[:3]):
                        # Handle CitationResult objects
                        if hasattr(citation, 'citation'):
                            citation_text = citation.citation
                        elif hasattr(citation, '__dict__'):
                            citation_text = str(citation)
                        else:
                            citation_text = citation.get('citation', 'N/A') if hasattr(citation, 'get') else str(citation)
                        print(f"    {i+1}. {citation_text}")
                        print(f"        Type: {type(citation)}")
                        if hasattr(citation, '__dict__'):
                            print(f"        Attributes: {list(citation.__dict__.keys())}")
                else:
                    print(f"  ❌ No citations found!")
                    return False
                    
            except Exception as e:
                print(f"  💥 Processing failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        print(f"\n✅ All document sizes processed successfully!")
        return True
        
    except Exception as e:
        print(f"💥 Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the direct processor test."""
    success = asyncio.run(test_processor_v2_directly())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Direct processor test")
    return success

if __name__ == "__main__":
    main()
