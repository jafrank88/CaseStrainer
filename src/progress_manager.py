"""
Progress Bar Solutions for CaseStrainer Citation Processing
Multiple approaches to provide real-time progress feedback to users
"""

import os
import sys
import time
import json
import uuid
import logging
import threading
import traceback
import requests
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, Response, stream_with_context

# Configure requests to be less verbose
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

# User agent to use for web requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

import asyncio
from typing import Dict, List, Any, Optional, Generator, Callable, TYPE_CHECKING
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

# Flask-SocketIO import with proper fallback
# Note: flask-socketio is optional and not required for basic functionality
try:
    from flask_socketio import SocketIO, emit  # type: ignore
    FLASK_SOCKETIO_AVAILABLE = True
except ImportError:
    FLASK_SOCKETIO_AVAILABLE = False
    # Create dummy classes for type checking when flask_socketio is not available
    class SocketIO:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
    
    def emit(*args, **kwargs):  # type: ignore
        pass

# Redis import with proper fallback
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore

logger = logging.getLogger(__name__)

# ============================================================================
# SOLUTION 1: Server-Sent Events (SSE) - Recommended for most cases
# ============================================================================

class ProgressTracker:
    """Thread-safe progress tracking for citation processing"""
    
    def __init__(self, task_id: str, total_steps: int):
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
        self.status = "starting"
        self.message = "Initializing..."
        self.results = []
        self.errors = []
        self.start_time = datetime.now()
        self.estimated_completion = None
        
    def update(self, step: int, status: str, message: str, 
               partial_results: Optional[List] = None, error: Optional[str] = None):
        """Update progress and optionally add partial results"""
        self.current_step = step
        self.status = status
        self.message = message
        
        if partial_results:
            self.results.extend(partial_results)
            
        if error:
            self.errors.append(error)
            
        # Calculate estimated completion
        if step > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            estimated_total = (elapsed / step) * self.total_steps
            remaining = estimated_total - elapsed
            self.estimated_completion = remaining
    
    def get_progress_data(self) -> Dict:
        """Get current progress data for client updates"""
        progress_percent = (self.current_step / self.total_steps * 100) if self.total_steps > 0 else 0
        
        return {
            'task_id': self.task_id,
            'progress': round(progress_percent, 2),
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'status': self.status,
            'message': self.message,
            'results_count': len(self.results),
            'error_count': len(self.errors),
            'estimated_completion': self.estimated_completion,
            'timestamp': datetime.now().isoformat()
        }
    
    def is_complete(self) -> bool:
        return self.status in ['completed', 'failed']


class SSEProgressManager:
    """Manages Server-Sent Events for real-time progress updates"""
    
    def __init__(self):
        self.active_tasks: Dict[str, ProgressTracker] = {}
        self.redis_client = None
        if REDIS_AVAILABLE and redis is not None:
            try:
                # Optional Redis for multi-instance deployment
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            except:
                logger.warning("Redis not available, using in-memory progress tracking")
                self.redis_client = None
        else:
            logger.info("Redis not installed, using in-memory progress tracking")
    
    def start_task(self, total_steps: int) -> str:
        """Start a new task and return task ID"""
        task_id = str(uuid.uuid4())
        tracker = ProgressTracker(task_id, total_steps)
        self.active_tasks[task_id] = tracker
        
        if self.redis_client:
            self._store_progress_in_redis(task_id, tracker)
            
        return task_id
    
    def update_progress(self, task_id: str, step: int, status: str, 
                       message: str, partial_results: Optional[List] = None, error: Optional[str] = None):
        """Update task progress"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update(step, status, message, partial_results, error)
            
            if self.redis_client:
                self._store_progress_in_redis(task_id, self.active_tasks[task_id])
    
    def get_progress(self, task_id: str) -> Dict:
        """Get current progress for a task"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].get_progress_data()
        
        if self.redis_client:
            return self._get_progress_from_redis(task_id)
            
        return {'error': 'Task not found'}
    
    def get_results(self, task_id: str) -> Dict:
        """Get final results for a completed task"""
        if task_id in self.active_tasks:
            tracker = self.active_tasks[task_id]
            return {
                'task_id': task_id,
                'status': tracker.status,
                'results': tracker.results,
                'errors': tracker.errors,
                'progress_data': tracker.get_progress_data()
            }
        return {'error': 'Task not found'}
    
    def cleanup_task(self, task_id: str):
        """Clean up completed task"""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            
        if self.redis_client:
            self.redis_client.delete(f"progress:{task_id}")
    
    def _store_progress_in_redis(self, task_id: str, tracker: ProgressTracker):
        """Store progress in Redis for multi-instance support"""
        try:
            if self.redis_client is not None:
                data = tracker.get_progress_data()
                data['results'] = tracker.results
                data['errors'] = tracker.errors
                self.redis_client.setex(  # type: ignore
                    f"progress:{task_id}", 
                    3600,  # 1 hour expiration
                    json.dumps(data, default=str)
                )
        except Exception as e:
            logger.error(f"Failed to store progress in Redis: {e}")
    
    def _get_progress_from_redis(self, task_id: str) -> Dict:
        """Get progress from Redis"""
        try:
            if self.redis_client is not None:
                data = self.redis_client.get(f"progress:{task_id}")  # type: ignore
                if data:
                    return json.loads(data.decode('utf-8') if isinstance(data, bytes) else data)  # type: ignore
        except Exception as e:
            logger.error(f"Failed to get progress from Redis: {e}")
        return {'error': 'Task not found'}


# ============================================================================
# SOLUTION 2: WebSocket Implementation
# ============================================================================

class WebSocketProgressManager:
    """WebSocket-based real-time progress updates"""
    
    def __init__(self, socketio: Any):
        self.socketio = socketio
        self.active_tasks: Dict[str, ProgressTracker] = {}
    
    def start_task(self, total_steps: int, client_id: str) -> str:
        """Start task and join client to room for updates"""
        task_id = str(uuid.uuid4())
        tracker = ProgressTracker(task_id, total_steps)
        self.active_tasks[task_id] = tracker
        
        # Join client to task-specific room
        self.socketio.server.enter_room(client_id, f"task_{task_id}")
        
        # Send initial progress
        self.socketio.emit('progress_update', 
                          tracker.get_progress_data(), 
                          room=f"task_{task_id}")
        
        return task_id
    
    def update_progress(self, task_id: str, step: int, status: str, 
                       message: str, partial_results: Optional[List] = None, error: Optional[str] = None):
        """Update progress and emit to all clients watching this task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update(step, status, message, partial_results or [], error)
            
            # Emit progress update to all clients in task room
            progress_data = self.active_tasks[task_id].get_progress_data()
            
            # Include partial results if available
            if partial_results:
                progress_data['partial_results'] = partial_results
            
            self.socketio.emit('progress_update', 
                              progress_data, 
                              room=f"task_{task_id}")


# ============================================================================
# SOLUTION 3: Chunked Citation Processing
# ============================================================================

class ChunkedCitationProcessor:
    """Process citations in chunks to provide incremental progress"""
    
    def __init__(self, progress_manager: SSEProgressManager):
        self.progress_manager = progress_manager
        self.chunk_size = 1000  # Characters per chunk
    
    async def process_document_with_progress(self, 
                                           document_text: str, 
                                           document_type: str = "legal_brief") -> str:
        """Process document in chunks with progress updates"""
        logger.info("\n" + "="*80)
        logger.info("Starting process_document_with_progress")
        logger.info(f"Document type: {document_type}")
        logger.info(f"Document text length: {len(document_text)} characters")
        
        try:
            # Validate input
            if not document_text or not isinstance(document_text, str):
                error_msg = f"Invalid document text. Type: {type(document_text)}, Length: {len(str(document_text)) if document_text is not None else 'None'}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Create a new task for this document
            task_id = str(uuid.uuid4())
            logger.info(f"Created task ID: {task_id}")
            
            # Initialize progress tracker with 100 total steps
            tracker = ProgressTracker(task_id, total_steps=100)
            logger.info("Initialized progress tracker")
            
            # Store the task
            self.progress_manager.active_tasks[task_id] = tracker
            logger.info(f"Stored task in active_tasks. Total active tasks: {len(self.progress_manager.active_tasks)}")
            
            # Log Redis availability
            logger.info(f"Redis available: {hasattr(self.progress_manager, 'redis_client') and self.progress_manager.redis_client is not None}")
            
            # Start processing in a background task
            logger.info("Creating background task for document processing...")
            asyncio.create_task(self._process_document_async(task_id, document_text, document_type, tracker))
            logger.info("Background task created successfully")
            
            # Initial progress update - the rest will be handled by the background task
            self.progress_manager.update_progress(
                task_id, 0, "started", 
                "Document processing started...",
                partial_results=[]
            )
            
            return task_id
            
        except Exception as e:
            self.progress_manager.update_progress(
                task_id, 0, "failed", f"Processing failed: {str(e)}", error=str(e)
            )
            raise
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Split document into processable chunks"""
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunk = text[i:i + self.chunk_size]
            
            # Don't split in the middle of a potential citation
            if i + self.chunk_size < len(text):
                # Look for a good break point (sentence end, paragraph, etc.)
                break_points = ['. ', '\n\n', '\n', '. ']
                for bp in break_points:
                    last_bp = chunk.rfind(bp)
                    if last_bp > self.chunk_size * 0.8:  # Don't make chunks too small
                        chunk = chunk[:last_bp + len(bp)]
                        break
            
            chunks.append(chunk)
        
        return chunks
    
    async def _preprocess_chunks(self, chunks: List[str]) -> List[str]:
        """Preprocess chunks for better citation extraction"""
        # Normalize text, fix common OCR errors, etc.
        processed = []
        for chunk in chunks:
            # Simulate preprocessing work
            processed_chunk = chunk.replace('  ', ' ').strip()
            processed.append(processed_chunk)
        
        return processed
    
    async def _process_chunk(self, chunk: str, document_type: str) -> List[Dict]:
        """Process a single chunk for citations using the canonical UnifiedCitationProcessorV2."""
        chunk_hash = hash(chunk) % 1000
        logger.info(f"[Chunk-{chunk_hash}] Starting chunk processing (size: {len(chunk)} chars)")
        
        try:
            # Use the canonical UnifiedCitationProcessorV2 for real citation extraction
            logger.info(f"[Chunk-{chunk_hash}] Importing UnifiedCitationProcessorV2...")
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
            
            logger.info(f"[Chunk-{chunk_hash}] Creating ProcessingConfig...")
            config = ProcessingConfig(
                use_eyecite=True,
                use_regex=True,
                extract_case_names=True,
                extract_dates=True,
                enable_clustering=True,  # Enable clustering to detect parallel citations
                enable_verification=True  # Enable verification for complete analysis
            )
            
            logger.info(f"[Chunk-{chunk_hash}] Creating processor instance...")
            processor = UnifiedCitationProcessorV2(config)
            
            logger.info(f"[Chunk-{chunk_hash}] Starting process_text()...")
            start_time = time.time()
            results = processor.process_text(chunk)
            process_time = time.time() - start_time
            logger.info(f"[Chunk-{chunk_hash}] process_text() completed in {process_time:.2f}s, got {len(results)} results")
            
            # Convert CitationResult objects to dictionaries
            logger.info(f"[Chunk-{chunk_hash}] Converting {len(results)} results to dicts...")
            citations = []
            for i, result in enumerate(results, 1):  # type: ignore
                try:
                    citation_data = {
                        'id': len(citations) + 1,
                        'citation': result.citation,
                        'raw_text': result.citation,
                        'case_name': result.canonical_name or result.extracted_case_name or 'Unknown Case',
                        'year': result.canonical_date or result.extracted_date or 'No year',
                        'confidence_score': 0.85,  # Default confidence
                        'chunk_index': chunk_hash,
                        'extracted_case_name': result.extracted_case_name,
                        'canonical_name': result.canonical_name,
                        'extracted_date': result.extracted_date,
                        'canonical_date': result.canonical_date,
                        'verified': result.verified,
                        'source': result.source,
                        'method': result.method,
                        'is_parallel': result.is_parallel,
                        'parallel_citations': result.parallel_citations or [],
                        'start_index': result.start_index,
                        'end_index': result.end_index,
                        'context': result.context,
                        'url': result.url,
                        'metadata': result.metadata or {}
                    }
                    citations.append(citation_data)
                    
                    # Log first few citations for debugging
                    if i <= 3:  # Only log first 3 citations to avoid log spam
                        logger.debug(f"[Chunk-{chunk_hash}] Citation {i}: {result.citation} | "
                                   f"Name: {result.extracted_case_name} | "
                                   f"Date: {result.extracted_date} | "
                                   f"Verified: {result.verified}")
                except Exception as cite_err:
                    logger.error(f"[Chunk-{chunk_hash}] Error processing citation {i}: {str(cite_err)}")
                    logger.error(traceback.format_exc())
            
            logger.info(f"[Chunk-{chunk_hash}] Processed {len(citations)} citations")
            return citations
            
        except Exception as e:
            error_msg = f"[Chunk-{chunk_hash}] Error processing chunk: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return []
    
    async def _process_document_async(self, task_id: str, document_text: str, document_type: str, tracker: 'ProgressTracker'):
        """Background task to process document asynchronously"""
        logger.info("\n" + "="*80)
        logger.info(f"Starting _process_document_async for task {task_id}")
        logger.info(f"Document type: {document_type}")
        logger.info(f"Document text length: {len(document_text)} characters")
        logger.info(f"Tracker status: {tracker.status if tracker else 'No tracker'}")
        
        try:
            # Validate input
            if not document_text or not isinstance(document_text, str):
                error_msg = f"Invalid document text in _process_document_async. Type: {type(document_text)}"
                logger.error(error_msg)
                self.progress_manager.update_progress(
                    task_id, 0, "failed", error_msg, error=error_msg
                )
                return
                
            # Log first 200 chars of document
            logger.info(f"Document sample: {document_text[:200]}...")
            
            # Split document into chunks
            logger.info("Splitting document into chunks...")
            chunks = self._split_into_chunks(document_text)
            logger.info(f"Document split into {len(chunks)} chunks")
            
            # Update progress (10% for splitting)
            logger.info("Updating progress to 10% (chunking complete)")
            self.progress_manager.update_progress(
                task_id, 10, "processing", "Processing document chunks..."
            )
            
            # Process each chunk
            results = []
            total_chunks = len(chunks)
            logger.info(f"Starting to process {total_chunks} chunks...")
            
            for i, chunk in enumerate(chunks, 1):
                try:
                    logger.info(f"\nProcessing chunk {i}/{total_chunks}")
                    logger.debug(f"Chunk size: {len(chunk)} characters")
                    
                    # Process chunk (this would call your citation processor)
                    logger.info("Calling _process_chunk...")
                    chunk_results = await self._process_chunk(chunk, document_type)
                    logger.info(f"Processed chunk {i}, found {len(chunk_results)} citations")
                    
                    results.extend(chunk_results)
                    
                    # Update progress (10% + 70% for processing chunks)
                    progress = 10 + int(70 * i / total_chunks)
                    progress_msg = f"Processed chunk {i}/{total_chunks} with {len(chunk_results)} citations"
                    logger.info(f"Updating progress to {progress}%: {progress_msg}")
                    
                    self.progress_manager.update_progress(
                        task_id, progress, "processing", progress_msg,
                        partial_results=chunk_results
                    )
                    
                except Exception as chunk_error:
                    error_msg = f"Error processing chunk {i}/{total_chunks}: {str(chunk_error)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    
                    self.progress_manager.update_progress(
                        task_id, 0, "failed", error_msg, error=error_msg
                    )
                    return
            
            # Perform final analysis (20% for final processing)
            logger.info("\nPerforming final analysis...")
            self.progress_manager.update_progress(
                task_id, 90, "processing", "Performing final analysis..."
            )
            
            try:
                final_results = await self._perform_final_analysis(results)
                
                # Mark as complete
                logger.info("Marking task as complete")
                self.progress_manager.update_progress(
                    task_id, 100, "completed", 
                    f"Processing complete! Found {len(results)} citations.",
                    partial_results=results
                )
                logger.info("Task completed successfully")
                
            except Exception as analysis_error:
                error_msg = f"Error in final analysis: {str(analysis_error)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                
                self.progress_manager.update_progress(
                    task_id, 0, "failed", error_msg, error=error_msg
                )
            
        except Exception as e:
            error_msg = f"Unexpected error in _process_document_async: {str(e)}"
            logger.error("\n" + "!"*80)
            logger.error("UNEXPECTED ERROR IN _process_document_async")
            logger.error("!"*80)
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            logger.error("!"*80 + "\n")
            
            # Try to update tracker if available
            try:
                self.progress_manager.update_progress(
                    task_id, 0, "failed", error_msg, error=error_msg
                )
            except Exception as update_error:
                logger.error(f"Failed to update progress with error: {str(update_error)}")
            
            # Re-raise to ensure the error is logged by the caller
            raise
    
    async def _perform_final_analysis(self, citations: List[Dict]) -> Dict:
        """Perform final analysis on all collected citations with proper clustering"""
        await asyncio.sleep(0.2)  # Simulate analysis time
        
        # Convert dict citations back to CitationResult objects for clustering
        from src.models import CitationResult
        from src.unified_citation_clustering import cluster_citations_unified
        
        citation_objects = []
        for citation_dict in citations:
            # Create CitationResult object from dict
            citation_obj = CitationResult(
                citation=citation_dict.get('citation', ''),
                extracted_case_name=citation_dict.get('extracted_case_name'),
                extracted_date=citation_dict.get('extracted_date'),
                canonical_name=citation_dict.get('canonical_name'),
                canonical_date=citation_dict.get('canonical_date'),
                verified=citation_dict.get('verified', False),
                is_parallel=citation_dict.get('is_parallel', False),
                parallel_citations=citation_dict.get('parallel_citations', []),
                start_index=citation_dict.get('start_index', 0),
                end_index=citation_dict.get('end_index', 0),
                context=citation_dict.get('context', ''),
                source=citation_dict.get('source', ''),
                url=citation_dict.get('url'),
                metadata=citation_dict.get('metadata', {})
            )
            citation_objects.append(citation_obj)
        
        # Perform clustering
        clusters = cluster_citations_unified(citation_objects)
        
        return {
            'citations': citations,
            'clusters': clusters,
            'total_citations': len(citations),
            'high_confidence': len([c for c in citations if c.get('confidence_score', 0) > 0.8]),
            'needs_review': len([c for c in citations if c.get('confidence_score', 0) < 0.6])
        }


# ============================================================================
# SOLUTION 4: Flask Route Implementations
# ============================================================================

def fetch_url_content(url: str) -> str:
    """Fetch content from a URL with proper error handling and user agent."""
    try:
        logger.info(f"Fetching URL: {url}")
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Special handling for PDFs
        if url.lower().endswith('.pdf'):
            headers['Accept'] = 'application/pdf,application/x-pdf,application/octet-stream'
        
        logger.debug(f"Request headers: {headers}")
        
        response = requests.get(
            url,
            headers=headers,
            timeout=30,  # 30 second timeout
            allow_redirects=True,
            stream=True  # Stream the response for large files
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        logger.info(f"Content type: {content_type}")
        
        # If it's a PDF, use PyPDF2 to extract text
        if 'pdf' in content_type or url.lower().endswith('.pdf'):
            try:
                import PyPDF2
                import io
                
                # Read the PDF content
                pdf_content = io.BytesIO(response.content)
                pdf_reader = PyPDF2.PdfReader(pdf_content)
                text_parts = []
                
                # Extract text from each page
                for i, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                        logger.debug(f"Extracted {len(text)} characters from page {i}")
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {i}: {str(e)}")
                
                result = '\n\n'.join(text_parts) if text_parts else ''
                logger.info(f"Extracted {len(result)} characters total from PDF")
                return result
                
            except Exception as e:
                logger.error(f"Error processing PDF: {str(e)}\n{traceback.format_exc()}")
                raise Exception(f"Error processing PDF: {str(e)}")
        
        # For HTML content, just return the text
        elif 'html' in content_type:
            logger.info(f"Returning HTML content, length: {len(response.text)}")
            return response.text
        
        # For plain text
        elif 'text/plain' in content_type:
            logger.info(f"Returning plain text content, length: {len(response.text)}")
            return response.text
        
        # For other content types, try to decode as text
        else:
            try:
                logger.info(f"Attempting to decode unknown content type: {content_type}")
                return response.text
            except UnicodeDecodeError:
                logger.warning(f"Could not decode content as text: {content_type}")
                return f"[Binary content from {url} - cannot be processed as text]"
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {str(e)}\n{traceback.format_exc()}")
        raise Exception(f"Failed to fetch URL: {str(e)}")

def create_progress_routes(app: Flask, progress_manager: SSEProgressManager, 
                          citation_processor: ChunkedCitationProcessor):
    """Create Flask routes for progress-enabled citation processing"""
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    @app.route('/casestrainer/api/analyze', methods=['POST'])
    async def start_citation_analysis():
        """Start citation analysis and return task ID
        
        Supports multiple input types:
        1. File upload (multipart/form-data)
        2. Direct text input (application/json)
        3. URL to fetch content from (via 'url' parameter in JSON)
        """
        task_id = str(uuid.uuid4())
        logger.info(f"=== Starting citation analysis for task {task_id} ===")
        
        try:
            # Enhanced request logging
            logger.info(f"[Task {task_id}] Request method: {request.method}")
            logger.info(f"[Task {task_id}] Request URL: {request.url}")
            logger.info(f"[Task {task_id}] Request headers: {dict(request.headers)}")
            logger.info(f"[Task {task_id}] Content-Type: {request.content_type}")
            logger.info(f"[Task {task_id}] Form data: {request.form}")
            logger.info(f"[Task {task_id}] Files: {request.files}")
            
            # Log JSON data if present
            json_data = request.get_json(silent=True, force=True)
            if json_data:
                logger.info(f"[Task {task_id}] JSON data received:")
                # Log a sanitized version of JSON data (in case it contains sensitive info)
                sanitized_data = {k: v if k not in ['text', 'content'] else f'[content of length {len(str(v))}]' 
                                for k, v in json_data.items()}
                logger.info(f"[Task {task_id}] {sanitized_data}")
                
                # Log JSON content details (truncated if too long)
                for key, value in json_data.items():
                    if key == 'text' and value and len(value) > 100:
                        logger.info(f"[Task {task_id}] {key}: {value[:100]}... (truncated, total length: {len(value)})")
                    elif key == 'url':
                        logger.info(f"[Task {task_id}] URL provided: {value}")
                    else:
                        logger.info(f"[Task {task_id}] {key}: {value}")
            else:
                logger.info(f"[Task {task_id}] No JSON data in request")
                
            # Log environment info for debugging
            logger.info(f"[Task {task_id}] Python version: {sys.version}")
            logger.info(f"[Task {task_id}] Working directory: {os.getcwd()}")
            logger.info(f"[Task {task_id}] Module search path: {sys.path}")
            
            # Log form data if present
            if request.form:
                logger.info(f"[Task {task_id}] Form data received:")
                for key, value in request.form.items():
                    if key == 'text' and value and len(value) > 100:
                        logger.info(f"[Task {task_id}] {key}: {value[:100]}... (truncated, total length: {len(value)})")
                    else:
                        logger.info(f"[Task {task_id}] {key}: {value}")
            
            # Log file details if present
            if request.files:
                logger.info(f"[Task {task_id}] Files received:")
                for key, file in request.files.items():
                    file_data = file.read(1024)
                    logger.info(f"[Task {task_id}] {key}: {file.filename} ({file.content_type}, {len(file_data)} bytes)")
                    file.seek(0)  # Reset file pointer after reading
                logger.info("\nFiles in request:")
                for key in request.files:
                    file = request.files[key]
                    file_content = file.read()
                    logger.info(f"  {key}: {file.filename} ({file.content_type}, {len(file_content)} bytes)")
                    file.seek(0)  # Reset file pointer
            
            # Log form data
            if request.form:
                logger.info("\nForm data:")
                for key, value in request.form.items():
                    logger.info(f"  {key}: {value}")
            
            # Log JSON data if present
            json_data = None
            if request.is_json:
                try:
                    json_data = request.get_json()
                    logger.info("\nJSON data in request:")
                    logger.info(json.dumps(json_data, indent=2))
                except Exception as e:
                    logger.error(f"Error parsing JSON: {str(e)}")
                    return jsonify({'error': 'Invalid JSON data'}), 400
            
            logger.info("\nRequest environment:")
            for key in ['CONTENT_TYPE', 'REQUEST_METHOD', 'PATH_INFO', 'QUERY_STRING']:
                if key in request.environ:
                    logger.info(f"  {key}: {request.environ[key]}")
            
            logger.info("\nRequest data (first 1000 chars):")
            try:
                data = request.get_data(as_text=True)
                logger.info(data[:1000] + ('...' if len(data) > 1000 else ''))
            except Exception as e:
                logger.error(f"Error reading request data: {str(e)}")
            
            document_text = ''
            document_type = 'legal_brief'
            
            # Check if this is a file upload
            if 'file' in request.files:
                logger.info("Processing file upload")
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No selected file'}), 400
                    
                # Read file content based on file type
                filename = file.filename.lower() if file.filename else ''
                if filename.endswith('.pdf'):
                    try:
                        # For PDF files, we need PyPDF2 to extract text
                        import PyPDF2
                        import io
                        
                        # Read the PDF file
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
                        text_parts = []
                        for page in pdf_reader.pages:
                            text = page.extract_text()
                            if text:
                                text_parts.append(text)
                        document_text = '\n\n'.join(text_parts)
                        logger.info(f"Extracted {len(document_text)} characters from PDF")
                    except Exception as e:
                        logger.error(f"Error reading PDF: {str(e)}")
                        return jsonify({'error': 'Error reading PDF file'}), 400
                else:
                    # For text files, just read the content
                    try:
                        document_text = file.read().decode('utf-8')
                    except UnicodeDecodeError:
                        return jsonify({'error': 'Invalid file encoding. Please use UTF-8 encoded text files.'}), 400
            else:
                # Handle JSON input
                data = request.get_json()
                if not data:
                    logger.error("No data received in request")
                    return jsonify({'error': 'No data received'}), 400
                
                # Check if this is a URL fetch request
                if 'url' in data and data['url']:
                    url = data['url'].strip()
                    logger.info(f"Processing URL: {url}")
                    
                    try:
                        # Validate URL
                        parsed = urlparse(url)
                        if not all([parsed.scheme, parsed.netloc]):
                            return jsonify({'error': 'Invalid URL format'}), 400
                        
                        # Fetch content from URL
                        document_text = fetch_url_content(url)
                        if not document_text.strip():
                            return jsonify({'error': 'No content could be extracted from the URL'}), 400
                            
                        logger.info(f"Fetched {len(document_text)} characters from URL")
                        document_type = data.get('document_type', 'legal_brief')
                    except Exception as e:
                        error_id = str(uuid.uuid4())
                        logger.error(f"\n{'*'*80}")
                        logger.error(f"ERROR ID: {error_id}")
                        logger.error(f"Error in start_citation_analysis: {str(e)}")
                        logger.error(f"Error type: {type(e).__name__}")
                        logger.error("Traceback:")
                        logger.error(traceback.format_exc())
                        
                        # Log request details that might have caused the error
                        logger.error("Request details at time of error:")
                        logger.error(f"  Method: {request.method}")
                        logger.error(f"  URL: {request.url}")
                        logger.error(f"  Content-Type: {request.content_type}")
                        logger.error(f"  Headers: {dict(request.headers)}")
                        
                        if request.is_json:
                            try:
                                json_data = request.get_json()
                                logger.error("  JSON data:")
                                for key, value in json_data.items():
                                    if key == 'text' and value and len(value) > 100:
                                        logger.error(f"    {key}: {value[:100]}... (truncated, total length: {len(value)})")
                                    else:
                                        logger.error(f"    {key}: {value}")
                            except Exception as json_err:
                                logger.error(f"  Could not parse JSON data: {str(json_err)}")
                        
                        if request.files:
                            logger.error("  Files in request:")
                            for key, file in request.files.items():
                                logger.error(f"    {key}: {file.filename} ({file.content_type}, {len(file.read(1024))} bytes)")
                                file.seek(0)
                        
                        logger.error(f"{'*'*80}\n")
                        
                        return jsonify({
                            "error": "An unexpected error occurred while processing your request",
                            "error_id": error_id,
                            "details": str(e),
                            "type": type(e).__name__
                        }), 500
                else:
                    # Regular text input
                    document_text = data.get('text', '')
                    document_type = data.get('document_type', 'legal_brief')
            
            if not document_text.strip():
                logger.error("No document text provided in request")
                return jsonify({'error': 'No document text provided, file was empty, or URL returned no content'}), 400
            
            logger.info(f"Starting analysis for document type: {document_type}")
            
            # Log the document info before processing
            logger.info("\nDocument info before processing:")
            logger.info(f"Document type: {document_type}")
            logger.info(f"Document text length: {len(document_text)} characters")
            logger.info(f"First 200 chars: {document_text[:200]}...")
            
            # Start processing asynchronously
            try:
                task_id = await citation_processor.process_document_with_progress(
                    document_text, document_type
                )
                
                if not task_id:
                    raise ValueError("No task ID returned from process_document_with_progress")
                
                logger.info(f"Started analysis with task_id: {task_id}")
                
                response_data = {
                    'task_id': task_id,
                    'status': 'started',
                    'message': 'Citation analysis started',
                    'document_length': len(document_text)
                }
                
                logger.info(f"Returning success response: {json.dumps(response_data)}")
                return jsonify(response_data)
                
            except Exception as proc_error:
                logger.error("Error in process_document_with_progress:")
                logger.error(f"Error type: {type(proc_error).__name__}")
                logger.error(f"Error message: {str(proc_error)}")
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                raise proc_error
            
        except Exception as e:
            error_trace = traceback.format_exc()
            error_msg = f"Error in start_citation_analysis: {str(e)}\n{error_trace}"
            logger.error("\n" + "!"*80)
            logger.error("ERROR PROCESSING REQUEST")
            logger.error("!"*80)
            logger.error(error_msg)
            logger.error("!"*80 + "\n")
            
            # Return detailed error in development, generic in production
            error_response = {
                'error': 'Failed to start analysis',
                'details': str(e),
            }
            
            if app.debug:
                error_response['traceback'] = error_trace.split('\n')  # type: ignore
                error_response['request_info'] = {  # type: ignore
                    'content_type': request.content_type,
                    'method': request.method,
                    'endpoint': request.endpoint,
                }
            
            return jsonify(error_response), 500
    
    @app.route('/casestrainer/api/analyze/progress/<task_id>')
    def get_progress(task_id: str):
        """Get current progress for a task"""
        try:
            progress_data = progress_manager.get_progress(task_id)
            return jsonify(progress_data)
        except Exception as e:
            logger.error(f"Error getting progress: {e}")
            return jsonify({'error': 'Failed to get progress'}), 500
    
    @app.route('/casestrainer/api/analyze/results/<task_id>')
    def get_results(task_id: str):
        """Get final results for a completed task"""
        try:
            results = progress_manager.get_results(task_id)
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error getting results: {e}")
            return jsonify({'error': 'Failed to get results'}), 500
    
    @app.route('/casestrainer/api/analyze/progress-stream/<task_id>')
    def progress_stream(task_id: str):
        """Server-Sent Events stream for real-time progress"""
        def generate_progress_events():
            """Generator for SSE progress events"""
            while True:
                try:
                    progress_data = progress_manager.get_progress(task_id)
                    
                    if 'error' in progress_data:
                        yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                        break
                    
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    
                    if progress_data.get('status') in ['completed', 'failed']:
                        # Send final results
                        final_results = progress_manager.get_results(task_id)
                        yield f"data: {json.dumps(final_results)}\n\n"
                        break
                    
                    time.sleep(0.5)  # Update every 500ms
                    
                except Exception as e:
                    logger.error(f"Error in progress stream: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    break
        
        return Response(
            generate_progress_events(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Nginx compatibility
            }
        )


# ============================================================================
# SOLUTION 5: Frontend JavaScript Integration
# ============================================================================

frontend_js_example = '''
// Frontend JavaScript for progress tracking
class CitationProgressTracker {
    constructor() {
        this.taskId = null;
        this.eventSource = null;
        this.progressCallback = null;
        this.completeCallback = null;
    }
    
    // Method 1: Server-Sent Events (Recommended)
    startAnalysisWithSSE(documentText, documentType, progressCallback, completeCallback) {
        this.progressCallback = progressCallback;
        this.completeCallback = completeCallback;
        
        // Start the analysis
        fetch('/casestrainer/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: documentText,
                document_type: documentType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                this.taskId = data.task_id;
                this.connectToProgressStream();
            } else {
                throw new Error(data.error || 'Failed to start analysis');
            }
        })
        .catch(error => {
            console.error('Error starting analysis:', error);
            this.completeCallback({ error: error.message });
        });
    }
    
    connectToProgressStream() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        this.eventSource = new EventSource(
            `/casestrainer/api/analyze/progress-stream/${this.taskId}`
        );
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    this.handleError(data.error);
                    return;
                }
                
                if (data.results) {
                    // Final results received
                    this.handleComplete(data);
                } else {
                    // Progress update
                    this.handleProgress(data);
                }
                
            } catch (error) {
                console.error('Error parsing progress data:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            this.eventSource.close();
            // Fallback to polling
            this.startPolling();
        };
    }
    
    // Method 2: Polling Fallback
    startPolling() {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/casestrainer/api/analyze/progress/${this.taskId}`);
                const data = await response.json();
                
                if (data.error) {
                    clearInterval(pollInterval);
                    this.handleError(data.error);
                    return;
                }
                
                this.handleProgress(data);
                
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollInterval);
                    
                    // Get final results
                    const resultsResponse = await fetch(`/casestrainer/api/analyze/results/${this.taskId}`);
                    const results = await resultsResponse.json();
                    this.handleComplete(results);
                }
                
            } catch (error) {
                clearInterval(pollInterval);
                this.handleError(error.message);
            }
        }, 1000); // Poll every second
    }
    
    handleProgress(progressData) {
        if (this.progressCallback) {
            this.progressCallback({
                progress: progressData.progress,
                message: progressData.message,
                currentStep: progressData.current_step,
                totalSteps: progressData.total_steps,
                resultsCount: progressData.results_count,
                estimatedCompletion: progressData.estimated_completion
            });
        }
        
        // Update UI
        this.updateProgressBar(progressData.progress);
        this.updateStatusMessage(progressData.message);
        
        // Show partial results if available
        if (progressData.partial_results) {
            this.showPartialResults(progressData.partial_results);
        }
    }
    
    handleComplete(results) {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        if (this.completeCallback) {
            this.completeCallback(results);
        }
        
        // Hide progress bar, show final results
        this.hideProgressBar();
        this.showFinalResults(results);
    }
    
    handleError(error) {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        console.error('Citation analysis error:', error);
        this.hideProgressBar();
        this.showError(error);
    }
    
    updateProgressBar(progress) {
        const progressBar = document.getElementById('citation-progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }
        
        const progressText = document.getElementById('progress-text');
        if (progressText) {
            progressText.textContent = `${Math.round(progress)}%`;
        }
    }
    
    updateStatusMessage(message) {
        const statusElement = document.getElementById('progress-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }
    
    showPartialResults(partialResults) {
        // Show citations as they're found
        const partialContainer = document.getElementById('partial-results');
        if (partialContainer && partialResults.length > 0) {
            partialResults.forEach(citation => {
                const citationElement = this.createCitationElement(citation);
                partialContainer.appendChild(citationElement);
            });
        }
    }
    
    createCitationElement(citation) {
        const div = document.createElement('div');
        div.className = 'citation-preview';
        div.innerHTML = `
            <div class="citation-case-name">${citation.case_name || 'Unknown Case'}</div>
            <div class="citation-details">
                <span class="year">${citation.year || 'No year'}</span>
                <span class="confidence">Confidence: ${Math.round((citation.confidence_score || 0) * 100)}%</span>
            </div>
        `;
        return div;
    }
    
    hideProgressBar() {
        const progressContainer = document.getElementById('progress-container');
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    }
    
    showFinalResults(results) {
        const resultsContainer = document.getElementById('final-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = this.formatFinalResults(results);
            resultsContainer.style.display = 'block';
        }
    }
    
    formatFinalResults(results) {
        return `
            <h3>Citation Analysis Complete</h3>
            <p>Found ${results.results.length} citations</p>
            <div class="citations-list">
                ${results.results.map(citation => this.formatCitation(citation)).join('')}
            </div>
        `;
    }
    
    showError(error) {
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
            errorContainer.style.display = 'block';
        }
    }
}

// Usage example
const tracker = new CitationProgressTracker();

document.getElementById('analyze-button').addEventListener('click', () => {
    const documentText = document.getElementById('document-text').value;
    const documentType = document.getElementById('document-type').value;
    
    // Show progress container
    document.getElementById('progress-container').style.display = 'block';
    
    tracker.startAnalysisWithSSE(
        documentText,
        documentType,
        // Progress callback
        (progressData) => {
            console.log('Progress:', progressData);
        },
        // Complete callback
        (results) => {
            console.log('Analysis complete:', results);
        }
    );
});
'''

# SOLUTION 6: Configuration and Setup
# ============================================================================

def process_citation_task_direct(task_id: str, input_type: str, input_data: dict):
    """
    Process citation task directly (for use with RQ workers).
    
    Args:
        task_id: Unique task ID
        input_type: Type of input ('text', 'url', 'file')
        input_data: Dictionary containing the input data
        
    Returns:
        Dictionary with processing results
    """
    from src.unified_input_processor import UnifiedInputProcessor
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"[Task {task_id}] Starting direct citation processing for {input_type}")
    
    try:
        # Initialize processor
        processor = UnifiedInputProcessor()
        
        # Process based on input type
        if input_type == 'text':
            text = input_data.get('text', '')
            if not text:
                raise ValueError("No text provided for processing")
                
            result = processor.process_any_input(
                input_data=text,
                input_type='text',
                request_id=task_id
            )
            
            return {
                'success': True,
                'task_id': task_id,
                'status': 'completed',
                'result': result
            }
            
        else:
            raise ValueError(f"Unsupported input type for direct processing: {input_type}")
            
    except Exception as e:
        logger.error(f"[Task {task_id}] Error in direct citation processing: {str(e)}", exc_info=True)
        return {
            'success': False,
            'task_id': task_id,
            'status': 'failed',
            'error': str(e)
        }


def setup_progress_enabled_app():
    """Complete setup example for progress-enabled citation processing"""
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize progress manager
    progress_manager = SSEProgressManager()
    
    # Initialize citation processor
    citation_processor = ChunkedCitationProcessor(progress_manager)
    
    # Create routes
    create_progress_routes(app, progress_manager, citation_processor)
    
    return app

# Example usage
if __name__ == "__main__":
    app = setup_progress_enabled_app()
    # Only enable debug mode in development
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, threaded=True)  # nosec B201 - Debug mode is environment-controlled


# Configuration for different deployment scenarios
PROGRESS_CONFIG = {
    'sse': {
        'description': 'Server-Sent Events - Best for most cases',
        'pros': ['Simple to implement', 'Works with load balancers', 'Automatic reconnection'],
        'cons': ['HTTP/1.1 connection limit', 'Some proxy issues'],
        'recommended_for': 'Most web applications'
    },
    'websockets': {
        'description': 'WebSocket - Best for real-time applications',
        'pros': ['Full bidirectional', 'Lower latency', 'More efficient'],
        'cons': ['More complex', 'Load balancer challenges', 'Sticky sessions needed'],
        'recommended_for': 'Real-time collaborative features'
    },
    'polling': {
        'description': 'HTTP Polling - Most compatible fallback',
        'pros': ['Universal compatibility', 'Simple to implement', 'Works everywhere'],
        'cons': ['Higher server load', 'Delayed updates', 'Less efficient'],
        'recommended_for': 'Fallback mechanism'
    }
} 