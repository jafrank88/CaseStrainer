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
    print(f"[DEBUG PRINT] ENTERED verify_with_courtlistener for citation: {citation}")
    result = {
        "canonical_name": None,
        "canonical_date": None,
        "url": None,
        "verified": False,
        "raw": None,
        "source": None
    }
    if courtlistener_api_key:
        headers = {"Authorization": f"Token {courtlistener_api_key}"}
        try:
            lookup_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            lookup_data = {"text": citation}
            print(f"[DEBUG PRINT] About to POST to {lookup_url} with data: {lookup_data}")
            response = requests.post(lookup_url, headers=headers, data=lookup_data, timeout=30)
            print(f"[DEBUG PRINT] CourtListener response status: {response.status_code}")
            print(f"[DEBUG PRINT] CourtListener response body: {response.text[:1000]}")
            result['raw'] = response.text
            # ... existing code to parse response ...
        except Exception as e:
            print(f"[DEBUG PRINT] Exception during CourtListener single call: {e}")
            logger.error(f"[CL citation-lookup] {citation} exception: {e}")
    return result

def verify_citations_with_canonical_service(citations):
    print(f"[DEBUG PRINT] ENTERED verify_citations_with_canonical_service with {len(citations)} citations")
    # ... move logic from unified_citation_processor_v2.py ...
    pass

def verify_citations_with_legal_websearch(citations):
    print(f"[DEBUG PRINT] ENTERED verify_citations_with_legal_websearch with {len(citations)} citations")
    # ... move logic from unified_citation_processor_v2.py ...
    pass 