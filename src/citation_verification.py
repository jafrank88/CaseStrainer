import requests
import logging
import json
from typing import List
import sys

logger = logging.getLogger(__name__)

# Placeholders for CitationResult and other types
# from src.models import CitationResult

# Move the verification functions here, as previously refactored
# (see previous code for verify_citations_with_courtlistener_batch and verify_with_courtlistener)
# Add stubs for canonical_service and websearch verification as well

def verify_citations_with_courtlistener_batch(courtlistener_api_key, citations, text):
    print(f"[DEBUG PRINT] ENTERED verify_citations_with_courtlistener_batch with {len(citations)} citations")
    if not courtlistener_api_key:
        print("[DEBUG PRINT] No CourtListener API key available")
        logger.warning("[CL batch] No API key available")
        return
    if not citations:
        print("[DEBUG PRINT] No citations to verify in batch")
        return
    logger.info(f"[CL batch] Verifying {len(citations)} citations with text length: {len(text)}")
    logger.debug(f"[CL batch] Text preview: {text[:100]}...")
    try:
        citations_to_verify = [citation.citation for citation in citations]
        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        headers = {
            'Authorization': f'Token {courtlistener_api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'text': ' '.join(citations_to_verify)
        }
        print(f"[DEBUG PRINT] About to POST to {url} with data: {data}")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"[DEBUG PRINT] CourtListener response status: {response.status_code}")
        print(f"[DEBUG PRINT] CourtListener response body: {response.text[:1000]}")
        logger.info(f"[CL batch] API response status: {response.status_code}")
        logger.debug(f"[CL batch] API raw response: {response.text[:500]}...")
        
        # Process the response and update citations
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"[DEBUG PRINT] Processing {len(response_data)} citation results")
                
                # Create a mapping from citation text to verification results
                verification_results = {}
                for result in response_data:
                    citation_text = result.get('citation', '')
                    if citation_text:
                        clusters = result.get('clusters', [])
                        if clusters:
                            # Use the first cluster (most relevant)
                            cluster = clusters[0]
                            verification_results[citation_text] = {
                                'verified': True,
                                'canonical_name': cluster.get('case_name', ''),
                                'canonical_date': cluster.get('date_filed', '')[:4] if cluster.get('date_filed') else '',  # Extract year
                                'url': f"https://www.courtlistener.com{cluster.get('absolute_url', '')}" if cluster.get('absolute_url') else None,
                                'source': 'CourtListener',
                                'court': cluster.get('court', ''),
                                'docket_number': cluster.get('docket_id', '')
                            }
                        else:
                            verification_results[citation_text] = {
                                'verified': False,
                                'source': 'CourtListener',
                                'error': 'No clusters found'
                            }
                    else:
                        verification_results[citation_text] = {
                            'verified': False,
                            'source': 'CourtListener',
                            'error': 'No citation text in response'
                        }
                
                # Update the citation objects with verification results
                for citation in citations:
                    citation_text = citation.citation
                    if citation_text in verification_results:
                        result = verification_results[citation_text]
                        citation.verified = result.get('verified', False)
                        citation.canonical_name = result.get('canonical_name')
                        citation.canonical_date = result.get('canonical_date')
                        citation.url = result.get('url')
                        citation.source = result.get('source', 'CourtListener')
                        citation.court = result.get('court')
                        citation.docket_number = result.get('docket_number')
                        print(f"[DEBUG PRINT] Updated citation {citation_text}: verified={citation.verified}, canonical_name={citation.canonical_name}")
                    else:
                        # Citation not found in response
                        citation.verified = False
                        citation.source = 'CourtListener'
                        citation.error = 'Citation not found in CourtListener response'
                        print(f"[DEBUG PRINT] Citation {citation_text} not found in CourtListener response")
                
                print(f"[DEBUG PRINT] Updated {len([c for c in citations if c.verified])} citations with verification results")
                
            except json.JSONDecodeError as e:
                print(f"[DEBUG PRINT] Error parsing JSON response: {e}")
                logger.error(f"[CL batch] JSON decode error: {e}")
                # Mark all citations as unverified due to parsing error
                for citation in citations:
                    citation.verified = False
                    citation.source = 'CourtListener'
                    citation.error = f'JSON parsing error: {e}'
        else:
            print(f"[DEBUG PRINT] CourtListener API returned error status: {response.status_code}")
            logger.error(f"[CL batch] API error status: {response.status_code}")
            # Mark all citations as unverified due to API error
            for citation in citations:
                citation.verified = False
                citation.source = 'CourtListener'
                citation.error = f'API error: {response.status_code}'
        
        return response
    except Exception as e:
        print(f"[DEBUG PRINT] Exception during CourtListener batch call: {e}")
        logger.error(f"[CL batch] Exception: {e}")
        # Mark all citations as unverified due to exception
        for citation in citations:
            citation.verified = False
            citation.source = 'CourtListener'
            citation.error = f'Exception: {e}'
        return None

def verify_with_courtlistener(courtlistener_api_key, citation, extracted_case_name=None):
    """
    DEPRECATED: This function is broken and should not be used.
    
    Issues with this function:
    1. Uses wrong request format (data= instead of json=)
    2. Incomplete response parsing logic
    3. Always returns verified=False
    
    Use the correct function from src.courtlistener_verification instead:
    from src.courtlistener_verification import verify_with_courtlistener
    """
    import warnings
    warnings.warn(
        "This verify_with_courtlistener function in citation_verification.py is DEPRECATED and BROKEN. "
        "Use the correct function from src.courtlistener_verification instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    print(f"[DEPRECATED WARNING] Using broken verify_with_courtlistener from citation_verification.py for: {citation}")
    print(f"[DEPRECATED WARNING] This function always returns verified=False. Use src.courtlistener_verification.verify_with_courtlistener instead.")
    
    # Return a clear failure result to avoid silent bugs
    return {
        "canonical_name": None,
        "canonical_date": None,
        "url": None,
        "verified": False,
        "raw": None,
        "source": "DEPRECATED_FUNCTION",
        "error": "This function is deprecated. Use src.courtlistener_verification.verify_with_courtlistener instead."
    }

def verify_citations_with_canonical_service(citations):
    print(f"[DEBUG PRINT] ENTERED verify_citations_with_canonical_service with {len(citations)} citations")
    # ... move logic from unified_citation_processor_v2.py ...
    pass

async def verify_citations_with_legal_websearch(citations):
    """
    Verify citations using trusted legal databases with web search as a fallback.
    Only one verifying source is needed per citation.
    
    Args:
        citations: List of CitationResult objects to verify
        
    Returns:
        List of verified CitationResult objects
    """
    from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
    import logging
    import asyncio
    
    logger = logging.getLogger(__name__)
    logger.info(f"[VERIFY] Starting legal web search verification for {len(citations)} citations")
    
    if not citations:
        return []
        
    try:
        # Initialize the web search engine with experimental engines enabled
        search_engine = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
        verified_citations = []
        
        # Define search methods in order of preference/reliability
        search_methods = [
            ('courtlistener', search_engine.search_courtlistener_web),
            ('justia', search_engine.search_justia),
            ('findlaw', search_engine.search_findlaw),
            ('leagle', search_engine.search_leagle),
            ('casetext', search_engine.search_casetext),
            ('vlex', search_engine.search_vlex),
            ('casemine', search_engine.search_casemine),
            ('openjurist', search_engine.search_openjurist),
            ('google_scholar', search_engine.search_google_scholar),
            ('bing', search_engine.search_bing),
            ('duckduckgo', search_engine.search_duckduckgo)
        ]
        
        for citation in citations:
            if hasattr(citation, 'verified') and citation.verified:
                logger.debug(f"[VERIFY] Citation {citation.citation} already verified, skipping")
                verified_citations.append(citation)
                continue
                
            try:
                logger.info(f"[VERIFY] Processing citation: {citation.citation}")
                case_name = getattr(citation, 'extracted_case_name', None)
                verified = False
                
                # Try each search method in order until we find a match
                for source_name, search_method in search_methods:
                    if not hasattr(search_engine, search_method.__name__):
                        logger.debug(f"[VERIFY] Search method {search_method.__name__} not available, skipping")
                        continue
                        
                    try:
                        logger.debug(f"[VERIFY] Trying {source_name} search for {citation.citation}")
                        # Await the async search method
                        result = await search_method(citation.citation, case_name)
                        
                        if result and result.get('verified', False):
                            logger.info(f"[VERIFY] Verified {citation.citation} via {source_name}")
                            
                            # Update citation with verification data
                            citation.verified = True
                            citation.source = source_name
                            citation.url = result.get('url', '')
                            
                            # Only set canonical data if it comes from a trusted source
                            if source_name in ['courtlistener', 'justia', 'findlaw', 'leagle', 'casetext']:
                                if 'canonical_name' in result:
                                    citation.canonical_name = result['canonical_name']
                                if 'canonical_date' in result:
                                    citation.canonical_date = str(result['canonical_date'])
                            
                            verified = True
                            verified_citations.append(citation)
                            break  # Stop after first successful verification
                            
                    except Exception as e:
                        logger.warning(f"[VERIFY] Error searching {source_name} for {citation.citation}: {str(e)}")
                        continue
                
                if not verified:
                    logger.debug(f"[VERIFY] No verification found for {citation.citation}")
                    
            except Exception as e:
                logger.error(f"[VERIFY] Error processing citation {citation.citation}: {str(e)}", exc_info=True)
                continue
                
        return verified_citations
        
    except Exception as e:
        logger.error(f"[VERIFY] Fatal error in legal web search verification: {str(e)}", exc_info=True)
        return []