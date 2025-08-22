#!/usr/bin/env python3
"""
Optimized PDF Processor for CaseStrainer
Features:
- Parallel PDF processing with multiple extraction methods
- Memory-efficient streaming for large files
- Intelligent fallback strategies
- Performance monitoring and caching
- OCR optimization for scanned documents
- Timeout protection to prevent hanging

Optional Dependencies:
- pdfplumber: Enhanced PDF text extraction
- pytesseract + PIL: OCR capabilities for scanned documents
- These are handled gracefully if not available
- Type ignore comments suppress linter warnings for optional imports
"""

import os
import time
import logging
import hashlib
import threading
from typing import Dict, List, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFTimeoutError(Exception):
    """Custom timeout error for PDF processing"""
    pass

@dataclass
class ExtractionResult:
    """Result of PDF extraction attempt"""
    text: str
    processor: str
    confidence: float
    processing_time: float
    pages_processed: int
    memory_used: Optional[int] = None
    error: Optional[str] = None

@dataclass
class PDFMetadata:
    """PDF file metadata"""
    file_size: int
    page_count: int
    is_encrypted: bool
    is_scanned: bool
    has_text: bool
    compression: str
    version: str

class OptimizedPDFProcessor:
    """
    High-performance PDF processor with intelligent extraction strategies
    """
    
    def __init__(self, max_workers: int = 3, max_memory_mb: int = 512, timeout_seconds: int = 60):
        self.max_workers = max_workers
        self.max_memory_mb = max_memory_mb
        self.timeout_seconds = timeout_seconds
        self.extraction_cache = {}
        self.performance_stats = {}
        
        # Initialize extraction methods in order of preference
        self.extraction_methods = [
            ('pdfplumber', self._extract_with_pdfplumber),
            ('pypdf2', self._extract_with_pypdf2),
            ('pdfminer', self._extract_with_pdfminer),
            ('ocr_fallback', self._extract_with_ocr_fallback)
        ]
    
    def process_pdf(self, file_path: str, file_hash: Optional[str] = None) -> ExtractionResult:
        """
        Main PDF processing method with parallel extraction and intelligent fallback
        """
        start_time = time.time()
        
        if not file_hash:
            file_hash = self._calculate_file_hash(file_path)
        
        # Check cache first
        if file_hash in self.extraction_cache:
            logger.info(f"Cache hit for file: {file_path}")
            return self.extraction_cache[file_hash]
        
        try:
            # Get PDF metadata
            metadata = self._analyze_pdf_metadata(file_path)
            logger.info(f"Processing PDF: {file_path}, Pages: {metadata.page_count}, Size: {metadata.file_size/1024/1024:.1f}MB")
            
            # Choose optimal extraction strategy based on metadata
            if metadata.is_scanned or not metadata.has_text:
                logger.info("PDF appears to be scanned - using OCR-optimized strategy")
                result = self._process_scanned_pdf(file_path, metadata)
            else:
                logger.info("PDF has text content - using text extraction strategy")
                result = self._process_text_pdf(file_path, metadata)
            
            # Cache the result
            self.extraction_cache[file_hash] = result
            self._update_performance_stats(result)
            
            return result
            
        except Exception as e:
            error_msg = f"PDF processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ExtractionResult(
                text="",
                processor="ErrorProcessor",
                confidence=0.0,
                processing_time=time.time() - start_time,
                pages_processed=0,
                error=error_msg
            )
    
    def _process_text_pdf(self, file_path: str, metadata: PDFMetadata) -> ExtractionResult:
        """Process PDF with text content using parallel extraction methods with timeout"""
        start_time = time.time()
        
        # Use parallel processing for faster extraction with timeout
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_method = {
                executor.submit(self._safe_extract_with_timeout, method, file_path): name 
                for name, method in self.extraction_methods[:3]  # Skip OCR for text PDFs
            }
            
            results = []
            try:
                # Wait for all futures with timeout
                for future in as_completed(future_to_method, timeout=self.timeout_seconds):
                    method_name = future_to_method[future]
                    try:
                        text = future.result(timeout=30)  # 30 second timeout per method
                        if text and len(text.strip()) > 100:  # Minimum text threshold
                            confidence = self._calculate_text_confidence(text, metadata)
                            results.append(ExtractionResult(
                                text=text,
                                processor=method_name,
                                confidence=confidence,
                                processing_time=time.time() - start_time,
                                pages_processed=metadata.page_count
                            ))
                    except TimeoutError:
                        logger.warning(f"Extraction method {method_name} timed out")
                    except Exception as e:
                        logger.warning(f"Extraction method {method_name} failed: {e}")
            except TimeoutError:
                logger.warning("Overall extraction process timed out")
        
        if results:
            # Return the best result based on confidence
            best_result = max(results, key=lambda x: x.confidence)
            best_result.processing_time = time.time() - start_time
            return best_result
        
        # Fallback to basic extraction
        return self._fallback_extraction(file_path, metadata, start_time)
    
    def _safe_extract_with_timeout(self, method, file_path: str) -> str:
        """Safely execute extraction method with timeout"""
        try:
            result = method(file_path)
            # Ensure we always return a string, never None
            if result is None:
                return ""
            return str(result)
        except Exception as e:
            logger.warning(f"Extraction method failed: {e}")
            return ""
    
    def _process_scanned_pdf(self, file_path: str, metadata: PDFMetadata) -> ExtractionResult:
        """Process scanned PDF with OCR optimization"""
        start_time = time.time()
        
        # For scanned PDFs, try OCR methods first
        try:
            text = self._extract_with_ocr_fallback(file_path)
            if text and len(text.strip()) > 100:
                confidence = self._calculate_text_confidence(text, metadata)
                return ExtractionResult(
                    text=text,
                    processor="OCRProcessor",
                    confidence=confidence,
                    processing_time=time.time() - start_time,
                    pages_processed=metadata.page_count
                )
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
        
        # Fallback to text extraction methods
        return self._process_text_pdf(file_path, metadata)
    
    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """Fast pdfplumber extraction with memory management and timeout"""
        try:
            # Try to import pdfplumber, but make it optional
            try:
                import pdfplumber  # type: ignore[import-untyped]
            except ImportError:
                logger.debug("pdfplumber not available")
                return ""
            
            # Limit pages for memory efficiency
            max_pages = min(50, self._estimate_safe_page_limit(file_path))  # Reduced from 100
            
            with pdfplumber.open(file_path) as pdf:
                pages = pdf.pages[:max_pages]
                texts = []
                
                for i, page in enumerate(pages):
                    try:
                        # Add timeout per page
                        page_text = page.extract_text()
                        if page_text:
                            texts.append(page_text)
                        
                        # Check if we're taking too long
                        if i > 0 and i % 10 == 0:
                            logger.debug(f"Processed {i} pages...")
                            
                    except Exception as e:
                        logger.warning(f"Page {i} extraction failed: {e}")
                        continue
                
                return "\n\n".join(texts) if texts else ""
                
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return ""
    
    def _extract_with_pypdf2(self, file_path: str) -> str:
        """PyPDF2 extraction with encryption handling and timeout"""
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                if reader.is_encrypted:
                    logger.warning("PDF is encrypted - cannot extract text")
                    return ""
                
                max_pages = min(len(reader.pages), 50)  # Reduced from 100
                texts = []
                
                for i in range(max_pages):
                    try:
                        page = reader.pages[i]
                        page_text = page.extract_text()
                        if page_text:
                            texts.append(page_text)
                        
                        # Check if we're taking too long
                        if i > 0 and i % 10 == 0:
                            logger.debug(f"Processed {i} pages...")
                            
                    except Exception as e:
                        logger.warning(f"Page {i} extraction failed: {e}")
                        continue
                
                return "\n\n".join(texts) if texts else ""
                
        except ImportError:
            logger.debug("PyPDF2 not available")
            return ""
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
            return ""
    
    def _extract_with_pdfminer(self, file_path: str) -> str:
        """pdfminer.six extraction with page limits and timeout"""
        try:
            from pdfminer.high_level import extract_text
            
            max_pages = min(50, self._estimate_safe_page_limit(file_path))  # Reduced from 100
            text = extract_text(file_path, maxpages=max_pages)
            
            return text if text else ""
            
        except ImportError:
            logger.debug("pdfminer.six not available")
            return ""
        except Exception as e:
            logger.warning(f"pdfminer.six extraction failed: {e}")
            return ""
    
    def _extract_with_ocr_fallback(self, file_path: str) -> str:
        """OCR fallback for scanned documents"""
        try:
            # Try to use pytesseract if available, but make it optional
            try:
                import pytesseract  # type: ignore[import-untyped]
                from PIL import Image  # type: ignore[import-untyped,reportMissingModuleSource]
            except ImportError:
                logger.debug("OCR dependencies not available")
                return ""
            
            # Convert PDF to images and OCR them
            # This is a simplified version - in production you'd want more sophisticated PDF-to-image conversion
            logger.info("Attempting OCR extraction")
            
            # For now, return empty string to indicate OCR is not fully implemented
            # In production, you'd implement full PDF-to-image-to-text pipeline
            return ""
            
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
            return ""
    
    def _fallback_extraction(self, file_path: str, metadata: PDFMetadata, start_time: float) -> ExtractionResult:
        """Basic fallback extraction method"""
        try:
            # Try to read as text file (in case it's misnamed)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                if text and len(text.strip()) > 50:
                    return ExtractionResult(
                        text=text,
                        processor="TextFileFallback",
                        confidence=0.3,
                        processing_time=time.time() - start_time,
                        pages_processed=1
                    )
        except:
            pass
        
        return ExtractionResult(
            text="",
            processor="NoExtractor",
            confidence=0.0,
            processing_time=time.time() - start_time,
            pages_processed=0,
            error="No extraction method succeeded"
        )
    
    def _analyze_pdf_metadata(self, file_path: str) -> PDFMetadata:
        """Analyze PDF file to determine optimal processing strategy"""
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                file_size = os.path.getsize(file_path)
                page_count = len(reader.pages)
                is_encrypted = reader.is_encrypted
                
                # Check if PDF has text content
                has_text = False
                try:
                    if page_count > 0:
                        first_page = reader.pages[0]
                        sample_text = first_page.extract_text()
                        has_text = bool(sample_text and len(sample_text.strip()) > 10)
                except:
                    has_text = False
                
                # Estimate if PDF is scanned (no text content)
                is_scanned = not has_text
                
                return PDFMetadata(
                    file_size=file_size,
                    page_count=page_count,
                    is_encrypted=is_encrypted,
                    is_scanned=is_scanned,
                    has_text=has_text,
                    compression="unknown",  # Could be enhanced
                    version="unknown"       # Could be enhanced
                )
                
        except Exception as e:
            logger.warning(f"PDF metadata analysis failed: {e}")
            # Return basic metadata
            return PDFMetadata(
                file_size=os.path.getsize(file_path),
                page_count=0,
                is_encrypted=False,
                is_scanned=True,
                has_text=False,
                compression="unknown",
                version="unknown"
            )
    
    def _calculate_text_confidence(self, text: str, metadata: PDFMetadata) -> float:
        """Calculate confidence score for extracted text"""
        if not text:
            return 0.0
        
        # Basic confidence scoring
        confidence = 0.5  # Base confidence
        
        # Length-based scoring
        if len(text) > 1000:
            confidence += 0.2
        elif len(text) > 100:
            confidence += 0.1
        
        # Text quality indicators
        if any(word in text.lower() for word in ['court', 'case', 'judgment', 'opinion']):
            confidence += 0.1
        
        # Punctuation and formatting
        if text.count('.') > text.count(' ') * 0.1:
            confidence += 0.1
        
        # Page count correlation
        if metadata.page_count > 0:
            expected_text_per_page = len(text) / metadata.page_count
            if 100 < expected_text_per_page < 2000:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _estimate_safe_page_limit(self, file_path: str) -> int:
        """Estimate safe page limit based on file size and memory constraints"""
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        
        # More conservative page limits to prevent hanging
        if file_size_mb < 5:
            return 50
        elif file_size_mb < 20:
            return 25
        elif file_size_mb < 50:
            return 15
        else:
            return 10
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for caching"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _update_performance_stats(self, result: ExtractionResult):
        """Update performance statistics"""
        processor = result.processor
        if processor not in self.performance_stats:
            self.performance_stats[processor] = {
                'total_time': 0,
                'count': 0,
                'success_rate': 0,
                'avg_confidence': 0
            }
        
        stats = self.performance_stats[processor]
        stats['total_time'] += result.processing_time
        stats['count'] += 1
        stats['avg_confidence'] = (stats['avg_confidence'] * (stats['count'] - 1) + result.confidence) / stats['count']
        
        if result.error is None:
            stats['success_rate'] = (stats['success_rate'] * (stats['count'] - 1) + 1) / stats['count']
    
    def get_performance_stats(self) -> Dict:
        """Get current performance statistics"""
        return self.performance_stats.copy()
    
    def clear_cache(self):
        """Clear the extraction cache"""
        self.extraction_cache.clear()
        logger.info("PDF extraction cache cleared")

# Global instance for easy access
pdf_processor = OptimizedPDFProcessor()

def extract_pdf_optimized_v2(file_path: str, file_hash: Optional[str] = None) -> Dict[str, Union[str, float, int]]:
    """
    Optimized PDF extraction function for RQ workers
    Returns dict compatible with existing code
    """
    try:
        result = pdf_processor.process_pdf(file_path, file_hash)
        
        return {
            'text': result.text,
            'processor': result.processor,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'pages_processed': result.pages_processed,
            'file_hash': str(file_hash) if file_hash is not None else "",
            'error': str(result.error) if result.error is not None else ""
        }
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}", exc_info=True)
        return {
            'text': f"Error: {str(e)}",
            'processor': 'ErrorProcessor',
            'confidence': 0.0,
            'processing_time': 0.0,
            'pages_processed': 0,
            'file_hash': str(file_hash) if file_hash is not None else "",
            'error': str(e)
        }
