"""
Source Prediction Module
ML-based source prediction for optimal search strategy.
"""

import re
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

from typing import List, Optional


class SourcePredictor:
    """ML-based source prediction for optimal search strategy."""
    
    def __init__(self):
        self.citation_patterns = {
            'washington_state': [r'Wn\.?\s*\d+', r'Wash\.?\s*\d+', r'Washington\s+\d+'],
            'federal_supreme': [r'U\.S\.?\s+\d+', r'US\s+\d+'],
            'federal_circuit': [r'F\.?\s*\d+', r'Fed\.?\s*\d+'],
            'pacific_reporter': [r'P\.?\s*\d+', r'Pac\.?\s*\d+', r'Pacific\s+\d+'],
        }
        
        self.source_affinity = {
            'washington_state': ['justia', 'findlaw', 'courtlistener_web', 'leagle'],
            'federal_supreme': ['justia', 'findlaw', 'google_scholar', 'courtlistener_web'],
            'federal_circuit': ['justia', 'findlaw', 'leagle', 'casetext'],
            'pacific_reporter': ['justia', 'findlaw', 'leagle', 'vlex'],
        }
    
    def predict_best_sources(self, citation: str, case_name: Optional[str] = None) -> List[str]:
        """Predict the best sources for a given citation."""
        predicted_sources = set()
        
        for pattern_type, patterns in self.citation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, citation, re.IGNORECASE):
                    predicted_sources.update(self.source_affinity.get(pattern_type, []))
                    break
        
        year_match = re.search(r'\b(19|20)\d{2}\b', citation)
        if year_match:
            year = int(year_match.group(0))
            if year >= 2010:
                predicted_sources.update(['casetext', 'vlex', 'google_scholar'])
            if year >= 2000:
                predicted_sources.update(['justia', 'findlaw'])
        
        if case_name:
            if re.search(r'\bUnited States\b', case_name, re.IGNORECASE):
                predicted_sources.update(['justia', 'findlaw', 'google_scholar'])
            if re.search(r'\bState\b.*\bv\b', case_name, re.IGNORECASE):
                predicted_sources.update(['justia', 'findlaw', 'leagle'])
        
        all_sources = ['justia', 'findlaw', 'courtlistener_web', 'leagle', 'casetext', 
                      'vlex', 'google_scholar', 'bing', 'duckduckgo']
        
        result = [s for s in all_sources if s in predicted_sources]
        result.extend([s for s in all_sources if s not in predicted_sources])
        
        return result 