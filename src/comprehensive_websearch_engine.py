"""
Comprehensive Legal Web Search Engine
This module has been refactored into smaller, focused modules in the websearch package.
For backward compatibility, all classes and functions are imported from the new structure.
"""

from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT
from .websearch import (

    EnhancedCitationNormalizer,
    SearchEngineMetadata,
    CacheManager,
    SourcePredictor,
    SemanticMatcher,
    EnhancedLinkrotDetector,
    ResultFusionEngine,
    AdvancedMLPredictor,
    AdvancedErrorRecovery,
    AdvancedAnalytics,
    ComprehensiveWebExtractor,
    ComprehensiveWebSearchEngine,
    search_cluster_for_canonical_sources,
    search_all_engines,
    test_comprehensive_web_search
)

__all__ = [
    'EnhancedCitationNormalizer',
    'SearchEngineMetadata',
    'CacheManager',
    'SourcePredictor',
    'SemanticMatcher',
    'EnhancedLinkrotDetector',
    'ResultFusionEngine',
    'AdvancedMLPredictor',
    'AdvancedErrorRecovery',
    'AdvancedAnalytics',
    'ComprehensiveWebExtractor',
    'ComprehensiveWebSearchEngine',
    'search_cluster_for_canonical_sources',
    'search_all_engines',
    'test_comprehensive_web_search'
] 