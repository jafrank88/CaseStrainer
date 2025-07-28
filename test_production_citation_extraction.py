#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the production citation extraction system with known citation text.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_production_citation_system():
    """Test the production citation extraction system."""
    
    print("Production Citation Extraction Test")
    print("=" * 45)
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        
        print("✅ Successfully imported UnifiedCitationProcessorV2")
        
        # Create processor with debug mode enabled
        config = ProcessingConfig(
            enable_verification=True,
            debug_mode=True,
            use_eyecite=True,
            enable_clustering=True
        )
        
        processor = UnifiedCitationProcessorV2(config)
        print("✅ Successfully initialized citation processor")
        
        # Test with sample text containing various citation types
        test_text = """
        In Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016), 
        the Supreme Court held that criminal defendants have a right to use untainted assets 
        to pay for counsel. This decision built upon the precedent in Caplin & Drysdale, 
        Chartered v. United States, 491 U.S. 617 (1989).
        
        The Washington Supreme Court in State v. Smith, 123 Wn.2d 456, 789 P.2d 123 (2020), 
        followed similar reasoning. See also Johnson v. State, 456 F.3d 789 (9th Cir. 2019).
        
        Federal courts have consistently applied this principle. Brown v. Board of Education, 
        347 U.S. 483 (1954), remains a landmark decision.
        """
        
        print(f"\nTesting with sample text ({len(test_text)} characters)")
        print("Sample citations expected:")
        print("- Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016)")
        print("- Caplin & Drysdale, Chartered v. United States, 491 U.S. 617 (1989)")
        print("- State v. Smith, 123 Wn.2d 456, 789 P.2d 123 (2020)")
        print("- Johnson v. State, 456 F.3d 789 (9th Cir. 2019)")
        print("- Brown v. Board of Education, 347 U.S. 483 (1954)")
        
        # Process the text
        print("\n" + "-" * 40)
        print("PROCESSING TEXT...")
        print("-" * 40)
        
        result = processor.process_document_citations(test_text)
        
        print(f"\nRESULTS:")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Success: {result.get('success', False)}")
        print(f"Total citations found: {len(result.get('citations', []))}")
        print(f"Total clusters found: {len(result.get('clusters', []))}")
        
        # Display individual citations
        citations = result.get('citations', [])
        if citations:
            print(f"\nINDIVIDUAL CITATIONS ({len(citations)}):")
            for i, citation in enumerate(citations):
                print(f"  {i+1}. {citation.get('citation', 'N/A')}")
                if citation.get('extracted_case_name'):
                    print(f"      Case: {citation.get('extracted_case_name')}")
                if citation.get('extracted_date'):
                    print(f"      Date: {citation.get('extracted_date')}")
                if citation.get('canonical_name'):
                    print(f"      Canonical: {citation.get('canonical_name')}")
                if citation.get('verified'):
                    print(f"      Verified: {citation.get('verified')}")
                print()
        
        # Display clusters
        clusters = result.get('clusters', [])
        if clusters:
            print(f"CITATION CLUSTERS ({len(clusters)}):")
            for i, cluster in enumerate(clusters):
                print(f"  Cluster {i+1}:")
                cluster_citations = cluster.get('citations', [])
                for j, citation in enumerate(cluster_citations):
                    print(f"    {j+1}. {citation.get('citation', 'N/A')}")
                print()
        
        # Test the specific Luis v. United States scenario
        print("-" * 40)
        print("TESTING LUIS V. UNITED STATES SCENARIO")
        print("-" * 40)
        
        luis_citations = [c for c in citations if '578 U.S.' in c.get('citation', '') or 
                         '136 S. Ct.' in c.get('citation', '') or 
                         '194 L. Ed.' in c.get('citation', '')]
        
        if luis_citations:
            print(f"Found {len(luis_citations)} Luis v. United States citations:")
            for citation in luis_citations:
                print(f"  - {citation.get('citation')}")
                print(f"    Canonical name: {citation.get('canonical_name', 'None')}")
                print(f"    Canonical date: {citation.get('canonical_date', 'None')}")
                print(f"    Verified: {citation.get('verified', False)}")
        else:
            print("❌ No Luis v. United States citations found")
        
        if len(citations) > 0:
            print(f"\n✅ Citation extraction is working! Found {len(citations)} citations.")
            return True
        else:
            print(f"\n❌ No citations found - there may be an issue with extraction.")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_production_citation_system()
    if success:
        print("\n🎉 Production citation system is working correctly!")
    else:
        print("\n⚠️  Production citation system may have issues.")
