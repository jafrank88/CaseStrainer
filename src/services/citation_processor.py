"""
Citation Processor Orchestrator

This service coordinates all citation processing services and provides the main API
for citation extraction, verification, and clustering.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import time
from dataclasses import asdict

from .interfaces import ICitationProcessor, ICitationExtractor, ICitationVerifier, ICitationClusterer
from .citation_extractor import CitationExtractor
from .citation_verifier import CitationVerifier
from .citation_clusterer import CitationClusterer
from src.models import CitationResult, ProcessingConfig

logger = logging.getLogger(__name__)


class CitationProcessor(ICitationProcessor):
    """
    Main citation processing orchestrator that coordinates all services.
    
    This service orchestrates the complete citation processing pipeline:
    1. Extract citations from text
    2. Verify citations using external APIs
    3. Detect parallel citations and create clusters
    4. Format results for output
    """
    
    def __init__(self, 
                 config: Optional[ProcessingConfig] = None,
                 extractor: Optional[ICitationExtractor] = None,
                 verifier: Optional[ICitationVerifier] = None,
                 clusterer: Optional[ICitationClusterer] = None):
        """
        Initialize the citation processor with optional service dependencies.
        
        Args:
            config: Processing configuration
            extractor: Citation extractor service (will create default if None)
            verifier: Citation verifier service (will create default if None)
            clusterer: Citation clusterer service (will create default if None)
        """
        self.config = config or ProcessingConfig()
        
        # Initialize services (dependency injection pattern)
        # CitationExtractor expects Dict[str, Any], others expect ProcessingConfig
        config_dict = asdict(self.config) if self.config else {}
        self.extractor = extractor or CitationExtractor(config_dict)
        self.verifier = verifier or CitationVerifier(self.config)
        self.clusterer = clusterer or CitationClusterer(self.config)
        
        # Performance tracking
        self._processing_stats = {
            'total_processed': 0,
            'total_citations_found': 0,
            'total_citations_verified': 0,
            'total_clusters_created': 0,
            'average_processing_time': 0.0
        }
        
        if self.config.debug_mode:
            logger.info("CitationProcessor initialized with modular services")
    
    async def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text through the complete citation pipeline.
        
        Args:
            text: Text to process
            
        Returns:
            Dictionary with citations and clusters
        """
        start_time = time.time()
        
        try:
            # Step 1: Extract citations
            if self.config.debug_mode:
                logger.info("Step 1: Extracting citations")
            
            citations = self.extractor.extract_citations(text)
            
            if not citations:
                return self._create_empty_result("No citations found in text")
            
            # Step 2: Verify citations
            if self.config.debug_mode:
                logger.info(f"Step 2: Verifying {len(citations)} citations")
            
            verified_citations = await self.verifier.verify_citations(citations)
            
            # Step 3: Detect parallel citations
            if self.config.debug_mode:
                logger.info("Step 3: Detecting parallel citations")
            
            citations_with_parallels = self.clusterer.detect_parallel_citations(verified_citations, text)
            
            # Step 4: Create clusters
            if self.config.debug_mode:
                logger.info("Step 4: Creating citation clusters")
            
            clusters = self.clusterer.cluster_citations(citations_with_parallels)
            
            # Step 5: Format results
            result = self._format_results(citations_with_parallels, clusters, text)
            
            # Update performance stats
            processing_time = time.time() - start_time
            self._update_stats(citations_with_parallels, clusters, processing_time)
            
            if self.config.debug_mode:
                logger.info(f"Processing completed in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in citation processing pipeline: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(str(e))
    
    async def process_document_citations(self, document_text: str, document_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Process document citations with optional type-specific handling.
        
        Args:
            document_text: Document text to process
            document_type: Optional document type for specialized processing
            
        Returns:
            Dictionary with processing results
        """
        # For now, delegate to process_text
        # In the future, this could include document-type-specific processing
        result = await self.process_text(document_text)
        
        # Add document metadata
        result['document_type'] = document_type
        result['document_length'] = len(document_text)
        
        return result
    
    def _format_results(self, citations: List[CitationResult], clusters: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        """Format the processing results for output."""
        # Format individual citations
        formatted_citations = []
        for citation in citations:
            citation_dict = {
                'citation': citation.citation,
                'extracted_case_name': citation.extracted_case_name or 'N/A',
                'extracted_date': citation.extracted_date or 'N/A',
                'canonical_name': citation.canonical_name or 'N/A',
                'canonical_date': citation.canonical_date or 'N/A',
                'verified': citation.verified,
                'confidence': citation.confidence,
                'method': citation.method,
                'pattern': citation.pattern,
                'context': citation.context or '',
                'start_index': citation.start_index,
                'end_index': citation.end_index,
                'parallel_citations': citation.parallel_citations or [],
                'court': citation.court,
                'docket_number': citation.docket_number,
                'url': citation.url,
                'source': citation.source,
                'metadata': citation.metadata or {}
            }
            formatted_citations.append(citation_dict)
        
        # Calculate summary statistics
        verified_count = sum(1 for c in citations if c.verified)
        parallel_count = sum(1 for c in citations if c.parallel_citations)
        
        return {
            'success': True,
            'citations': formatted_citations,
            'clusters': clusters,
            'summary': {
                'total_citations': len(citations),
                'verified_citations': verified_count,
                'unverified_citations': len(citations) - verified_count,
                'citations_with_parallels': parallel_count,
                'total_clusters': len(clusters),
                'verification_rate': verified_count / len(citations) if citations else 0.0
            },
            'processing_info': {
                'extractor_method': 'modular_services',
                'services_used': ['CitationExtractor', 'CitationVerifier', 'CitationClusterer'],
                'config': {
                    'use_eyecite': self.config.use_eyecite,
                    'debug_mode': self.config.debug_mode
                }
            }
        }
    
    def _create_empty_result(self, message: str) -> Dict[str, Any]:
        """Create an empty result with a message."""
        return {
            'success': True,
            'citations': [],
            'clusters': [],
            'summary': {
                'total_citations': 0,
                'verified_citations': 0,
                'unverified_citations': 0,
                'citations_with_parallels': 0,
                'total_clusters': 0,
                'verification_rate': 0.0
            },
            'message': message,
            'processing_info': {
                'extractor_method': 'modular_services',
                'services_used': ['CitationExtractor', 'CitationVerifier', 'CitationClusterer']
            }
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create an error result."""
        return {
            'success': False,
            'error': error_message,
            'citations': [],
            'clusters': [],
            'summary': {
                'total_citations': 0,
                'verified_citations': 0,
                'unverified_citations': 0,
                'citations_with_parallels': 0,
                'total_clusters': 0,
                'verification_rate': 0.0
            }
        }
    
    def _update_stats(self, citations: List[CitationResult], clusters: List[Dict[str, Any]], processing_time: float) -> None:
        """Update processing statistics."""
        self._processing_stats['total_processed'] += 1
        self._processing_stats['total_citations_found'] += len(citations)
        self._processing_stats['total_citations_verified'] += sum(1 for c in citations if c.verified)
        self._processing_stats['total_clusters_created'] += len(clusters)
        
        # Update average processing time
        current_avg = self._processing_stats['average_processing_time']
        total_processed = self._processing_stats['total_processed']
        self._processing_stats['average_processing_time'] = (
            (current_avg * (total_processed - 1) + processing_time) / total_processed
        )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self._processing_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self._processing_stats = {
            'total_processed': 0,
            'total_citations_found': 0,
            'total_citations_verified': 0,
            'total_clusters_created': 0,
            'average_processing_time': 0.0
        }


class ServiceContainer:
    """
    Simple dependency injection container for citation processing services.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """Initialize the service container."""
        self.config = config or ProcessingConfig()
        self._services = {}
    
    def get_extractor(self) -> ICitationExtractor:
        """Get citation extractor service."""
        if 'extractor' not in self._services:
            # CitationExtractor expects Dict[str, Any], convert ProcessingConfig
            config_dict = asdict(self.config) if self.config else {}
            self._services['extractor'] = CitationExtractor(config_dict)
        return self._services['extractor']
    
    def get_verifier(self) -> ICitationVerifier:
        """Get citation verifier service."""
        if 'verifier' not in self._services:
            self._services['verifier'] = CitationVerifier(self.config)
        return self._services['verifier']
    
    def get_clusterer(self) -> ICitationClusterer:
        """Get citation clusterer service."""
        if 'clusterer' not in self._services:
            self._services['clusterer'] = CitationClusterer(self.config)
        return self._services['clusterer']
    
    def get_processor(self) -> ICitationProcessor:
        """Get main citation processor."""
        if 'processor' not in self._services:
            self._services['processor'] = CitationProcessor(
                config=self.config,
                extractor=self.get_extractor(),
                verifier=self.get_verifier(),
                clusterer=self.get_clusterer()
            )
        return self._services['processor']
    
    def reset(self) -> None:
        """Reset all services (useful for testing)."""
        self._services.clear()


# Convenience function for easy use
async def process_citations(text: str, config: Optional[ProcessingConfig] = None) -> Dict[str, Any]:
    """
    Convenience function for processing citations using the modular services.
    
    Args:
        text: Text to extract citations from
        config: Optional processing configuration
        
    Returns:
        Dictionary with citations and clusters
    """
    container = ServiceContainer(config)
    processor = container.get_processor()
    return await processor.process_text(text)
