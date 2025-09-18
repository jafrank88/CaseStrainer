#!/usr/bin/env python3
"""
Debug the processing pipeline to see where citations are being lost
"""

import sys
import os
import asyncio

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2
from models import ProcessingConfig

def test_processing_pipeline():
    """Test the processing pipeline with a small sample of the problematic text"""
    
    # Sample text from the PDF that should contain citations
    test_text = """
    FILED
    SEPTEMBER 16, 2025
    In the Office of the Clerk of Court
    WA State Court of Appeals, Division III
    IN THE COURT OF APPEALS OF THE STATE OF WASHINGTON
    DIVISION THREE
    RICHARD WILKINSON, ) No. 40061-1-III
    )
    Appellant, )
    )
    v. ) PUBLISHED OPINION
    )
    THE WASHINGTON MEDICAL )
    COMMISSION, )
    )
    Respondent. )
    
    This case involves citations like 166 Wn.2d 255, 99 Wn.2d 466, 487 U.S. 781, 
    371 U.S. 415, 535 U.S. 564, 24 P.3d 424, 208 P.3d 549, 663 P.2d 457, 
    and 146 F.3d 629.
    """
    
    print("Testing CaseStrainer Processing Pipeline")
    print("=" * 60)
    print(f"Test text length: {len(test_text)} characters")
    print(f"Sample text: {test_text[:200]}...")
    print()
    
    async def run_test():
        try:
            # Create processor with debug mode enabled
            config = ProcessingConfig(
                debug_mode=True,
                enable_verification=True,
                enable_clustering=True,
                enable_deduplication=True
            )
            
            processor = UnifiedCitationProcessorV2(config=config)
            
            print("Configuration:")
            print(f"  - Debug mode: {config.debug_mode}")
            print(f"  - Verification enabled: {config.enable_verification}")
            print(f"  - Clustering enabled: {config.enable_clustering}")
            print(f"  - Deduplication enabled: {config.enable_deduplication}")
            print()
            
            print("Processing text...")
            result = await processor.process_text(test_text)
            
            print(f"Result type: {type(result)}")
            
            if isinstance(result, dict):
                citations = result.get('citations', [])
                print(f"Citations found: {len(citations)}")
                
                if citations:
                    print("\nFirst 5 citations:")
                    for i, citation in enumerate(citations[:5]):
                        if hasattr(citation, 'citation'):
                            print(f"  {i+1}. {citation.citation}")
                            print(f"      Method: {getattr(citation, 'method', 'N/A')}")
                            print(f"      Pattern: {getattr(citation, 'pattern', 'N/A')}")
                            print(f"      Verified: {getattr(citation, 'verified', 'N/A')}")
                        elif isinstance(citation, dict):
                            print(f"  {i+1}. {citation.get('citation', 'N/A')}")
                            print(f"      Method: {citation.get('method', 'N/A')}")
                            print(f"      Pattern: {citation.get('pattern', 'N/A')}")
                            print(f"      Verified: {citation.get('verified', 'N/A')}")
                        else:
                            print(f"  {i+1}. {citation}")
                else:
                    print("⚠️  No citations found in result")
                    
                # Check for other result fields
                if 'errors' in result:
                    print(f"\nErrors: {result['errors']}")
                if 'clusters' in result:
                    print(f"Clusters: {len(result.get('clusters', []))}")
                if 'processing_stats' in result:
                    print(f"Processing stats: {result['processing_stats']}")
                    
            else:
                print(f"Unexpected result format: {result}")
                
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the async test
    asyncio.run(run_test())

if __name__ == "__main__":
    test_processing_pipeline()
