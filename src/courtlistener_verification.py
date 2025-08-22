import os
import requests
import logging
import sys
import json

# Handle both relative and absolute imports
try:
    from src.name_similarity_matcher import select_best_courtlistener_result, calculate_case_name_similarity
except ImportError:
    from name_similarity_matcher import select_best_courtlistener_result, calculate_case_name_similarity

logger = logging.getLogger(__name__)

def select_best_cluster_from_result(result, extracted_case_name, debug=False):
    """Select the best cluster from a CourtListener result based on name similarity."""
    clusters = result.get('clusters', [])
    
    if not clusters:
        return None
    
    if len(clusters) == 1:
        if debug:
            print(f"[DEBUG] Only one cluster available, using it")
        return clusters[0]
    
    if not extracted_case_name:
        if debug:
            print(f"[DEBUG] No extracted case name, using first cluster")
        return clusters[0]
    
    best_cluster = None
    best_similarity = 0.0
    
    if debug:
        print(f"[DEBUG] Comparing {len(clusters)} clusters to extracted name: '{extracted_case_name}'")
    
    for i, cluster in enumerate(clusters):
        case_name = cluster.get('case_name', '')
        
        if not case_name:
            if debug:
                print(f"[DEBUG] Cluster {i+1}: No case name, skipping")
            continue
        
        similarity = calculate_case_name_similarity(extracted_case_name, case_name)
        
        if debug:
            print(f"[DEBUG] Cluster {i+1}: '{case_name}' - Similarity: {similarity:.3f}")
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_cluster = cluster
    
    # Use a threshold to determine if we found a good match
    similarity_threshold = 0.3
    
    if best_cluster and best_similarity >= similarity_threshold:
        if debug:
            print(f"[DEBUG] Selected cluster with similarity {best_similarity:.3f} (above threshold {similarity_threshold})")
        return best_cluster
    else:
        if debug:
            print(f"[DEBUG] No cluster above similarity threshold {similarity_threshold}, using first cluster")
        return clusters[0]

def verify_citations_with_courtlistener_batch(courtlistener_api_key, citations, text):
    """DEPRECATED: Batch verification is no longer used.
    
    This function has been replaced by individual verification with name similarity matching.
    Use verify_with_courtlistener() for individual citations instead.
    This function will be removed in a future version.
    """
    import warnings
    warnings.warn(
        "verify_citations_with_courtlistener_batch is deprecated. Use individual verification instead.",
        DeprecationWarning,
        stacklevel=2
    )
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
        response = requests.post(url, headers=headers, json=data, timeout=5)
        print(f"[DEBUG PRINT] CourtListener response status: {response.status_code}")
        print(f"[DEBUG PRINT] CourtListener response body: {response.text[:1000]}")
        logger.info(f"[CL batch] API response status: {response.status_code}")
        logger.debug(f"[CL batch] API raw response: {response.text[:500]}...")
        return response
    except Exception as e:
        print(f"[DEBUG PRINT] Exception during CourtListener batch call: {e}")
        logger.error(f"[CL batch] Exception: {e}")
        return None

def verify_with_courtlistener(courtlistener_api_key, citation, extracted_case_name=None):
    """
    Verify a citation with CourtListener using enhanced cross-validation system.
    This replaces the previous two-step verification with a more robust approach.
    """
    
    print(f"[DEBUG PRINT] ENTERED verify_with_courtlistener for citation: {citation}")
    
    # Import the enhanced verification system
    try:
        from src.enhanced_courtlistener_verification import verify_with_courtlistener_enhanced
        
        print(f"[DEBUG PRINT] Using enhanced cross-validation verification")
        result = verify_with_courtlistener_enhanced(courtlistener_api_key, citation, extracted_case_name)
        
        print(f"[DEBUG PRINT] Enhanced verification result: verified={result.get('verified')}, source={result.get('source')}")
        return result
        
    except ImportError as e:
        print(f"[DEBUG PRINT] Enhanced verification not available, falling back to basic verification: {e}")
        
        # Fallback to basic verification if enhanced system is not available
        return _verify_with_courtlistener_basic(courtlistener_api_key, citation, extracted_case_name)

def _verify_with_courtlistener_basic(courtlistener_api_key, citation, extracted_case_name=None):
    """Two-step CourtListener verification with strict validation requiring both canonical name and year"""
    print(f"[DEBUG PRINT] ENTERED _verify_with_courtlistener_basic for citation: {citation}")
    result = {
        "canonical_name": None,
        "canonical_date": None,
        "url": None,
        "verified": False,
        "source": None
    }
    
    if not courtlistener_api_key:
        print(f"[DEBUG PRINT] No CourtListener API key available")
        return result
    
    headers = {"Authorization": f"Token {courtlistener_api_key}"}
    
    # STEP 1: Try citation-lookup API first
    print(f"[DEBUG PRINT] STEP 1: Trying citation-lookup API for {citation}")
    try:
        lookup_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        lookup_data = {"text": citation}
        print(f"[DEBUG PRINT] POST to {lookup_url} with data: {lookup_data}")
        
        response = requests.post(lookup_url, headers=headers, json=lookup_data, timeout=5)
        print(f"[DEBUG PRINT] Citation-lookup response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                api_results = response.json()
                print(f"[DEBUG PRINT] Parsed {len(api_results)} results from citation-lookup")
                result['raw'] = response.text
                
                # Check if any results were found (status != 404)
                found_results = [r for r in api_results if r.get('status') != 404 and r.get('clusters')]
                
                if found_results:
                    print(f"[DEBUG PRINT] Found {len(found_results)} valid results in citation-lookup")
                    
                    # Check if we need name similarity matching
                    needs_similarity_matching = False
                    total_clusters = 0
                    
                    for api_result in found_results:
                        clusters = api_result.get('clusters', [])
                        total_clusters += len(clusters)
                    
                    needs_similarity_matching = extracted_case_name and (len(found_results) > 1 or total_clusters > 1)
                    
                    if needs_similarity_matching:
                        print(f"[DEBUG PRINT] Using name similarity matching: {len(found_results)} results, {total_clusters} total clusters")
                        # For multiple results, use the original function
                        if len(found_results) > 1:
                            best_result = select_best_courtlistener_result(
                                found_results, 
                                extracted_case_name or "", 
                                debug=os.getenv("FLASK_DEBUG", "False").lower() == "true"
                            )
                            cluster = best_result['clusters'][0] if best_result and best_result.get('clusters') else None
                        else:
                            # For single result with multiple clusters, use cluster-level matching
                            best_result = found_results[0]
                            cluster = select_best_cluster_from_result(
                                best_result,
                                extracted_case_name,
                                debug=os.getenv("FLASK_DEBUG", "False").lower() == "true"
                            )
                    else:
                        print(f"[DEBUG PRINT] Using first cluster from first result")
                        # Use first cluster from first result
                        best_result = found_results[0]
                        cluster = best_result['clusters'][0] if best_result.get('clusters') else None
                    
                    if cluster:
                        case_name = cluster.get("case_name")
                        date_filed = cluster.get("date_filed")
                        absolute_url = cluster.get("absolute_url")
                        
                        # STRICT VALIDATION: Require both canonical name and year
                        if case_name and date_filed and absolute_url:
                            print(f"[DEBUG PRINT] Found valid cluster with case name and date: {case_name} ({date_filed})")
                            result.update({
                                "canonical_name": case_name,
                                "canonical_date": date_filed,
                                "url": absolute_url,
                                "verified": True,
                                "source": "CourtListener"
                            })
                            return result
                        else:
                            print(f"[DEBUG PRINT] Cluster missing required data: case_name={case_name}, date_filed={date_filed}, absolute_url={absolute_url}")
                
                print(f"[DEBUG PRINT] No valid clusters found in citation-lookup")
                
            except (KeyError, IndexError) as e:
                print(f"[DEBUG PRINT] Error parsing citation-lookup response: {e}")
                
        elif response.status_code == 404:
            print(f"[DEBUG PRINT] Citation not found in citation-lookup")
        else:
            print(f"[DEBUG PRINT] Citation-lookup returned status: {response.status_code}")
            
    except Exception as e:
        print(f"[DEBUG PRINT] Error in citation-lookup: {e}")
        
    # STEP 2: Fallback to search API
    print(f"[DEBUG PRINT] STEP 2: Trying search API fallback for {citation}")
    try:
        search_url = "https://www.courtlistener.com/api/rest/v4/search/"
        search_params = {
            "type": "opinion",
            "q": f'citation:"{citation}"',
            "format": "json",
            "order_by": "score desc",
            "limit": 1
        }
        print(f"[DEBUG PRINT] GET to {search_url} with params: {search_params}")
        
        response = requests.get(search_url, headers=headers, params=search_params, timeout=5)
        print(f"[DEBUG PRINT] Search API response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                search_results = response.json()
                print(f"[DEBUG PRINT] Search API returned {len(search_results.get('results', []))} results")
                
                if search_results.get('results'):
                    best_result = search_results['results'][0]
                    case_name = best_result.get("case_name")
                    date_filed = best_result.get("date_filed")
                    
                    # STRICT VALIDATION: Require both canonical name and year
                    if case_name and date_filed:
                        print(f"[DEBUG PRINT] Found valid search result with case name and date: {case_name} ({date_filed})")
                        result.update({
                            "canonical_name": case_name,
                            "canonical_date": date_filed,
                            "url": absolute_url,
                            "verified": True,
                            "source": "CourtListener"
                        })
                        print(f"[DEBUG PRINT] SUCCESS: Search API found valid canonical data:")
                        print(f"[DEBUG PRINT]   Name: {result['canonical_name']}")
                        print(f"[DEBUG PRINT]   Date: {result['canonical_date']}")
                        print(f"[DEBUG PRINT]   URL: {result['url']}")
                        print(f"[DEBUG PRINT]   caseName: '{case_name}'")
                        print(f"[DEBUG PRINT]   absolute_url: '{absolute_url}'")
                        print(f"[DEBUG PRINT]   This prevents false positive verification")
                        return result
                    else:
                        print(f"[DEBUG PRINT] Search result missing case name or date")
                else:
                    print(f"[DEBUG PRINT] Search API returned empty results")
                        
            except json.JSONDecodeError as e:
                print(f"[DEBUG PRINT] Failed to parse search API JSON: {e}")
                logger.error(f"[CL search] {citation} JSON decode error: {e}")
        else:
            print(f"[DEBUG PRINT] Search API error: {response.status_code}")
            
    except Exception as e:
        print(f"[DEBUG PRINT] Exception in search API: {e}")
        logger.error(f"[CL search] {citation} exception: {e}")
    
    print(f"[DEBUG PRINT] Both citation-lookup and search APIs failed for {citation}")
    return result 