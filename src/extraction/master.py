"""
Unified Case Extraction Master (Refactored)
=============================================

This is a refactored version that delegates to the modular extraction package.
Maintains backward compatibility while using the new modular implementation.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from . import strategies, validation, utils

logger = logging.getLogger(__name__)


@dataclass
class MasterExtractionResult:
    """Standardized result from the master extraction function."""
    
    case_name: str
    year: str
    confidence: float
    method: str
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    context: str = ""
    debug_info: Optional[Dict[str, Any]] = None
    canonical_name: Optional[str] = None
    canonical_year: Optional[str] = None
    extracted_case_name: Optional[str] = None
    extracted_year: Optional[str] = None


class UnifiedCaseExtractionMaster:
    """
    THE SINGLE, AUTHORITATIVE case name extraction implementation (MODULAR VERSION).
    
    This refactored class uses the modular extraction package:
    - strategies: Different extraction strategies
    - validation: Case name validation
    - utils: Utility functions
    
    Maintains full backward compatibility with the original implementation.
    """

    def __init__(self, document_primary_case_name: Optional[str] = None):
        """Initialize the master extraction engine."""
        self.document_primary_case_name = document_primary_case_name
        self.citation_metadata_cache: Dict[str, Dict[str, Any]] = {}
        
        # Initialize strategies
        self.strategies = strategies.get_strategies()
        
        if document_primary_case_name:
            logger.warning(f"[CONTAMINATION-FILTER] Document primary case: '{document_primary_case_name}'")

    def extract_case_name_and_date(
        self,
        text: str,
        citation: Optional[str] = None,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        debug: bool = False
    ) -> MasterExtractionResult:
        """
        Extract case name and date using modular strategies.
        
        Args:
            text: Text to extract from
            citation: Optional citation text for context
            start_index: Start position in document
            end_index: End position in document
            debug: Enable debug output
            
        Returns:
            MasterExtractionResult with extraction data
        """
        # Try each strategy in order
        best_result = None
        best_confidence = 0.0
        
        for strategy in self.strategies:
            try:
                result = strategy.extract(text, citation)
                if result and result.get("confidence", 0) > best_confidence:
                    best_confidence = result["confidence"]
                    best_result = result
                    best_result["strategy"] = strategy.name
            except Exception as e:
                logger.debug(f"Strategy {strategy.name} failed: {e}")
                continue
        
        # Validate the best result
        if best_result:
            validation_result = validation.validate_case_name(best_result.get("case_name", ""))
            
            # Adjust confidence based on validation
            best_result["confidence"] *= validation_result["quality_score"]
            best_result["validation"] = validation_result
        
        # Extract year from text
        year = utils.extract_year_from_text(text)
        
        # Build final result
        if best_result:
            case_name = utils.clean_case_name(best_result.get("case_name", "N/A"))
            confidence = best_result.get("confidence", 0.5)
            method = best_result.get("strategy", "unknown")
        else:
            case_name = "N/A"
            confidence = 0.0
            method = "extraction_failed"
        
        return MasterExtractionResult(
            case_name=case_name,
            year=str(year) if year else "N/A",
            confidence=confidence,
            method=method,
            start_index=start_index,
            end_index=end_index,
            context=text[:100] + "..." if len(text) > 100 else text,
            debug_info=best_result if best_result else {},
            extracted_case_name=case_name if case_name != "N/A" else None,
            extracted_year=str(year) if year else None,
        )


# Convenience function for direct use
def extract_case_name_and_date_unified_master(
    text: str,
    citation: Optional[str] = None,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    debug: bool = False,
    canonical_name: Optional[str] = None,
    canonical_date: Optional[str] = None,
    document_primary_case_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    THE SINGLE, UNIFIED EXTRACTION FUNCTION (MODULAR VERSION).
    
    This function replaces ALL 120+ duplicate extraction functions.
    Uses the new modular extraction package internally.
    
    Returns:
        Dictionary with case_name, year, confidence, method, and debug_info
    """
    extractor = UnifiedCaseExtractionMaster(document_primary_case_name)
    
    result = extractor.extract_case_name_and_date(
        text=text,
        citation=citation,
        start_index=start_index,
        end_index=end_index,
        debug=debug
    )
    
    return {
        "case_name": result.case_name,
        "year": result.year,
        "date": result.year,
        "confidence": result.confidence,
        "method": result.method,
        "start_index": result.start_index,
        "end_index": result.end_index,
        "context": result.context,
        "debug_info": result.debug_info or {},
        "canonical_name": canonical_name,
        "canonical_year": canonical_date,
        "extracted_case_name": result.extracted_case_name or "N/A",
        "extracted_year": result.extracted_year or "N/A",
    }


_extractor_instance: Optional[UnifiedCaseExtractionMaster] = None


def get_master_extractor() -> UnifiedCaseExtractionMaster:
    """Return the shared UnifiedCaseExtractionMaster instance (for health checks, etc.)."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = UnifiedCaseExtractionMaster()
    return _extractor_instance
