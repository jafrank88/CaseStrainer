#!/usr/bin/env python3
"""
Adaptive Learning Service for Citation Processing

This service integrates the existing adaptive learning system with the new modular architecture.
It provides adaptive learning capabilities for citation extraction, verification, and clustering.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_adaptive_learning_config
from src.services.interfaces import CitationResult

# Import the existing adaptive learning processor
try:
    from src.enhanced_adaptive_processor import EnhancedAdaptiveProcessor
    ADAPTIVE_LEARNING_AVAILABLE = True
    ImportedEnhancedAdaptiveProcessor = EnhancedAdaptiveProcessor  # type: ignore
except ImportError:
    try:
        # Try alternative import path
        sys.path.append(str(project_root / "scripts"))
        from enhanced_adaptive_processor import EnhancedAdaptiveProcessor
        ADAPTIVE_LEARNING_AVAILABLE = True
        ImportedEnhancedAdaptiveProcessor = EnhancedAdaptiveProcessor  # type: ignore
    except ImportError:
        ADAPTIVE_LEARNING_AVAILABLE = False
        # Create a dummy class for when adaptive learning is not available
        class ImportedEnhancedAdaptiveProcessor:  # type: ignore
            def __init__(self, *args, **kwargs):
                pass
            def extract_case_names(self, text, document_name=""):
                return []
            def process_text_optimized(self, text, document_name=""):
                return {"citations": [], "clusters": [], "learning_info": {}}
            def get_performance_summary(self):
                return {"enabled": False, "error": "Adaptive learning not available"}

logger = logging.getLogger(__name__)

@dataclass
class AdaptiveLearningResult:
    """Result from adaptive learning processing."""
    improved_citations: List[CitationResult]
    learned_patterns: List[Dict[str, Any]]
    confidence_adjustments: Dict[str, float]
    case_name_mappings: Dict[str, str]
    performance_metrics: Dict[str, Any]

class AdaptiveLearningService:
    """
    Service that provides adaptive learning capabilities for citation processing.
    
    This service:
    1. Learns from citation extraction failures and successes
    2. Builds pattern databases for improved extraction
    3. Adjusts confidence thresholds dynamically
    4. Maintains case name databases for better clustering
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the adaptive learning service.
        
        Args:
            config: Configuration dictionary, will use default config if None
        """
        self.config = config or get_adaptive_learning_config()
        self.enabled = self.config.get('enabled', True) and ADAPTIVE_LEARNING_AVAILABLE
        
        if self.enabled:
            # Initialize the enhanced adaptive processor
            learning_data_dir = self.config.get('learning_data_dir', 'data/adaptive_learning')
            os.makedirs(learning_data_dir, exist_ok=True)
            
            try:
                self.adaptive_processor = ImportedEnhancedAdaptiveProcessor(learning_data_dir)
                logger.info(f"Adaptive learning service initialized with data directory: {learning_data_dir}")
            except Exception as e:
                logger.warning(f"Failed to initialize adaptive processor: {e}")
                self.enabled = False
                self.adaptive_processor = None
        else:
            self.adaptive_processor = None
            if not ADAPTIVE_LEARNING_AVAILABLE:
                logger.info("Adaptive learning service disabled: EnhancedAdaptiveProcessor not available")
            else:
                logger.info("Adaptive learning service disabled by configuration")
    
    def is_enabled(self) -> bool:
        """Check if adaptive learning is enabled and available."""
        return self.enabled and self.adaptive_processor is not None
    
    def enhance_citation_extraction(self, 
                                  text: str, 
                                  document_name: str = "",
                                  existing_citations: Optional[List[CitationResult]] = None) -> AdaptiveLearningResult:
        """
        Enhance citation extraction using adaptive learning.
        
        Args:
            text: The text to process
            document_name: Name/identifier of the document
            existing_citations: Citations already found by other methods
            
        Returns:
            AdaptiveLearningResult with enhanced citations and learning data
        """
        if not self.is_enabled():
            # Return empty result if not enabled
            return AdaptiveLearningResult(
                improved_citations=existing_citations or [],
                learned_patterns=[],
                confidence_adjustments={},
                case_name_mappings={},
                performance_metrics={}
            )
        
        try:
            # Use the adaptive processor to enhance extraction
            if self.adaptive_processor is not None:
                result = self.adaptive_processor.process_text_optimized(text, document_name)
            else:
                result = {"citations": [], "clusters": [], "learning_info": {}}
            
            # Convert adaptive processor results to our format
            improved_citations = self._convert_adaptive_citations(
                result.get('citations', []), 
                existing_citations or []
            )
            
            # Extract learning information
            learning_info = result.get('learning_info', {})
            
            return AdaptiveLearningResult(
                improved_citations=improved_citations,
                learned_patterns=learning_info.get('new_patterns', []),
                confidence_adjustments=learning_info.get('confidence_adjustments', {}),
                case_name_mappings=learning_info.get('case_name_mappings', {}),
                performance_metrics=learning_info.get('performance_metrics', {})
            )
            
        except Exception as e:
            logger.error(f"Error in adaptive citation enhancement: {e}")
            return AdaptiveLearningResult(
                improved_citations=existing_citations or [],
                learned_patterns=[],
                confidence_adjustments={},
                case_name_mappings={},
                performance_metrics={}
            )
    
    def learn_from_verification_results(self, 
                                      citations: List[CitationResult], 
                                      verification_results: List[Dict[str, Any]],
                                      document_name: str = "") -> None:
        """
        Learn from citation verification results to improve future extractions.
        
        Args:
            citations: Original citations that were verified
            verification_results: Results from verification process
            document_name: Name/identifier of the document
        """
        if not self.is_enabled():
            return
        
        try:
            # Process verification feedback for learning
            for citation, verification in zip(citations, verification_results):
                if verification.get('verified', False):
                    # Successful verification - reinforce patterns
                    self._reinforce_successful_pattern(citation, verification, document_name)
                else:
                    # Failed verification - learn from failure
                    self._learn_from_verification_failure(citation, verification, document_name)
                    
        except Exception as e:
            logger.error(f"Error learning from verification results: {e}")
    
    def learn_from_clustering_results(self, 
                                    citations: List[CitationResult],
                                    clusters: List[Dict[str, Any]],
                                    document_name: str = "") -> None:
        """
        Learn from clustering results to improve case name extraction and clustering.
        
        Args:
            citations: Citations that were clustered
            clusters: Clustering results
            document_name: Name/identifier of the document
        """
        if not self.is_enabled():
            return
        
        try:
            # Extract case name mappings from successful clusters
            for cluster in clusters:
                if cluster.get('size', 0) > 1:  # Multi-citation clusters
                    canonical_name = cluster.get('canonical_name')
                    if canonical_name:
                        # Learn mappings between extracted and canonical names
                        for citation_id in cluster.get('citation_ids', []):
                            citation = next((c for c in citations if getattr(c, 'id', None) == citation_id), None)
                            if citation and citation.extracted_case_name:
                                self._learn_case_name_mapping(
                                    citation.extracted_case_name,
                                    canonical_name,
                                    document_name
                                )
                                
        except Exception as e:
            logger.error(f"Error learning from clustering results: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from the adaptive learning system."""
        if not self.is_enabled():
            return {"enabled": False}
        
        try:
            if self.adaptive_processor is not None:
                summary = self.adaptive_processor.get_performance_summary()
                summary["enabled"] = True
                return summary
            else:
                return {"enabled": False, "error": "Adaptive processor not initialized"}
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"enabled": True, "error": str(e)}
    
    def _convert_adaptive_citations(self, 
                                  adaptive_citations: List[Dict[str, Any]], 
                                  existing_citations: List[CitationResult]) -> List[CitationResult]:
        """Convert adaptive processor citations to CitationResult format."""
        converted = []
        
        # Start with existing citations
        converted.extend(existing_citations)
        
        # Add new citations found by adaptive processor
        for adaptive_citation in adaptive_citations:
            # Check if this citation is already in existing citations
            citation_text = adaptive_citation.get('citation', '')
            if not any(c.citation == citation_text for c in existing_citations):
                # Create new CitationResult
                citation = CitationResult(
                    citation=citation_text,
                    start_index=adaptive_citation.get('start_index', 0),
                    end_index=adaptive_citation.get('end_index', 0),
                    method="adaptive_learning",
                    confidence=adaptive_citation.get('confidence', 0.8)
                )
                
                # Add extracted metadata
                citation.extracted_case_name = adaptive_citation.get('case_name', '')
                citation.extracted_date = adaptive_citation.get('date', '')
                citation.context = adaptive_citation.get('context', '')
                
                converted.append(citation)
        
        return converted
    
    def _reinforce_successful_pattern(self, 
                                    citation: CitationResult, 
                                    verification: Dict[str, Any],
                                    document_name: str) -> None:
        """Reinforce patterns that led to successful verification."""
        try:
            # This would update pattern success rates in the adaptive processor
            # For now, we'll log the success for future implementation
            logger.debug(f"Reinforcing successful pattern for citation: {citation.citation}")
        except Exception as e:
            logger.error(f"Error reinforcing successful pattern: {e}")
    
    def _learn_from_verification_failure(self, 
                                       citation: CitationResult, 
                                       verification: Dict[str, Any],
                                       document_name: str) -> None:
        """Learn from verification failures to improve extraction."""
        try:
            # This would analyze why verification failed and adjust patterns
            # For now, we'll log the failure for future implementation
            logger.debug(f"Learning from verification failure for citation: {citation.citation}")
        except Exception as e:
            logger.error(f"Error learning from verification failure: {e}")
    
    def _learn_case_name_mapping(self, 
                               extracted_name: str, 
                               canonical_name: str,
                               document_name: str) -> None:
        """Learn mapping between extracted and canonical case names."""
        try:
            # This would update the case name database in the adaptive processor
            logger.debug(f"Learning case name mapping: '{extracted_name}' -> '{canonical_name}'")
        except Exception as e:
            logger.error(f"Error learning case name mapping: {e}")

# Factory function for easy instantiation
def create_adaptive_learning_service(config: Optional[Dict[str, Any]] = None) -> AdaptiveLearningService:
    """Create an adaptive learning service instance."""
    return AdaptiveLearningService(config)
