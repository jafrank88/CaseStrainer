"""
Performance optimization package for citation processing.

This package provides tools and optimizations for improving citation processing performance.
"""

from .profiler import PerformanceProfiler, PerformanceBenchmark, profiler, create_standard_benchmark
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
