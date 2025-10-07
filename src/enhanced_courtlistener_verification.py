"""
Enhanced CourtListener verification with cross-validation to prevent false positives
"""

import re
import json
import logging
import time
from typing import Dict, Optional, List, Any, Tuple, Union

from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT
import requests

from src.enhanced_case_name_matcher import enhanced_matcher, is_likely_same_case

logger = logging.getLogger(__name__)

def _deprecated_warning():
    """Issue deprecation warning for EnhancedCourtListenerVerifier."""
    import warnings
    warnings.warn(
        "EnhancedCourtListenerVerifier is deprecated and will be removed in v3.0.0. "
        "Use unified verification system in cluster_citations_unified() instead.",
        DeprecationWarning,
        stacklevel=3
    )

class EnhancedCourtListenerVerifier:
    """Enhanced verification with cross-validation between API endpoints"""
    
    def __init__(self, api_key: str):
        _deprecated_warning()  # Issue deprecation warning
        self.api_key = api_key
        self.headers = {"Authorization": f"Token {api_key}"}
    
    def verify_citation_enhanced(self, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
        """
        DEPRECATED: Use verify_citation_unified_master_sync() instead.
        
        This function now delegates to the new unified master implementation
        that consolidates all 80+ duplicate verification functions.
        
        MIGRATION: Replace calls with:
        from src.unified_verification_master import verify_citation_unified_master_sync
        """
        import warnings
        warnings.warn(
            "EnhancedCourtListenerVerifier.verify_citation_enhanced() is deprecated. Use verify_citation_unified_master_sync() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Delegate to the new master implementation
        from src.unified_verification_master import verify_citation_unified_master_sync
        return verify_citation_unified_master_sync(
            citation=citation,
            extracted_case_name=extracted_case_name
        )
        result = {
            "citation": citation,
            "extracted_case_name": extracted_case_name,
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "source": None,
            "confidence": 0.0,
            "validation_method": "none",
            "raw": None,
            "warnings": []
        }
        
        # Check for test citation
        if self._is_test_citation(citation):
            logger.warning(f"[VERIFICATION] Test citation detected and rejected: {citation}")
            return {
                **result,
                "source": "test_citation_rejected",
                "validation_method": "test_citation_filter",
                "verified": False,
                "confidence": 0.0
            }
        
        result = {
            "citation": citation,
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None,
            "source": None,
            "confidence": 0.0,
            "validation_method": "citation_lookup_v4"
        }
        
        # First try the citation as-is
        lookup_result = self._verify_with_citation_lookup_v4_enhanced(citation, extracted_case_name)
        
        # If that fails and it's a state court citation, try alternative formats
        if not lookup_result['verified'] and self._is_state_court_citation(citation):
            print(f"[ENHANCED] Trying alternative formats for state court citation: {citation}")
            alt_formats = self._get_alternative_citation_formats(citation)
            
            for alt_cite in alt_formats:
                print(f"[ENHANCED] Trying alternative format: {alt_cite}")
                alt_result = self._verify_with_citation_lookup_v4_enhanced(alt_cite, extracted_case_name)
                if alt_result['verified']:
                    lookup_result = alt_result
                    lookup_result['original_citation'] = citation
                    break
        
        # If we have a result, update the main result
        if lookup_result['verified']:
            result.update(lookup_result)
            result['validation_method'] = "citation_lookup_v4_success"
            result['confidence'] = 0.95  # High confidence for citation-lookup matches
            
            # If this is a parallel citation, store the parallel citation info
            if 'parallel_citations' in lookup_result:
                result['parallel_citations'] = lookup_result['parallel_citations']
                
            print(f"[ENHANCED] Citation-lookup succeeded - using citation-lookup data")
        else:
            print(f"[ENHANCED] Citation-lookup failed for: {citation}")
            
            # If we have an extracted case name and the citation looks valid, use it with lower confidence
            if extracted_case_name and self._is_valid_citation_format(citation):
                result.update({
                    'canonical_name': extracted_case_name,
                    'verified': True,
                    'confidence': 0.7,
                    'validation_method': 'extracted_name_validation',
                    'source': 'extracted_with_validation'
                })
                print(f"[ENHANCED] Using extracted case name with validation for: {citation}")
            else:
                result['verified'] = False
                result['validation_method'] = "citation_lookup_v4_failed"
                result['confidence'] = 0.0
        
        return result
    
    def verify_citations_batch(self, citations: List[str], extracted_case_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Verify multiple citations using individual verification requests.
        
        Note: This method processes each citation individually since the batch API endpoint
        has issues with the required request format.
        
        Args:
            citations: List of citation strings to verify
            extracted_case_names: Optional list of extracted case names (must match citations length)
            
        Returns:
            Dictionary with verification results for each citation
        """
        if not citations:
            return {}
        
        if extracted_case_names and len(extracted_case_names) != len(citations):
            logger.warning("extracted_case_names length doesn't match citations length")
            extracted_case_names = [None] * len(citations)
        
        results = {}
        
        try:
            # Process each citation individually to ensure consistent behavior with single verification
            for i, citation in enumerate(citations):
                case_name = extracted_case_names[i] if extracted_case_names and i < len(extracted_case_names) else None
                results[citation] = self.verify_citation_enhanced(citation, case_name)
                
            logger.info(f"Successfully processed {len(citations)} citations")
            
        except Exception as e:
            logger.error(f"Error in batch verification: {str(e)}", exc_info=True)
            # If there's an error, try to process as many citations as possible
            for i, citation in enumerate(citations):
                if citation not in results:
                    try:
                        case_name = extracted_case_names[i] if extracted_case_names and i < len(extracted_case_names) else None
                        results[citation] = self.verify_citation_enhanced(citation, case_name)
                    except Exception as inner_e:
                        logger.error(f"Error processing citation {citation}: {str(inner_e)}")
                        results[citation] = {
                            "citation": citation,
                            "canonical_name": None,
                            "canonical_date": None,
                            "url": None,
                            "verified": False,
                            "raw": None,
                            "source": "error",
                            "confidence": 0.0,
                            "validation_method": "error",
                            "error": str(inner_e)
                        }
        
        return results
    
    def _process_batch_citation_result(self, citation: str, extracted_case_name: Optional[str], api_result: Optional[Dict]) -> Dict:
        """Process a single citation result from batch API response.
        
        Args:
            citation: The citation string being verified
            extracted_case_name: Optional extracted case name for additional validation
            api_result: The API response data for this citation
            
        Returns:
            Dictionary with verification results for the citation
        """
        result = {
            "citation": citation,
            "canonical_name": None,
            "canonical_date": None,
            "canonical_url": None,
            "verified": False,
            "raw": api_result,
            "source": "courtlistener_batch",
            "confidence": 0.0,
            "validation_method": "citation_lookup_v4"
        }
        
        # If we have a direct API result for this citation
        if api_result and isinstance(api_result, dict):
            # Handle case where the API returned a successful verification
            if 'citation' in api_result and 'case_name' in api_result:
                result.update({
                    "canonical_name": api_result.get('case_name'),
                    "canonical_date": api_result.get('date_filed', '').split('-')[0] if api_result.get('date_filed') else None,
                    "canonical_url": f"https://www.courtlistener.com{api_result.get('absolute_url', '')}" if api_result.get('absolute_url') else None,
                    "verified": True,
                    "confidence": 0.9,
                    "validation_method": "citation_lookup_v4_success"
                })
            # Handle case where the API returned an error
            elif 'status' in api_result and api_result['status'] == 'error':
                result.update({
                    "verified": False,
                    "confidence": 0.0,
                    "validation_method": f"citation_lookup_v4_error_{api_result.get('error_type', 'unknown')}",
                    "error": api_result.get('message', 'Unknown error')
                })
        
        # If we have an extracted case name but no verification, try to match it
        if not result['verified'] and extracted_case_name:
            # Simple validation: check if the citation format looks valid
            if self._is_valid_citation_format(citation):
                result.update({
                    "verified": True,
                    "confidence": 0.7,  # Medium confidence for unverified but well-formatted citations
                    "validation_method": "format_validation",
                    "canonical_name": extracted_case_name,
                    "source": "extracted"
                })
        
        return result
    
    def _is_state_court_citation(self, citation: str) -> bool:
        """Check if a citation is from a state court.
        
        Args:
            citation: The citation string to check
            
        Returns:
            bool: True if the citation is from a state court, False otherwise
        """
        state_reporters = [
            r'Wn\.?2d',  # Washington Reports, 2nd series
            r'Wn\.?',    # Washington Reports
            r'P\.?2d',   # Pacific Reporter, 2nd series
            r'P\.?3d',   # Pacific Reporter, 3rd series
            r'P\.?',     # Pacific Reporter
            r'Cal\.?',   # California Reports
            r'Cal\.?\s*App\.?',  # California Appellate Reports
            r'N\.?Y\.?S\.?',    # New York Supplement
            r'N\.?E\.?',        # North Eastern Reporter
            r'N\.?W\.?',        # North Western Reporter
            r'S\.?E\.?',        # South Eastern Reporter
            r'S\.?W\.?',        # South Western Reporter
            r'So\.?',           # Southern Reporter
            r'A\.?2d',          # Atlantic Reporter, 2nd series
            r'A\.?',            # Atlantic Reporter
        ]
        
        # Check if the citation contains any state reporter abbreviation
        for reporter in state_reporters:
            if re.search(reporter, citation, re.IGNORECASE):
                return True
                
        return False
        
    def _get_alternative_citation_formats(self, citation: str) -> List[str]:
        """Generate alternative citation formats for a given citation.
        
        This is particularly useful for state court citations that might be
        reported in multiple reporters.
        
        Args:
            citation: The original citation
            
        Returns:
            List[str]: List of alternative citation formats to try
        """
        alternatives = []
        
        # Extract components from the citation
        parts = re.split(r'\s+', citation.strip())
        if len(parts) < 3:
            return alternatives
            
        volume = parts[0]
        reporter = parts[1]
        page = parts[2]
        
        # Common state court citation patterns
        if re.match(r'Wn\.?2d', reporter, re.IGNORECASE):
            # Washington Reports, 2nd series
            alternatives.append(f"{volume} Wash.2d {page}")
            alternatives.append(f"{volume} Wn. App. {page}")  # Check Court of Appeals
            alternatives.append(f"{volume} Wn {page}")  # Check older reports
            
        elif re.match(r'P\.?3d', reporter, re.IGNORECASE):
            # Pacific Reporter, 3rd series
            alternatives.append(f"{volume} P.2d {page}")  # Check 2nd series
            alternatives.append(f"{volume} P. {page}")    # Check 1st series
            
        elif re.match(r'P\.?2d', reporter, re.IGNORECASE):
            # Pacific Reporter, 2nd series
            alternatives.append(f"{volume} P.3d {page}")  # Check 3rd series
            alternatives.append(f"{volume} P. {page}")    # Check 1st series
            
        elif re.match(r'P\.?', reporter, re.IGNORECASE):
            # Pacific Reporter, 1st series
            alternatives.append(f"{volume} P.2d {page}")  # Check 2nd series
            alternatives.append(f"{volume} P.3d {page}")  # Check 3rd series
            
        # Add variations with and without periods
        if '.' in reporter:
            alternatives.append(citation.replace('.', ''))
        else:
            # Try adding periods if they're missing
            if len(reporter) > 1 and not reporter.endswith('.'):
                with_period = f"{reporter[0]}.{reporter[1:]}"
                alternatives.append(citation.replace(reporter, with_period, 1))
        
        return alternatives
        
    def _clean_citation(self, citation: str) -> str:
        """Clean and standardize a citation string.
        
        Args:
            citation: The citation string to clean
            
        Returns:
            str: The cleaned citation
        """
        # Remove extra whitespace
        cleaned = ' '.join(citation.split())
        
        # Standardize common reporter abbreviations
        replacements = [
            (r'\bWash\.?\s*2d\b', 'Wn.2d'),
            (r'\bWash\.?\s*App\.?\b', 'Wn. App.'),
            (r'\bP\.?\s*2d\b', 'P.2d'),
            (r'\bP\.?\s*3d\b', 'P.3d'),
            (r'\bU\.?\s*S\.?\b', 'U.S.'),
            (r'\bS\.?\s*Ct\.?\b', 'S. Ct.'),
            (r'\bL\.?\s*Ed\.?\s*2d\b', 'L. Ed. 2d'),
            (r'\bL\.?\s*Ed\.?\b', 'L. Ed.'),
            (r'\bF\.?\s*Supp\.?\s*2d\b', 'F. Supp. 2d'),
            (r'\bF\.?\s*Supp\.?\b', 'F. Supp.'),
        ]
        
        for pattern, replacement in replacements:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
            
        return cleaned.strip()
    
    def _clean_case_name(self, case_name: str) -> str:
        """Clean and standardize a case name.
        
        Args:
            case_name: The case name to clean
            
        Returns:
            str: The cleaned case name
        """
        if not case_name:
            return ""
            
        # Remove extra whitespace and standardize spacing
        cleaned = ' '.join(case_name.split())
        
        # Remove common prefixes/suffixes
        prefixes = [
            'In re ', 'In the Matter of ', 'Matter of ', 'Ex parte ', 'Ex rel. ',
            'State of ', 'Commonwealth of ', 'People of the State of '
        ]
        
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
                
        # Standardize v. vs. v vs. vs
        cleaned = re.sub(r'\b(vs?\.?|versus)\b', 'v.', cleaned, flags=re.IGNORECASE)
        
        # Remove any remaining extra spaces
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def _calculate_cluster_score(self, cluster: Dict, citation: str, extracted_case_name: Optional[str]) -> float:
        """Calculate a relevance score for a cluster.
        
        Args:
            cluster: The cluster from CourtListener
            citation: The original citation
            extracted_case_name: Optional extracted case name
            
        Returns:
            float: A score between 0 and 1 indicating relevance
        """
        score = 0.0
        
        # Check if any citation in the cluster matches exactly
        for cite in cluster.get('citations', []):
            cite_str = f"{cite.get('volume', '')} {cite.get('reporter', '')} {cite.get('page', '')}"
            if cite_str.strip() == citation.strip():
                score += 0.5  # Exact match bonus
                break
        
        # Check case name similarity if we have an extracted case name
        if extracted_case_name and 'case_name' in cluster:
            cleaned_cluster_name = self._clean_case_name(cluster['case_name'])
            cleaned_extracted_name = self._clean_case_name(extracted_case_name)
            
            # Simple word overlap
            cluster_words = set(cleaned_cluster_name.lower().split())
            extracted_words = set(cleaned_extracted_name.lower().split())
            
            # Remove common words
            common_words = {'v', 'in', 're', 'ex', 'parte', 'matter', 'of', 'the', 'and', 'et', 'al'}
            cluster_words -= common_words
            extracted_words -= common_words
            
            if cluster_words and extracted_words:
                overlap = len(cluster_words & extracted_words)
                union = len(cluster_words | extracted_words)
                jaccard = overlap / union if union > 0 else 0
                score += jaccard * 0.5  # Weight for name similarity
        
        # Normalize to 0-1 range
        return min(1.0, max(0.0, score))
    
    def _process_parallel_citations(self, result: Dict, cluster: Dict, original_citation: str) -> None:
        """Process parallel citations from a cluster.
        
        Args:
            result: The result dict to update
            cluster: The cluster from CourtListener
            original_citation: The original citation that was looked up
        """
        if 'citations' not in cluster or len(cluster['citations']) <= 1:
            return
            
        parallel_cites = []
        
        for cite in cluster['citations']:
            if not all(key in cite for key in ['volume', 'reporter', 'page']):
                continue
                
            cite_str = f"{cite['volume']} {cite['reporter']} {cite['page']}"
            if cite_str == original_citation:
                continue  # Skip the original citation
                
            parallel_cites.append({
                'volume': cite['volume'],
                'reporter': cite['reporter'],
                'page': cite['page'],
                'type': cite.get('type', '')
            })
        
        if parallel_cites:
            result['parallel_citations'] = parallel_cites
    
    def _enhance_state_court_result(self, result: Dict, cluster: Dict, extracted_case_name: Optional[str]) -> None:
        """Enhance results for state court citations.
        
        Args:
            result: The result dict to update
            cluster: The cluster from CourtListener
            extracted_case_name: Optional extracted case name
        """
        # Add state court specific metadata
        if 'docket_number' in cluster:
            result['docket_number'] = cluster['docket_number']
            
        if 'court' in cluster and cluster['court']:
            result['court'] = cluster['court'].get('name_abbreviation', '')
            
        # If we have parallel citations, try to find a national reporter citation
        if 'parallel_citations' in result and result['parallel_citations']:
            for cite in result['parallel_citations']:
                reporter = cite.get('reporter', '').lower()
                if 'p.2d' in reporter or 'p.3d' in reporter or 'f.2d' in reporter or 'f.3d' in reporter:
                    result['national_reporter_citation'] = f"{cite['volume']} {cite['reporter']} {cite['page']}"
                    break
    
    def _is_valid_citation_format(self, citation: str) -> bool:
        """Check if a citation has a valid format.
        
        Args:
            citation: The citation string to validate
            
        Returns:
            bool: True if the citation has a valid format, False otherwise
        """
        # Common patterns for legal citations
        patterns = [
            # Washington Reports (e.g., 183 Wn.2d 649)
            r'^\d+\s+Wn\.?\s*\d*[a-z]?\s+\d+',
            # Pacific Reporter (e.g., 976 P.2d 1229)
            r'^\d+\s+P\.?\s*\d*[a-z]?\s+\d+',
            # U.S. Reports (e.g., 578 U.S. 5)
            r'^\d+\s+U\.?\s*S\.?\s+\d+',
            # Supreme Court Reporter (e.g., 136 S. Ct. 1937)
            r'^\d+\s+S\.?\s*Ct\.?\s+\d+',
            # Federal Reporter (e.g., 987 F.2d 1234)
            r'^\d+\s+F\.?\s*\d*[a-z]?\s+\d+',
            # Federal Supplement (e.g., 123 F. Supp. 2d 456)
            r'^\d+\s+F\.?\s*Supp\.?\s*\d*[a-z]?\s+\d+',
            # Federal Rules Decisions (e.g., 123 F.R.D. 123)
            r'^\d+\s+F\.?\s*R\.?\s*D\.?\s+\d+',
            # U.S. Supreme Court Reports, Lawyer's Edition (e.g., 194 L. Ed. 2d 256)
            r'^\d+\s+L\.?\s*Ed\.?\s*\d*[a-z]?\s+\d+',
            # U.S. Law Week (e.g., 88 U.S.L.W. 1234)
            r'^\d+\s+U\.?\s*S\.?\s*L\.?\s*W\.?\s+\d+',
            # State court citations with various reporters
            r'^\d+\s+\w+\.?\s*\d*[a-z]?\s+\d+',
        ]
        
        # Check if the citation matches any of the patterns
        for pattern in patterns:
            if re.fullmatch(pattern, citation, re.IGNORECASE):
                return True
                
        return False
        
    def _find_best_case_with_strict_criteria(self, clusters: List[Dict], citation: str, extracted_case_name: Optional[str]) -> Optional[Dict]:
        """
        Find the best case using strict criteria:
        1. Same year and citation
        2. At least one non-stopword in common between extracted and canonical names
        
        Args:
            clusters: List of case clusters from CourtListener API
            citation: Citation text to match
            extracted_case_name: Extracted case name from document
            
        Returns:
            Best matching case or None
        """
        if not clusters:
            return None
        
        best_match = None
        best_score = 0.0
        
        for cluster in clusters:
            score = self._calculate_strict_match_score(cluster, citation, extracted_case_name)
            if score > best_score:
                best_score = score
                best_match = cluster
        
        if best_match and best_score >= 1.0:  # Reduced from 1.5 to 1.0 for more leniency
            print(f"[ENHANCED] Primary case found with score {best_score:.3f}: {best_match.get('case_name')}")
            return best_match
        
        return None
    
    def _calculate_strict_match_score(self, case: Dict, citation: str, extracted_case_name: Optional[str]) -> float:
        """
        Calculate match score using strict criteria.
        
        Returns:
            float: Score >= 1.5 for a match, 0.0 for no match
        """
        score = 0.0
        
        case_citations = case.get('citations', [])
        citation_found = False
        
        
        for case_citation in case_citations:
            if case_citation.get('volume') and case_citation.get('reporter') and case_citation.get('page'):
                case_citation_str = f"{case_citation['volume']} {case_citation['reporter']} {case_citation['page']}"
                
                if self._citations_match(citation, case_citation_str):
                    citation_found = True
                    break
                else:
                    continue  # Check next citation
        
        if not citation_found:
            return 0.0
        
        score += 1.0
        
        exp_year = self._extract_year_from_citation(citation)
        can_year = self._extract_year_from_date(case.get('date_filed') or '')
        
        
        if exp_year and can_year:
            try:
                year_diff = abs(int(exp_year) - int(can_year))
                if year_diff == 0:
                    score += 1.0  # Exact match
                elif year_diff <= 5:  # Allow up to 5 years difference
                    score += 0.5
                elif year_diff <= 10:  # Allow up to 10 years with penalty
                    score += 0.2
            except (ValueError, TypeError):
                score += 0.3
        else:
            score += 0.3
        
        if extracted_case_name:
            if self._has_meaningful_words_in_common(extracted_case_name, case.get('case_name', '')):
                score += 1.0
            else:
                score += 0.5  # Moderate bonus for continuing
        else:
            score += 0.5
        
        return score
    
    def _extract_year_from_citation(self, citation: str) -> Optional[str]:
        """Extract year from citation text."""
        import re
        year_match = re.search(r'(19|20)\d{2}', citation)
        return year_match.group(0) if year_match else None
    
    def _extract_year_from_date(self, date_str: str) -> Optional[str]:
        """Extract year from date string."""
        if not date_str:
            return None
        
        import re
        year_match = re.search(r'(19|20)\d{2}', str(date_str))
        return year_match.group(0) if year_match else None
    
    def _citations_match(self, citation1: str, citation2: str) -> bool:
        """Check if two citations match (allowing for reporter variations)."""
        if not citation1 or not citation2:
            return False
        
        norm1 = self._normalize_citation(citation1)
        norm2 = self._normalize_citation(citation2)
        
        return norm1 == norm2
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for comparison."""
        norm = citation.replace(' ', '').lower()
        
        norm = norm.replace('wn.', 'wn').replace('wash.', 'wn')
        norm = norm.replace('wn2d', 'wn2d').replace('wash2d', 'wn2d')
        norm = norm.replace('wnapp', 'wnapp').replace('washapp', 'wnapp')
        
        norm = norm.replace('wash.app.', 'wnapp').replace('wash.app', 'wnapp')
        norm = norm.replace('wash.2d', 'wn2d').replace('wash.2d.', 'wn2d')
        
        norm = norm.replace('p.', 'p').replace('pac.', 'p')
        norm = norm.replace('p2d', 'p2d').replace('pac2d', 'p2d')
        norm = norm.replace('p3d', 'p3d').replace('pac3d', 'p3d')
        
        return norm
    
    def _has_meaningful_words_in_common(self, name1: str, name2: str) -> bool:
        """
        Check if two case names have at least one meaningful (non-stopword) word in common.
        
        Args:
            name1: First case name
            name2: Second case name
            
        Returns:
            True if they share at least one meaningful word
        """
        if not name1 or not name2:
            return False
        
        stopwords = {
            'in', 're', 'of', 'the', 'and', 'or', 'for', 'to', 'a', 'an', 'v', 'vs', 'versus',
            'petition', 'petitioner', 'respondent', 'appellant', 'appellee', 'plaintiff', 'defendant',
            'state', 'united', 'states', 'county', 'city', 'town', 'village', 'corporation',
            'inc', 'llc', 'ltd', 'co', 'company', 'association', 'foundation', 'trust'
        }
        
        words1 = set(self._extract_meaningful_words(name1, stopwords))
        words2 = set(self._extract_meaningful_words(name2, stopwords))
        
        common_words = words1.intersection(words2)
        
        if len(common_words) == 0:
            return False
        
        if len(common_words) >= 1:
            return True
        
        return True
        
        print(f"  Name1: '{name1}' -> {words1}")
        print(f"  Name2: '{name2}' -> {words2}")
        print(f"  Common words: {common_words}")
        print(f"  Total score: {total_score}, Max possible: {max_possible_score}")
        print(f"  Normalized score: {normalized_score:.3f}, Required: {min_score}")
        
        return normalized_score >= min_score
    
    def _extract_meaningful_words(self, name: str, stopwords: set) -> List[str]:
        """Extract meaningful (non-stopword) words from a case name."""
        if not name:
            return []
        
        words = re.findall(r'\b[a-zA-Z]+\b', name.lower())
        meaningful_words = [word for word in words if word not in stopwords and len(word) > 2]
        
        return meaningful_words
    
    def _create_failed_batch_result(self, citation: str) -> Dict:
        """Create a result for a failed batch verification."""
        return {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None,
            "source": "CourtListener Batch API",
            "confidence": 0.0,
            "validation_method": "batch_failed",
            "error": "Batch verification failed"
        }
    
    def _verify_with_search_api(self, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
        """Verify using search API with fuzzy case name matching - focus on PRIMARY cases"""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None
        }
        
        try:
            
            if extracted_case_name:
                search_query = extracted_case_name
                citation_filter = citation
                
                best_result = self._search_for_primary_case_multiple_strategies(
                    extracted_case_name, citation, citation_filter
                )
                
                if best_result:
                    result.update({
                        "canonical_name": best_result.get('caseName', ''),
                        "canonical_date": best_result.get('dateFiled', ''),
                        "url": self._normalize_url(best_result.get('absolute_url', '')),
                        "verified": True,
                        "source": "CourtListener Search API"
                    })
                    
                    similarity = enhanced_matcher.calculate_similarity(
                        extracted_case_name, 
                        best_result.get('caseName', '')
                    )
                    result['confidence'] = min(0.9, 0.6 + similarity * 0.3)
            else:
                search_query = citation
                citation_filter = None
                
                url = f"https://www.courtlistener.com/api/rest/v4/search/"
                params = {
                    'q': search_query,
                    'format': 'json',
                    'stat_Precedential': 'on',  # Only published opinions
                    'type': 'o',  # Opinions only
                    'order_by': 'dateFiled desc'  # Most recent first
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    api_results = response.json()
                    result['raw'] = response.text
                    
                    found_results = [r for r in api_results.get('results', []) if r.get('status') != 404]
                    
                    if found_results:
                        best_result = self._find_primary_case_with_enhanced_matching(
                            found_results, extracted_case_name, citation, citation_filter
                        )
                        
                        if best_result:
                            result.update({
                                "canonical_name": best_result.get('caseName', ''),
                                "canonical_date": best_result.get('dateFiled', ''),
                                "url": best_result.get('absolute_url', ''),
                                "verified": True,
                                "source": "CourtListener Search API"
                            })
                            
                            result['confidence'] = 0.7
                
        except Exception as e:
            print(f"[ENHANCED] Search API error: {e}")
            logger.error(f"Search API error: {e}")
        
        return result
    
    def _verify_with_citation_lookup(self, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
        """Verify using citation-lookup API with citation-first search strategy"""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None
        }
        
        try:
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            data = {"text": citation}
            
            response = requests.post(url, headers=self.headers, json=data, timeout=DEFAULT_REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                api_results = response.json()
                result['raw'] = response.text
                
                found_results = [r for r in api_results if r.get('status') != 404 and r.get('clusters')]
                
                if found_results:
                    best_result = self._find_primary_case_with_enhanced_matching(
                        found_results, extracted_case_name, citation, citation
                    )
                    
                    if best_result:
                        result.update({
                            "canonical_name": best_result.get('caseName', ''),
                            "canonical_date": best_result.get('dateFiled', ''),
                            "url": self._normalize_url(best_result.get('absolute_url', '')),
                            "verified": True,
                            "source": "CourtListener Citation-Lookup API"
                        })
                        
                        if extracted_case_name:
                            similarity = enhanced_matcher.calculate_similarity(
                                extracted_case_name, 
                                best_result.get('caseName', '')
                            )
                            result['confidence'] = min(0.9, 0.6 + similarity * 0.3)
                        else:
                            result['confidence'] = 0.7
                
        except Exception as e:
            print(f"[ENHANCED] Citation-lookup API error: {e}")
            logger.error(f"Citation-lookup API error: {e}")
        """
        Enhanced verification using CourtListener's citation-lookup API v4.
        
        Args:
            citation: The citation to verify
            extracted_case_name: Optional extracted case name for additional validation
            
        Returns:
            Dict with verification results
        """
        logger.info(f"[API] Starting citation lookup for: {citation}")
        
        result = {
            "citation": citation,
            "extracted_case_name": extracted_case_name,
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "source": "courtlistener_v4",
            "confidence": 0.0,
            "validation_method": "citation_lookup_v4",
            "raw": None,
            "warnings": [],
            "api_requests": []
        }
        
        try:
            # Clean the citation to handle common formatting issues
            cleaned_citation = self._clean_citation(citation)
            logger.info(f"[API] Cleaned citation: {cleaned_citation}")
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare the request data
            request_data = {"citation": cleaned_citation}
            
            # Add extracted case name if available for better matching
            if extracted_case_name:
                request_data["case_name"] = extracted_case_name
            
            logger.info(f"[ENHANCED] Sending request to CourtListener API: {cleaned_citation}")
            
            response = requests.post(
                url,
                headers=headers,
                json=request_data,
                timeout=15  # Increased timeout for better reliability
            )
            
            if response.status_code == 200:
                data = response.json()
                result["raw"] = data
                
                # Check if we have any results
                if data and "clusters" in data and data["clusters"]:
                    # Sort clusters by relevance (prioritize exact matches)
                    clusters = sorted(
                        data["clusters"],
                        key=lambda x: self._calculate_cluster_score(x, citation, extracted_case_name),
                        reverse=True
                    )
                    
                    # Get the best matching cluster
                    best_cluster = clusters[0]
                    
                    # Extract case information
                    case_name = best_cluster.get("case_name")
                    date_filed = best_cluster.get("date_filed")
                    absolute_url = best_cluster.get("absolute_url")
                    
                    if case_name and date_filed:
                        # Clean up the case name
                        case_name = self._clean_case_name(case_name)
                        
                        # Extract year from date
                        year = date_filed.split("-")[0] if date_filed else None
                        
                        # Build the full URL if we have a path
                        full_url = f"https://www.courtlistener.com{absolute_url}" if absolute_url else None
                        
                        result.update({
                            "canonical_name": case_name,
                            "canonical_date": year,
                            "url": full_url,
                            "verified": True,
                            "confidence": 0.95,  # High confidence for direct citation matches
                            "validation_method": "citation_lookup_v4_success"
                        })
                        
                        # Process parallel citations if available
                        self._process_parallel_citations(result, best_cluster, citation)
                        
                        # If this is a state court case, try to enhance with additional metadata
                        if self._is_state_court_citation(citation):
                            self._enhance_state_court_result(result, best_cluster, extracted_case_name)
                        
                        logger.info(f"[ENHANCED] Successfully verified citation: {citation}")
                    else:
                        logger.warning(f"[ENHANCED] Incomplete cluster data for citation: {citation}")
                else:
                    logger.info(f"[ENHANCED] No clusters found for citation: {citation}")
            else:
                logger.warning(f"[ENHANCED] API request failed with status {response.status_code}: {response.text}")
                result["error"] = f"API request failed with status {response.status_code}"
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[ENHANCED] Network error verifying citation {citation}: {str(e)}")
            result["error"] = f"Network error: {str(e)}"
            return result
            
        except Exception as e:
            logger.error(f"[ENHANCED] Error verifying citation {citation}: {str(e)}", exc_info=True)
            result["error"] = f"Unexpected error: {str(e)}"
            return result
    
    def _find_best_match_with_fuzzy_matching(self, api_results: List[Dict], 
                                           extracted_case_name: Optional[str], 
                                           citation: str) -> Optional[Dict]:
        """
        Find the best matching result using fuzzy case name matching.
        
        Args:
            api_results: List of results from CourtListener API
            extracted_case_name: Case name extracted from document
            citation: Citation text
            
        Returns:
            Best matching result or None
        """
        if not api_results:
            return None
        
        if extracted_case_name:
            best_match = None
            best_score = 0.0
            
            for result in api_results:
                api_case_name = result.get('caseName', '')
                if api_case_name:
                    similarity = enhanced_matcher.calculate_similarity(
                        extracted_case_name, api_case_name
                    )
                    
                    print(f"[ENHANCED] Case name similarity: '{extracted_case_name}' vs '{api_case_name}' = {similarity:.3f}")
                    
                    if similarity >= 0.6 and similarity > best_score:
                        best_score = similarity
                        best_match = result
            
            if best_match:
                print(f"[ENHANCED] Best match found with similarity {best_score:.3f}")
                return best_match
        
        for result in api_results:
            if result.get('caseName') and result.get('absolute_url'):
                return result
        
        return None
    
    def _search_for_primary_case_multiple_strategies(self, extracted_case_name: str, citation: str, citation_filter: str) -> Optional[Dict]:
        """
        Use multiple search strategies to find the primary case.
        
        Strategy 1: Search by citation (highest priority) - FIND THE ACTUAL CASE
        Strategy 2: Search by citation + case name (medium priority)
        Strategy 3: Search by case name only (lower priority) - FALLBACK
        
        Args:
            extracted_case_name: Case name extracted from document
            citation: Citation text
            citation_filter: Citation to use as filter
            
        Returns:
            Best matching primary case result or None
        """
        url = f"https://www.courtlistener.com/api/rest/v4/search/"
        
        print(f"[ENHANCED] Strategy 1: Searching by citation: '{citation}'")
        params = {
            'q': citation,
            'format': 'json',
            'stat_Precedential': 'on',
            'type': 'o',
            'order_by': 'dateFiled desc'
        }
        
        response = requests.get(url, headers=self.headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
        if response.status_code == 200:
            api_results = response.json()
            found_results = [r for r in api_results.get('results', []) if r.get('status') != 404]
            
            if found_results:
                best_result = self._find_primary_case_with_enhanced_matching(
                    found_results, extracted_case_name, citation, citation_filter
                )
                if best_result:
                    print(f"[ENHANCED] Strategy 1 successful: Found primary case by citation")
                    return best_result
        
        print(f"[ENHANCED] Strategy 2: Searching by citation + case name")
        params = {
            'q': f'{citation} {extracted_case_name}',
            'format': 'json',
            'stat_Precedential': 'on',
            'type': 'o',
            'order_by': 'dateFiled desc'
        }
        
        response = requests.get(url, headers=self.headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
        if response.status_code == 200:
            api_results = response.json()
            found_results = [r for r in api_results.get('results', []) if r.get('status') != 404]
            
            if found_results:
                best_result = self._find_primary_case_with_enhanced_matching(
                    found_results, extracted_case_name, citation, citation_filter
                )
                if best_result:
                    print(f"[ENHANCED] Strategy 2 successful: Found primary case by citation + name")
                    return best_result
        
        print(f"[ENHANCED] Strategy 3: Searching by exact case name (fallback)")
        params = {
            'q': f'"{extracted_case_name}"',  # Exact phrase match
            'format': 'json',
            'stat_Precedential': 'on',
            'type': 'o',
            'order_by': 'dateFiled desc'
        }
        
        response = requests.get(url, headers=self.headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
        if response.status_code == 200:
            api_results = response.json()
            found_results = [r for r in api_results.get('results', []) if r.get('status') != 404]
            
            if found_results:
                best_result = self._find_primary_case_with_enhanced_matching(
                    found_results, extracted_case_name, citation, citation_filter
                )
                if best_result:
                    print(f"[ENHANCED] Strategy 3 successful: Found primary case by name (fallback)")
                    return best_result
        
        print(f"[ENHANCED] All search strategies failed to find primary case")
        return None
    
    def _find_primary_case_with_enhanced_matching(self, api_results: List[Dict], 
                                                extracted_case_name: Optional[str], 
                                                citation: str,
                                                citation_filter: Optional[str] = None) -> Optional[Dict]:
        """
        Find the PRIMARY case (the one in header/metadata) rather than cases that just cite it.
        
        Strategy:
        1. Prioritize exact case name matches
        2. Use citation as a filter to eliminate cases that just cite the target
        3. Focus on finding the case that IS the citation, not cases that CONTAIN the citation
        
        Args:
            api_results: List of results from CourtListener API
            extracted_case_name: Case name extracted from document
            citation: Citation text
            citation_filter: Citation to use as a filter
            
        Returns:
            Primary case result or None
        """
        if not api_results:
            return None
        
        if extracted_case_name:
            best_match = None
            best_score = 0.0
            
            for result in api_results:
                api_case_name = result.get('caseName', '')
                if not api_case_name:
                    continue
                
                similarity = enhanced_matcher.calculate_similarity(
                    extracted_case_name, api_case_name
                )
                
                print(f"[ENHANCED] Primary case similarity: '{extracted_case_name}' vs '{api_case_name}' = {similarity:.3f}")
                
                if citation_filter:
                    result_text = result.get('plain_text', '') or result.get('html', '') or ''
                    
                    if True:

                    
                        pass  # Empty block

                    
                    
                        pass  # Empty block

                    
                    
                        case_name_contains_citation = citation_filter.lower() in api_case_name.lower()
                        metadata_contains_citation = any(
                            citation_filter.lower() in str(value).lower() 
                            for key, value in result.items() 
                            if key in ['docket_number', 'case_number', 'citation', 'parallel_citations']
                        )
                        
                        if case_name_contains_citation or metadata_contains_citation:
                            print(f"[ENHANCED] Citation found in metadata - likely primary case: {api_case_name}")
                        else:
                            print(f"[ENHANCED] Citation only in text content - likely not primary: {api_case_name}")
                            citation_penalty = 0.3
                            print(f"[ENHANCED] Applying citation penalty: {citation_penalty}")
                        continue
                
                citation_penalty = 0.0
                if self._case_appears_to_cite_target(result, citation, extracted_case_name):
                    print(f"[ENHANCED] Case appears to cite target, reducing score: {api_case_name}")
                    citation_penalty = 0.2
                
                score = similarity - citation_penalty
                
                if extracted_case_name.lower() == api_case_name.lower():
                    score += 0.3
                
                if similarity >= 0.8:
                    score += 0.2
                elif similarity >= 0.6:
                    score += 0.1
                
                if similarity < 0.4:
                    score -= 0.3
                
                if citation_filter and citation_filter in api_case_name:
                    score += 0.2
                    print(f"[ENHANCED] Citation found in case name - bonus applied: {api_case_name}")
                
                if extracted_case_name and extracted_case_name.lower() in api_case_name.lower() and similarity < 0.7:
                    score -= 0.3
                    print(f"[ENHANCED] Case name contains target but low similarity - penalty applied: {api_case_name}")
                
                print(f"[ENHANCED] Case '{api_case_name}' scored: {score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_match = result
            
            if best_match and best_score >= 0.5:  # Require minimum score for primary case
                print(f"[ENHANCED] Primary case found with score {best_score:.3f}: {best_match.get('caseName')}")
                
                if best_score < 0.3:
                    print(f"[ENHANCED] REJECTING result: Score {best_score:.3f} too low - likely wrong case")
                    print(f"[ENHANCED] Extracted: '{extracted_case_name}' vs API: '{best_match.get('caseName')}'")
                    return None
                
                return best_match
        
        for result in api_results:
            if result.get('caseName') and result.get('absolute_url'):
                return result
        
        return None
    
    def _case_appears_to_cite_target(self, result: Dict, citation: str, extracted_case_name: Optional[str] = None) -> bool:
        """
        Check if a case result appears to be citing the target case rather than being the target.
        
        Args:
            result: Case result from CourtListener API
            citation: Citation text we're looking for
            extracted_case_name: Extracted case name
            
        Returns:
            True if the case appears to cite the target, False otherwise
        """
        case_text = result.get('plain_text', '') or result.get('html', '') or ''
        if not case_text:
            return False
        
        citation_patterns = [
            rf'(?:see|citing|cited)\s+{re.escape(citation)}',
            rf'\({re.escape(citation)}\)',
            rf'(?:in|see)\s+{re.escape(citation)}',
        ]
        
        for pattern in citation_patterns:
            if re.search(pattern, case_text, re.IGNORECASE):
                print(f"[ENHANCED] Found citation pattern '{pattern}' in case text")
                return True
        
        if extracted_case_name:
            # but the case name doesn't match the result's case name, it's likely citing
            case_name_patterns = [
                rf'(?:see|citing|cited)\s+{re.escape(extracted_case_name)}',
                rf'\({re.escape(extracted_case_name)}\)',
                rf'(?:in|see)\s+{re.escape(extracted_case_name)}',
            ]
            
            for pattern in case_name_patterns:
                if re.search(pattern, case_text, re.IGNORECASE):
                    print(f"[ENHANCED] Found case name citation pattern '{pattern}' in case text")
                    return True
        
        return False
    
    def _is_test_citation(self, citation: str) -> bool:
        """Check if citation is a known test citation."""
        test_patterns = [
            r'\b123\s+f\.?3d\s+456\b',
            r'\b999\s+u\.?s\.?\s+999\b',
            r'\bsmith\s+v\.?\s+jones\b',
            r'\btest\s+citation\b',
            r'\bsample\s+citation\b',
            r'\bfake\s+citation\b'
        ]
        
        citation_lower = citation.lower()
        for pattern in test_patterns:
            if re.search(pattern, citation_lower):
                return True
        
        return False

    def _normalize_url(self, url: str) -> str:
        """
        Normalize a CourtListener URL to ensure it's absolute.
        CourtListener URLs are often relative, but the API expects absolute.
        """
        if url and not url.startswith('http://') and not url.startswith('https://'):
            if url.startswith('/'):
                return f"https://www.courtlistener.com{url}"
            if url.startswith('api/'):
                return f"https://www.courtlistener.com{url}"
            return f"https://www.courtlistener.com{url}"
        return url

    def _verify_with_citation_lookup_v4(self, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
        """Verify using citation-lookup API v4 with strict matching criteria."""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None,
            "source": "CourtListener Citation-Lookup API v4"
        }
        
        try:
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            data = {"text": citation}
            
            print(f"[ENHANCED] Citation-lookup API v4 request: {url}")
            print(f"[ENHANCED] Citation-lookup API v4 data: {data}")
            
            response = requests.post(url, headers=self.headers, json=data, timeout=DEFAULT_REQUEST_TIMEOUT)
            
            print(f"[ENHANCED] Citation-lookup API v4 response status: {response.status_code}")
            
            if response.status_code == 200:
                api_results = response.json()
                result['raw'] = response.text
                
                print(f"[ENHANCED] Citation-lookup API v4 raw response: {api_results}")
                
                found_results = [r for r in api_results if r.get('status') != 404 and r.get('clusters')]
                
                print(f"[ENHANCED] Citation-lookup API v4 found {len(found_results)} valid results")
                
                if found_results:
                    all_clusters = []
                    for api_response in found_results:
                        clusters = api_response.get('clusters', [])
                        all_clusters.extend(clusters)
                    
                    print(f"[ENHANCED] Extracted {len(all_clusters)} clusters from {len(found_results)} API responses")
                    
                    best_case = self._find_best_case_with_strict_criteria(
                        all_clusters, citation, extracted_case_name
                    )
                    
                    if best_case:
                        print(f"[ENHANCED] Citation-lookup API v4 found best case: {best_case.get('case_name', 'N/A')}")
                        # CRITICAL: Extract only year from date_filed to prevent contamination
                        date_filed = best_case.get('date_filed', '')
                        canonical_year = None
                        if date_filed:
                            year_match = re.search(r'(\d{4})', date_filed)
                            if year_match:
                                canonical_year = year_match.group(1)
                        
                        result.update({
                            "canonical_name": best_case.get('case_name', ''),
                            "canonical_date": canonical_year or '',  # Only year, never full date
                            "url": self._normalize_url(best_case.get('absolute_url', '')),
                            "verified": True,
                            "confidence": 0.9
                        })
                    else:
                        print(f"[ENHANCED] Citation-lookup API v4 found results but strict criteria failed")
                else:
                    print(f"[ENHANCED] Citation-lookup API v4 found no valid results")
            else:
                print(f"[ENHANCED] Citation-lookup API v4 failed with status: {response.status_code}")
                print(f"[ENHANCED] Citation-lookup API v4 error response: {response.text}")
                
        except Exception as e:
            print(f"[ENHANCED] Citation-lookup API v4 error: {e}")
            logger.error(f"Citation-lookup API v4 error: {e}")
        
        return result

    def _verify_with_citation_lookup_v4_enhanced(self, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
        """Enhanced citation-lookup API v4 with WA reporter normalization and strict matching."""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None,
            "source": "CourtListener Citation-Lookup API v4"
        }
        
        try:
            def normalize_reporter(cit: str) -> str:
                c = cit
                c = c.replace('\u2019', "'")  # Fix smart quotes
                c = re.sub(r'\bWn\.?\s*2d\b', 'Wash. 2d', c, flags=re.IGNORECASE)
                c = re.sub(r'\bWash\.?\s*2d\b', 'Wash. 2d', c, flags=re.IGNORECASE)
                c = re.sub(r'\bWn\.?\s*App\.?\b', 'Wash. App.', c, flags=re.IGNORECASE)
                c = re.sub(r'\bWash\.?\s*App\.?\b', 'Wash. App.', c, flags=re.IGNORECASE)
                return c

            norm_citation = normalize_reporter(citation)
            
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            data = {"text": norm_citation}
            
            response = requests.post(url, headers=self.headers, json=data, timeout=COURTLISTENER_TIMEOUT)
            
            if response.status_code == 200:
                api_results = response.json()
                result['raw'] = response.text
                
                found_results = [r for r in api_results if r.get('status') != 404 and r.get('clusters')]
                
                if found_results:
                    all_clusters = []
                    for api_response in found_results:
                        clusters = api_response.get('clusters', [])
                        all_clusters.extend(clusters)
                    
                    best_case = self._find_best_case_with_strict_criteria(
                        all_clusters, citation, extracted_case_name
                    )
                    
                    if best_case:
                        # CRITICAL: Extract only year from date_filed to prevent contamination
                        date_filed = best_case.get('date_filed', '')
                        canonical_year = None
                        if date_filed:
                            year_match = re.search(r'(\d{4})', date_filed)
                            if year_match:
                                canonical_year = year_match.group(1)
                        
                        result.update({
                            "canonical_name": best_case.get('case_name', ''),
                            "canonical_date": canonical_year or '',  # Only year, never full date
                            "url": self._normalize_url(best_case.get('absolute_url', '')),
                            "verified": True,
                            "confidence": 0.95
                        })
                else:
                    result['verified'] = False
                    result['confidence'] = 0.0
            else:
                result['verified'] = False
                result['confidence'] = 0.0
                
        except Exception as e:
            result['verified'] = False
            result['confidence'] = 0.0
        
        return result
    

def verify_with_courtlistener_enhanced(courtlistener_api_key: str, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
    """Enhanced verification function with cross-validation"""
    
    verifier = EnhancedCourtListenerVerifier(courtlistener_api_key)
    return verifier.verify_citation_enhanced(citation, extracted_case_name)
