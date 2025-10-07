#!/usr/bin/env python3
"""
API Data Preference Logic - Prefer verified API data over extractions when available.
This module implements validation to use canonical data from APIs (like CourtListener)
instead of our extracted data when verification succeeds.
"""

import logging
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)

class APIDataPreferenceManager:
    """Manages preference of verified API data over extracted data."""
    
    def __init__(self):
        self.preference_stats = {
            'total_processed': 0,
            'api_preferred': 0,
            'extraction_kept': 0,
            'improvements_made': 0
        }
    
    def apply_api_preference(self, citations: List[Any]) -> List[Any]:
        """
        Apply API data preference to a list of citations.
        
        Args:
            citations: List of citation objects
            
        Returns:
            List of citations with API data preferred over extractions
        """
        if not citations:
            return citations
        
        improved_citations = []
        
        for citation in citations:
            improved_citation = self._apply_preference_to_citation(citation)
            improved_citations.append(improved_citation)
            
        logger.info(f"🔄 API Preference applied to {len(citations)} citations: "
                   f"{self.preference_stats['api_preferred']} improved, "
                   f"{self.preference_stats['extraction_kept']} kept original")
        
        return improved_citations
    
    def _apply_preference_to_citation(self, citation: Any) -> Any:
        """Apply API data preference to a single citation."""
        
        self.preference_stats['total_processed'] += 1
        
        # Get current values
        extracted_name = getattr(citation, 'extracted_case_name', None)
        canonical_name = getattr(citation, 'canonical_name', None)
        extracted_date = getattr(citation, 'extracted_date', None)
        canonical_date = getattr(citation, 'canonical_date', None)
        verified = getattr(citation, 'verified', False)
        verification_status = getattr(citation, 'verification_status', '')
        
        improvements = []
        
        # Only prefer API data if verification was successful
        if self._is_verification_successful(verified, verification_status):
            
            # Prefer canonical case name over extracted name
            if canonical_name and self._should_prefer_canonical_name(extracted_name, canonical_name):
                logger.debug(f"🔄 Preferring canonical name: '{canonical_name}' over extracted: '{extracted_name}'")
                citation.extracted_case_name = canonical_name
                improvements.append('case_name')
                
            # Prefer canonical date over extracted date
            if canonical_date and self._should_prefer_canonical_date(extracted_date, canonical_date):
                logger.debug(f"🔄 Preferring canonical date: '{canonical_date}' over extracted: '{extracted_date}'")
                citation.extracted_date = canonical_date
                improvements.append('date')
        
        # Update statistics
        if improvements:
            self.preference_stats['api_preferred'] += 1
            self.preference_stats['improvements_made'] += len(improvements)
            
            # Add metadata about the improvement
            if hasattr(citation, 'metadata'):
                citation.metadata['api_preference_applied'] = True
                citation.metadata['api_improvements'] = improvements
            
            logger.debug(f"✅ API preference applied to {citation.citation}: {', '.join(improvements)}")
        else:
            self.preference_stats['extraction_kept'] += 1
        
        return citation
    
    def _is_verification_successful(self, verified: bool, verification_status: str) -> bool:
        """Check if verification was successful."""
        
        # Check both boolean and string verification indicators
        boolean_verified = verified is True
        string_verified = verification_status and verification_status.lower() in ['verified', 'success', 'found']
        
        return boolean_verified or string_verified
    
    def _should_prefer_canonical_name(self, extracted_name: Optional[str], canonical_name: str) -> bool:
        """Determine if canonical name should be preferred over extracted name."""
        
        if not extracted_name or extracted_name in ['N/A', '', 'Unknown']:
            # Always prefer canonical over missing/empty extracted
            return True
        
        if not canonical_name or canonical_name in ['N/A', '', 'Unknown']:
            # Don't prefer empty canonical data
            return False
        
        # Check for contamination in extracted name
        if self._has_contamination(extracted_name):
            logger.debug(f"🧹 Contamination detected in extracted name: '{extracted_name}'")
            return True
        
        # Check for truncation in extracted name
        if self._is_truncated(extracted_name, canonical_name):
            logger.debug(f"✂️ Truncation detected: '{extracted_name}' vs '{canonical_name}'")
            return True
        
        # Check for obvious quality differences
        if self._canonical_is_higher_quality(extracted_name, canonical_name):
            logger.debug(f"📈 Higher quality canonical: '{canonical_name}' vs '{extracted_name}'")
            return True
        
        return False
    
    def _should_prefer_canonical_date(self, extracted_date: Optional[str], canonical_date: str) -> bool:
        """Determine if canonical date should be preferred over extracted date."""
        
        if not extracted_date or extracted_date in ['N/A', '', 'Unknown']:
            # Always prefer canonical over missing extracted
            return True
        
        if not canonical_date or canonical_date in ['N/A', '', 'Unknown']:
            # Don't prefer empty canonical data
            return False
        
        # Check if dates are significantly different (more than 2 years)
        try:
            extracted_year = int(extracted_date) if extracted_date.isdigit() else int(extracted_date[:4])
            canonical_year = int(canonical_date) if canonical_date.isdigit() else int(canonical_date[:4])
            
            year_diff = abs(extracted_year - canonical_year)
            if year_diff > 2:
                logger.debug(f"📅 Significant date difference: {extracted_date} vs {canonical_date} ({year_diff} years)")
                return True
        except (ValueError, TypeError, IndexError):
            # If we can't parse dates, prefer canonical if it looks like a valid year
            if re.match(r'^\d{4}$', canonical_date):
                return True
        
        return False
    
    def _has_contamination(self, extracted_name: str) -> bool:
        """Check if extracted name has contamination."""
        
        contamination_patterns = [
            r'^(See|Cf\.|Compare|But see|See also|The|A|An|In|Also)\s+',
            r'^(However|Moreover|Furthermore|Additionally|Similarly|Therefore)\s*,?\s+',
            r'^(Thus|Hence|Consequently|Accordingly|Following|Pursuant to)\s*,?\s+',
            r'\b(case of|ruling in|decided in|held in)\s+',
            r'\s+(at|in|from|with|by|for|on|under)\s*$',
            r'^(Compare with|Contrast with|Unlike|Similar to)\s+',
            r'^(Relying on|Citing|Quoting|Referencing)\s+'
        ]
        
        for pattern in contamination_patterns:
            if re.search(pattern, extracted_name, re.IGNORECASE):
                return True
        
        return False
    
    def _is_truncated(self, extracted_name: str, canonical_name: str) -> bool:
        """Check if extracted name appears to be truncated compared to canonical."""
        
        # Simple length-based check
        if len(extracted_name) < len(canonical_name) - 10:  # Allow some variance
            return True
        
        # Check if extracted is a suffix of canonical (like "Inc. v. Robins" vs "Spokeo, Inc. v. Robins")
        if canonical_name.endswith(extracted_name) and len(canonical_name) > len(extracted_name):
            return True
        
        # Check for missing party names
        canonical_parts = canonical_name.split(' v. ')
        extracted_parts = extracted_name.split(' v. ')
        
        if len(canonical_parts) == 2 and len(extracted_parts) == 2:
            # Check if either party is significantly shorter
            for i in range(2):
                if len(extracted_parts[i]) < len(canonical_parts[i]) - 5:
                    return True
        
        return False
    
    def _canonical_is_higher_quality(self, extracted_name: str, canonical_name: str) -> bool:
        """Check if canonical name appears to be higher quality."""
        
        # Prefer names without obvious extraction artifacts
        extraction_artifacts = ['N/A', 'Unknown', 'Inc.', 'Corp.', 'LLC']
        
        if extracted_name in extraction_artifacts and canonical_name not in extraction_artifacts:
            return True
        
        # Prefer longer, more complete names (within reason)
        if len(canonical_name) > len(extracted_name) + 5 and len(canonical_name) < len(extracted_name) * 2:
            return True
        
        # Prefer names that follow standard case name patterns
        if ' v. ' in canonical_name and ' v. ' not in extracted_name:
            return True
        
        return False
    
    def get_preference_stats(self) -> Dict[str, Any]:
        """Get statistics about API preference application."""
        
        stats = self.preference_stats.copy()
        
        if stats['total_processed'] > 0:
            stats['preference_rate'] = (stats['api_preferred'] / stats['total_processed']) * 100
            stats['improvement_rate'] = (stats['improvements_made'] / stats['total_processed']) * 100
        else:
            stats['preference_rate'] = 0
            stats['improvement_rate'] = 0
        
        return stats
    
    def reset_stats(self):
        """Reset preference statistics."""
        self.preference_stats = {
            'total_processed': 0,
            'api_preferred': 0,
            'extraction_kept': 0,
            'improvements_made': 0
        }

# Global instance for easy access
api_preference_manager = APIDataPreferenceManager()

def apply_api_data_preference(citations: List[Any]) -> List[Any]:
    """
    Convenience function to apply API data preference to citations.
    
    Args:
        citations: List of citation objects
        
    Returns:
        List of citations with API data preferred over extractions
    """
    return api_preference_manager.apply_api_preference(citations)

def get_api_preference_stats() -> Dict[str, Any]:
    """Get API preference statistics."""
    return api_preference_manager.get_preference_stats()

def reset_api_preference_stats():
    """Reset API preference statistics."""
    api_preference_manager.reset_stats()
