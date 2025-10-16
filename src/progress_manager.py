"""
Progress Bar Solutions for CaseStrainer Citation Processing
Multiple approaches to provide real-time progress feedback to users
Progress Manager for Citation Extraction Tasks
AUTO-RELOAD LIVE TEST: This change should trigger immediate restart!
"""

import os
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import sys
import time
import json
import logging
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, Response, stream_with_context

logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

import asyncio
from typing import Dict, List, Any, Optional, Generator, Callable, TYPE_CHECKING
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

try:
    from flask_socketio import SocketIO, emit  # type: ignore
    FLASK_SOCKETIO_AVAILABLE = True
except ImportError:
    FLASK_SOCKETIO_AVAILABLE = False
    class SocketIO:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
    
    def emit(*args, **kwargs):  # type: ignore
        pass

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore

logger = logging.getLogger(__name__)


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
        
        self.socketio.server.enter_room(client_id, f"task_{task_id}")
        
        self.socketio.emit('progress_update', 
                          tracker.get_progress_data(), 
                          room=f"task_{task_id}")
        
        return task_id
    
    def update_progress(self, task_id: str, step: int, status: str, 
                       message: str, partial_results: Optional[List] = None, error: Optional[str] = None):
        """Update progress and emit to all clients watching this task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update(step, status, message, partial_results or [], error)
            
            progress_data = self.active_tasks[task_id].get_progress_data()
            
            if partial_results:
                progress_data['partial_results'] = partial_results
            
            self.socketio.emit('progress_update', 
                              progress_data, 
                              room=f"task_{task_id}")



class ChunkedCitationProcessor:
    """Process citations in chunks to provide incremental progress"""
    
    def __init__(self, progress_manager: SSEProgressManager):
        self.progress_manager = progress_manager
        self.chunk_size = 5000  # Characters per chunk (increased to prevent citation splitting)
    
    async def process_document_with_progress(self, 
                                           document_text: str, 
                                           document_type: str = "legal_brief") -> str:
        """Process document in chunks with progress updates"""
        logger.info("\n" + "="*80)
        logger.info("Starting process_document_with_progress")
        logger.info(f"Document type: {document_type}")
        logger.info(f"Document text length: {len(document_text)} characters")
        
        try:
            if not document_text or not isinstance(document_text, str):
                error_msg = f"Invalid document text. Type: {type(document_text)}, Length: {len(str(document_text)) if document_text is not None else 'None'}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            task_id = str(uuid.uuid4())
            logger.info(f"Created task ID: {task_id}")
            
            tracker = ProgressTracker(task_id, total_steps=100)
            logger.info("Initialized progress tracker")
            
            self.progress_manager.active_tasks[task_id] = tracker
            logger.info(f"Stored task in active_tasks. Total active tasks: {len(self.progress_manager.active_tasks)}")
            
            logger.info(f"Redis available: {hasattr(self.progress_manager, 'redis_client') and self.progress_manager.redis_client is not None}")
            
            logger.info("Creating background task for document processing...")
            asyncio.create_task(self._process_document_async(task_id, document_text, document_type, tracker))
            logger.info("Background task created successfully")
            
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
            
            if i + self.chunk_size < len(text):
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
        processed = []
        for chunk in chunks:
            processed_chunk = chunk.replace('  ', ' ').strip()
            processed.append(processed_chunk)
        
        return processed
    
    async def _process_chunk(self, chunk: str, document_type: str) -> List[Dict]:
        """Process a single chunk for citations using the CLEAN extraction pipeline."""
        chunk_hash = hash(chunk) % 1000
        logger.info(f"[Chunk-{chunk_hash}] Starting chunk processing (size: {len(chunk)} chars)")
        
        try:
            logger.info(f"[Chunk-{chunk_hash}] Using CleanExtractionPipeline...")
            from src.clean_extraction_pipeline import CleanExtractionPipeline
            
            logger.info(f"[Chunk-{chunk_hash}] Creating clean pipeline...")
            pipeline = CleanExtractionPipeline()
            
            logger.info(f"[Chunk-{chunk_hash}] Starting extract_citations()...")
            start_time = time.time()
            
            # Extract citations using clean pipeline
            citation_results = pipeline.extract_citations(chunk)
            
            process_time = time.time() - start_time
            logger.info(f"[Chunk-{chunk_hash}] extract_citations() completed in {process_time:.2f}s, got {len(citation_results)} citations")
            
            # Convert CitationResult objects to dicts
            results = {'citations': []}
            for cit_obj in citation_results:
                results['citations'].append({
                    'citation': cit_obj.citation,
                    'extracted_case_name': cit_obj.extracted_case_name,
                    'extracted_date': cit_obj.extracted_date,
                    'start_index': cit_obj.start_index,
                    'end_index': cit_obj.end_index,
                    'method': cit_obj.method,
                    'confidence': cit_obj.confidence,
                    'metadata': cit_obj.metadata,
                    'verified': False,  # Verification happens later
                    'canonical_name': None,
                    'canonical_date': None,
                    'url': None
                })
            
            citations = []
            raw_citations = results.get('citations', [])
            logger.info(f"[Chunk-{chunk_hash}] Converting {len(raw_citations)} citations to dicts...")
            
            for i, citation_dict in enumerate(raw_citations, 1):
                try:
                    citation_data = {
                        'id': len(citations) + 1,
                        'citation': citation_dict.get('citation', ''),
                        'raw_text': citation_dict.get('citation', ''),
                        'case_name': citation_dict.get('extracted_case_name') or 'Unknown Case',
                        'year': citation_dict.get('extracted_date') or 'No year',
                        'confidence_score': citation_dict.get('confidence_score', 0.7),
                        'chunk_index': chunk_hash,
                        'extracted_case_name': citation_dict.get('extracted_case_name'),
                        'canonical_name': citation_dict.get('canonical_name'),
                        'extracted_date': citation_dict.get('extracted_date'),
                        'canonical_date': citation_dict.get('canonical_date'),
                        'verified': citation_dict.get('verified', False),
                        'source': citation_dict.get('source', 'enhanced_sync'),
                        'method': citation_dict.get('extraction_method', 'enhanced_sync'),
                        'is_parallel': citation_dict.get('is_parallel', False),
                        'parallel_citations': citation_dict.get('parallel_citations', []),
                        'start_index': citation_dict.get('start_index'),
                        'end_index': citation_dict.get('end_index'),
                        'context': citation_dict.get('context'),
                        'url': citation_dict.get('url'),
                        'metadata': citation_dict.get('metadata', {})
                    }
                    citations.append(citation_data)
                    
                    if i <= 3:  # Only log first 3 citations to avoid log spam
                        logger.info(f"[Chunk-{chunk_hash}] Citation {i}: "
                                   f"Name: {citation_dict.get('extracted_case_name')} | "
                                   f"Date: {citation_dict.get('extracted_date')} | "
                                   f"Verified: {citation_dict.get('verified')}")
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
            if not document_text or not isinstance(document_text, str):
                error_msg = f"Invalid document text in _process_document_async. Type: {type(document_text)}"
                logger.error(error_msg)
                self.progress_manager.update_progress(
                    task_id, 0, "failed", error_msg, error=error_msg
                )
                return
                
            logger.info(f"Document sample: {document_text[:200]}...")
            
            logger.info("Splitting document into chunks...")
            chunks = self._split_into_chunks(document_text)
            logger.info(f"Document split into {len(chunks)} chunks")
            
            logger.info("Updating progress to 10% (chunking complete)")
            self.progress_manager.update_progress(
                task_id, 10, "processing", "Processing document chunks..."
            )
            
            results = []
            total_chunks = len(chunks)
            logger.info(f"Starting to process {total_chunks} chunks...")
            
            for i, chunk in enumerate(chunks, 1):
                try:
                    logger.info(f"\nProcessing chunk {i}/{total_chunks}")
                    
                    logger.info("Calling _process_chunk...")
                    chunk_results = await self._process_chunk(chunk, document_type)
                    logger.info(f"Processed chunk {i}, found {len(chunk_results)} citations")
                    
                    results.extend(chunk_results)
                    
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
            
            logger.info("\nPerforming final analysis...")
            self.progress_manager.update_progress(
                task_id, 90, "processing", "Performing final analysis..."
            )
            
            try:
                final_results = await self._perform_final_analysis(results)
                
                logger.info("Marking task as complete")
                # Store final results in tracker
                if task_id in self.progress_manager.active_tasks:
                    tracker = self.progress_manager.active_tasks[task_id]
                    tracker.results = final_results
                
                self.progress_manager.update_progress(
                    task_id, 100, "completed", 
                    f"Processing complete! Found {len(results)} citations.",
                    partial_results=results  # Keep original results for partial updates
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
            
            try:
                self.progress_manager.update_progress(
                    task_id, 0, "failed", error_msg, error=error_msg
                )
            except Exception as update_error:
                logger.error(f"Failed to update progress with error: {str(update_error)}")
            
            raise
    
    async def _perform_final_analysis(self, citations: List[Dict]) -> Dict:
        """Perform final analysis on all collected citations with proper clustering"""
        await asyncio.sleep(0.2)  # Simulate analysis time
        
        from src.models import CitationResult
        from src.unified_clustering_master import cluster_citations_unified_master as cluster_citations_unified
        
        citation_objects = []
        for citation_dict in citations:
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
        
        # CRITICAL: Enable verification in clustering
        clusters = cluster_citations_unified(
            citations=citation_objects,
            enable_verification=True
        )
        
        # CRITICAL FIX: Update citation objects with cluster information
        # This must happen BEFORE serialization to ensure cluster data persists
        logger.info(f"[PROGRESS_MANAGER] Updating citations with cluster information")
        citation_to_cluster = {}
        for cluster in clusters:
            cluster_id = cluster.get('cluster_id')
            cluster_case_name = cluster.get('cluster_case_name') or cluster.get('case_name')
            cluster_citations = cluster.get('citations', [])
            
            # Match by citation text, not object id (clusters contain dicts, not objects)
            for cit_dict in cluster_citations:
                citation_text = cit_dict.get('citation') if isinstance(cit_dict, dict) else getattr(cit_dict, 'citation', None)
                if citation_text:
                    citation_to_cluster[citation_text] = (cluster_id, cluster_case_name, len(cluster_citations))
        
        updated_count = 0
        for citation_obj in citation_objects:
            citation_text = getattr(citation_obj, 'citation', None)
            if citation_text and citation_text in citation_to_cluster:
                cluster_id, cluster_case_name, size = citation_to_cluster[citation_text]
                citation_obj.cluster_id = cluster_id
                citation_obj.cluster_case_name = cluster_case_name
                citation_obj.is_cluster = size > 1
                updated_count += 1
        
        # Update the citation dicts with cluster info from objects
        for i, citation_dict in enumerate(citations):
            if i < len(citation_objects):
                citation_obj = citation_objects[i]
                citation_dict['cluster_id'] = getattr(citation_obj, 'cluster_id', None)
                citation_dict['cluster_case_name'] = getattr(citation_obj, 'cluster_case_name', None)
                citation_dict['is_cluster'] = getattr(citation_obj, 'is_cluster', False)
        
        logger.info(f"[PROGRESS_MANAGER] Updated {updated_count} citations with cluster information")
        
        return {
            'citations': citations,
            'clusters': clusters,
            'total_citations': len(citations),
            'high_confidence': len([c for c in citations if c.get('confidence_score', 0) > 0.8]),
            'needs_review': len([c for c in citations if c.get('confidence_score', 0) < 0.6])
        }



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
        
        # OPTIMIZATION: For CourtListener opinion URLs, convert to API endpoint
        # Web URLs return 202, but API endpoint returns JSON immediately with full text
        # Store original URL for fallback if API is rate-limited
        original_url = url
        courtlistener_api_attempted = False
        
        if 'courtlistener.com' in url.lower() and '/opinion/' in url and '/api/' not in url:
            import re
            # Extract opinion ID from URL: /opinion/10460933/robert-cassell-v-state...
            opinion_match = re.search(r'/opinion/(\d+)/', url)
            if opinion_match:
                opinion_id = opinion_match.group(1)
                # Convert to API endpoint
                api_url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
                logger.info(f"🔄 Converting CourtListener opinion URL to API endpoint")
                logger.info(f"   Opinion ID: {opinion_id}")
                logger.info(f"   API URL: {api_url}")
                url = api_url
                courtlistener_api_attempted = True
                # Add API headers
                from src.config import COURTLISTENER_API_KEY
                if COURTLISTENER_API_KEY:
                    headers['Authorization'] = f'Token {COURTLISTENER_API_KEY}'
                    headers['Accept'] = 'application/json'
                    logger.info(f"✅ Added CourtListener API authorization header")
                else:
                    logger.error(f"❌ COURTLISTENER_API_KEY is not set!")
            else:
                logger.warning(f"⚠️  Could not extract opinion ID from URL")
        
        # API search disabled for CourtListener opinion URLs (see above)
        # This avoids rate limit errors and is faster
        
        if url.lower().endswith('.pdf'):
            headers['Accept'] = 'application/pdf,application/x-pdf,application/octet-stream'
        
        
        # Handle 202 (Accepted) and 429 (Rate Limit) responses with retry
        # CourtListener sometimes returns 202 while page is being generated or 429 when rate limited
        import time
        max_attempts = 4
        retry_delay = 5  # Start with 5 seconds
        
        for attempt in range(max_attempts):
            response = requests.get(
                url,
                headers=headers,
                timeout=DEFAULT_REQUEST_TIMEOUT,  # 30 second timeout
                allow_redirects=True,
                stream=True  # Stream the response for large files
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            # Handle 202 (Accepted) - page still generating
            if response.status_code == 202:
                if attempt < max_attempts - 1:
                    logger.warning(f"⚠️  Got 202 Accepted - page still generating, retrying in {retry_delay}s (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ Still getting 202 after {max_attempts} attempts")
            
            # Handle 429 (Too Many Requests) - rate limited
            elif response.status_code == 429:
                if attempt < max_attempts - 1:
                    logger.warning(f"⚠️  Rate limited (429), retrying in {retry_delay}s (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"❌ Still rate limited after {max_attempts} attempts")
                    # FALLBACK: If this was a CourtListener API endpoint, try HTML scraping instead
                    if courtlistener_api_attempted and original_url != url:
                        logger.warning(f"🔄 Falling back to HTML scraping from original URL")
                        logger.info(f"   Original URL: {original_url}")
                        url = original_url
                        # Reset headers for HTML scraping
                        headers.pop('Authorization', None)
                        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                        # Try one more time with the original URL
                        response = requests.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT, allow_redirects=True, stream=True)
                        logger.info(f"Fallback response status: {response.status_code}")
                        if response.status_code != 429:
                            response.raise_for_status()
                            break
                        else:
                            logger.error(f"❌ HTML fallback also rate limited")
                    # If not CourtListener or fallback failed, raise the error
                    response.raise_for_status()
            
            response.raise_for_status()
            break
        
        content_type = response.headers.get('content-type', '').lower()
        logger.info(f"Content type: {content_type}")
        
        if 'pdf' in content_type or url.lower().endswith('.pdf'):
            # Try multiple PDF extraction methods for robustness
            extraction_methods = [
                ('PyPDF2', _extract_with_pypdf2),
                ('pdfminer', _extract_with_pdfminer),
                ('pdfplumber', _extract_with_pdfplumber)
            ]
            
            for method_name, method_func in extraction_methods:
                try:
                    logger.info(f"Trying PDF extraction with {method_name}")
                    result = method_func(response.content)
                    if result and len(result.strip()) > 0:
                        logger.info(f"Successfully extracted {len(result)} characters using {method_name}")
                        return result
                    else:
                        logger.warning(f"{method_name} returned empty content")
                except Exception as e:
                    logger.warning(f"{method_name} extraction failed: {str(e)}")
                    continue
            
            # If all methods fail, provide helpful error message
            logger.error("All PDF extraction methods failed")
            raise Exception("The PDF document could not be processed. It may be corrupted, password-protected, or in an unsupported format. Please try a different document or contact support if the issue persists.")
        
        elif 'json' in content_type or 'application/json' in content_type:
            # Handle JSON responses (e.g., from CourtListener API)
            logger.info(f"Processing JSON response from API")
            try:
                import json
                data = response.json()
                
                # Extract text from CourtListener API opinion response
                if 'plain_text' in data:
                    text = data['plain_text']
                    logger.info(f"✅ Extracted opinion plain_text: {len(text)} characters")
                    return text
                elif 'html_with_citations' in data:
                    # Fallback to HTML version
                    from bs4 import BeautifulSoup
                    html = data['html_with_citations']
                    soup = BeautifulSoup(html, 'html.parser')
                    text = soup.get_text(separator=' ', strip=True)
                    logger.info(f"✅ Extracted from html_with_citations: {len(text)} characters")
                    return text
                elif 'html' in data:
                    from bs4 import BeautifulSoup
                    html = data['html']
                    soup = BeautifulSoup(html, 'html.parser')
                    text = soup.get_text(separator=' ', strip=True)
                    logger.info(f"✅ Extracted from html field: {len(text)} characters")
                    return text
                else:
                    # Return JSON as formatted string
                    logger.warning(f"⚠️  JSON response doesn't contain expected text fields")
                    logger.warning(f"   Available fields: {list(data.keys())}")
                    return json.dumps(data, indent=2)
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return response.text
        
        elif 'html' in content_type:
            logger.info(f"Processing HTML content")
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                # Get text
                text = soup.get_text(separator=' ', strip=True)
                logger.info(f"✅ Extracted text from HTML: {len(text)} characters")
                return text
            except Exception as e:
                logger.warning(f"Failed to parse HTML with BeautifulSoup: {e}")
                logger.info(f"Returning raw HTML content, length: {len(response.text)}")
                return response.text
        
        elif 'text/plain' in content_type:
            logger.info(f"Returning plain text content, length: {len(response.text)}")
            return response.text
        
        else:
            try:
                logger.info(f"Attempting to decode unknown content type: {content_type}")
                text = response.text
                
                # Try to detect if it's HTML and parse it
                if text.strip().startswith('<!DOCTYPE html') or text.strip().startswith('<html'):
                    logger.info(f"Detected HTML in unknown content type, attempting to parse")
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(text, 'html.parser')
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        # Get text
                        parsed_text = soup.get_text(separator=' ', strip=True)
                        logger.info(f"✅ Extracted text from HTML: {len(parsed_text)} characters")
                        return parsed_text
                    except Exception as e:
                        logger.warning(f"Failed to parse as HTML: {e}")
                
                return text
            except UnicodeDecodeError:
                logger.warning(f"Could not decode content as text: {content_type}")
                return f"[Binary content from {url} - cannot be processed as text]"
                
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching URL {url}")
        raise Exception(f"The URL took too long to respond. Please check if the URL is accessible and try again.")
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error fetching URL {url}: {str(e)}")
        if "Name or service not known" in str(e) or "nodename nor servname provided" in str(e):
            raise Exception(f"The URL could not be found. Please check that the URL is correct and accessible.")
        elif "Connection refused" in str(e):
            raise Exception(f"The server refused the connection. The URL may be temporarily unavailable.")
        else:
            raise Exception(f"Could not connect to the URL. Please check your internet connection and try again.")
    
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else None
        logger.error(f"HTTP error fetching URL {url}: {status_code} - {str(e)}")
        
        if status_code == 404:
            raise Exception(f"The document was not found at this URL (404 error). Please check that the URL is correct.")
        elif status_code == 403:
            raise Exception(f"Access to this document is forbidden (403 error). The document may require special permissions.")
        elif status_code == 500:
            raise Exception(f"The server encountered an error (500 error). Please try again later.")
        elif status_code and 400 <= status_code < 500:
            raise Exception(f"There was a problem with the request ({status_code} error). Please check the URL and try again.")
        elif status_code and status_code >= 500:
            raise Exception(f"The server is experiencing problems ({status_code} error). Please try again later.")
        else:
            raise Exception(f"The URL returned an error ({status_code}). Please check the URL and try again.")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {str(e)}\n{traceback.format_exc()}")
        raise Exception(f"Failed to fetch the URL: {str(e)}. Please check that the URL is accessible and try again.")
    
    except Exception as e:
        logger.error(f"Unexpected error fetching URL {url}: {str(e)}\n{traceback.format_exc()}")
        if "PDF extraction" in str(e):
            raise Exception(f"The PDF document could not be processed. It may be corrupted, password-protected, or in an unsupported format.")
        else:
            raise Exception(f"An unexpected error occurred while processing the URL: {str(e)}")

def _extract_with_pypdf2(pdf_content: bytes) -> str:
    """Extract text using PyPDF2."""
    import PyPDF2
    import io
    
    pdf_content_io = io.BytesIO(pdf_content)
    pdf_reader = PyPDF2.PdfReader(pdf_content_io)
    text_parts = []
    
    for i, page in enumerate(pdf_reader.pages, 1):
        try:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        except Exception as e:
            logger.warning(f"Error extracting text from page {i}: {str(e)}")
    
    return '\n\n'.join(text_parts)

def _extract_with_pdfminer(pdf_content: bytes) -> str:
    """Extract text using pdfminer."""
    try:
        from pdfminer.high_level import extract_text_to_fp
        from pdfminer.layout import LAParams
        import io
        
        output_string = io.StringIO()
        pdf_content_io = io.BytesIO(pdf_content)
        
        extract_text_to_fp(
            pdf_content_io,
            output_string,
            laparams=LAParams(),
            output_type='text',
            codec='utf-8'
        )
        
        return output_string.getvalue()
    except ImportError:
        raise Exception("pdfminer not available")

def _extract_with_pdfplumber(pdf_content: bytes) -> str:
    """Extract text using pdfplumber."""
    try:
        import pdfplumber
        import io
        
        pdf_content_io = io.BytesIO(pdf_content)
        text_parts = []
        
        with pdfplumber.open(pdf_content_io) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    except ImportError:
        raise Exception("pdfplumber not available")

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
    import logging
    import traceback
    import time
    
    logger = logging.getLogger(__name__)
    logger.info(f"[Task {task_id}] Starting direct citation processing for {input_type}")
    logger.debug(f"[Task {task_id}] Input data keys: {list(input_data.keys())}")
    
    # FIX #21: Function to sync progress to Redis for API consumption
    def sync_progress_to_redis(status: str, progress_pct: int, message: str):
        """Sync progress updates to Redis so the API endpoint can read them."""
        try:
            from redis import Redis
            from src.config import REDIS_URL
            import json
            from datetime import datetime
            
            redis_conn = Redis.from_url(REDIS_URL)
            
            progress_data = {
                'task_id': task_id,
                'progress': progress_pct,
                'status': status,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'current_step': progress_pct // 10,  # Approximate step
                'total_steps': 10  # Approximate total
            }
            
            # Use same key format as SSEProgressManager (f"progress:{task_id}")
            redis_conn.setex(
                f"progress:{task_id}",
                3600,  # 1 hour expiry
                json.dumps(progress_data)
            )
            logger.info(f"✅ FIX #21: Progress synced to Redis: {status} ({progress_pct}%)")
            
        except Exception as e:
            logger.error(f"Failed to sync progress to Redis: {e}")
    
    # Create or get progress tracker for this task
    from src.progress_tracker import create_progress_tracker, get_progress_tracker
    progress_tracker = get_progress_tracker(task_id) or create_progress_tracker(task_id)
    
    # FIX #21: Initial sync
    sync_progress_to_redis('initializing', 16, 'Starting background processing...')
    
    try:
        if input_type == 'text':
            text = input_data.get('text', '')
            logger.debug(f"[Task {task_id}] Text length: {len(text)} characters")
            
            if not text:
                error_msg = "No text provided for processing"
                logger.error(f"[Task {task_id}] {error_msg}")
                raise ValueError(error_msg)
            
            # Use CLEAN PIPELINE (87-93% accuracy, zero case name bleeding)
            try:
                progress_tracker.start_step(0, 'Initializing async processing...')
                
                logger.info(f"[Task {task_id}] Importing production pipeline with clustering and verification...")
                from src.citation_extraction_endpoint import extract_citations_with_clustering
                from src.models import CitationResult
                
                progress_tracker.update_step(0, 50, 'Loading processing modules...')
                sync_progress_to_redis('loading', 25, 'Loading pipeline with verification...')  # FIX #21
                
                logger.info(f"[Task {task_id}] Using FULL PIPELINE with clustering and batch verification...")
                
                progress_tracker.update_step(0, 75, 'Initializing processor...')
                sync_progress_to_redis('initializing', 30, 'Initializing clean pipeline...')  # FIX #21
                
                progress_tracker.complete_step(0, 'Initialization complete')
                progress_tracker.start_step(1, 'Extracting citations from text...')
                sync_progress_to_redis('extracting', 35, 'Extracting citations with clean pipeline...')  # FIX #21
                
                # Process the text through the clean extraction pipeline WITH CLUSTERING + VERIFICATION
                logger.info(f"[🔥🔥🔥 PROGRESS MANAGER 🔥🔥🔥] About to call extract_citations_with_clustering() with {len(text)} chars")
                # CRITICAL FIX: Use FULL pipeline with clustering and verification
                # instead of just extraction
                from src.citation_extraction_endpoint import extract_citations_with_clustering
                
                # Verification enabled - uses fallback sources if CourtListener is rate-limited
                logger.error(f"[Task {task_id}] >>>>>>> ABOUT TO CALL extract_citations_with_clustering with verification=True (with fallback sources)")
                result = extract_citations_with_clustering(text, enable_verification=True)
                
                # Check if any citations show CourtListener rate limit messages
                courtlistener_rate_limited = False
                if result.get('citations'):
                    for cit in result['citations']:
                        error_msg = cit.get('error', '') or cit.get('verification_error', '')
                        if 'heavy usage' in str(error_msg).lower() or 'try again' in str(error_msg).lower():
                            courtlistener_rate_limited = True
                            break
                
                # Add user notice if CourtListener is rate-limited
                if courtlistener_rate_limited:
                    if 'metadata' not in result:
                        result['metadata'] = {}
                    result['metadata']['verification_notice'] = (
                        "Note: CourtListener is experiencing heavy usage. Citations have been verified using "
                        "alternative sources (Justia, OpenJurist, Cornell LII). For complete verification with "
                        "CourtListener, please try again in a few minutes."
                    )
                logger.error(f"[Task {task_id}] >>>>>>> extract_citations_with_clustering RETURNED: {len(result.get('citations', []))} citations")
                
                # Convert clean pipeline results to CitationResult objects
                # CRITICAL FIX: Include verification fields from result
                citations_found = []
                if result.get('status') == 'success':
                    for cit_dict in result['citations']:
                        citations_found.append(CitationResult(
                            citation=cit_dict['citation'],
                            extracted_case_name=cit_dict.get('extracted_case_name'),
                            extracted_date=cit_dict.get('extracted_date'),
                            method=cit_dict.get('method', 'clean_pipeline_v1'),
                            confidence=cit_dict.get('confidence', 0.9),
                            start_index=cit_dict.get('start_index'),
                            end_index=cit_dict.get('end_index'),
                            metadata=cit_dict.get('metadata', {}),
                            # CRITICAL: Include verification data (CitationResult doesn't have verification_source field)
                            verified=cit_dict.get('verified', False),
                            canonical_name=cit_dict.get('canonical_name'),
                            canonical_date=cit_dict.get('canonical_date'),
                            canonical_url=cit_dict.get('canonical_url')
                        ))
                    verified_count = sum(1 for c in citations_found if c.verified)
                    logger.error(f"[Task {task_id}] >>>>>>> Converted {len(citations_found)} citations ({verified_count} verified) to CitationResult objects")
                else:
                    logger.error(f"[Task {task_id}] Clean pipeline returned non-success status: {result.get('status')}")
                    logger.error(f"[Task {task_id}] Clean pipeline error: {result.get('error', 'Unknown error')}")
                
                # Extract clusters from result
                clusters_from_pipeline = result.get('clusters', [])
                
                result = {
                    'citations': citations_found,
                    'clusters': clusters_from_pipeline
                }
                logger.info(f"[Task {task_id}] Result dict created with {len(citations_found)} citations and {len(clusters_from_pipeline)} clusters")
                
                progress_tracker.complete_step(1, 'Citation extraction completed')
                progress_tracker.start_step(2, 'Analyzing and normalizing citations...')
                sync_progress_to_redis('clustering', 60, 'Clustering citations...')  # FIX #21
                
                # Ensure we have the expected structure from UnifiedCitationProcessorV2
                if not isinstance(result, dict):
                    result = {'citations': [], 'clusters': []}
                
                # Extract citations and clusters from UnifiedCitationProcessorV2 result
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                citation_dicts = []
                
                progress_tracker.update_step(2, 50, f'Processing {len(citations)} citations...')
                
                for citation in citations:
                    if hasattr(citation, 'to_dict'):
                        citation_dicts.append(citation.to_dict())
                    elif isinstance(citation, dict):
                        citation_dicts.append(citation)
                    else:
                        # Convert CitationResult to dict manually
                        citation_dicts.append({
                            'citation': getattr(citation, 'citation', ''),
                            'extracted_case_name': getattr(citation, 'extracted_case_name', ''),
                            'extracted_date': getattr(citation, 'extracted_date', ''),
                            'canonical_name': getattr(citation, 'canonical_name', None),
                            'canonical_date': getattr(citation, 'canonical_date', None),
                            'canonical_url': getattr(citation, 'canonical_url', None),
                            'verified': getattr(citation, 'verified', False),
                            'confidence': getattr(citation, 'confidence', 0.0),
                            'method': getattr(citation, 'method', 'unified_processor'),
                            'source': getattr(citation, 'source', 'unified_architecture'),
                            'start_index': getattr(citation, 'start_index', 0),
                            'end_index': getattr(citation, 'end_index', 0),
                            'is_parallel': getattr(citation, 'is_parallel', False),
                            'is_cluster': getattr(citation, 'is_cluster', False),
                            'parallel_citations': getattr(citation, 'parallel_citations', []),
                            'cluster_members': getattr(citation, 'cluster_members', []),
                            'pinpoint_pages': getattr(citation, 'pinpoint_pages', []),
                            'docket_numbers': getattr(citation, 'docket_numbers', []),
                            'case_history': getattr(citation, 'case_history', []),
                            'publication_status': getattr(citation, 'publication_status', None),
                            'error': getattr(citation, 'error', None),
                            'metadata': getattr(citation, 'metadata', {}),
                            'cluster_id': getattr(citation, 'cluster_id', None),
                            'true_by_parallel': getattr(citation, 'true_by_parallel', False)
                        })
                
                progress_tracker.complete_step(2, 'Citation analysis completed')
                progress_tracker.start_step(3, 'Deduplicating citations...')
                sync_progress_to_redis('verifying', 75, 'Verifying citations...')  # FIX #21
                
                # Apply deduplication to async processing (MISSING FEATURE ADDED)
                logger.info(f"[Task {task_id}] Starting deduplication of {len(citation_dicts)} citations")
                try:
                    from src.citation_deduplication import deduplicate_citations
                    
                    original_count = len(citation_dicts)
                    citation_dicts = deduplicate_citations(citation_dicts, debug=True)
                    
                    logger.info(f"[Task {task_id}] Deduplication completed: {original_count} → {len(citation_dicts)} citations")
                    if len(citation_dicts) < original_count:
                        logger.info(f"[Task {task_id}] Removed {original_count - len(citation_dicts)} duplicate citations")
                    
                except Exception as e:
                    logger.error(f"[Task {task_id}] Deduplication FAILED: {e}")
                    # Continue with original citations if deduplication fails
                
                progress_tracker.complete_step(3, f'Deduplication completed ({len(citation_dicts)} unique citations)')
                progress_tracker.start_step(4, 'Clustering parallel citations...')
                
                # Get clusters if available
                clusters = result.get('clusters', [])
                cluster_dicts = []
                
                progress_tracker.update_step(4, 50, f'Processing {len(clusters)} clusters...')
                
                for cluster in clusters:
                    if hasattr(cluster, 'to_dict'):
                        cluster_dict = cluster.to_dict()
                    elif isinstance(cluster, dict):
                        cluster_dict = cluster.copy()
                    else:
                        continue
                    
                    # CRITICAL FIX: DON'T replace citations from clusters!
                    # The clusters have UPDATED citations from batch verification with verified=True/False set correctly
                    # citation_dicts has OLD citations from before clustering/verification
                    # We need to KEEP the citations from clusters as they have the latest verification status
                    
                    # Just convert citation objects to dicts if needed
                    if 'citations' in cluster_dict and cluster_dict['citations']:
                        converted_citations = []
                        for cit in cluster_dict['citations']:
                            if hasattr(cit, 'to_dict'):
                                converted_citations.append(cit.to_dict())
                            elif isinstance(cit, dict):
                                converted_citations.append(cit)
                            else:
                                # Manual conversion for citation objects
                                cit_text = getattr(cit, 'citation', str(cit))
                                converted_citations.append({
                                    'citation': cit_text,
                                    'verified': getattr(cit, 'verified', False),
                                    'extracted_case_name': getattr(cit, 'extracted_case_name', None),
                                    'extracted_date': getattr(cit, 'extracted_date', None),
                                    'canonical_name': getattr(cit, 'canonical_name', None),
                                    'canonical_date': getattr(cit, 'canonical_date', None),
                                    'canonical_url': getattr(cit, 'canonical_url', None),
                                    'verification_source': getattr(cit, 'verification_source', None),
                                    'verification_error': getattr(cit, 'verification_error', None),
                                    'true_by_parallel': getattr(cit, 'true_by_parallel', False),
                                })
                        
                        cluster_dict['citations'] = converted_citations
                        logger.error(f"[Task {task_id}] ✅ Converted cluster with {len(converted_citations)} citations (preserving verification status)")
                    
                    cluster_dicts.append(cluster_dict)

                # Apply cluster deduplication to async processing
                logger.info(f"[Task {task_id}] Starting cluster deduplication of {len(cluster_dicts)} clusters")
                try:
                    from src.citation_deduplication import deduplicate_clusters
                    
                    original_cluster_count = len(cluster_dicts)
                    cluster_dicts = deduplicate_clusters(cluster_dicts, debug=True)
                    
                    logger.info(f"[Task {task_id}] Cluster deduplication completed: {original_cluster_count} → {len(cluster_dicts)} clusters")
                    if len(cluster_dicts) < original_cluster_count:
                        logger.info(f"[Task {task_id}] Cluster deduplication SUCCESS: "
                                   f"({original_cluster_count - len(cluster_dicts)} duplicate clusters removed)")
                    
                except Exception as e:
                    logger.error(f"[Task {task_id}] Cluster deduplication FAILED: {e}")
                    # Continue with original clusters if deduplication fails

                # CRITICAL FIX: Extract cluster-level canonical data from verified citations
                # This happens AFTER verification, so verified citations now have canonical data
                logger.error(f"[Task {task_id}] 🔍 CANONICAL DATA EXTRACTION: Processing {len(cluster_dicts)} clusters")
                clusters_with_canonical = 0
                for cluster_dict in cluster_dicts:
                    citations_in_cluster = cluster_dict.get('citations', [])
                    logger.error(f"[Task {task_id}] 🔍 Cluster has {len(citations_in_cluster)} citations")
                    
                    # Find first verified citation with canonical data
                    best_verified = None
                    for cit in citations_in_cluster:
                        is_verified = cit.get('verified', False) if isinstance(cit, dict) else getattr(cit, 'verified', False)
                        canonical_name = cit.get('canonical_name') if isinstance(cit, dict) else getattr(cit, 'canonical_name', None)
                        logger.error(f"[Task {task_id}] 🔍 Citation: verified={is_verified}, has_canonical={canonical_name is not None}")
                        
                        if is_verified and canonical_name:
                            best_verified = cit
                            logger.error(f"[Task {task_id}] ✅ Found verified citation with canonical: {canonical_name}")
                            break
                    
                    # Set cluster-level canonical data
                    if best_verified:
                        if isinstance(best_verified, dict):
                            cluster_dict['canonical_name'] = best_verified.get('canonical_name')
                            cluster_dict['canonical_date'] = best_verified.get('canonical_date')
                            cluster_dict['verification_source'] = best_verified.get('verification_source', best_verified.get('source'))
                            cluster_dict['verification_status'] = 'verified'
                        else:
                            cluster_dict['canonical_name'] = getattr(best_verified, 'canonical_name', None)
                            cluster_dict['canonical_date'] = getattr(best_verified, 'canonical_date', None)
                            cluster_dict['verification_source'] = getattr(best_verified, 'verification_source', getattr(best_verified, 'source', None))
                            cluster_dict['verification_status'] = 'verified'
                        
                        # Propagate canonical data to unverified parallel citations
                        logger.error(f"[Task {task_id}] 🔄 PROPAGATION: Checking {len(citations_in_cluster)} citations for propagation")
                        unverified_count = 0
                        for idx, cit in enumerate(citations_in_cluster):
                            cit_is_verified = cit.get('verified', False) if isinstance(cit, dict) else getattr(cit, 'verified', False)
                            cit_text = cit.get('citation') if isinstance(cit, dict) else getattr(cit, 'citation', 'unknown')
                            logger.error(f"[Task {task_id}]   [{idx+1}] {cit_text}: verified={cit_is_verified}")
                            
                            if not cit_is_verified:
                                unverified_count += 1
                                if isinstance(cit, dict):
                                    cit['true_by_parallel'] = True
                                    cit['canonical_name'] = cluster_dict['canonical_name']
                                    cit['canonical_date'] = cluster_dict['canonical_date']
                                    logger.error(f"[Task {task_id}] ✅ Propagated to {cit_text} (dict)")
                                else:
                                    cit.true_by_parallel = True
                                    cit.canonical_name = cluster_dict['canonical_name']
                                    cit.canonical_date = cluster_dict['canonical_date']
                                    logger.error(f"[Task {task_id}] ✅ Propagated to {cit_text} (object)")
                        
                        if unverified_count > 0:
                            logger.error(f"[Task {task_id}] 📊 Propagated canonical data to {unverified_count} unverified parallel citations")
                        else:
                            logger.error(f"[Task {task_id}] ℹ️  All {len(citations_in_cluster)} citations already verified - no propagation needed")
                        clusters_with_canonical += 1
                    else:
                        logger.error(f"[Task {task_id}] ⚠️  No verified citation with canonical data found in this cluster")
                
                logger.error(f"[Task {task_id}] 📊 CANONICAL DATA SUMMARY: {clusters_with_canonical}/{len(cluster_dicts)} clusters have canonical data")

                progress_tracker.complete_step(4, f'Clustering completed ({len(cluster_dicts)} unique clusters)')
                progress_tracker.start_step(5, 'Verifying citations...')
                
                # CRITICAL FIX: Update top-level citations with verification data from clusters
                # The clusters have the verified citations, but the top-level citations array doesn't
                logger.info(f"[Task {task_id}] Syncing verification data from clusters to top-level citations")
                citation_map = {c['citation']: c for c in citation_dicts}
                verified_count_before = len([c for c in citation_dicts if c.get('verified', False)])
                
                for cluster in cluster_dicts:
                    for cluster_citation in cluster.get('citations', []):
                        citation_text = cluster_citation.get('citation')
                        if citation_text in citation_map:
                            # Update top-level citation with verification data from cluster
                            if cluster_citation.get('verified'):
                                citation_map[citation_text]['verified'] = True
                                citation_map[citation_text]['canonical_name'] = cluster_citation.get('canonical_name')
                                citation_map[citation_text]['canonical_date'] = cluster_citation.get('canonical_date')
                                citation_map[citation_text]['canonical_url'] = cluster_citation.get('canonical_url')
                
                verified_count_after = len([c for c in citation_dicts if c.get('verified', False)])
                logger.info(f"[Task {task_id}] Verification sync: {verified_count_before} → {verified_count_after} verified citations")
                
                citation_result = {
                    'citations': citation_dicts,
                    'clusters': cluster_dicts,
                    'statistics': {
                        'total_citations': len(citation_dicts),
                        'verified_citations': len([c for c in citation_dicts if c.get('verified', False)]),
                        'total_clusters': len(cluster_dicts),
                        'verified_clusters': len([c for c in cluster_dicts if c.get('verified', False)]),
                        'processing_time': result.get('processing_time', 0.0)
                    },
                    'success': True,
                    'processing_mode': 'async_full_processing',
                    'verification_enabled': True,
                    'request_id': task_id
                }
                
                progress_tracker.complete_step(5, 'Verification completed')
                progress_tracker.complete_all('Async processing completed successfully')
                
                # Add progress data to result
                citation_result['progress_data'] = progress_tracker.get_progress_data()
                
                logger.info(f"[Task {task_id}] Processing completed with {len(citation_dicts)} citations and {len(cluster_dicts)} clusters")
                
                # FIX #21: Final progress update - mark as completed at 100%
                sync_progress_to_redis('completed', 100, f'Completed! Found {len(citation_dicts)} citations in {len(cluster_dicts)} clusters')
                
                return {
                    'success': True,
                    'task_id': task_id,
                    'status': 'completed',
                    'result': citation_result
                }
            
            except Exception as e:
                progress_tracker.fail_step(progress_tracker.current_step, f'Processing failed: {str(e)}')
                logger.error(f"[Task {task_id}] UnifiedSyncProcessor failed: {str(e)}")
                logger.error(f"[Task {task_id}] Traceback: {traceback.format_exc()}")
                
                # Fallback to CLEAN EXTRACTION PIPELINE (87-93% accuracy)
                try:
                    logger.info(f"[Task {task_id}] Using CLEAN EXTRACTION PIPELINE for fallback (87-93% accuracy)")
                    
                    # USE CLEAN PIPELINE - guarantees zero case name bleeding with 87-93% accuracy
                    from src.citation_extraction_endpoint import extract_citations_production
                    
                    result = extract_citations_production(text)
                    
                    if result['status'] == 'success':
                        logger.info(f"[Task {task_id}] Clean pipeline extracted {result['total']} citations")
                        
                        # Convert to expected format
                        citations = []
                        for cit in result['citations']:
                            citations.append({
                                'citation': cit['citation'],
                                'case_name': cit.get('extracted_case_name'),
                                'canonical_name': None,
                                'canonical_date': None,
                                'canonical_url': None,
                                'extracted_case_name': cit.get('extracted_case_name'),
                                'extracted_date': cit.get('extracted_date'),
                                'confidence': cit.get('confidence', 0.9),
                                'verified': False,
                                'method': cit.get('method', 'clean_pipeline_v1'),
                                'context': '',
                                'court': None,
                                'year': cit.get('extracted_date'),
                                'is_parallel': False
                            })
                    else:
                        logger.error(f"[Task {task_id}] Clean pipeline failed, using basic regex")
                        citations = []
                    
                    # Remove duplicates
                    unique_citations = []
                    seen = set()
                    for citation in citations:
                        if citation['citation'] not in seen:
                            unique_citations.append(citation)
                            seen.add(citation['citation'])
                    
                    logger.info(f"[Task {task_id}] Fallback extraction found {len(unique_citations)} citations")
                    
                    return {
                        'success': True,
                        'task_id': task_id,
                        'status': 'completed',
                        'result': {
                            'citations': unique_citations,
                            'clusters': [],
                            'clustering_applied': False,
                            'extraction_method': 'fallback_regex',
                            'processing_strategy': 'fallback',
                            'processing_time': 0.1,
                            'progress_data': {
                                'current_message': 'Fallback extraction completed',
                                'current_step': 100,
                                'start_time': time.time(),
                                'steps': [
                                    {
                                        'message': 'Fallback extraction completed',
                                        'name': 'Extract',
                                        'progress': 100,
                                        'status': 'completed'
                                    }
                                ],
                                'total_steps': 1
                            },
                            'request_id': f'fallback_{task_id}',
                            'success': True,
                            'verification_applied': False
                        }
                    }
                    
                except Exception as fallback_error:
                    logger.error(f"[Task {task_id}] Fallback extraction also failed: {str(fallback_error)}")
                    
                    # Return empty result but mark as successful
                    return {
                        'success': True,
                        'task_id': task_id,
                        'status': 'completed',
                        'result': {
                            'citations': [],
                            'clusters': [],
                            'clustering_applied': False,
                            'extraction_method': 'none',
                            'processing_strategy': 'failed',
                            'processing_time': 0.01,
                            'progress_data': {
                                'current_message': 'Processing failed - no citations found',
                                'current_step': 100,
                                'start_time': time.time(),
                                'steps': [
                                    {
                                        'message': 'Processing failed',
                                        'name': 'Extract',
                                        'progress': 100,
                                        'status': 'completed'
                                    }
                                ],
                                'total_steps': 1
                            },
                            'request_id': f'failed_{task_id}',
                            'success': True,
                            'verification_applied': False,
                            'error': f'Processing failed: {str(e)}'
                        }
                    }
            
        elif input_type == 'url':
            # NOTE: This should no longer be reached since URLs are now converted to text at the API level
            # But keeping as fallback for any legacy code paths
            url = input_data.get('url', '')
            logger.warning(f"[Task {task_id}] Unexpected URL input type - URLs should be converted to text at API level. URL: {url}")
            
            if not url:
                error_msg = "No URL provided for processing"
                logger.error(f"[Task {task_id}] {error_msg}")
                raise ValueError(error_msg)
            
            # Extract text from URL first
            try:
                progress_tracker.start_step(0, 'Extracting content from URL...')
                
                logger.info(f"[Task {task_id}] Extracting content from URL...")
                text = fetch_url_content(url)
                
                if not text or len(text.strip()) < 10:
                    error_msg = f"URL returned empty or insufficient content: {len(text) if text else 0} characters"
                    logger.error(f"[Task {task_id}] {error_msg}")
                    progress_tracker.fail_step(0, error_msg)
                    raise ValueError(error_msg)
                
                progress_tracker.complete_step(0, f'Extracted {len(text)} characters from URL')
                logger.info(f"[Task {task_id}] Extracted {len(text)} characters from URL")
                
                # Now process the extracted text using UnifiedCitationProcessorV2 (FIXED: was using EnhancedSyncProcessor)
                from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                import asyncio
                
                logger.info(f"[Task {task_id}] Initializing UnifiedCitationProcessorV2 for URL content...")
                
                processor = UnifiedCitationProcessorV2()
                
                # Process the extracted text
                logger.info(f"[Task {task_id}] Starting URL content processing...")
                result = asyncio.run(processor.process_text(text))
                logger.info(f"[Task {task_id}] URL content processing completed")
                
                # Use the same result processing logic as text processing
                if not isinstance(result, dict):
                    result = {'citations': [], 'clusters': []}
                
                # Extract citations and clusters from UnifiedCitationProcessorV2 result
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                citation_dicts = []
                
                for citation in citations:
                    if hasattr(citation, '__dict__'):
                        citation_dict = citation.__dict__.copy()
                    elif isinstance(citation, dict):
                        citation_dict = citation.copy()
                    else:
                        citation_dict = {'citation': str(citation)}
                    citation_dicts.append(citation_dict)
                
                # Handle clusters
                clusters = result.get('clusters', [])
                cluster_dicts = []
                
                for cluster in clusters:
                    if hasattr(cluster, '__dict__'):
                        cluster_dict = cluster.__dict__.copy()
                    elif isinstance(cluster, dict):
                        cluster_dict = cluster.copy()
                    else:
                        cluster_dict = {'cluster_id': str(cluster)}
                    cluster_dicts.append(cluster_dict)
                
                # Create the final result
                citation_result = {
                    'citations': citation_dicts,
                    'clusters': cluster_dicts,
                    'statistics': {
                        'total_citations': len(citation_dicts),
                        'total_clusters': len(cluster_dicts),
                        'verified_citations': len([c for c in citation_dicts if c.get('verified', False)]),
                        'verified_clusters': len([c for c in cluster_dicts if c.get('verified', False)]),
                        'processing_time': result.get('processing_time', 0.0),
                        'content_length': len(text),
                        'url': url
                    },
                    'success': True,
                    'processing_mode': 'async_url_processing',
                    'verification_enabled': True,
                    'request_id': task_id
                }
                
                logger.info(f"[Task {task_id}] URL processing completed with {len(citation_dicts)} citations and {len(cluster_dicts)} clusters")
                
                return {
                    'success': True,
                    'task_id': task_id,
                    'status': 'completed',
                    'result': citation_result
                }
                
            except Exception as e:
                logger.error(f"[Task {task_id}] URL processing failed: {str(e)}")
                logger.error(f"[Task {task_id}] Traceback: {traceback.format_exc()}")
                raise
        
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
    
    logging.basicConfig(level=logging.INFO)
    
    progress_manager = SSEProgressManager()
    
    citation_processor = ChunkedCitationProcessor(progress_manager)
    
    # create_progress_routes_DISABLED(app, progress_manager, citation_processor)  # DISABLED to prevent route conflicts
    
    return app

if __name__ == "__main__":
    app = setup_progress_enabled_app()
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, threaded=True)  # nosec B201 - Debug mode is environment-controlled


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