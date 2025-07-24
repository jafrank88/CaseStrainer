import requests
import logging
import sys

logger = logging.getLogger(__name__)

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
        return response
    except Exception as e:
        print(f"[DEBUG PRINT] Exception during CourtListener batch call: {e}")
        logger.error(f"[CL batch] Exception: {e}")
        return None

def verify_with_courtlistener(courtlistener_api_key, citation):
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