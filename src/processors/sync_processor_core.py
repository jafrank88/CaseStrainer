"""
Core Sync Processor Module

This module provides the core processing logic for the enhanced sync processor,
orchestrating citation extraction, normalization, name/year extraction, and clustering.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .citation_extractor import CitationExtractor
from .citation_normalizer import CitationNormalizer
from .name_year_extractor import NameYearExtractor
from .error_handler import handle_processor_errors, ProcessorErrorHandler

logger = logging.getLogger(__name__)

@dataclass
class ProcessingOptions:
    """Configuration options for text processing."""
    enable_enhanced_verification: bool = True
    enable_confidence_scoring: bool = True
    enable_false_positive_prevention: bool = True
    enable_clustering: bool = True
    enable_caching: bool = True
    processing_mode: str = "enhanced"  # enhanced, fast, ultra_fast
    courtlistener_api_key: Optional[str] = None

class SyncProcessorCore:
    """
    Core processor that orchestrates citation extraction, normalization,
    name/year extraction, and clustering using modular components.
    """
    
    def __init__(self, options: Optional[ProcessingOptions] = None, progress_callback: Optional[Any] = None):
        """Initialize the core processor with configuration options."""
        self.options = options or ProcessingOptions()
        self.progress_callback = progress_callback
        self.error_handler = ProcessorErrorHandler("SyncProcessorCore")
        
        # Initialize modular components
        self.citation_extractor = CitationExtractor()
        self.citation_normalizer = CitationNormalizer()
        
        # Initialize enhanced components if available
        self.enhanced_verifier = None
        self.confidence_scorer = None
        self._initialize_enhanced_components()
        
        self.name_year_extractor = NameYearExtractor(
            enhanced_verifier=self.enhanced_verifier,
            confidence_scorer=self.confidence_scorer,
            options=self.options.__dict__
        )
    
    def _initialize_enhanced_components(self):
        """Initialize enhanced verification and confidence scoring components."""
        try:
            from src.enhanced_courtlistener_verification import EnhancedCourtListenerVerifier
            if (self.options.enable_enhanced_verification and 
                self.options.courtlistener_api_key):
                self.enhanced_verifier = EnhancedCourtListenerVerifier(self.options.courtlistener_api_key)
                logger.info("Enhanced verification initialized successfully")
        except ImportError:
            logger.warning("Enhanced verification not available")
        except Exception as e:
            logger.warning(f"Failed to initialize enhanced verification: {e}")
        
        try:
            from src.citation_utils_consolidated import ConfidenceScorer
            if self.options.enable_confidence_scoring:
                self.confidence_scorer = ConfidenceScorer()
                logger.info("Confidence scoring initialized successfully")
        except ImportError:
            logger.warning("Confidence scoring not available")
        except Exception as e:
            logger.warning(f"Failed to initialize confidence scoring: {e}")
    
    @handle_processor_errors("process_enhanced_sync", default_return={'citations': [], 'clusters': [], 'metadata': {'error': 'Processing failed'}})
    def process_enhanced_sync(self, text: str, request_id: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """Enhanced sync processing with local normalization and clustering."""
        try:
            logger.info(f"[SyncProcessorCore {request_id}] Enhanced sync processing for {len(text)} characters")
            
            self._update_progress(0, "Initializing...", "Starting enhanced sync processing")
            
            # Step 1: Extract citations
            self._update_progress(20, "Extract", "Extracting citations from text")
            citations = self.citation_extractor.extract_citations_fast(text)
            
            # Step 2: Normalize citations
            self._update_progress(40, "Analyze", "Normalizing citations locally")
            normalized_citations = self.citation_normalizer.normalize_citations_local(citations, text)
            
            # Step 3: Extract names and years
            self._update_progress(60, "Extract Names", "Extracting case names and years")
            enhanced_citations = self.name_year_extractor.extract_names_years_local(normalized_citations, text)
            
            # Step 4: Apply canonical names
            self._update_progress(75, "Pre-verify", "Updating citations with canonical data")
            self._apply_canonical_names_to_objects(enhanced_citations)
            
            # Step 5: Cluster citations
            self._update_progress(80, "Cluster", "Clustering citations locally")
            clusters = self._cluster_citations_local(enhanced_citations, text, request_id)
            
            # Step 6: Prepare results
            self._update_progress(90, "Verify", "Preparing results")
            citations_list = self._convert_citations_to_dicts_simplified(enhanced_citations, clusters)
            clusters_list = self._convert_clusters_to_dicts(clusters)
            
            self._update_progress(100, "Complete", "Processing completed successfully")
            
            return {
                'citations': citations_list,
                'clusters': clusters_list,
                'metadata': {
                    'processing_mode': 'enhanced_sync',
                    'total_citations': len(citations_list),
                    'total_clusters': len(clusters_list),
                    'request_id': request_id
                }
            }
            
        except Exception as e:
            logger.error(f"[SyncProcessorCore {request_id}] Processing failed: {e}")
            return {
                'citations': [],
                'clusters': [],
                'metadata': {
                    'processing_mode': 'enhanced_sync',
                    'error': str(e),
                    'request_id': request_id
                }
            }
    
    def _update_progress(self, progress: int, step: str, message: str):
        """Update progress if callback is available."""
        if self.progress_callback:
            try:
                self.progress_callback(progress, step, message)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def _apply_canonical_names_to_objects(self, citations: List):
        """Apply canonical names to citation objects."""
        try:
            for citation in citations:
                if hasattr(citation, 'verification_result') and citation.verification_result:
                    verification_result = citation.verification_result
                    if verification_result.get('verified'):
                        canonical_url = verification_result.get('canonical_url') or verification_result.get('url')
                        citation.update({
                            'verified': verification_result.get('verified', False),
                            'canonical_name': verification_result.get('canonical_name'),
                            'canonical_date': verification_result.get('canonical_date'),
                            'canonical_url': canonical_url,
                            'url': canonical_url,
                            'source': verification_result.get('source'),
                            'validation_method': verification_result.get('validation_method'),
                            'verification_confidence': verification_result.get('confidence', 0.0)
                        })
        except Exception as e:
            logger.warning(f"Failed to apply canonical names: {e}")
    
    def _cluster_citations_local(self, citations: List, text: str, request_id: str) -> List:
        """Cluster citations locally using enhanced clustering."""
        try:
            from src.enhanced_clustering import EnhancedCitationClusterer
            
            clusterer = EnhancedCitationClusterer()
            clusters = clusterer.cluster_citations(citations, text)
            
            logger.info(f"[SyncProcessorCore {request_id}] Clustering completed: {len(clusters)} clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"[SyncProcessorCore {request_id}] Clustering failed: {e}")
            return []
    
    def _convert_citations_to_dicts_simplified(self, citations: List, clusters: List = None) -> List[Dict[str, Any]]:
        """Convert citations to simplified format for frontend."""
        try:
            converted = []
            true_by_parallel_citations = set()
            
            # Build true_by_parallel set from clusters
            if clusters:
                for cluster in clusters:
                    cluster_has_verified = cluster.get('cluster_has_verified', False)
                    if cluster_has_verified:
                        cluster_citations = cluster.get('citations', [])
                        for cluster_citation in cluster_citations:
                            if not cluster_citation.get('verified', False):
                                true_by_parallel_citations.add(cluster_citation.get('citation', ''))
            
            for citation in citations:
                if isinstance(citation, dict):
                    citation_text = citation.get('citation', '')
                    converted_citation = {
                        'citation': citation_text,
                        'extracted_case_name': citation.get('extracted_case_name'),
                        'extracted_date': citation.get('extracted_date'),
                        'confidence_score': citation.get('confidence_score', 0.5),
                        'extraction_method': citation.get('extraction_method', 'unknown'),
                        'false_positive_filtered': citation.get('false_positive_filtered', False),
                        'start_index': citation.get('start_index'),
                        'end_index': citation.get('end_index'),
                        'verified': citation.get('verified', False),
                        'canonical_name': citation.get('canonical_name'),
                        'canonical_date': citation.get('canonical_date'),
                        'canonical_url': citation.get('canonical_url'),
                        'url': citation.get('url'),
                        'source': citation.get('source'),
                        'validation_method': citation.get('validation_method'),
                        'verification_confidence': citation.get('verification_confidence', 0.0),
                        'true_by_parallel': citation_text in true_by_parallel_citations
                    }
                else:
                    # Handle CitationResult objects
                    citation_text = getattr(citation, 'citation', str(citation))
                    converted_citation = {
                        'citation': citation_text,
                        'extracted_case_name': getattr(citation, 'extracted_case_name', None),
                        'extracted_date': getattr(citation, 'extracted_date', None),
                        'confidence_score': getattr(citation, 'confidence_score', 0.5),
                        'extraction_method': getattr(citation, 'extraction_method', 'unknown'),
                        'false_positive_filtered': getattr(citation, 'false_positive_filtered', False),
                        'start_index': getattr(citation, 'start_index', None),
                        'end_index': getattr(citation, 'end_index', None),
                        'verified': getattr(citation, 'verified', False),
                        'canonical_name': getattr(citation, 'canonical_name', None),
                        'canonical_date': getattr(citation, 'canonical_date', None),
                        'canonical_url': getattr(citation, 'canonical_url', None),
                        'url': getattr(citation, 'url', None),
                        'source': getattr(citation, 'source', 'unknown'),
                        'validation_method': getattr(citation, 'validation_method', 'none'),
                        'verification_confidence': getattr(citation, 'verification_confidence', 0.0),
                        'true_by_parallel': citation_text in true_by_parallel_citations
                    }
                
                converted.append(converted_citation)
            
            return converted
            
        except Exception as e:
            logger.error(f"Citation conversion failed: {e}")
            return []
    
    def _convert_clusters_to_dicts(self, clusters: List) -> List[Dict[str, Any]]:
        """Convert clusters to dictionary format."""
        try:
            converted_clusters = []
            for cluster in clusters:
                converted_cluster = {
                    'cluster_id': cluster.get('cluster_id'),
                    'cluster_has_verified': cluster.get('cluster_has_verified', False),
                    'citations': cluster.get('citations', []),
                    'case_name': cluster.get('case_name'),
                    'case_date': cluster.get('case_date'),
                    'confidence': cluster.get('confidence', 0.5)
                }
                converted_clusters.append(converted_cluster)
            
            return converted_clusters
            
        except Exception as e:
            logger.error(f"Cluster conversion failed: {e}")
            return []
