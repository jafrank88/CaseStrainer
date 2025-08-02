"""
Unified Citation Processor v2 - Refactored

This is the refactored version of the unified citation processor that uses
modular components for better maintainability and type safety.
"""

import logging
from typing import List, Dict, Any, Optional
from src.models import CitationResult, ProcessingConfig
from src.citation_types import CitationList, CitationDict
from src.citation_extractor import CitationExtractor
from src.citation_verifier import CitationVerifier
from src.citation_processor import CitationProcessor
from src.citation_utils import deduplicate_citations

logger = logging.getLogger(__name__)

class UnifiedCitationProcessorV2:
    """
    Unified citation processor that consolidates the best parts of all existing implementations.
    This refactored version uses modular components for better maintainability.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        logger.info('[DEBUG] ENTERED UnifiedCitationProcessorV2.__init__')
        self.config = config or ProcessingConfig()
        
        # Initialize components
        self.extractor = CitationExtractor()
        self.verifier = CitationVerifier(
            courtlistener_api_key=getattr(self.config, 'COURTLISTENER_API_KEY', None)
        )
        self.processor = CitationProcessor()
        
        logger.info('[DEBUG] UnifiedCitationProcessorV2 initialized successfully')
    
    async def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text to extract, verify, and cluster citations.
        
        Args:
            text: The text to process
            
        Returns:
            Dictionary containing processing results
        """
        if not text:
            return {
                'citations': [],
                'clusters': [],
                'metadata': {
                    'total_citations': 0,
                    'verified_citations': 0,
                    'processing_time': 0
                }
            }
        
        logger.info(f"[PROCESS_TEXT] Processing text of length {len(text)}")
        
        # Step 1: Extract citations
        citations = self.extractor.extract_citations(
            text, 
            use_eyecite=getattr(self.config, 'use_eyecite', True)
        )
        logger.info(f"[PROCESS_TEXT] Extracted {len(citations)} citations")
        
        # Step 2: Verify citations
        if getattr(self.config, 'enable_verification', True):
            citations = await self.verifier.verify_citations(citations, text)
        
        # Step 3: Process and cluster citations
        citations = self.processor.detect_parallel_citations(citations, text)
        clusters = self.processor.cluster_citations_by_name_and_year(citations)
        
        # Step 4: Calculate final confidence scores
        for citation in citations:
            citation.confidence = self.processor.calculate_confidence(citation, text)
        
        # Step 5: Prepare results
        verified_count = len([c for c in citations if getattr(c, 'verified', False)])
        
        result = {
            'citations': citations,
            'clusters': clusters,
            'metadata': {
                'total_citations': len(citations),
                'verified_citations': verified_count,
                'clusters_count': len(clusters),
                'verification_rate': verified_count / len(citations) if citations else 0
            }
        }
        
        logger.info(f"[PROCESS_TEXT] Processing complete: {len(citations)} citations, {verified_count} verified")
        return result
    
    async def process_document_citations(self, document_text: str, document_type: Optional[str] = None, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process document citations with additional context.
        
        Args:
            document_text: The document text to process
            document_type: Type of document (e.g., 'brief', 'opinion')
            user_context: Additional user context
            
        Returns:
            Dictionary containing processing results
        """
        logger.info(f"[PROCESS_DOCUMENT] Processing document of type: {document_type}")
        
        # Process the text
        result = await self.process_text(document_text)
        
        # Add document-specific metadata
        result['metadata']['document_type'] = document_type
        result['metadata']['user_context'] = user_context
        
        # Convert citations to dictionaries for serialization
        result['citations'] = [self._citation_to_dict(citation) for citation in result['citations']]
        result['clusters'] = [self._cluster_to_dict(cluster) for cluster in result['clusters']]
        
        return result
    
    def _citation_to_dict(self, citation: CitationResult) -> Dict[str, Any]:
        """Convert CitationResult to dictionary."""
        return {
            'citation': citation.citation,
            'start': getattr(citation, 'start', None),
            'end': getattr(citation, 'end', None),
            'extracted_case_name': getattr(citation, 'extracted_case_name', None),
            'extracted_date': getattr(citation, 'extracted_date', None),
            'canonical_name': getattr(citation, 'canonical_name', None),
            'canonical_date': getattr(citation, 'canonical_date', None),
            'url': getattr(citation, 'url', None),
            'verified': getattr(citation, 'verified', False),
            'source': getattr(citation, 'source', 'unknown'),
            'confidence': getattr(citation, 'confidence', 0.0),
            'metadata': getattr(citation, 'metadata', {})
        }
    
    def _cluster_to_dict(self, cluster: CitationList) -> Dict[str, Any]:
        """Convert citation cluster to dictionary."""
        return {
            'citations': [self._citation_to_dict(citation) for citation in cluster],
            'size': len(cluster),
            'representative_citation': self._citation_to_dict(cluster[0]) if cluster else None
        }
    
    def extract_citations_from_text(self, text: str) -> CitationList:
        """
        Extract citations from text without verification or clustering.
        
        Args:
            text: The text to extract citations from
            
        Returns:
            List of CitationResult objects
        """
        if not text:
            return []
        
        return self.extractor.extract_citations(
            text, 
            use_eyecite=getattr(self.config, 'use_eyecite', True)
        )

# Standalone functions for backward compatibility
def extract_citations_unified(text: str, config: Optional[ProcessingConfig] = None) -> CitationList:
    """Extract citations from text using the unified processor."""
    processor = UnifiedCitationProcessorV2(config)
    return processor.extract_citations_from_text(text)

def extract_case_clusters_by_name_and_year(text: str) -> List[CitationList]:
    """Extract and cluster citations by case name and year."""
    processor = UnifiedCitationProcessorV2()
    citations = processor.extract_citations_from_text(text)
    return processor.processor.cluster_citations_by_name_and_year(citations)

def cluster_citations_by_citation_and_year(text: str) -> List[CitationList]:
    """Cluster citations by citation text and year."""
    processor = UnifiedCitationProcessorV2()
    citations = processor.extract_citations_from_text(text)
    return processor.processor.cluster_citations_by_name_and_year(citations) 