"""
Performance optimization package for citation processing.

This package provides tools and optimizations for improving citation processing performance.
"""

from .profiler import PerformanceProfiler, PerformanceBenchmark, profiler, create_standard_benchmarkfrom src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

from .cache import CitationCache, MemoryCache, RedisCache
from .optimizations import OptimizedCitationExtractor, OptimizedCitationVerifier, OptimizedCitationClusterer, performance_monitor

__all__ = [
    'PerformanceProfiler',
    'PerformanceBenchmark', 
    'profiler',
    'create_standard_benchmark',
    'CitationCache',
    'MemoryCache',
    'RedisCache',
    'OptimizedCitationExtractor',
    'OptimizedCitationVerifier',
    'OptimizedCitationClusterer',
    'performance_monitor'
]
