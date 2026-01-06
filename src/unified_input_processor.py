"""
Unified Input Processor
Consolidates all input types (file, URL, text) into a single text processing pipeline.
"""

import os

import asyncio
import time
import logging
import tempfile
import threading
from typing import Dict, Any, Optional, Union
from urllib.parse import urlparse
from werkzeug.datastructures import FileStorage

from src.robust_pdf_extractor import extract_text_from_pdf_smart
from src.progress_manager import fetch_url_content, SSEProgressManager, ProgressTracker, estimate_citations_cheap
from src.api.services.citation_service import CitationService

logger = logging.getLogger(__name__)

# Global progress manager instance
_progress_manager = None


def get_progress_manager():
    """Get or create the global progress manager instance."""
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = SSEProgressManager()
    return _progress_manager


class UnifiedInputProcessor:
    """
    Unified processor that converts any input type to text and processes citations.
    Eliminates redundancy between file, URL, and text handlers.
    """

    def __init__(self, verbose: bool = False):
        self.citation_service = CitationService()
        self.progress_manager = get_progress_manager()
        self.verbose = verbose
        self.supported_file_extensions = {"pdf", "txt", "doc", "docx", "rtf", "md", "html", "htm", "xml", "xhtml"}

    def process_any_input(
        self,
        input_data: Any,
        input_type: str,
        request_id: str,
        source_name: Optional[str] = None,
        force_mode: Optional[str] = None,
        enable_verification: bool = True,
    ) -> Dict[str, Any]:
        """
        Universal input processor - converts any input to text, then processes citations.

        Args:
            input_data: The input data (file, URL string, or text string)
            input_type: Type of input ('file', 'url', 'text')
            request_id: Unique request identifier
            source_name: Optional source name for metadata
            force_mode: Optional user override for sync/async processing ('sync', 'async', or None)
            enable_verification: Whether to enable citation verification (default: True)

        Returns:
            Dictionary with citation processing results
        """
        print(f"[DEBUG] process_any_input CALLED with input_type={input_type}, request_id={request_id}")
        logger.error(f"[Unified Processor {request_id}] [DEBUG] process_any_input CALLED!")
        logger.error(f"[Unified Processor {request_id}] Processing {input_type} input")
        logger.error(f"[Unified Processor {request_id}] Input data type: {type(input_data)}")
        logger.error(
            f"[Unified Processor {request_id}] Input data length: {len(input_data) if isinstance(input_data, str) else 'N/A'}"
        )
        logger.error(f"[Unified Processor {request_id}] Source name: {source_name}, Force mode: {force_mode}")

        try:
            logger.error(f"[Unified Processor {request_id}] [INFO] Calling _extract_text_from_input...")
            text_result = self._extract_text_from_input(input_data, input_type, request_id)
            logger.error(
                f"[Unified Processor {request_id}] [SUCCESS] _extract_text_from_input returned: success={text_result.get('success')}"
            )

            if not text_result["success"]:
                return text_result

            text = text_result["text"]
            metadata = text_result.get("metadata", {})

            logger.error(
                f"[Unified Processor {request_id}] [INFO] enable_verification={enable_verification} passed through"
            )
            logger.error(
                f"[Unified Processor {request_id}] [DEBUG] About to call _process_citations_unified with verification flag"
            )

            return self._process_citations_unified(
                text=text,
                request_id=request_id,
                source_name=source_name or input_type,
                force_mode=force_mode,  # Pass force_mode through
                enable_verification=enable_verification,  # Pass verification flag through
                input_metadata=metadata,
            )

        except Exception as e:
            logger.error(f"[Unified Processor {request_id}] Error processing {input_type}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error processing {input_type} input: {str(e)}",
                "citations": [],
                "clusters": [],
                "request_id": request_id,
                "metadata": {"input_type": input_type, "error_type": "processing_error"},
            }

    def _extract_text_from_input(self, input_data: Any, input_type: str, request_id: str) -> Dict[str, Any]:
        """
        Extract text from any input type.

        Returns:
            Dictionary with success status, text, and metadata
        """
        if input_type == "text":
            # Extract text from dict if needed
            if isinstance(input_data, dict):
                text = input_data.get("text", "")
            else:
                text = input_data
            return self._extract_from_text(text, request_id)
        elif input_type == "url":
            return self._extract_from_url(input_data, request_id)
        elif input_type == "file":
            return self._extract_from_file(input_data, request_id)
        else:
            return {
                "success": False,
                "error": f"Unsupported input type: {input_type}",
                "text": "",
                "metadata": {"input_type": input_type},
            }

    def _extract_from_text(self, text: str, request_id: str) -> Dict[str, Any]:
        """Extract text from direct text input (passthrough)."""
        logger.info(f"[Unified Processor {request_id}] Processing direct text input ({len(text)} chars)")

        if not text or len(text.strip()) < 10:
            return {
                "success": False,
                "error": "Text input is empty or too short for analysis",
                "text": "",
                "metadata": {"input_type": "text", "text_length": len(text)},
            }

        return {
            "success": True,
            "text": text,
            "metadata": {"input_type": "text", "text_length": len(text), "source": "direct_text"},
        }

    def _extract_from_url(self, url: str, request_id: str) -> Dict[str, Any]:
        """Extract text from URL by fetching and processing content."""
        logger.info(f"[Unified Processor {request_id}] Extracting text from URL: {url}")

        try:
            logger.info(f"[Unified Processor {request_id}] Validating URL...")
            if not self._validate_url(url):
                logger.warning(f"[Unified Processor {request_id}] URL validation failed: {url}")
                return {
                    "success": False,
                    "error": "Invalid or unsafe URL provided",
                    "text": "",
                    "metadata": {"input_type": "url", "url": url, "error": "validation_failed"},
                }

            logger.info(f"[Unified Processor {request_id}] URL validation passed, determining content type...")

            # Determine content-type via HEAD (fallback to suffix check)
            content_type = ""
            is_pdf = False
            try:
                import requests

                head = requests.head(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
                content_type = (head.headers.get("Content-Type") or "").lower()
                is_pdf = "application/pdf" in content_type
                logger.info(f"[Unified Processor {request_id}] HEAD Content-Type='{content_type}' → is_pdf={is_pdf}")
            except Exception as e:
                # Fallback to suffix if HEAD fails
                is_pdf = url.lower().endswith(".pdf")
                logger.warning(f"[Unified Processor {request_id}] HEAD failed ({e}); fallback is_pdf={is_pdf}")

            # Prefer content-type over suffix; only treat as PDF if HEAD agrees
            # If suffix is .pdf but HEAD says text/html, handle as HTML path

            # Special handling for PDFs: download bytes and extract via RobustPDFExtractor
            if is_pdf:
                logger.info(f"[Unified Processor {request_id}] Detected PDF URL - downloading for PDF extraction")
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36",
                        "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": "https://www.courts.wa.gov/",
                    }
                    # HEAD check for content-type and length
                    try:
                        import requests

                        head = requests.head(url, headers=headers, allow_redirects=True, timeout=20)
                        ct = head.headers.get("Content-Type", "")
                        cl = head.headers.get("Content-Length", "")
                        logger.info(
                            f"[Unified Processor {request_id}] PDF HEAD: Content-Type={ct}, Content-Length={cl}"
                        )
                    except Exception:
                        pass
                    tmp_path = None
                    try:
                        try:
                            import requests

                            # First attempt: non-streamed (some servers object to ranged/streamed)
                            # CRITICAL FIX: Follow redirects to handle HTTP→HTTPS redirects
                            resp = requests.get(url, headers=headers, timeout=60, stream=False, allow_redirects=True)
                            if resp.status_code != 200:
                                logger.warning(
                                    f"[Unified Processor {request_id}] PDF download failed: status={resp.status_code}"
                                )
                                raise Exception(f"HTTP {resp.status_code}")
                            data = resp.content
                            # If unexpectedly small, retry with stream=True
                            if not data or len(data) < 1024:
                                logger.warning(
                                    f"[Unified Processor {request_id}] PDF content small ({len(data) if data else 0} bytes) - retrying with stream"
                                )
                                resp = requests.get(url, headers=headers, timeout=60, stream=True, allow_redirects=True)
                                if resp.status_code != 200:
                                    raise Exception(f"HTTP {resp.status_code}")
                                chunks = []
                                for chunk in resp.iter_content(chunk_size=16384):
                                    if chunk:
                                        chunks.append(chunk)
                                data = b"".join(chunks)
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                                tmp_pdf.write(data)
                                tmp_path = tmp_pdf.name
                        except ImportError:
                            # Fallback to urllib if requests is unavailable
                            from urllib.request import Request, urlopen

                            req = Request(url, headers=headers)
                            with urlopen(req, timeout=60) as r, tempfile.NamedTemporaryFile(
                                delete=False, suffix=".pdf"
                            ) as tmp_pdf:
                                while True:
                                    chunk = r.read(16384)
                                    if not chunk:
                                        break
                                    tmp_pdf.write(chunk)
                                tmp_path = tmp_pdf.name

                        from src.robust_pdf_extractor import RobustPDFExtractor

                        extractor = RobustPDFExtractor()
                        result = extractor.extract_text(tmp_path)
                        text = result[0] if isinstance(result, tuple) else result
                        # Fallback to alternate smart extractor if primary returns too little
                        if not text or len(text.strip()) < 50:
                            try:
                                alt_text = extract_text_from_pdf_smart(tmp_path)
                                if alt_text and len(alt_text.strip()) > len(text or ""):
                                    text = alt_text
                            except Exception:
                                pass
                        # Optional third attempt: try OCR if available and content still too short
                        # Leave OCR as an optional internal path only if supported by RobustPDFExtractor in deployment
                        if not text or len(text.strip()) < 50:
                            return {
                                "success": False,
                                "error": "URL returned empty or insufficient content for analysis",
                                "text": "",
                                "metadata": {
                                    "input_type": "url",
                                    "url": url,
                                    "content_length": 0,
                                    "error": "insufficient_content_pdf",
                                },
                            }
                        logger.info(f"[Unified Processor {request_id}] Extracted {len(text)} characters from PDF URL")

                        # If a local comparison file exists, log comparative length for diagnostics
                        try:
                            local_test_path = os.path.join(
                                os.path.dirname(os.path.dirname(__file__)), "D2 60382-9-II Published Opinion.pdf"
                            )
                            if os.path.exists(local_test_path):
                                try:
                                    local_alt = extract_text_from_pdf_smart(local_test_path)
                                    logger.info(
                                        f"[Unified Processor {request_id}] Local test PDF extracted: {len(local_alt or '')} chars (for comparison)"
                                    )
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        return {
                            "success": True,
                            "text": text,
                            "metadata": {
                                "input_type": "url",
                                "url": url,
                                "url_domain": urlparse(url).netloc,
                                "content_length": len(text),
                                "source": "url_fetch_pdf",
                            },
                        }
                    finally:
                        if tmp_path:
                            try:
                                os.unlink(tmp_path)
                            except Exception:
                                pass
                except Exception as pdf_err:
                    logger.error(f"[Unified Processor {request_id}] PDF fetch/extract failed: {pdf_err}")
                    # Fall through to generic fetch as a fallback

            # Generic fetch path (for HTML/text URLs)
            content = fetch_url_content(url)
            logger.info(f"[Unified Processor {request_id}] Content fetched, length: {len(content) if content else 0}")

            if not content or len(content.strip()) < 10:
                logger.warning(
                    f"[Unified Processor {request_id}] Insufficient content from URL: {len(content) if content else 0} chars"
                )
                return {
                    "success": False,
                    "error": "URL returned empty or insufficient content for analysis",
                    "text": "",
                    "metadata": {
                        "input_type": "url",
                        "url": url,
                        "content_length": len(content),
                        "error": "insufficient_content",
                    },
                }

            logger.info(f"[Unified Processor {request_id}] Successfully extracted {len(content)} characters from URL")
            return {
                "success": True,
                "text": content,
                "metadata": {
                    "input_type": "url",
                    "url": url,
                    "url_domain": urlparse(url).netloc,
                    "content_length": len(content),
                    "source": "url_fetch",
                },
            }

        except Exception as e:
            logger.error(f"[Unified Processor {request_id}] Error fetching URL {url}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to fetch content from URL: {str(e)}",
                "text": "",
                "metadata": {"input_type": "url", "url": url, "error": "fetch_failed", "error_details": str(e)},
            }

    def _extract_from_file(self, input_data: Union[FileStorage, Dict], request_id: str) -> Dict[str, Any]:
        """Extract text from uploaded file."""
        if isinstance(input_data, dict):
            file = input_data.get("file")
            filename = input_data.get("filename", "unknown")
        else:
            file = input_data
            filename = getattr(file, "filename", "unknown") if file else "unknown"

        logger.info(f"[Unified Processor {request_id}] Extracting text from file: {filename}")

        try:
            if not file or not filename:
                return {
                    "success": False,
                    "error": "No file provided or empty filename",
                    "text": "",
                    "metadata": {"input_type": "file", "error": "no_file"},
                }

            file_ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""

            if file_ext not in self.supported_file_extensions:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_ext}",
                    "text": "",
                    "metadata": {
                        "input_type": "file",
                        "filename": filename,
                        "file_extension": file_ext,
                        "error": "unsupported_type",
                    },
                }

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
                file.save(temp_file.name)
                temp_file_path = temp_file.name

            try:
                # Use UnifiedTextExtractor for consistent text extraction across all inputs
                from src.unified_text_extractor import extract_text_from_file_unified

                text, method = extract_text_from_file_unified(temp_file_path, verbose=True)

                logger.info(f"[Unified Processor {request_id}] Extracted {len(text):,} chars using {method}")

                if not text or len(text.strip()) < 10:
                    return {
                        "success": False,
                        "error": "Extracted text is empty or too short",
                        "text": "",
                        "metadata": {
                            "input_type": "file",
                            "filename": filename,
                            "file_extension": file_ext,
                            "extraction_method": method,
                            "text_length": len(text),
                            "error": "empty_extraction",
                        },
                    }

                return {
                    "success": True,
                    "text": text,
                    "metadata": {
                        "input_type": "file",
                        "filename": filename,
                        "file_extension": file_ext,
                        "extraction_method": method,
                        "text_length": len(text),
                        "source": "file_upload",
                    },
                }

            finally:
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass

        except Exception as e:
            logger.error(f"[Unified Processor {request_id}] Error processing file {filename}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to process file: {str(e)}",
                "text": "",
                "metadata": {
                    "input_type": "file",
                    "filename": filename,
                    "error": "processing_failed",
                    "error_details": str(e),
                },
            }

    def _process_citations_unified(
        self,
        text: str,
        request_id: str,
        source_name: str,
        input_metadata: Dict[str, Any],
        force_mode: Optional[str] = None,
        enable_verification: bool = True,
    ) -> Dict[str, Any]:
        """
        Process citations using the unified pipeline (same for all input types).

        Args:
            force_mode: Optional user override for sync/async processing
            enable_verification: Whether to enable citation verification
        """
        print(f"[DEBUG] _process_citations_unified CALLED with {len(text)} chars, request_id={request_id}")
        logger.error(f"[Unified Processor {request_id}] [DEBUG] _process_citations_unified CALLED!")
        logger.error(f"[Unified Processor {request_id}] Processing citations from {source_name}")
        logger.error(f"[Unified Processor {request_id}] Text length: {len(text)} characters")
        logger.error(f"[Unified Processor {request_id}] Text preview: {text[:200]}...")
        logger.error(f"[Unified Processor {request_id}] Input metadata: {input_metadata}")
        if force_mode:
            logger.error(f"[Unified Processor {request_id}] [INFO] force_mode='{force_mode}' passed through")

        logger.error(
            f"[Unified Processor {request_id}] [INFO] enable_verification={enable_verification} passed through"
        )

        try:
            input_data = {"type": "text", "text": text}
            logger.error(f"[Unified Processor {request_id}] 🔍 DEBUG: Checking if should process immediately...")
            logger.error(f"[Unified Processor {request_id}] 🔍 DEBUG: force_mode parameter = '{force_mode}'")
            logger.error(f"[Unified Processor {request_id}] 🔍 DEBUG: Text length = {len(text)} chars")

            # Pass force_mode to honor user override
            should_process_immediately = self.citation_service.should_process_immediately(
                input_data, force_mode=force_mode
            )
            logger.error(
                f"[Unified Processor {request_id}] 🔍 DEBUG: should_process_immediately = {should_process_immediately}"
            )
            logger.error(
                f"[Unified Processor {request_id}] 🔍 DEBUG: force_mode was '{force_mode}', result is {should_process_immediately}"
            )

            if should_process_immediately:
                logger.warning(
                    f"[Unified Processor {request_id}] *** SYNC PATH: Processing immediately using UNIFIED PIPELINE"
                )
                try:
                    # Create progress callback that updates the progress manager
                    def progress_callback(progress: int, step: str, message: str):
                        try:
                            self.progress_manager.update_progress(request_id, progress, step, message)
                            logger.debug(f"[Progress {request_id}] {progress}% - {step}: {message}")
                        except Exception as e:
                            logger.warning(f"[Progress {request_id}] Failed to update: {e}")

                    # Initialize progress tracking - use existing tracker if available
                    if request_id not in self.progress_manager.active_tasks:
                        tracker = ProgressTracker(request_id, total_steps=100)
                        self.progress_manager.active_tasks[request_id] = tracker
                    else:
                        tracker = self.progress_manager.active_tasks[request_id]

                    # Update progress
                    progress_callback(10, "Extract", "Using unified processing pipeline with verification")

                    # Start centralized ETA heartbeat towards ~85% using cheap citation estimate
                    try:
                        qn = estimate_citations_cheap(input_data.get("text", "") or "")
                        text_size = len(input_data.get("text", "") or "")
                        # Enhanced ETA calculation for sync processing
                        base_time = 5.0  # Minimum 5 seconds
                        citation_time = min(60.0, 1.5 * qn)  # 1.5 seconds per citation, max 1 minute
                        size_time = min(120.0, text_size / 20000)  # 0.5 seconds per 20KB, max 2 minutes
                        expected_seconds = max(base_time, base_time + citation_time + size_time)
                        # Cap at 3 minutes for sync processing
                        expected_seconds = min(expected_seconds, 180.0)
                        logger.error(f"[Unified Processor {request_id}] ETA: {expected_seconds:.1f}s (sync, citations: {qn}, size: {text_size//1024}KB)")
                        self.progress_manager.start_eta_heartbeat(
                            request_id,
                            start_pct=10,
                            cap_pct=85,
                            expected_seconds=expected_seconds,
                            message="Analyzing document...",
                            interval=0.8,
                        )
                    except Exception:
                        pass

                    logger.error(
                        f"[Unified Processor {request_id}] 🔧 DEBUG: About to call process_citations_unified with enable_verification={enable_verification}"
                    )
                    # Run unified pipeline (includes extraction, verification, and parallel propagation)
                    from src.unified_processing_pipeline import process_citations_unified

                    text = input_data.get("text", "")
                    logger.error(
                        f"[Unified Processor {request_id}] >>>>>>> ABOUT TO CALL process_citations_unified with enable_verification={enable_verification}"
                    )
                    pipeline_result = asyncio.run(
                        process_citations_unified(
                            text,
                            processing_mode="enhanced_sync",
                            enable_parallel_verification=enable_verification,
                            enable_verification=enable_verification,
                        )
                    )

                    # Prepare response
                    citations_list = pipeline_result.get("citations", [])
                    clusters = pipeline_result.get("clusters", [])

                    progress_callback(
                        100, "Complete", f"Unified pipeline: {len(citations_list)} citations, {len(clusters)} clusters"
                    )
                    # Cleanup completed task after a brief delay (but keep Redis data for polling)
                    try:

                        def _cleanup_done():
                            try:
                                time.sleep(3.0)
                                self.progress_manager.cleanup_task(request_id, keep_redis_data=True)
                            except Exception:
                                pass

                        threading.Thread(target=_cleanup_done, daemon=True).start()
                    except Exception:
                        pass

                    # Build metadata
                    response_metadata = {
                        **input_metadata,
                        "processing_mode": "immediate",
                        "source": source_name,
                        "processing_strategy": "unified_processing_pipeline",
                    }
                    # Pass through any notices from pipeline metadata
                    if pipeline_result.get("metadata", {}).get("verification_notice"):
                        response_metadata["verification_notice"] = pipeline_result["metadata"]["verification_notice"]

                    return {
                        "success": True,
                        "citations": citations_list,
                        "clusters": clusters,
                        "request_id": request_id,
                        "metadata": response_metadata,
                    }
                except Exception as e:
                    logger.error(
                        f"[Unified Processor {request_id}] Error in immediate processing via unified pipeline: {str(e)}",
                        exc_info=True,
                    )
                    should_process_immediately = False

            if not should_process_immediately:
                logger.error(
                    f"[Unified Processor {request_id}] 🚀 ASYNC PATH TRIGGERED - Queuing for async processing (large content)"
                )
                logger.error(f"[Unified Processor {request_id}] 📝 Text length: {len(text)} chars")
                logger.error(
                    f"[Unified Processor {request_id}] 📋 Source: {source_name}, Input type from metadata: {input_metadata.get('input_type')}"
                )

                try:
                    from rq import Queue
                    from redis import Redis

                    logger.error(f"[Unified Processor {request_id}] ✅ Imported RQ and Redis modules")

                    # CRITICAL FIX: Use string path, not imported function object
                    # RQ needs the module path as a string to properly serialize the job

                    # Try multiple Redis configurations for better connectivity
                    redis_configs = [
                        os.environ.get("REDIS_URL", "redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0"),
                        "redis://localhost:6379/0",  # Local Redis fallback
                        "redis://127.0.0.1:6379/0",  # Alternative local Redis
                    ]

                    logger.error(
                        f"[Unified Processor {request_id}] 🔍 Trying {len(redis_configs)} Redis configurations..."
                    )

                    redis_conn = None
                    for i, redis_url in enumerate(redis_configs, 1):
                        try:
                            logger.error(f"[Unified Processor {request_id}] 🔗 Attempt {i}: Connecting to {redis_url}")
                            redis_conn = Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
                            redis_conn.ping()  # Test connection
                            logger.error(f"[Unified Processor {request_id}] ✅ Connected to Redis: {redis_url}")
                            break
                        except Exception as e:
                            logger.error(
                                f"[Unified Processor {request_id}] ❌ Redis connection failed for {redis_url}: {e}"
                            )
                            continue

                    if not redis_conn:
                        logger.error(
                            f"[Unified Processor {request_id}] 🚨 CRITICAL: No Redis instance available after trying all configs"
                        )
                        raise Exception("No Redis instance available")

                    logger.error(f"[Unified Processor {request_id}] 🎯 Creating queue 'casestrainer'...")
                    queue = Queue("casestrainer", connection=redis_conn)
                    logger.error(f"[Unified Processor {request_id}] ✅ Queue created successfully")

                    logger.error(f"[Unified Processor {request_id}] 📤 About to enqueue job...")
                    logger.error(
                        f"[Unified Processor {request_id}]    Function: src.rq_worker.process_citation_task_direct"
                    )
                    logger.error(
                        f"[Unified Processor {request_id}]    Args: ({request_id}, 'text', {{text: {len(text)} chars}})"
                    )
                    logger.error(f"[Unified Processor {request_id}]    Job ID: {request_id}")

                    job = queue.enqueue(
                        "src.rq_worker.process_citation_task_direct",  # Use RQ worker that reports VM progress
                        args=(request_id, "text", {"text": text}),
                        job_id=request_id,  # Use request_id as the job ID
                        job_timeout=300,  # 5 minutes timeout
                        result_ttl=86400,
                        failure_ttl=86400,
                    )

                    logger.error(f"[Unified Processor {request_id}] ✅ Task enqueued successfully!")
                    logger.error(f"[Unified Processor {request_id}]    Job ID: {job.id}")
                    logger.error(f"[Unified Processor {request_id}]    Job status: {job.get_status()}")

                    # Heartbeat for async path: ETA-based progress while background job runs (centralized)
                    try:
                        tracker = ProgressTracker(request_id, total_steps=100)
                        self.progress_manager.active_tasks[request_id] = tracker
                        self.progress_manager.update_progress(
                            request_id, 10, "queued", "Queued for background processing"
                        )
                        # Estimate duration from cheap citation estimate and start ETA heartbeat up to ~60%
                        try:
                            qn = estimate_citations_cheap(text)
                            text_size = len(text)
                            # Enhanced ETA calculation for large documents
                            # Base time + citation factor + size factor
                            base_time = 10.0  # Minimum 10 seconds for any document
                            citation_time = min(120.0, 2.0 * qn)  # 2 seconds per citation, max 2 minutes
                            size_time = min(180.0, text_size / 10000)  # 1 second per 10KB, max 3 minutes
                            expected_seconds = max(base_time, base_time + citation_time + size_time)
                            # Cap at 5 minutes for very large documents
                            expected_seconds = min(expected_seconds, 300.0)
                            logger.error(f"[Unified Processor {request_id}] ETA: {expected_seconds:.1f}s (citations: {qn}, size: {text_size//1024}KB)")
                            self.progress_manager.start_eta_heartbeat(
                                request_id,
                                start_pct=10,
                                cap_pct=60,
                                expected_seconds=expected_seconds,
                                message="Processing in background...",
                                interval=1.0,
                            )
                        except Exception:
                            pass

                        def _async_heartbeat_and_watcher():
                            try:
                                hb = 12
                                # Lazy import to avoid heavy deps at import time
                                from src.verification_manager import VerificationManager

                                vm = VerificationManager()
                                while True:
                                    time.sleep(1.0)
                                    task = self.progress_manager.active_tasks.get(request_id)
                                    if not task:
                                        break
                                    status = getattr(task, "status", "")
                                    # Poll verification status; when done, complete and exit
                                    vstat = None
                                    try:
                                        vstat = vm.get_verification_status(request_id) or vm.get_verification_status(
                                            job.id
                                        )
                                    except Exception:
                                        vstat = None
                                    if isinstance(vstat, dict):
                                        pct = int(vstat.get("progress_percent", 0))
                                        msg = vstat.get("current_message", "Verifying...")
                                        if pct > hb:
                                            hb = pct
                                        if pct >= 100 or str(vstat.get("state", "")).lower() in (
                                            "completed",
                                            "complete",
                                            "done",
                                            "success",
                                        ):
                                            self.progress_manager.update_progress(
                                                request_id, 100, "completed", "Verification completed"
                                            )
                                            # Cleanup after a brief delay
                                            try:

                                                def _cleanup_async():
                                                    try:
                                                        time.sleep(3.0)
                                                        self.progress_manager.cleanup_task(request_id)
                                                    except Exception:
                                                        pass

                                                threading.Thread(target=_cleanup_async, daemon=True).start()
                                            except Exception:
                                                pass
                                            break
                                        # Reflect verification progress above heartbeat floor
                                        self.progress_manager.update_progress(
                                            request_id, max(hb, min(95, pct)), "processing", msg
                                        )
                                        continue
                                    # No verification yet; rely on central ETA heartbeat; do not double-update
                                    if status in ("completed", "failed"):
                                        break
                            except Exception:
                                pass

                        threading.Thread(target=_async_heartbeat_and_watcher, daemon=True).start()
                    except Exception:
                        pass

                    return {
                        "success": True,
                        "task_id": request_id,
                        "status": "processing",
                        "message": f"{source_name.title()} processing started",
                        "request_id": request_id,
                        "metadata": {
                            **input_metadata,
                            "processing_mode": "queued",
                            "source": source_name,
                            "job_id": job.id,
                        },
                    }
                except Exception as e:
                    logger.error(
                        f"[Unified Processor {request_id}] Error enqueueing async task: {str(e)}", exc_info=True
                    )

                    # Fallback to sync processing when Redis is unavailable
                    redis_error_indicators = [
                        "loading the dataset in memory",
                        "connection",
                        "getaddrinfo failed",
                        "redis",
                        "timeout",
                        "refused",
                    ]
                    should_fallback = any(indicator in str(e).lower() for indicator in redis_error_indicators)

                    if should_fallback:
                        logger.warning(
                            f"[Unified Processor {request_id}] Redis unavailable, falling back to CLEAN PIPELINE (87-93% accuracy)"
                        )

                        try:
                            # USE CLEAN PIPELINE for extraction (87-93% accuracy)
                            pass

                            # Create progress callback for fallback path
                            def progress_callback(progress: int, step: str, message: str):
                                """Update progress via the progress manager."""
                                try:
                                    self.progress_manager.update_progress(request_id, progress, step, message)
                                    logger.debug(f"[Progress {request_id}] {progress}% - {step}: {message}")
                                except Exception as e:
                                    logger.warning(f"[Progress {request_id}] Failed to update: {e}")

                            # Initialize progress tracking
                            tracker = ProgressTracker(request_id, total_steps=100)
                            self.progress_manager.active_tasks[request_id] = tracker

                            # Update progress
                            progress_callback(10, "Extract", "Using full pipeline with verification (Redis fallback)")

                            # CRITICAL FIX: Use FULL pipeline with clustering and verification
                            # instead of just extraction
                            from src.citation_extraction_endpoint import extract_citations_with_clustering

                            # Extract enable_verification flag from input_data
                            raw_enable = input_data.get("enable_verification", True)
                            enable_verification = (
                                (str(raw_enable).strip().lower() in ("1", "true", "yes"))
                                if isinstance(raw_enable, str)
                                else bool(raw_enable)
                            )
                            result = extract_citations_with_clustering(
                                text, enable_verification=enable_verification, progress_callback=progress_callback
                            )

                            # Check if any citations show CourtListener rate limit messages
                            courtlistener_rate_limited = False
                            if result.get("citations"):
                                for cit in result["citations"]:
                                    error_msg = cit.get("error", "") or cit.get("verification_error", "")
                                    if "heavy usage" in str(error_msg).lower() or "try again" in str(error_msg).lower():
                                        courtlistener_rate_limited = True
                                        break

                            # Add user notice if CourtListener is rate-limited
                            if courtlistener_rate_limited:
                                if "metadata" not in result:
                                    result["metadata"] = {}
                                result["metadata"]["verification_notice"] = (
                                    "Note: CourtListener is experiencing heavy usage. Citations have been verified using "
                                    "alternative sources (Justia, OpenJurist, Cornell LII). For complete verification with "
                                    "CourtListener, please try again in a few minutes."
                                )

                            # The result already has citations and clusters in the right format
                            citations = result.get("citations", [])
                            clusters = result.get("clusters", [])

                            progress_callback(
                                100, "Complete", f"Full pipeline: {len(citations)} citations, {len(clusters)} clusters"
                            )
                            logger.info(
                                f"[Sync Fallback] Extracted {len(citations)} citations, clustered into {len(clusters)} groups"
                            )

                            # CRITICAL: Mark progress as complete to stop frontend polling
                            if request_id in self.progress_manager.active_tasks:
                                tracker = self.progress_manager.active_tasks[request_id]
                                tracker.status = "completed"
                                logger.info(f"[Sync Fallback] Marked progress tracker as complete for {request_id}")

                            # Convert to CitationResult objects for consistency
                            from src.models import CitationResult

                            citation_objects = []
                            for cit_dict in citations:
                                citation_objects.append(
                                    CitationResult(
                                        citation=cit_dict["citation"],
                                        extracted_case_name=cit_dict.get("extracted_case_name"),
                                        extracted_date=cit_dict.get("extracted_date"),
                                        method=cit_dict.get("method", "clean_pipeline_v1"),
                                        confidence=cit_dict.get("confidence", 0.9),
                                        verified=cit_dict.get("verified", False),
                                        canonical_name=cit_dict.get("canonical_name"),
                                        canonical_date=cit_dict.get("canonical_date"),
                                        canonical_url=cit_dict.get("canonical_url"),
                                        metadata=cit_dict.get("metadata", {}),  # Include verification metadata
                                    )
                                )

                            result = {"citations": citation_objects, "clusters": clusters}

                            logger.info(
                                f"[Unified Processor {request_id}] Sync fallback processing completed successfully"
                            )

                            # Convert CitationResult objects to dictionaries for API response
                            citations = result.get("citations", [])
                            converted_citations = []
                            for citation in citations:
                                if hasattr(citation, "to_dict"):
                                    # Use the fixed to_dict method that doesn't include case_name
                                    citation_dict = citation.to_dict()

                                    cluster_case_name = citation_dict.get("cluster_case_name")
                                    extracted_case_name = citation_dict.get("extracted_case_name")
                                    canonical_name = citation_dict.get("canonical_name")
                                    logger.debug(
                                        f"FALLBACK_DATA_SEPARATION: cluster='{cluster_case_name}', extracted='{extracted_case_name}', canonical='{canonical_name}'"
                                    )

                                    converted_citations.append(citation_dict)
                                else:
                                    # Already a dictionary - maintain data separation
                                    citation_dict = citation.copy()

                                    # REMOVED: case_name field eliminated to prevent contamination
                                    # Frontend will use extracted_case_name and canonical_name directly

                                    cluster_case_name = citation_dict.get("cluster_case_name")
                                    extracted_case_name = citation_dict.get("extracted_case_name")
                                    canonical_name = citation_dict.get("canonical_name")
                                    logger.debug(
                                        f"FALLBACK_DICT_DATA_SEPARATION: cluster='{cluster_case_name}', extracted='{extracted_case_name}', canonical='{canonical_name}'"
                                    )

                                    converted_citations.append(citation_dict)

                            # Build metadata including any verification notices
                            response_metadata = {
                                **input_metadata,
                                "processing_mode": "sync_fallback",
                                "source": source_name,
                                "fallback_reason": "redis_unavailable",
                            }

                            # Include verification notice if CourtListener was rate-limited
                            if result.get("metadata", {}).get("verification_notice"):
                                response_metadata["verification_notice"] = result["metadata"]["verification_notice"]

                            return {
                                "success": True,
                                "citations": converted_citations,
                                "clusters": result.get("clusters", []),
                                "request_id": request_id,
                                "task_id": request_id,  # Frontend expects task_id for progress polling
                                "metadata": response_metadata,
                            }
                        except Exception as fallback_error:
                            logger.error(
                                f"[Unified Processor {request_id}] Sync fallback also failed: {str(fallback_error)}",
                                exc_info=True,
                            )

                    return {
                        "success": False,
                        "error": f"Failed to enqueue processing task: {str(e)}",
                        "citations": [],
                        "clusters": [],
                        "request_id": request_id,
                        "metadata": {
                            **input_metadata,
                            "processing_mode": "enqueue_failed",
                            "source": source_name,
                            "error_details": str(e),
                        },
                    }

        except Exception as e:
            logger.error(f"[Unified Processor {request_id}] Error in citation processing: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error processing citations: {str(e)}",
                "citations": [],
                "clusters": [],
                "request_id": request_id,
                "metadata": {**input_metadata, "error": "citation_processing_failed", "error_details": str(e)},
            }

        logger.error(f"[Unified Processor {request_id}] Unexpected end of function reached")
        return {
            "success": False,
            "error": "Unexpected processing state",
            "citations": [],
            "clusters": [],
            "request_id": request_id,
            "metadata": {
                **input_metadata,
                "error": "unexpected_state",
                "error_details": "Function reached unexpected end",
            },
        }

    def _validate_url(self, url: str) -> bool:
        """Validate URL format and safety."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False

            if parsed.scheme not in ["http", "https"]:
                return False

            unsafe_domains = ["localhost", "127.0.0.1", "0.0.0.0"]
            if parsed.netloc.lower() in unsafe_domains:
                return False

            return True

        except Exception:
            return False


def process_file_input(file: FileStorage, request_id: str) -> Dict[str, Any]:
    """Process file input using unified processor."""
    processor = UnifiedInputProcessor()
    return processor.process_any_input(file, "file", request_id, "file_upload")


def process_url_input(url: str, request_id: str) -> Dict[str, Any]:
    """Process URL input using unified processor."""
    processor = UnifiedInputProcessor()
    return processor.process_any_input(url, "url", request_id, "url_input")


def process_text_input(text: str, request_id: str) -> Dict[str, Any]:
    """Process text input using unified processor."""
    processor = UnifiedInputProcessor()
    return processor.process_any_input(text, "text", request_id, "text_input")
