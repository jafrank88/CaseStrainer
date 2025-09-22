#!/usr/bin/env python3
"""
Test verification in the document processing pipeline
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2
from models import ProcessingConfig
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_verification_pipeline():
    """Test if verification is working in the processing pipeline"""
    
    print("🔍 Testing Verification Pipeline")
    print("=" * 60)
    
    # Sample text with the citations you mentioned
    test_text = """
    In State v. M.Y.G., 199 Wash.2d 528, 509 P.3d 818 (2022), the court held that...
    
    Similarly, in Inc. v. Cananwill, 559 P.3d 545, 4 Wash.3d 1021 (2024), the decision was...
    
    The precedent from Fode v. Dep't of Ecology, 159 Wash.2d 700, 153 P.3d 846 (2007) established...
    """
    
    # Create config with verification explicitly enabled
    config = ProcessingConfig()
    print(f"📋 Configuration:")
    print(f"   enable_verification: {config.enable_verification}")
    print(f"   enable_clustering: {config.enable_clustering}")
    print(f"   extract_case_names: {config.extract_case_names}")
    print()
    
    # Create processor
    processor = UnifiedCitationProcessorV2(config=config)
    
    print("🔄 Processing text with verification enabled...")
    print("-" * 40)
    
    try:
        # Process the text
        result = processor.process_text(test_text)
        
        print(f"📊 Results:")
        print(f"   Citations found: {len(result.get('citations', []))}")
        print(f"   Clusters found: {len(result.get('clusters', []))}")
        print()
        
        # Check verification status of each citation
        citations = result.get('citations', [])
        if citations:
            print("📋 Citation Verification Status:")
            print("-" * 30)
            
            verified_count = 0
            for i, citation in enumerate(citations, 1):
                verified = getattr(citation, 'verified', False)
                case_name = getattr(citation, 'extracted_case_name', 'Unknown')
                canonical_name = getattr(citation, 'canonical_name', None)
                
                status = "✅ VERIFIED" if verified else "❌ UNVERIFIED"
                print(f"{i:2d}. {citation.citation}")
                print(f"    Status: {status}")
                print(f"    Extracted: {case_name}")
                print(f"    Canonical: {canonical_name}")
                print()
                
                if verified:
                    verified_count += 1
            
            print(f"📈 Verification Summary:")
            print(f"   Verified: {verified_count}/{len(citations)} ({(verified_count/len(citations)*100):.1f}%)")
            
            if verified_count == 0:
                print("⚠️  NO CITATIONS WERE VERIFIED!")
                print("   This suggests the verification system is not working properly.")
            else:
                print("✅ Verification system is working!")
                
        else:
            print("❌ No citations found in the text!")
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main execution"""
    test_verification_pipeline()

if __name__ == "__main__":
    main()
