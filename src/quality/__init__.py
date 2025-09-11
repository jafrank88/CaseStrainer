"""
Code quality improvements package for citation processing.

This package provides type annotations, error handling, logging, and testing utilities.
"""

from .type_annotations import (

    CitationText, CaseNameText, DateText, UrlText, ConfidenceScore, 
    ProcessingMethod, VerificationStatus, CitationDict, ClusterDict,
    ProcessingResultDict, ConfigDict, Extractable, Verifiable, Clusterable,
    TypedCitationResult, TypeValidator, TypedServiceMixin, type_checked
)

from .error_handling import (
    CaseStrainerError, CitationExtractionError, CitationVerificationError,
    CitationClusteringError, APIError, ValidationError, ConfigurationError,
    CacheError, RateLimitError, ErrorSeverity, ErrorContext, ErrorTracker,
    error_tracker, handle_errors, retry_on_error, error_context,
    LoggingConfig, JsonFormatter, HealthChecker, health_checker
)

from .testing_framework import (
    CitationTestCase, TestDataGenerator, MockAPIResponse, TestRunner,
    PerformanceTestSuite, QualityMetrics, CodeCoverageAnalyzer
)

__all__ = [
    'CitationText', 'CaseNameText', 'DateText', 'UrlText', 'ConfidenceScore',
    'ProcessingMethod', 'VerificationStatus', 'CitationDict', 'ClusterDict',
    'ProcessingResultDict', 'ConfigDict', 'Extractable', 'Verifiable', 'Clusterable',
    'TypedCitationResult', 'TypeValidator', 'TypedServiceMixin', 'type_checked',
    
    'CaseStrainerError', 'CitationExtractionError', 'CitationVerificationError',
    'CitationClusteringError', 'APIError', 'ValidationError', 'ConfigurationError',
    'CacheError', 'RateLimitError', 'ErrorSeverity', 'ErrorContext', 'ErrorTracker',
    'error_tracker', 'handle_errors', 'retry_on_error', 'error_context',
    'LoggingConfig', 'JsonFormatter', 'HealthChecker', 'health_checker',
    
    'CitationTestCase', 'TestDataGenerator', 'MockAPIResponse', 'TestRunner',
    'PerformanceTestSuite', 'QualityMetrics', 'CodeCoverageAnalyzer'
]
