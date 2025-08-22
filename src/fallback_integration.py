#!/usr/bin/env python3
"""
Fallback Verification Integration

This module integrates the fallback verifier into the CaseStrainer system
to verify citations that are not found in CourtListener.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

async def enhance_citations_with_fallback_verification(citations_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhance citations with fallback verification results.
    
    Args:
        citations_data: List of citation dictionaries
        
    Returns:
        Enhanced citations with fallback verification data
    """
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
        verifier = EnhancedFallbackVerifier()
        
        enhanced_citations = []
        verified_count = 0
        
        for citation_dict in citations_data:
            # Make a copy to avoid modifying the original
            enhanced_citation = citation_dict.copy()
            
            # Check if citation needs fallback verification
            is_verified = citation_dict.get('verified', 'false').lower() == 'true'
            has_canonical_data = bool(citation_dict.get('canonical_name') and citation_dict.get('canonical_date'))
            
            # Only try fallback verification if not already verified and no canonical data
            if not is_verified and not has_canonical_data:
                citation_text = citation_dict.get('citation_text', '')
                extracted_case_name = citation_dict.get('extracted_case_name', '')
                extracted_date = citation_dict.get('extracted_date', '')
                
                if citation_text:
                    logger.info(f"Attempting fallback verification for: {citation_text}")
                    
                    result = await verifier.verify_citation(
                        citation_text, 
                        extracted_case_name if extracted_case_name else None,
                        extracted_date if extracted_date else None
                    )
                    
                    if result['verified']:
                        # Update the citation with fallback verification results
                        enhanced_citation.update({
                            'verified': 'true',
                            'canonical_name': result['canonical_name'],
                            'canonical_date': result['canonical_date'],
                            'canonical_url': result['url'],
                            'source': f"fallback_{result['source']}",
                            'confidence': result['confidence'],
                            'verification_status': 'found_via_fallback',
                            'fallback_sources': [result['source']],
                            'verification_details': result['verification_details']
                        })
                        verified_count += 1
                        logger.info(f"Successfully verified {citation_text} via {result['source']}")
                    else:
                        # Mark as attempted but failed
                        enhanced_citation['fallback_attempted'] = True
            
            enhanced_citations.append(enhanced_citation)
        
        logger.info(f"Fallback verification enhanced {verified_count}/{len(citations_data)} citations")
        return enhanced_citations
        
    except Exception as e:
        logger.error(f"Error in fallback verification integration: {str(e)}")
        # Return original data if fallback verification fails
        return citations_data

async def verify_single_citation_with_fallback(citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify a single citation using fallback sources.
    
    Args:
        citation_text: The citation to verify
        extracted_case_name: Optional extracted case name
        extracted_date: Optional extracted date
        
    Returns:
        Verification result dictionary
    """
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
        verifier = EnhancedFallbackVerifier()
        
        result = await verifier.verify_citation(citation_text, extracted_case_name, extracted_date)
        
        # Format result for CaseStrainer compatibility
        if result['verified']:
            return {
                'verified': True,
                'canonical_name': result['canonical_name'],
                'canonical_date': result['canonical_date'],
                'canonical_url': result['url'],
                'source': f"fallback_{result['source']}",
                'confidence': result['confidence'],
                'verification_status': 'found_via_fallback',
                'fallback_sources': [result['source']],
                'verification_details': result['verification_details']
            }
        else:
            return {
                'verified': False,
                'verification_status': 'unverified',
                'fallback_attempted': True
            }
            
    except Exception as e:
        logger.error(f"Error verifying citation {citation_text}: {str(e)}")
        return {
            'verified': False,
            'verification_status': 'unverified',
            'fallback_error': str(e)
        }

if __name__ == "__main__":
    # Test the integration
    import asyncio
    
    async def test_integration():
        test_citations = [
            {
                'citation_text': '385 U.S. 493',
                'extracted_case_name': 'Davis v. Alaska',
                'extracted_date': '1967',
                'verified': 'false',
                'canonical_name': None,
                'canonical_date': None
            },
            {
                'citation_text': '123 F.2d 456',
                'extracted_case_name': 'Test Case',
                'extracted_date': '1999',
                'verified': 'false',
                'canonical_name': None,
                'canonical_date': None
            }
        ]
        
        print("Testing fallback integration...")
        enhanced = await enhance_citations_with_fallback_verification(test_citations)
        
        for citation in enhanced:
            print(f"Citation: {citation['citation_text']}")
            print(f"  Verified: {citation.get('verified', 'false')}")
            print(f"  Source: {citation.get('source', 'none')}")
            print(f"  Canonical Name: {citation.get('canonical_name', 'none')}")
            print()
    
    # Run the async test
    asyncio.run(test_integration())
