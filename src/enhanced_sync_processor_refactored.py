"""
Enhanced Sync Processor with Async Verification - Refactored

DEPRECATED: This module is deprecated and will be removed in v3.0.0.
Use UnifiedCitationProcessorV2 directly instead.

The features from this processor have been integrated into the main pipeline:
- Progress callbacks: Use UnifiedCitationProcessorV2(progress_callback=callback)
- False positive prevention: Integrated into main processing pipeline
- Enhanced processing options: Use ProcessingConfig instead

Provides immediate results with local processing and optional background verification.
"""

import warnings
import os
import sys
import time
import logging
import hashlib
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from pathlib import Path

def _deprecated_warning():
    """Issue deprecation warning for this module."""
    warnings.warn(
        "enhanced_sync_processor_refactored is deprecated and will be removed in v3.0.0. "
        "Use UnifiedCitationProcessorV2 directly instead.",
        DeprecationWarning,
        stacklevel=3
    )

import re

from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT
from src.processors import SyncProcessorCore, ProcessingOptions

logger = logging.getLogger(__name__)

@dataclass
class EnhancedProcessingOptions(ProcessingOptions):
    """Enhanced processing options extending the base options."""
    enable_async_verification: bool = True
    enable_progress_tracking: bool = True
    processing_quality: str = "high"  # low, medium, high
    courtlistener_api_key: Optional[str] = None

class EnhancedSyncProcessor:
    """
    Enhanced processor that provides immediate results with local processing
    and queues verification for background async processing.
    
    Refactored to use modular components for better maintainability.
    """
    
    def __init__(self, options: Optional[EnhancedProcessingOptions] = None, progress_callback: Optional[Any] = None):
        """Initialize the enhanced sync processor with configuration options."""
        _deprecated_warning()  # Issue deprecation warning
        self.options = options or EnhancedProcessingOptions()
        self.progress_callback = progress_callback
        
        # Initialize the core processor with modular components
        self.core_processor = SyncProcessorCore(
            options=self.options,
            progress_callback=self.progress_callback
        )
        
        logger.info(f"[EnhancedSyncProcessor] Initialized with modular components")
    
    def process_any_input_enhanced(self, input_data: Any, input_type: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process any type of input (text, file, URL) using enhanced sync processing.
        
        Args:
            input_data: The input data (text string, file path, or URL)
            input_type: Type of input ('text', 'file', 'url')
            options: Optional processing options
            
        Returns:
            Dictionary with processing results
        """
        request_id = self._generate_request_id(input_data, input_type)
        
        try:
            logger.info(f"[EnhancedSyncProcessor {request_id}] Processing {input_type} input")
            
            # Extract text from input
            text_result = self._extract_text_from_input(input_data, input_type, request_id)
            if not text_result.get('success', False):
                return {
                    'success': False,
                    'error': text_result.get('error', 'Text extraction failed'),
                    'request_id': request_id
                }
            
            text = text_result['text']
            
            # Determine processing strategy
            if self._should_use_enhanced_sync(text):
                logger.info(f"[EnhancedSyncProcessor {request_id}] Using enhanced sync processing")
                result = self.core_processor.process_enhanced_sync(text, request_id, options)
            else:
                logger.info(f"[EnhancedSyncProcessor {request_id}] Using basic processing")
                result = self._process_basic_sync(text, request_id, options)
            
            # Add metadata
            result['success'] = True
            result['input_type'] = input_type
            result['text_length'] = len(text)
            result['metadata'].update(text_result.get('metadata', {}))
            
            return result
            
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] Processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'request_id': request_id,
                'input_type': input_type
            }
    
    def _should_use_enhanced_sync(self, text: str) -> bool:
        """Determine if enhanced sync processing should be used."""
        return len(text) > 100  # Use enhanced sync for text longer than 100 characters
    
    def _extract_text_from_input(self, input_data: Any, input_type: str, request_id: str) -> Dict[str, Any]:
        """Extract text from various input types."""
        try:
            if input_type == 'text':
                return self._extract_from_text(input_data, request_id)
            elif input_type == 'file':
                return self._extract_from_file(input_data, request_id)
            elif input_type == 'url':
                return self._extract_from_url(input_data, request_id)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported input type: {input_type}'
                }
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] Text extraction failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_from_text(self, text: str, request_id: str) -> Dict[str, Any]:
        """Extract text from string input."""
        return {
            'success': True,
            'text': text,
            'metadata': {'input_type': 'text'}
        }
    
    def _extract_from_file(self, file_path: str, request_id: str) -> Dict[str, Any]:
        """Extract text from file input."""
        try:
            from src.file_utils import extract_text_from_file
            
            text = extract_text_from_file(file_path)
            return {
                'success': True,
                'text': text,
                'metadata': {'input_type': 'file', 'file_path': file_path}
            }
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] File extraction failed: {e}")
            return {
                'success': False,
                'error': f'File extraction failed: {e}'
            }
    
    def _extract_from_url(self, url: str, request_id: str) -> Dict[str, Any]:
        """Extract text from URL input."""
        try:
            import requests
            
            response = requests.get(url, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Simple text extraction - could be enhanced with proper HTML parsing
            text = response.text
            return {
                'success': True,
                'text': text,
                'metadata': {'input_type': 'url', 'url': url}
            }
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] URL extraction failed: {e}")
            return {
                'success': False,
                'error': f'URL extraction failed: {e}'
            }
    
    def _process_basic_sync(self, text: str, request_id: str, options: Optional[Dict]) -> Dict[str, Any]:
        """Basic sync processing for simple cases."""
        try:
            # Use core processor with basic settings (enable clustering for better results)
            basic_options = ProcessingOptions(
                enable_enhanced_verification=False,
                enable_confidence_scoring=False,
                enable_false_positive_prevention=True,
                enable_clustering=True  # ENABLED: Basic clustering improves citation organization
            )
            
            basic_processor = SyncProcessorCore(
                options=basic_options,
                progress_callback=self.progress_callback
            )
            
            return basic_processor.process_enhanced_sync(text, request_id, options)
            
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] Basic processing failed: {e}")
            return {
                'citations': [],
                'clusters': [],
                'metadata': {
                    'processing_mode': 'basic_sync',
                    'error': str(e),
                    'request_id': request_id
                }
            }
    
    def _generate_request_id(self, input_data: Any, input_type: str) -> str:
        """Generate a unique request ID."""
        try:
            data_str = str(input_data)[:100]  # Limit length
            hash_input = f"{input_type}_{data_str}_{time.time()}"
            return hashlib.md5(hash_input.encode()).hexdigest()[:8]
        except Exception:
            return f"req_{int(time.time())}"









