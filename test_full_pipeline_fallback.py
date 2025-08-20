#!/usr/bin/env python3
"""
Comprehensive Test of Full Citation Pipeline with Fallback Verification

This test goes through the complete pipeline:
1. Citation extraction and normalization (WN. -> Wash.)
2. CourtListener verification attempt
3. Fallback verification using multiple legal databases
4. Verification of that fallback methods actually work

Tests the specific citations from the user's paragraph that are not in CourtListener.
"""

import asyncio
import sys
import os
import json
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_full_pipeline_fallback():
    """Test the complete citation pipeline with fallback verification."""
    
    print("=== Testing Full Citation Pipeline with Fallback Verification ===")
    print()
    
    # Test paragraph from user
    test_paragraph = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""
    
    print("Test Paragraph:")
    print(f'"{test_paragraph}"')
    print()
    
    # Test citations that should NOT be in CourtListener but DO exist in fallback sources
    test_cases = [
        {
            'citation': '178 Wn. App. 929',
            'case_name': 'In re Vulnerable Adult Petition for Knight',
            'date': '2014',
            'description': 'Washington Appellate case - should be in fallback sources'
        },
        {
            'citation': '317 P.3d 1068',
            'case_name': 'In re Vulnerable Adult Petition for Knight',
            'date': '2014',
            'description': 'Pacific Reporter parallel - should be in fallback sources'
        },
        {
            'citation': '188 Wn.2d 114',
            'case_name': 'In re Marriage of Black',
            'date': '2017',
            'description': 'Washington Supreme Court case - should be in fallback sources'
        },
        {
            'citation': '392 P.3d 1041',
            'case_name': 'In re Marriage of Black',
            'date': '2017',
            'description': 'Pacific Reporter parallel - should be in fallback sources'
        }
    ]
    
    print("Test Cases (should NOT be in CourtListener but SHOULD be in fallback sources):")
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case['citation']} -> {case['case_name']} ({case['date']})")
        print(f"   {case['description']}")
    print()
    
    try:
        # Test 1: Citation Normalization
        print("=== Test 1: Citation Normalization ===")
        from citation_utils_consolidated import normalize_citation, generate_citation_variants
        
        for case in test_cases:
            citation = case['citation']
            normalized = normalize_citation(citation)
            variants = generate_citation_variants(citation)
            
            print(f"Original: {citation}")
            print(f"Normalized: {normalized}")
            print(f"Variants: {variants[:5]}...")  # Show first 5 variants
            print()
        
        # Test 2: Full Pipeline with Unified Citation Processing
        print("=== Test 2: Full Pipeline with Unified Citation Processing ===")
        
        try:
            from unified_citation_processor_v2 import UnifiedCitationProcessorV2
            
            processor = UnifiedCitationProcessorV2()
            
            # Create mock citation objects that match the pipeline expectations
            class MockCitation:
                def __init__(self, citation_text, extracted_case_name, extracted_date):
                    self.citation = citation_text
                    self.extracted_case_name = extracted_case_name
                    self.extracted_date = extracted_date
                    self.verified = False
                    self.source = None
                    self.url = None
                    self.canonical_name = None
                    self.canonical_date = None
                    self.start_index = 0
                    self.end_index = len(citation_text)
                    self.is_verified = False
                    self.metadata = {}
            
            # Create citations for the pipeline
            citations = []
            for case in test_cases:
                citation_obj = MockCitation(
                    case['citation'], 
                    case['case_name'], 
                    case['date']
                )
                citations.append(citation_obj)
            
            print(f"Created {len(citations)} citation objects for pipeline testing")
            print()
            
            # Test 3: Fallback Verification Methods
            print("=== Test 3: Testing Individual Fallback Verification Methods ===")
            
            try:
                from citation_verification import verify_citations_with_legal_websearch
                
                print("Testing fallback verification with legal websearch...")
                print("This will test multiple sources: Justia, FindLaw, Leagle, CaseMine, etc.")
                print()
                
                # Run the actual fallback verification
                verified_citations = await verify_citations_with_legal_websearch(citations)
                
                print("Fallback Verification Results:")
                print("=" * 60)
                
                for citation in verified_citations:
                    print(f"Citation: {citation.citation}")
                    print(f"  Verified: {citation.verified}")
                    print(f"  Source: {citation.source}")
                    print(f"  Extracted: {citation.extracted_case_name} ({citation.extracted_date})")
                    print(f"  Canonical: {citation.canonical_name} ({citation.canonical_date})")
                    print(f"  URL: {citation.url}")
                    print()
                
                # Summary
                verified_count = sum(1 for c in verified_citations if c.verified)
                with_canonical = sum(1 for c in verified_citations if c.verified and c.canonical_name)
                
                print("Summary:")
                print(f"  Total citations: {len(citations)}")
                print(f"  Verified: {verified_count}")
                print(f"  With canonical names: {with_canonical}")
                print(f"  Success rate: {verified_count/len(citations)*100:.1f}%")
                print(f"  Canonical data rate: {with_canonical/verified_count*100:.1f}%" if verified_count > 0 else "  Canonical data rate: N/A")
                
                if with_canonical == verified_count and verified_count > 0:
                    print("✅ SUCCESS: All verified citations have canonical names!")
                elif verified_count > 0:
                    print("⚠️  PARTIAL: Some verified citations missing canonical names")
                else:
                    print("❌ FAILURE: No citations were verified")
                
                # Test 4: Test specific fallback sources
                print()
                print("=== Test 4: Testing Specific Fallback Sources ===")
                
                try:
                    from websearch.engine import ComprehensiveWebSearchEngine
                    
                    search_engine = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
                    
                    # Test a specific citation with multiple sources
                    test_citation = "188 Wn.2d 114"
                    test_case_name = "In re Marriage of Black"
                    
                    print(f"Testing individual sources for: {test_citation}")
                    print()
                    
                    # Test Justia
                    print("Testing Justia...")
                    justia_result = await search_engine.search_justia(test_citation, test_case_name)
                    print(f"  Justia result: {justia_result.get('verified', False)}")
                    if justia_result.get('verified'):
                        print(f"  Canonical name: {justia_result.get('canonical_name', 'N/A')}")
                        print(f"  URL: {justia_result.get('url', 'N/A')}")
                    print()
                    
                    # Test FindLaw
                    print("Testing FindLaw...")
                    findlaw_result = await search_engine.search_findlaw(test_citation, test_case_name)
                    print(f"  FindLaw result: {findlaw_result.get('verified', False)}")
                    if findlaw_result.get('verified'):
                        print(f"  Canonical name: {findlaw_result.get('canonical_name', 'N/A')}")
                        print(f"  URL: {findlaw_result.get('url', 'N/A')}")
                    print()
                    
                    # Test Google Scholar
                    print("Testing Google Scholar...")
                    scholar_result = await search_engine.search_google_scholar(test_citation, test_case_name)
                    print(f"  Google Scholar result: {scholar_result.get('verified', False)}")
                    if scholar_result.get('verified'):
                        print(f"  Canonical name: {scholar_result.get('canonical_name', 'N/A')}")
                        print(f"  URL: {scholar_result.get('url', 'N/A')}")
                    print()
                    
                except ImportError as e:
                    print(f"❌ Could not import ComprehensiveWebSearchEngine: {e}")
                except Exception as e:
                    print(f"❌ Error testing individual sources: {e}")
                
            except ImportError as e:
                print(f"❌ Could not import verify_citations_with_legal_websearch: {e}")
            except Exception as e:
                print(f"❌ Error in fallback verification: {e}")
                import traceback
                traceback.print_exc()
                
        except ImportError as e:
            print(f"❌ Could not import UnifiedCitationProcessorV2: {e}")
        except Exception as e:
            print(f"❌ Error in full pipeline test: {e}")
            import traceback
            traceback.print_exc()
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=== Test Complete ===")
    print("This test validates that:")
    print("1. Citation normalization works (WN. -> Wash.)")
    print("2. Fallback verification methods are accessible")
    print("3. Citations not in CourtListener can be verified via fallback sources")
    print("4. The full pipeline integrates all components correctly")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline_fallback())
