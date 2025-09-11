"""
Data Separation Validator

This module ensures strict separation between extracted data (from user's document)
and canonical data (from verification sources). It prevents contamination where
canonical names overwrite extracted names.

Key Principles:
1. extracted_case_name must always come from the user's document
2. canonical_name must always come from verification sources  
3. These should remain separate with similarity tolerance
4. Canonical data should never overwrite extracted data
"""

import logging
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

from typing import Dict, Any, Optional, List, Tuple
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

class DataSeparationValidator:
    """Validates and enforces separation between extracted and canonical data"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize validator.
        
        Args:
            similarity_threshold: Threshold above which names are considered too similar
                                (indicating possible contamination)
        """
        self.similarity_threshold = similarity_threshold
        self.contamination_warnings = []
        
    def validate_citation(self, citation: Dict[str, Any]) -> bool:
        """
        Validate a single citation for data separation.
        
        Args:
            citation: Citation dictionary with extracted_case_name and canonical_name
            
        Returns:
            True if validation passes, False if contamination detected
        """
        extracted_name = citation.get('extracted_case_name')
        canonical_name = citation.get('canonical_name')
        citation_text = citation.get('citation', 'unknown')
        
        if not extracted_name or not canonical_name:
            return True  # No contamination possible if one is missing
        
        if extracted_name == canonical_name:
            warning = f"EXACT MATCH: Citation '{citation_text}' has identical extracted and canonical names: '{extracted_name}'"
            self.contamination_warnings.append(warning)
            logger.warning(f"⚠️ {warning}")
            return False
        
        similarity = fuzz.ratio(extracted_name.lower(), canonical_name.lower()) / 100.0
        if similarity > self.similarity_threshold:
            warning = f"HIGH SIMILARITY ({similarity:.2f}): Citation '{citation_text}' - extracted: '{extracted_name}', canonical: '{canonical_name}'"
            self.contamination_warnings.append(warning)
            logger.warning(f"⚠️ {warning}")
            return False
        
        return True
    
    def validate_citations_batch(self, citations: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate a batch of citations for data separation.
        
        Args:
            citations: List of citation dictionaries
            
        Returns:
            Tuple of (all_valid, list_of_warnings)
        """
        self.contamination_warnings.clear()
        all_valid = True
        
        for i, citation in enumerate(citations):
            if not self.validate_citation(citation):
                all_valid = False
        
        return all_valid, self.contamination_warnings.copy()
    
    def fix_contamination(self, citation: Dict[str, Any], original_extracted_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Attempt to fix contamination by restoring original extracted name.
        
        Args:
            citation: Citation with potential contamination
            original_extracted_name: Original extracted name if available
            
        Returns:
            Fixed citation dictionary
        """
        extracted_name = citation.get('extracted_case_name')
        canonical_name = citation.get('canonical_name')
        
        if (original_extracted_name and 
            extracted_name == canonical_name and 
            original_extracted_name != canonical_name):
            
            logger.info(f"🔧 Fixing contamination: Restoring extracted name from '{extracted_name}' to '{original_extracted_name}'")
            citation['extracted_case_name'] = original_extracted_name
        
        return citation
    
    def create_separation_report(self, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a detailed report on data separation status.
        
        Args:
            citations: List of citations to analyze
            
        Returns:
            Report dictionary with separation analysis
        """
        total_citations = len(citations)
        contaminated_citations = 0
        exact_matches = 0
        high_similarity_matches = 0
        properly_separated = 0
        
        for citation in citations:
            extracted_name = citation.get('extracted_case_name')
            canonical_name = citation.get('canonical_name')
            
            if not extracted_name or not canonical_name:
                continue
            
            if extracted_name == canonical_name:
                exact_matches += 1
                contaminated_citations += 1
            else:
                similarity = fuzz.ratio(extracted_name.lower(), canonical_name.lower()) / 100.0
                if similarity > self.similarity_threshold:
                    high_similarity_matches += 1
                    contaminated_citations += 1
                else:
                    properly_separated += 1
        
        report = {
            'total_citations': total_citations,
            'contaminated_citations': contaminated_citations,
            'exact_matches': exact_matches,
            'high_similarity_matches': high_similarity_matches,
            'properly_separated': properly_separated,
            'contamination_rate': contaminated_citations / max(total_citations, 1),
            'separation_health': 'GOOD' if contaminated_citations == 0 else 'POOR' if contaminated_citations > total_citations * 0.5 else 'MODERATE',
            'warnings': self.contamination_warnings.copy()
        }
        
        return report

def validate_data_separation(citations: List[Dict[str, Any]], 
                           similarity_threshold: float = 0.85) -> Dict[str, Any]:
    """
    Convenience function to validate data separation for a list of citations.
    
    Args:
        citations: List of citation dictionaries
        similarity_threshold: Similarity threshold for contamination detection
        
    Returns:
        Validation report
    """
    validator = DataSeparationValidator(similarity_threshold)
    is_valid, warnings = validator.validate_citations_batch(citations)
    report = validator.create_separation_report(citations)
    report['is_valid'] = is_valid
    
    return report

def enforce_data_separation(citation_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce data separation by ensuring extracted_case_name is never overwritten.
    
    This should be called before any verification process to preserve original extraction.
    
    Args:
        citation_dict: Citation dictionary that may have contamination
        
    Returns:
        Citation dictionary with enforced separation
    """
    if 'extracted_case_name' in citation_dict and citation_dict['extracted_case_name']:
        citation_dict['_original_extracted_case_name'] = citation_dict['extracted_case_name']
    
    return citation_dict

def restore_extracted_name_if_contaminated(citation_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Restore original extracted name if contamination is detected.
    
    This should be called after verification to check for contamination.
    
    Args:
        citation_dict: Citation dictionary after verification
        
    Returns:
        Citation dictionary with restored extracted name if needed
    """
    original_extracted = citation_dict.get('_original_extracted_case_name')
    current_extracted = citation_dict.get('extracted_case_name')
    canonical_name = citation_dict.get('canonical_name')
    
    if (original_extracted and 
        current_extracted == canonical_name and 
        original_extracted != canonical_name):
        
        logger.info(f"🔧 Restoring contaminated extracted name: '{current_extracted}' -> '{original_extracted}'")
        citation_dict['extracted_case_name'] = original_extracted
    
    if '_original_extracted_case_name' in citation_dict:
        del citation_dict['_original_extracted_case_name']
    
    return citation_dict

