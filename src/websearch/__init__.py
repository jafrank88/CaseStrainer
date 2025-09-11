"""
Web Search Package
Refactored from comprehensive_websearch_engine.py for better maintainability.
"""

from .citation_normalizer import EnhancedCitationNormalizer
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

from .metadata import SearchEngineMetadata
from .cache import CacheManager
from .predictor import SourcePredictor
from .semantic import SemanticMatcher
from .linkrot import EnhancedLinkrotDetector
from .fusion import ResultFusionEngine
from .ml_predictor import AdvancedMLPredictor
from .error_recovery import AdvancedErrorRecovery
from .analytics import AdvancedAnalytics
from .extractor import ComprehensiveWebExtractor
from .engine import ComprehensiveWebSearchEngine
from .utils import search_cluster_for_canonical_sources, search_all_engines, test_comprehensive_web_search

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