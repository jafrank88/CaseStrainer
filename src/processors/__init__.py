"""
Processors Module

This module contains refactored processing components that were extracted
from the large enhanced_sync_processor.py file for better maintainability.
"""

from .sync_processor_core import SyncProcessorCore, ProcessingOptions
from .citation_extractor import CitationExtractor
from .citation_normalizer import CitationNormalizer
from .name_year_extractor import NameYearExtractor
from .error_handler import (
    ProcessorErrorHandler, 
    handle_processor_errors, 
    safe_execute,
    ProcessorError,
    CitationExtractionProcessorError,
    CitationNormalizationError,
    NameYearExtractionError,
    ClusteringProcessorError
)

__all__ = [
    'SyncProcessorCore',
    'ProcessingOptions', 
    'CitationExtractor',
    'CitationNormalizer',
    'NameYearExtractor',
    'ProcessorErrorHandler',
    'handle_processor_errors',
    'safe_execute',
    'ProcessorError',
    'CitationExtractionProcessorError',
    'CitationNormalizationError',
    'NameYearExtractionError',
    'ClusteringProcessorError'
]
