"""
Standardized Error Handler for Processors Module

This module provides consistent error handling patterns for all processor components,
integrating with the existing quality/error_handling.py system.
"""

import logging
from typing import Any, Dict, Optional, Callable
from functools import wraps

from src.quality.error_handling import (
    CaseStrainerError, 
    CitationExtractionError,
    CitationVerificationError,
    CitationClusteringError,
    handle_errors,
    retry_on_error,
    ErrorContext,
    ErrorSeverity,
    error_tracker
)

logger = logging.getLogger(__name__)

class ProcessorError(CaseStrainerError):
    """Base error for processor-related issues."""
    pass

class CitationExtractionProcessorError(CitationExtractionError):
    """Error specific to citation extraction in processors."""
    pass

class CitationNormalizationError(ProcessorError):
    """Error specific to citation normalization."""
    pass

class NameYearExtractionError(ProcessorError):
    """Error specific to name/year extraction."""
    pass

class ClusteringProcessorError(CitationClusteringError):
    """Error specific to clustering in processors."""
    pass

def handle_processor_errors(
    operation: str,
    reraise: bool = True,
    default_return: Optional[Any] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
):
    """
    Decorator for standardized error handling in processor components.
    
    Args:
        operation: Name of the operation being performed
        reraise: Whether to reraise the exception after handling
        default_return: Default return value if error occurs and reraise=False
        severity: Error severity level
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except CitationExtractionError as e:
                logger.error(f"[{operation}] Citation extraction failed: {e}")
                error_tracker.record_error(
                    e, 
                    ErrorContext(operation=operation, additional_context={'component': 'citation_extraction'}),
                    severity
                )
                if reraise:
                    raise CitationExtractionProcessorError(f"Citation extraction failed in {operation}: {e}")
                return default_return
                
            except CitationClusteringError as e:
                logger.error(f"[{operation}] Citation clustering failed: {e}")
                error_tracker.record_error(
                    e,
                    ErrorContext(operation=operation, additional_context={'component': 'citation_clustering'}),
                    severity
                )
                if reraise:
                    raise ClusteringProcessorError(f"Clustering failed in {operation}: {e}")
                return default_return
                
            except Exception as e:
                logger.error(f"[{operation}] Unexpected error: {e}")
                error_tracker.record_error(
                    e,
                    ErrorContext(operation=operation, additional_context={'component': 'processor'}),
                    severity
                )
                if reraise:
                    raise ProcessorError(f"Unexpected error in {operation}: {e}")
                return default_return
        
        return wrapper
    return decorator

def safe_execute(
    func: Callable,
    operation: str,
    default_return: Optional[Any] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    **kwargs
) -> Any:
    """
    Safely execute a function with standardized error handling.
    
    Args:
        func: Function to execute
        operation: Name of the operation for logging
        default_return: Value to return if function fails
        severity: Error severity level
        **kwargs: Arguments to pass to the function
        
    Returns:
        Function result or default_return if error occurs
    """
    try:
        return func(**kwargs)
    except Exception as e:
        logger.error(f"[{operation}] Function execution failed: {e}")
        error_tracker.record_error(
            e,
            ErrorContext(operation=operation, additional_context={'function': func.__name__}),
            severity
        )
        return default_return

def log_operation_start(operation: str, **context):
    """Log the start of an operation with context."""
    logger.info(f"[{operation}] Starting operation", extra={'context': context})

def log_operation_success(operation: str, result_summary: Dict[str, Any]):
    """Log successful completion of an operation."""
    logger.info(f"[{operation}] Operation completed successfully", extra={'result': result_summary})

def log_operation_failure(operation: str, error: Exception, **context):
    """Log operation failure with context."""
    logger.error(f"[{operation}] Operation failed: {error}", extra={'context': context})

class ProcessorErrorHandler:
    """Centralized error handler for processor components."""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = logging.getLogger(f"{__name__}.{component_name}")
    
    def handle_extraction_error(self, error: Exception, citation_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle citation extraction errors."""
        error_context = ErrorContext(
            operation=f"{self.component_name}_extraction",
            additional_context={
                'citation_text': citation_text[:100],  # Limit length
                'component': self.component_name,
                **(context or {})
            }
        )
        
        error_tracker.record_error(error, error_context, ErrorSeverity.MEDIUM)
        
        return {
            'success': False,
            'error': str(error),
            'error_type': 'extraction_error',
            'component': self.component_name,
            'citation_text': citation_text
        }
    
    def handle_normalization_error(self, error: Exception, citation_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle citation normalization errors."""
        error_context = ErrorContext(
            operation=f"{self.component_name}_normalization",
            additional_context={
                'citation_text': citation_text[:100],
                'component': self.component_name,
                **(context or {})
            }
        )
        
        error_tracker.record_error(error, error_context, ErrorSeverity.MEDIUM)
        
        return {
            'success': False,
            'error': str(error),
            'error_type': 'normalization_error',
            'component': self.component_name,
            'citation_text': citation_text
        }
    
    def handle_verification_error(self, error: Exception, citation_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle citation verification errors."""
        error_context = ErrorContext(
            operation=f"{self.component_name}_verification",
            additional_context={
                'citation_text': citation_text[:100],
                'component': self.component_name,
                **(context or {})
            }
        )
        
        error_tracker.record_error(error, error_context, ErrorSeverity.MEDIUM)
        
        return {
            'success': False,
            'error': str(error),
            'error_type': 'verification_error',
            'component': self.component_name,
            'citation_text': citation_text
        }
    
    def handle_clustering_error(self, error: Exception, citations_count: int, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle citation clustering errors."""
        error_context = ErrorContext(
            operation=f"{self.component_name}_clustering",
            additional_context={
                'citations_count': citations_count,
                'component': self.component_name,
                **(context or {})
            }
        )
        
        error_tracker.record_error(error, error_context, ErrorSeverity.MEDIUM)
        
        return {
            'success': False,
            'error': str(error),
            'error_type': 'clustering_error',
            'component': self.component_name,
            'citations_count': citations_count
        }

