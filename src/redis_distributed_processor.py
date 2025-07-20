"""
Redis-Distributed PDF Processing System for CaseTrainer

This system leverages Redis workers and Docker for maximum performance:
1. Redis caching for extracted text and processing results
2. Distributed processing across multiple workers
3. Async/await patterns for non-blocking operations
4. Docker-optimized resource usage
5. Smart caching strategies to avoid reprocessing

Key benefits:
- Cache extracted text to avoid re-extraction
- Distribute large documents across workers
- Use Redis for intermediate results
- Scale processing based on document size
"""

import os
import re
import time
import logging
import hashlib
import asyncio
from typing import Optional, Dict, List, Tuple, Any
from concurrent.futures import ThreadPoolExecutor
import json
import pickle
from dataclasses import dataclass, asdict

try:
    import redis
    import rq
    from rq import Queue, Worker, Connection
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis/RQ not available - falling back to local processing")

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Standard result format for caching and distribution."""
    text: str
    processor_used: str
    processing_time: float
    file_hash: str
    cache_hit: bool = False
    worker_id: Optional[str] = None

@dataclass
class CitationChunk:
    """Citation processing chunk for distribution."""
    chunk_id: str
    text: str
    start_position: int
    end_position: int
    file_hash: str

class RedisDistributedPDFSystem:
    """
    Redis-distributed PDF processing system optimized for Docker deployment.
    """
    
    def __init__(self, 
                 redis_url: str = "redis://casestrainer-redis-prod:6379/0",
                 cache_ttl: int = 3600,  # 1 hour cache
                 max_workers: int = 4,
                 chunk_size: int = 50000):
        
        self.cache_ttl = cache_ttl
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        
        # Initialize Redis connection
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.queue = Queue('casestrainer', connection=self.redis_client)
                self.redis_available = True
                
                # Test connection
                self.redis_client.ping()
                logger.info("Redis connection established")
                
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_available = False
        else:
            self.redis_available = False
        
        # Pre-compiled patterns for speed
        self._compile_patterns()
        
        # Worker identification for debugging
        self.worker_id = os.getenv('WORKER_ID', f'worker_{os.getpid()}')
    
    def _compile_patterns(self):
        """Pre-compile all regex patterns for maximum speed."""
        self._ocr_fixes = {
            'us_reports': re.compile(r'(\d+)\s*[Uu0o]\s*[.,]?\s*[Ss5]\s*[.,]?\s*(\d+)', re.IGNORECASE),
            'supreme_court': re.compile(r'(\d+)\s*[Ss5]\s*[.,]?\s*[CcGg][Tt7]\s*[.,]?\s*(\d+)', re.IGNORECASE),
            'lawyers_edition': re.compile(r'(\d+)\s*[Ll1I]\s*[.,]?\s*[Ee3]\s*[dD]\s*[.,]?\s*(\d+)', re.IGNORECASE),
            'federal': re.compile(r'(\d+)\s*[Ff]\s*[.,]?\s*(2[dD]|3[dD]|4th)?\s*(\d+)', re.IGNORECASE),
        }
        
        self._whitespace = re.compile(r'\s+')
        self._page_numbers = re.compile(r'^\s*\d{1,4}\s*$', re.MULTILINE)
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate file hash for caching."""
        try:
            # Use file path + modification time + size for hash
            stat = os.stat(file_path)
            hash_input = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
            return hashlib.md5(hash_input.encode('utf-8'), usedforsecurity=False).hexdigest()
        except Exception:
            return hashlib.md5(file_path.encode('utf-8'), usedforsecurity=False).hexdigest()
    
    def _cache_get(self, key: str) -> Optional[Any]:
        """Get item from Redis cache."""
        if not self.redis_available:
            return None
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                return pickle.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        return None
    
    def _cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set item in Redis cache."""
        if not self.redis_available:
            return False
        
        try:
            ttl = ttl or self.cache_ttl
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False
    
    async def extract_text_distributed(self, file_path: str) -> ProcessingResult:
        """
        Main entry point for distributed text extraction.
        Uses caching and worker distribution for optimal performance.
        """
        start_time = time.time()
        file_hash = self._get_file_hash(file_path)
        
        # Check cache first
        cache_key = f"extracted_text:{file_hash}"
        cached_result = self._cache_get(cache_key)
        
        if cached_result:
            logger.info(f"Cache hit for {file_path}")
            cached_result.cache_hit = True
            return cached_result
        
        # Determine processing strategy
        file_size = os.path.getsize(file_path)
        
        if file_size > 100 * 1024 * 1024:  # 100MB+
            # Large file - use distributed processing
            result = await self._extract_large_file_distributed(file_path, file_hash)
        elif file_size > 10 * 1024 * 1024:  # 10MB+
            # Medium file - use worker queue
            result = await self._extract_medium_file_worker(file_path, file_hash)
        else:
            # Small file - process locally
            result = await self._extract_small_file_local(file_path, file_hash)
        
        result.processing_time = time.time() - start_time
        result.worker_id = self.worker_id
        
        # Cache the result
        self._cache_set(cache_key, result)
        
        logger.info(f"Extraction completed in {result.processing_time:.3f}s using {result.processor_used}")
        return result
    
    async def _extract_large_file_distributed(self, file_path: str, file_hash: str) -> ProcessingResult:
        """
        Process large files by distributing across multiple workers.
        Split file into chunks and process in parallel.
        """
        logger.info(f"Processing large file with distributed workers: {file_path}")
        
        if not self.redis_available:
            # Fallback to local processing
            return await self._extract_small_file_local(file_path, file_hash)
        
        try:
            # For very large PDFs, we can split page-by-page
            from pdfminer.high_level import extract_text_to_fp
            from pdfminer.pdfpage import PDFPage
            import io
            
            # Get page count quickly
            with open(file_path, 'rb') as file:
                pages = list(PDFPage.get_pages(file))
                total_pages = len(pages)
            
            # Split into chunks of pages
            pages_per_chunk = max(1, total_pages // self.max_workers)
            chunk_jobs = []
            
            # Submit page chunks to workers
            for i in range(0, total_pages, pages_per_chunk):
                end_page = min(i + pages_per_chunk, total_pages)
                job = self.queue.enqueue(
                    'extract_pdf_pages',
                    file_path, i, end_page, file_hash,
                    timeout=300  # 5 minute timeout per chunk
                )
                chunk_jobs.append(job)
            
            # Collect results
            text_chunks = []
            for job in chunk_jobs:
                try:
                    result = job.result(timeout=300)
                    if result:
                        text_chunks.append(result)
                except Exception as e:
                    logger.warning(f"Worker job failed: {e}")
            
            combined_text = "\n".join(text_chunks)
            
            return ProcessingResult(
                text=combined_text,
                processor_used="DistributedPDFProcessor",
                processing_time=0,  # Will be set by caller
                file_hash=file_hash
            )
            
        except Exception as e:
            logger.error(f"Distributed processing failed: {e}")
            # Fallback to local processing
            return await self._extract_small_file_local(file_path, file_hash)
    
    async def _extract_medium_file_worker(self, file_path: str, file_hash: str) -> ProcessingResult:
        """
        Process medium files using worker queue for non-blocking operation.
        """
        logger.info(f"Processing medium file with worker: {file_path}")
        
        if not self.redis_available:
            return await self._extract_small_file_local(file_path, file_hash)
        
        try:
            # Submit to worker queue
            job = self.queue.enqueue(
                'extract_pdf_optimized',
                file_path, file_hash,
                timeout=180  # 3 minute timeout
            )
            
            # Wait for result (non-blocking in real async context)
            result = job.result(timeout=180)
            
            return ProcessingResult(
                text=result['text'],
                processor_used=result['processor'],
                processing_time=0,
                file_hash=file_hash
            )
            
        except Exception as e:
            logger.error(f"Worker processing failed: {e}")
            return await self._extract_small_file_local(file_path, file_hash)
    
    async def _extract_small_file_local(self, file_path: str, file_hash: str) -> ProcessingResult:
        """
        Process small files locally for minimum latency.
        """
        # Use the ultra-fast extraction from previous implementation
        text, processor = self._smart_pdf_extraction_strategy(file_path)
        
        return ProcessingResult(
            text=text,
            processor_used=processor,
            processing_time=0,
            file_hash=file_hash
        )
    
    def _smart_pdf_extraction_strategy(self, file_path: str) -> Tuple[str, str]:
        """
        Optimized extraction strategy that prioritizes PyPDF2 for speed and text extraction.
        """
        # Try PyPDF2 first (fastest and extracts most text)
        text = self._extract_with_pypdf2_fast(file_path)
        if text:
            return self._minimal_cleaning(text), "PyPDF2Processor"
        
        # Fall back to pdfplumber (best for OCR'ed PDFs and complex layouts)
        text = self._extract_with_pdfplumber(file_path)
        if text:
            return self._apply_ocr_fixes(text), "PdfPlumberProcessor"
        
        # Final fallback to pdfminer.six (reliable general extraction)
        text = self._extract_with_pdfminer_fast(file_path)
        return self._minimal_cleaning(text), "PdfMinerProcessor"
    
    # Note: _quick_ocr_detection method removed - pdfplumber is now used for all PDFs
    
    def _extract_with_pdfplumber(self, file_path: str) -> Optional[str]:
        """
        Fast pdfplumber extraction.
        
        Note: pdfplumber is an optional dependency. If not installed,
        this method will gracefully fall back to other extraction methods.
        """
        try:
            import pdfplumber  # type: ignore # Optional dependency - see requirements.txt
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages[:50])  # Limit pages
        except ImportError as e:
            logger.debug(f"pdfplumber not available - skipping pdfplumber extraction: {e}")
            return None
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return None
    
    def _extract_with_pdfminer_fast(self, file_path: str) -> Optional[str]:
        """Fast pdfminer extraction."""
        try:
            from pdfminer.high_level import extract_text
            return extract_text(file_path, maxpages=100)  # Limit pages for speed
        except:
            return None
    
    def _extract_with_pypdf2_fast(self, file_path: str) -> Optional[str]:
        """Fast PyPDF2 extraction."""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                if reader.is_encrypted:
                    return None
                pages = min(len(reader.pages), 100)  # Limit pages
                return "\n".join(reader.pages[i].extract_text() for i in range(pages))
        except:
            return None
    
    def _apply_ocr_fixes(self, text: str) -> str:
        """Apply OCR fixes efficiently."""
        if not text:
            return ""
        
        for pattern_name, pattern in self._ocr_fixes.items():
            if pattern_name == 'us_reports':
                text = pattern.sub(r'\1 U.S. \2', text)
            elif pattern_name == 'supreme_court':
                text = pattern.sub(r'\1 S.Ct. \2', text)
            elif pattern_name == 'lawyers_edition':
                text = pattern.sub(r'\1 L.Ed. \2', text)
            elif pattern_name == 'federal':
                text = pattern.sub(r'\1 F.\2 \3', text)
        
        return self._whitespace.sub(' ', text).strip()
    
    def _minimal_cleaning(self, text: str) -> str:
        """Minimal cleaning for maximum speed."""
        return self._whitespace.sub(' ', text).strip() if text else ""


# Integration with your existing system
class DockerOptimizedProcessor:
    """
    Drop-in replacement for your UnifiedDocumentProcessor.
    Optimized for Docker + Redis deployment.
    """
    
    def __init__(self, redis_url: str = None):
        redis_url = redis_url or os.getenv('REDIS_URL', 'redis://casestrainer-redis-prod:6379/0')
        self.system = RedisDistributedPDFSystem(redis_url=redis_url)
    
    async def extract_text_from_file(self, file_path: str) -> str:
        """Async version of text extraction."""
        result = await self.system.extract_text_distributed(file_path)
        return result.text
    
    def extract_text_from_file_sync(self, file_path: str) -> str:
        """Synchronous wrapper for compatibility."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.extract_text_from_file(file_path))
        finally:
            loop.close()
    
    async def process_document(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Full document processing with distributed citation extraction."""
        start_time = time.time()
        
        # Extract text
        extraction_result = await self.system.extract_text_distributed(file_path)
        text = extraction_result.text
        
        if text.startswith('Error:'):
            return {
                'success': False,
                'error': text,
                'processing_time': time.time() - start_time
            }
        
        # Process citations using existing citation service
        from src.api.services.citation_service import CitationService
        citation_service = CitationService()
        
        # Use existing citation processing
        citation_result = citation_service.process_citations_from_text(text)
        
        return {
            'success': True,
            'text_length': len(text),
            'citations': citation_result.get('citations', []),
            'statistics': {
                'total_citations': len(citation_result.get('citations', [])),
                'processor_used': extraction_result.processor_used,
                'cache_hit': extraction_result.cache_hit
            },
            'processing_time': time.time() - start_time
        }


# Worker functions (these run in Redis workers)
def extract_pdf_pages(file_path: str, start_page: int, end_page: int, file_hash: str) -> str:
    """
    Worker function to extract specific pages from PDF.
    This runs in Redis workers.
    """
    try:
        from pdfminer.high_level import extract_text
        
        # Extract specific page range
        text = extract_text(
            file_path,
            page_numbers=list(range(start_page, end_page))
        )
        
        return text or ""
        
    except Exception as e:
        logger.error(f"Page extraction failed: {e}")
        return ""

def extract_pdf_optimized(file_path: str, file_hash: str) -> Dict[str, str]:
    """
    Worker function for optimized PDF extraction.
    This runs in Redis workers.
    """
    try:
        system = RedisDistributedPDFSystem()
        text, processor = system._smart_pdf_extraction_strategy(file_path)
        
        return {
            'text': text,
            'processor': processor,
            'file_hash': file_hash
        }
        
    except Exception as e:
        logger.error(f"Worker extraction failed: {e}")
        return {
            'text': f"Error: {str(e)}",
            'processor': 'ErrorProcessor',
            'file_hash': file_hash
        } 