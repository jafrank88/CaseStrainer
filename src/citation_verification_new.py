    def verify_citation(self, citation: str, context: str = None) -> Dict[str, Any]:
        """
        Verify a citation using multiple methods with fallback.
        
        Args:
            citation: The legal citation to verify
            context: Optional context around the citation (text before and after)
            
        Returns:
            Dict with verification results including whether the citation is valid and its source.
        """
        print(f"DEBUG: Starting verification for citation: {citation}")
        logging.info(f"[DEBUG] Starting verification for citation: {citation}")
        
        # Check if this is a Westlaw citation
        is_westlaw = bool(re.search(r'\d+\s+WL\s+\d+', citation, re.IGNORECASE))
        is_us_citation = bool(re.search(r'\d+\s+U\.?\s*S\.?\s+\d+', citation, re.IGNORECASE))
        is_f3d_citation = bool(re.search(r'\d+\s+F\.?\s*3d\s+\d+', citation, re.IGNORECASE))
        is_sct_citation = bool(re.search(r'\d+\s+S\.?\s*Ct\.?\s+\d+', citation, re.IGNORECASE))
        
        result = {
            'citation': citation,
            'found': False,
            'source': None,
            'case_name': None,
            'url': None,
            'details': {},
            'explanation': None,
            'is_westlaw': is_westlaw
        }

        # First, try to verify using the CourtListener Citation Lookup API
        try:
            print(f"DEBUG: Trying CourtListener Citation Lookup API for: {citation}")
            logging.info(f"[DEBUG] Trying CourtListener Citation Lookup API for: {citation}")
            
            api_result = self.verify_with_courtlistener_citation_api(citation)
            
            if api_result.get('found'):
                print(f"DEBUG: Citation verified by CourtListener API: {citation}")
                logging.info(f"[DEBUG] Citation verified by CourtListener API: {citation}")
                return api_result
            else:
                print(f"DEBUG: Citation not found in CourtListener API: {citation}")
                logging.info(f"[DEBUG] Citation not found in CourtListener API: {citation}")
                # Store the explanation from the API result for later use
                if api_result.get('explanation'):
                    result['explanation'] = api_result['explanation']
        except Exception as e:
            print(f"DEBUG: Error using CourtListener Citation API: {str(e)}")
            logging.error(f"[ERROR] Error using CourtListener Citation API: {str(e)}")
            # Continue with fallback methods

        # If the API call failed or didn't find the citation, try other methods
        if USE_ENHANCED_VALIDATOR:
            logging.info(f"[DEBUG] Using Enhanced Validator mode for '{citation}'")
            print(f"DEBUG: Using Enhanced Validator mode")
            
            # Try the CourtListener Search API as a fallback
            try:
                print(f"DEBUG: Trying CourtListener Search API for: {citation}")
                logging.info(f"[DEBUG] Trying CourtListener Search API for: {citation}")
                
                search_result = self.verify_with_courtlistener_search_api(citation)
                if search_result.get('found'):
                    print(f"DEBUG: Citation verified by CourtListener Search API: {citation}")
                    logging.info(f"[DEBUG] Citation verified by CourtListener Search API: {citation}")
                    return search_result
                else:
                    print(f"DEBUG: Citation not found in CourtListener Search API: {citation}")
                    logging.info(f"[DEBUG] Citation not found in CourtListener Search API: {citation}")
                    # Store the explanation from the search result
                    if search_result.get('explanation'):
                        result['explanation'] = search_result['explanation']
            except Exception as e:
                print(f"DEBUG: Error using CourtListener Search API: {str(e)}")
                logging.error(f"[ERROR] Error using CourtListener Search API: {str(e)}")
                # Continue with other fallback methods

            # Try the LangSearch API as a backup
            try:
                print(f"DEBUG: Trying LangSearch API for: {citation}")
                logging.info(f"[DEBUG] Trying LangSearch API for: {citation}")
                
                lang_result = self.verify_with_langsearch_api(citation)
                if lang_result.get('found'):
                    print(f"DEBUG: Citation verified by LangSearch API: {citation}")
                    logging.info(f"[DEBUG] Citation verified by LangSearch API: {citation}")
                    return lang_result
                else:
                    print(f"DEBUG: Citation not found in LangSearch API: {citation}")
                    logging.info(f"[DEBUG] Citation not found in LangSearch API: {citation}")
                    # Store the explanation from the LangSearch result
                    if lang_result.get('explanation'):
                        result['explanation'] = lang_result['explanation']
            except Exception as e:
                print(f"DEBUG: Error using LangSearch API: {str(e)}")
                logging.error(f"[ERROR] Error using LangSearch API: {str(e)}")
                # Continue with final fallback

            # Try Google Scholar as a last resort
            try:
                print(f"DEBUG: Trying Google Scholar for: {citation}")
                logging.info(f"[DEBUG] Trying Google Scholar for: {citation}")
                
                scholar_result = self.verify_with_google_scholar(citation)
                if scholar_result.get('found'):
                    print(f"DEBUG: Citation verified by Google Scholar: {citation}")
                    logging.info(f"[DEBUG] Citation verified by Google Scholar: {citation}")
                    return scholar_result
                else:
                    print(f"DEBUG: Citation not found in Google Scholar: {citation}")
                    logging.info(f"[DEBUG] Citation not found in Google Scholar: {citation}")
                    # Store the explanation from the Scholar result
                    if scholar_result.get('explanation'):
                        result['explanation'] = scholar_result['explanation']
            except Exception as e:
                print(f"DEBUG: Error using Google Scholar: {str(e)}")
                logging.error(f"[ERROR] Error using Google Scholar: {str(e)}")
                # This is our last attempt, so we'll return whatever we have

            # If we get here, none of the verification methods worked
            return result
