"""
Citation Normalization Module

This module handles the normalization of citations, breaking them down into
standardized components like volume, reporter, and page numbers.
"""

import logging
from typing import List, Dict, Any
from .error_handler import handle_processor_errors, ProcessorErrorHandler

logger = logging.getLogger(__name__)

class CitationNormalizer:
    """Handles citation normalization without external API calls."""
    
    def __init__(self):
        self.error_handler = ProcessorErrorHandler("CitationNormalizer")
    
    @handle_processor_errors("normalize_citations_local", default_return=[])
    def normalize_citations_local(self, citations: List, text: str) -> List:
        """Local citation normalization without API calls."""
        try:
            normalized = []
            for citation in citations:
                if (not isinstance(citation, dict) and 
                    hasattr(citation, 'citation')):
                    normalized.append(citation)
                    continue
                
                if isinstance(citation, dict) and 'citation' in citation:
                    citation_text = citation['citation']
                else:
                    citation_text = str(citation).strip()
                
                parts = citation_text.split()
                if len(parts) >= 3:
                    volume = parts[0]
                    reporter = parts[1]
                    page = parts[2]
                    
                    normalized.append({
                        'citation': citation_text,
                        'volume': volume,
                        'reporter': reporter,
                        'page': page,
                        'normalized': True
                    })
                else:
                    normalized.append({
                        'citation': citation_text,
                        'normalized': False
                    })
            
            logger.info(f"[CitationNormalizer] Local normalization completed for {len(normalized)} citations")
            return normalized
            
        except Exception as e:
            logger.warning(f"[CitationNormalizer] Local normalization failed: {e}")
            return citations
    
    def normalize_citation_text(self, citation_text: str) -> Dict[str, Any]:
        """Normalize a single citation text into components."""
        try:
            parts = citation_text.strip().split()
            if len(parts) >= 3:
                return {
                    'citation': citation_text,
                    'volume': parts[0],
                    'reporter': parts[1],
                    'page': parts[2],
                    'normalized': True
                }
            else:
                return {
                    'citation': citation_text,
                    'normalized': False
                }
        except Exception as e:
            logger.warning(f"[CitationNormalizer] Failed to normalize citation '{citation_text}': {e}")
            return {
                'citation': citation_text,
                'normalized': False
            }
