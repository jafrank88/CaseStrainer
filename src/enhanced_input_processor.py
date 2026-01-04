"""
Enhanced Input Processor for CaseStrainer

This module provides improved text extraction from various input sources
and enhanced async processing for concurrent job handling.
"""

import os
import sys
import asyncio
import logging
import tempfile
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import aiohttp
import PyPDF2
import fitz  # PyMuPDF
from io import BytesIO
import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from robust_pdf_extractor import RobustPDFExtractor
from utils.text_normalizer import normalize_text


logger = logging.getLogger(__name__)


class EnhancedInputProcessor:
    """Enhanced processor for handling various input types with improved text extraction."""

    def __init__(self, max_concurrent_jobs: int = 10, timeout_seconds: int = 300):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.timeout_seconds = timeout_seconds
        self.pdf_extractor = RobustPDFExtractor()
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs)

        # Cache for processed content
        self.content_cache = {}
        self.cache_ttl = 3600  # 1 hour

        # Session for HTTP requests
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout_seconds),
            headers={
                "User-Agent": "CaseStrainer/1.0 (Legal Citation Processor)",
                "Accept": "application/pdf,text/plain,text/html,application/xhtml+xml",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=True)

    def _get_cache_key(self, content: str, source_type: str) -> str:
        """Generate cache key for content."""
        content_hash = hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()
        return f"{source_type}_{content_hash}"

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Get content from cache if available and not expired."""
        if cache_key in self.content_cache:
            cached_data = self.content_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data["text"]
            else:
                # Remove expired cache entry
                del self.content_cache[cache_key]
        return None

    def _cache_content(self, cache_key: str, text: str):
        """Cache processed content."""
        self.content_cache[cache_key] = {"text": text, "timestamp": time.time()}
        logger.debug(f"Cached content for {cache_key}")

    async def process_text_input(self, text: str, request_id: str = None) -> Dict[str, Any]:
        """Process direct text input with enhanced normalization."""
        try:
            logger.info(f"Processing text input ({len(text)} characters)")

            # Generate cache key
            cache_key = self._get_cache_key(text, "text")

            # Check cache first
            cached_text = self._get_from_cache(cache_key)
            if cached_text:
                logger.info(f"Using cached text for request {request_id}")
                return {
                    "success": True,
                    "text": cached_text,
                    "source_type": "text",
                    "original_length": len(text),
                    "processed_length": len(cached_text),
                    "cache_hit": True,
                    "request_id": request_id,
                }

            # Enhanced text normalization
            processed_text = self._enhanced_text_normalization(text)

            # Cache the result
            self._cache_content(cache_key, processed_text)

            return {
                "success": True,
                "text": processed_text,
                "source_type": "text",
                "original_length": len(text),
                "processed_length": len(processed_text),
                "cache_hit": False,
                "request_id": request_id,
            }

        except Exception as e:
            logger.error(f"Error processing text input: {str(e)}")
            return {"success": False, "error": str(e), "source_type": "text", "request_id": request_id}

    async def process_file_input(self, file_path: str, request_id: str = None) -> Dict[str, Any]:
        """Process file input with improved text extraction."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            file_size = os.path.getsize(file_path)
            logger.info(f"Processing file input: {file_path} ({file_size:,} bytes)")

            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Generate cache key based on file content
            cache_key = self._get_cache_key(file_content.hex()[:100], "file")

            # Check cache first
            cached_text = self._get_from_cache(cache_key)
            if cached_text:
                logger.info(f"Using cached file text for request {request_id}")
                return {
                    "success": True,
                    "text": cached_text,
                    "source_type": "file",
                    "file_path": file_path,
                    "file_size": file_size,
                    "processed_length": len(cached_text),
                    "cache_hit": True,
                    "request_id": request_id,
                }

            # Extract text based on file type
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == ".pdf":
                extracted_text = await self._extract_pdf_text(file_content, file_path)
            elif file_ext in [".txt", ".text"]:
                extracted_text = file_content.decode("utf-8", errors="ignore")
            elif file_ext in [".html", ".htm"]:
                extracted_text = await self._extract_html_text(file_content)
            elif file_ext in [".doc", ".docx"]:
                extracted_text = await self._extract_docx_text(file_content, file_path)
            else:
                # Try to decode as text
                try:
                    extracted_text = file_content.decode("utf-8")
                except UnicodeDecodeError:
                    extracted_text = file_content.decode("latin-1", errors="ignore")

            # Enhanced text normalization
            processed_text = self._enhanced_text_normalization(extracted_text)

            # Cache the result
            self._cache_content(cache_key, processed_text)

            return {
                "success": True,
                "text": processed_text,
                "source_type": "file",
                "file_path": file_path,
                "file_size": file_size,
                "file_extension": file_ext,
                "processed_length": len(processed_text),
                "cache_hit": False,
                "request_id": request_id,
            }

        except Exception as e:
            logger.error(f"Error processing file input {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "source_type": "file",
                "file_path": file_path,
                "request_id": request_id,
            }

    async def process_url_input(self, url: str, request_id: str = None) -> Dict[str, Any]:
        """Process URL input with improved download and extraction."""
        try:
            logger.info(f"Processing URL input: {url}")

            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid URL: {url}")

            # Generate cache key
            cache_key = self._get_cache_key(url, "url")

            # Check cache first
            cached_text = self._get_from_cache(cache_key)
            if cached_text:
                logger.info(f"Using cached URL text for request {request_id}")
                return {
                    "success": True,
                    "text": cached_text,
                    "source_type": "url",
                    "url": url,
                    "processed_length": len(cached_text),
                    "cache_hit": True,
                    "request_id": request_id,
                }

            # Download content
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")

                content_type = response.headers.get("content-type", "").lower()
                content = await response.read()

            logger.info(f"Downloaded {len(content):,} bytes from {url} (content-type: {content_type})")

            # Extract text based on content type
            if "pdf" in content_type or url.endswith(".pdf"):
                extracted_text = await self._extract_pdf_text(content, url)
            elif "html" in content_type or "xhtml" in content_type:
                extracted_text = await self._extract_html_text(content)
            elif "text" in content_type:
                extracted_text = content.decode("utf-8", errors="ignore")
            else:
                # Try to decode as text
                try:
                    extracted_text = content.decode("utf-8")
                except UnicodeDecodeError:
                    extracted_text = content.decode("latin-1", errors="ignore")

            # Enhanced text normalization
            processed_text = self._enhanced_text_normalization(extracted_text)

            # Cache the result
            self._cache_content(cache_key, processed_text)

            return {
                "success": True,
                "text": processed_text,
                "source_type": "url",
                "url": url,
                "content_type": content_type,
                "processed_length": len(processed_text),
                "cache_hit": False,
                "request_id": request_id,
            }

        except Exception as e:
            logger.error(f"Error processing URL input {url}: {str(e)}")
            return {"success": False, "error": str(e), "source_type": "url", "url": url, "request_id": request_id}

    def _enhanced_text_normalization(self, text: str) -> str:
        """Enhanced text normalization with multiple cleaning steps."""
        if not text:
            return text

        try:
            # Step 1: Basic Unicode normalization
            normalized = normalize_text(text)

            # Step 2: Remove problematic characters
            import re

            # Remove control characters except newlines and tabs
            normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", normalized)

            # Step 3: Normalize whitespace
            normalized = re.sub(r"\r\n", "\n", normalized)  # Windows newlines
            normalized = re.sub(r"\r", "\n", normalized)  # Old Mac newlines
            normalized = re.sub(r"\n{3,}", "\n\n", normalized)  # Multiple newlines
            normalized = re.sub(r"[ \t]+", " ", normalized)  # Multiple spaces/tabs
            normalized = re.sub(r" *\n *", "\n", normalized)  # Spaces around newlines

            # Step 4: Remove common document artifacts
            # Remove page numbers (standalone)
            normalized = re.sub(r"\n\d+\n", "\n", normalized)
            # Remove header/footer patterns
            normalized = re.sub(r"\n-+\s*\d+\s*-+\n", "\n", normalized)
            # Remove email addresses (optional)
            normalized = re.sub(r"\S+@\S+\.\S+", "", normalized)

            # Step 5: Final cleanup
            normalized = normalized.strip()

            logger.debug(f"Text normalization: {len(text)} → {len(normalized)} characters")

            return normalized

        except Exception as e:
            logger.error(f"Error in text normalization: {str(e)}")
            return text  # Return original if normalization fails

    async def _extract_pdf_text(self, content: bytes, source: str) -> str:
        """Extract text from PDF using multiple methods with fallback."""
        try:
            # Method 1: PyMuPDF (fitz) - preferred for quality
            text = await self._extract_with_pymupdf(content)
            if text and len(text.strip()) > 100:
                logger.info(f"PyMuPDF extraction successful: {len(text)} characters")
                return text

            # Method 2: PyPDF2 - fallback
            text = await self._extract_with_pypdf2(content)
            if text and len(text.strip()) > 100:
                logger.info(f"PyPDF2 extraction successful: {len(text)} characters")
                return text

            # Method 3: RobustPDFExtractor - final fallback
            logger.info("Using RobustPDFExtractor as final fallback")
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            try:
                result = self.pdf_extractor.extract_pdf_text(temp_file_path)
                if result and "success" in result and result["success"]:
                    text = result.get("text", "")
                    if text:
                        logger.info(f"RobustPDFExtractor extraction successful: {len(text)} characters")
                        return text
            finally:
                os.unlink(temp_file_path)

            raise Exception("All PDF extraction methods failed")

        except Exception as e:
            logger.error(f"Error extracting PDF text from {source}: {str(e)}")
            raise

    async def _extract_with_pymupdf(self, content: bytes) -> str:
        """Extract text using PyMuPDF with optimized settings."""
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text_parts = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Get page dimensions
                rect = page.rect
                width, height = rect.width, rect.height

                # Define text area (exclude headers and footers)
                text_area = fitz.Rect(0, 65, width, height - 50)

                # Extract text from defined area
                text = page.get_text("text", clip=text_area)

                if text.strip():
                    text_parts.append(text)

            doc.close()

            full_text = "\n".join(text_parts)
            return full_text

        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {str(e)}")
            return ""

    async def _extract_with_pypdf2(self, content: bytes) -> str:
        """Extract text using PyPDF2."""
        try:
            pdf_file = BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_file)
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)

            full_text = "\n".join(text_parts)
            return full_text

        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {str(e)}")
            return ""

    async def _extract_html_text(self, content: bytes) -> str:
        """Extract text from HTML content."""
        try:
            from bs4 import BeautifulSoup

            html_content = content.decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)

            return text

        except ImportError:
            logger.warning("BeautifulSoup not available, using basic HTML extraction")
            # Basic HTML tag removal
            import re

            html_content = content.decode("utf-8", errors="ignore")
            text = re.sub(r"<[^>]+>", " ", html_content)
            text = re.sub(r"\s+", " ", text)
            return text.strip()

        except Exception as e:
            logger.error(f"HTML extraction failed: {str(e)}")
            raise

    async def _extract_docx_text(self, content: bytes, file_path: str) -> str:
        """Extract text from DOCX files."""
        try:
            import docx

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            try:
                doc = docx.Document(temp_file_path)
                text_parts = []

                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text_parts.append(paragraph.text)

                full_text = "\n".join(text_parts)
                return full_text

            finally:
                os.unlink(temp_file_path)

        except ImportError:
            logger.warning("python-docx not available for DOCX processing")
            raise Exception("DOCX processing requires python-docx package")

        except Exception as e:
            logger.error(f"DOCX extraction failed: {str(e)}")
            raise

    async def process_multiple_inputs(self, inputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple inputs concurrently."""
        logger.info(f"Processing {len(inputs)} inputs concurrently")

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent_jobs)

        async def process_single_input(input_data):
            async with semaphore:
                input_type = input_data.get("type", "text")
                request_id = input_data.get("request_id", str(uuid.uuid4()))

                if input_type == "text":
                    return await self.process_text_input(input_data.get("text", ""), request_id)
                elif input_type == "file":
                    return await self.process_file_input(input_data.get("file_path", ""), request_id)
                elif input_type == "url":
                    return await self.process_url_input(input_data.get("url", ""), request_id)
                else:
                    return {"success": False, "error": f"Unknown input type: {input_type}", "request_id": request_id}

        # Process all inputs concurrently
        tasks = [process_single_input(input_data) for input_data in inputs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {"success": False, "error": str(result), "request_id": inputs[i].get("request_id", "unknown")}
                )
            else:
                processed_results.append(result)

        # Log summary
        successful = sum(1 for r in processed_results if r.get("success", False))
        logger.info(
            f"Processed {len(processed_results)} inputs: {successful} successful, {len(processed_results) - successful} failed"
        )

        return processed_results

    def clear_cache(self):
        """Clear the content cache."""
        self.content_cache.clear()
        logger.info("Content cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.content_cache)
        expired_entries = sum(
            1 for entry in self.content_cache.values() if time.time() - entry["timestamp"] >= self.cache_ttl
        )

        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_ttl": self.cache_ttl,
        }


# Async context manager for easy usage
async def get_enhanced_processor(max_concurrent_jobs: int = 10, timeout_seconds: int = 300) -> EnhancedInputProcessor:
    """Get enhanced input processor instance."""
    return EnhancedInputProcessor(max_concurrent_jobs, timeout_seconds)


# Utility function for quick processing
async def process_input(input_data: Dict[str, Any], max_concurrent_jobs: int = 10) -> Dict[str, Any]:
    """Quick utility function to process a single input."""
    async with EnhancedInputProcessor(max_concurrent_jobs) as processor:
        input_type = input_data.get("type", "text")
        request_id = input_data.get("request_id")

        if input_type == "text":
            return await processor.process_text_input(input_data.get("text", ""), request_id)
        elif input_type == "file":
            return await processor.process_file_input(input_data.get("file_path", ""), request_id)
        elif input_type == "url":
            return await processor.process_url_input(input_data.get("url", ""), request_id)
        else:
            return {"success": False, "error": f"Unknown input type: {input_type}", "request_id": request_id}


# Batch processing utility
async def process_batch(inputs: List[Dict[str, Any]], max_concurrent_jobs: int = 10) -> List[Dict[str, Any]]:
    """Process multiple inputs in batch."""
    async with EnhancedInputProcessor(max_concurrent_jobs) as processor:
        return await processor.process_multiple_inputs(inputs)
