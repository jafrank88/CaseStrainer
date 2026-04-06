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
import pickle
from dataclasses import dataclass
import sys

logging.warning(f"[DEBUG] sys.executable: {sys.executable}")
logging.warning(f"[DEBUG] sys.path: {sys.path}")

try:
    import redis
    from rq import Queue

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

    def __init__(
        self,
        redis_url: Optional[str] = None,
        cache_ttl: int = 3600,  # 1 hour cache
        max_workers: int = 4,
        chunk_size: int = 50000,
    ):
        from src.config import REDIS_URL
        redis_url = redis_url or REDIS_URL
        self.cache_ttl = cache_ttl
        self.max_workers = max_workers
        self.chunk_size = chunk_size

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.queue = Queue("casestrainer", connection=self.redis_client)
                self.redis_available = True

                self.redis_client.ping()
                logger.info("Redis connection established")

            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_available = False
        else:
            self.redis_available = False

        self._compile_patterns()

        self.worker_id = os.getenv("WORKER_ID", f"worker_{os.getpid()}")

    def _compile_patterns(self):
        """Pre-compile all regex patterns for maximum speed."""
        self._ocr_fixes = {
            "us_reports": re.compile(r"(\d+)\s*[Uu0o]\s*[.,]?\s*[Ss5]\s*[.,]?\s*(\d+)", re.IGNORECASE),
            "supreme_court": re.compile(r"(\d+)\s*[Ss5]\s*[.,]?\s*[CcGg][Tt7]\s*[.,]?\s*(\d+)", re.IGNORECASE),
            "lawyers_edition": re.compile(r"(\d+)\s*[Ll1I]\s*[.,]?\s*[Ee3]\s*[dD]\s*[.,]?\s*(\d+)", re.IGNORECASE),
            "federal": re.compile(r"(\d+)\s*[Ff]\s*[.,]?\s*(2[dD]|3[dD]|4th)?\s*(\d+)", re.IGNORECASE),
        }

        self._whitespace = re.compile(r"\s+")
        self._page_numbers = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)

    def _get_file_hash(self, file_path: str) -> str:
        """Generate file hash for caching."""
        try:
            stat = os.stat(file_path)
            hash_input = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
            return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        except Exception:
            return hashlib.sha256(file_path.encode("utf-8")).hexdigest()

    def _cache_get(self, key: str) -> Optional[Any]:
        """Get item from Redis cache."""
        if not self.redis_available:
            return None

        try:
            cached = self.redis_client.get(key)
            if cached:
                if isinstance(cached, bytes):
                    try:
                        return pickle.loads(cached)  # type: ignore
                    except Exception:
                        return None
                else:
                    try:
                        data_bytes = cached.encode("utf-8") if isinstance(cached, str) else cached
                        return pickle.loads(data_bytes)  # type: ignore
                    except Exception:
                        return None
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

        cache_key = f"extracted_text:{file_hash}"
        cached_result = self._cache_get(cache_key)

        if cached_result:
            logger.info(f"Cache hit for {file_path}")
            cached_result.cache_hit = True
            return cached_result

        file_size = os.path.getsize(file_path)

        if file_size > 100 * 1024 * 1024:  # 100MB+
            result = await self._extract_large_file_distributed(file_path, file_hash)
        elif file_size > 10 * 1024 * 1024:  # 10MB+
            result = await self._extract_medium_file_worker(file_path, file_hash)
        else:
            result = await self._extract_small_file_local(file_path, file_hash)

        result.processing_time = time.time() - start_time
        result.worker_id = self.worker_id

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
            return await self._extract_small_file_local(file_path, file_hash)

        try:
            from pdfminer.pdfpage import PDFPage

            with open(file_path, "rb") as file:
                pages = list(PDFPage.get_pages(file))
                total_pages = len(pages)

            pages_per_chunk = max(1, total_pages // self.max_workers)
            chunk_jobs = []

            for i in range(0, total_pages, pages_per_chunk):
                end_page = min(i + pages_per_chunk, total_pages)
                job = self.queue.enqueue(
                    "extract_pdf_pages", file_path, i, end_page, file_hash, timeout=300  # 5 minute timeout per chunk
                )
                chunk_jobs.append(job)

            chunk_results = []
            for job in chunk_jobs:
                try:
                    result = job.result(timeout=600)  # 10 minute total timeout
                    chunk_results.append(result)
                except Exception as e:
                    logger.error(f"Chunk job failed: {e}")
                    chunk_results.append("")

            combined_text = "\n".join(chunk_results)

            return ProcessingResult(
                text=combined_text,
                processor_used="DistributedWorkerProcessor",
                processing_time=0.0,  # Will be set by caller
                file_hash=file_hash,
            )

        except Exception as e:
            logger.error(f"Distributed processing failed: {e}")
            return await self._extract_small_file_local(file_path, file_hash)

    async def _extract_medium_file_worker(self, file_path: str, file_hash: str) -> ProcessingResult:
        """
        Process medium files using worker queue.
        """
        logger.info(f"Processing medium file with worker queue: {file_path}")

        if not self.redis_available:
            return await self._extract_small_file_local(file_path, file_hash)

        try:
            job = self.queue.enqueue("extract_pdf_optimized", file_path, file_hash, timeout=300)  # 5 minute timeout

            result = job.result(timeout=600)  # 10 minute total timeout

            return ProcessingResult(
                text=result.get("text", ""),
                processor_used=result.get("processor", "WorkerQueueProcessor"),
                processing_time=0.0,  # Will be set by caller
                file_hash=file_hash,
            )

        except Exception as e:
            logger.error(f"Worker queue processing failed: {e}")
            return await self._extract_small_file_local(file_path, file_hash)

    async def _extract_small_file_local(self, file_path: str, file_hash: str) -> ProcessingResult:
        """
        Process small files locally for maximum speed.
        """
        logger.info(f"Processing small file locally: {file_path}")

        text, processor = self._smart_pdf_extraction_strategy(file_path)

        return ProcessingResult(
            text=text or "", processor_used=processor, processing_time=0.0, file_hash=file_hash  # Will be set by caller
        )

    def _smart_pdf_extraction_strategy(self, file_path: str) -> Tuple[str, str]:
        """
        Smart file extraction strategy using the new optimized PDF processor.
        Handles both PDF and text files appropriately.
        """
        file_ext = file_path.lower().split(".")[-1] if "." in file_path else ""

        if file_ext in ["txt", "text", "md", "rtf", "html", "htm", "xhtml", "xml"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                return text, "TextFileProcessor"
            except UnicodeDecodeError:
                try:
                    with open(file_path, "r", encoding="latin-1") as f:
                        text = f.read()
                    return text, "TextFileProcessor"
                except Exception as e:
                    logger.warning(f"Text file reading failed: {e}")
                    return "", "TextFileProcessor"
            except Exception as e:
                logger.warning(f"Text file reading failed: {e}")
                return "", "TextFileProcessor"

        try:
            from src.optimized_pdf_processor import extract_pdf_optimized_v2

            result = extract_pdf_optimized_v2(file_path)

            if result.get("error"):
                logger.warning(f"Optimized PDF extraction failed: {result['error']}")
                text = self._extract_with_pdfplumber(file_path)
                if text:
                    return self._apply_ocr_fixes(text), "PdfPlumberProcessor"

                text = self._extract_with_pdfminer_fast(file_path)
                return self._minimal_cleaning(text or ""), "PdfMinerProcessor"

            text = result.get("text", "")
            processor = result.get("processor", "unknown")
            return str(text), f"OptimizedProcessor({processor})"

        except ImportError:
            text = self._extract_with_pdfplumber(file_path)
            if text:
                return self._apply_ocr_fixes(text), "PdfPlumberProcessor"

            text = self._extract_with_pdfminer_fast(file_path)
            return self._minimal_cleaning(text or ""), "PdfMinerProcessor"
        except Exception as e:
            logger.warning(f"Optimized PDF extraction failed: {e}")
            text = self._extract_with_pdfplumber(file_path)
            if text:
                return self._apply_ocr_fixes(text), "PdfPlumberProcessor"

            text = self._extract_with_pdfminer_fast(file_path)
            return self._minimal_cleaning(text or ""), "PdfMinerProcessor"

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
        except ImportError:
            return None
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return None

    def _extract_with_pdfminer_fast(self, file_path: str) -> Optional[str]:
        """Fast pdfminer extraction."""
        try:
            from pdfminer.high_level import extract_text

            return extract_text(file_path, maxpages=100)  # Limit pages for speed
        except Exception:
            return None

    def _extract_with_pypdf2_fast(self, file_path: str) -> Optional[str]:
        """Fast PyPDF2 extraction."""
        try:
            import PyPDF2

            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                if reader.is_encrypted:
                    return None
                pages = min(len(reader.pages), 100)  # Limit pages
                return "\n".join(reader.pages[i].extract_text() for i in range(pages))
        except Exception:
            return None

    def _apply_ocr_fixes(self, text: str) -> str:
        """Apply OCR fixes efficiently."""
        if not text:
            return ""

        for pattern_name, pattern in self._ocr_fixes.items():
            if pattern_name == "us_reports":
                text = pattern.sub(r"\1 U.S. \2", text)
            elif pattern_name == "supreme_court":
                text = pattern.sub(r"\1 S.Ct. \2", text)
            elif pattern_name == "lawyers_edition":
                text = pattern.sub(r"\1 L.Ed. \2", text)
            elif pattern_name == "federal":
                text = pattern.sub(r"\1 F.\2 \3", text)

        return self._whitespace.sub(" ", text).strip()

    def _minimal_cleaning(self, text: str) -> str:
        """Minimal cleaning for maximum speed."""
        return self._whitespace.sub(" ", text).strip() if text else ""


class DockerOptimizedProcessor:
    """
    Drop-in replacement for your UnifiedDocumentProcessor.
    Optimized for Docker + Redis deployment.
    """

    def __init__(self, redis_url: Optional[str] = None):
        from src.config import REDIS_URL
        redis_url = redis_url or REDIS_URL
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
        import logging

        logging.info(f"[DEBUG] ENTERED process_document for file_path={file_path}")
        start_time = time.time()

        options = kwargs.get("options", {})
        enable_verification = options.get("enable_verification", True)  # Default to True for backward compatibility

        logging.info(f"[DEBUG] About to call extract_text_distributed for file_path={file_path}")
        extraction_result = await self.system.extract_text_distributed(file_path)
        logging.info(
            f"[DEBUG] Returned from extract_text_distributed for file_path={file_path}, processor_used={getattr(extraction_result, 'processor_used', None)}"
        )
        text = extraction_result.text
        if text.startswith("Error:"):
            logging.error(f"[DEBUG] Extraction error for file_path={file_path}: {text}")
            return {"success": False, "error": text, "processing_time": time.time() - start_time}
        logging.info(f"[DEBUG] About to import and call CitationService for file_path={file_path}")
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.models import ProcessingConfig

        logging.info(
            f"[DEBUG] Creating citation processor with verification={'enabled' if enable_verification else 'disabled'} for async processing"
        )
        config = ProcessingConfig(
            enable_verification=enable_verification, debug_mode=False  # Disable debug mode to get real citation data
        )

        try:
            processor = UnifiedCitationProcessorV2(config)

            citation_result = await processor.process_document_citations(text)

            # Apply deduplication to citations
            citations = citation_result.get("citations", [])
            citations = self._deduplicate_citations(citations, file_path)

            result = {
                "status": "completed",
                "text_length": len(text),
                "citations": citations,
                "clusters": citation_result.get("clusters", []),
                "statistics": {
                    "total_citations": len(citation_result.get("citations", [])),
                    "processor_used": extraction_result.processor_used,
                    "cache_hit": extraction_result.cache_hit,
                },
                "processing_time": time.time() - start_time,
            }

            logging.info(
                f"[DEBUG] Successfully processed citations for file_path={file_path}, "
                f"citations_count={len(citation_result.get('citations', []))}"
            )

            try:
                import json

                json.dumps(result)
                logging.info(f"[DEBUG] Result is JSON serializable")
            except Exception as e:
                logging.error(f"[DEBUG] Result is NOT JSON serializable: {e}")

            return result

        except Exception as e:
            error_msg = f"Error processing citations: {str(e)}"
            logging.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg, "processing_time": time.time() - start_time}

    def _deduplicate_citations(self, citations: List[Dict[str, Any]], file_path: str) -> List[Dict[str, Any]]:
        """Apply deduplication to citations list."""
        if not citations:
            return citations

        try:
            from src.citation_deduplication import deduplicate_citations
            import logging

            original_count = len(citations)
            deduplicated = deduplicate_citations(citations, debug=True)

            if len(deduplicated) < original_count:
                logging.info(
                    f"[DockerOptimizedProcessor] Deduplication for {file_path}: {original_count} -> {len(deduplicated)} citations "
                    f"({original_count - len(deduplicated)} duplicates removed)"
                )

            return deduplicated

        except Exception as e:
            import logging

            logging.warning(f"[DockerOptimizedProcessor] Deduplication failed for {file_path}: {e}")
            return citations  # Return original citations if deduplication fails


def extract_pdf_pages(file_path: str, start_page: int, end_page: int, file_hash: str) -> str:
    """
    Worker function to extract specific pages from PDF.
    This runs in Redis workers.
    """
    try:
        from pdfminer.high_level import extract_text

        text = extract_text(file_path, page_numbers=list(range(start_page, end_page)))

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

        return {"text": text, "processor": processor, "file_hash": file_hash}

    except Exception as e:
        logger.error(f"Worker extraction failed: {e}")
        return {"text": f"Error: {str(e)}", "processor": "ErrorProcessor", "file_hash": file_hash}
