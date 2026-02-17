"""
Progress Bar Solutions for CaseStrainer Citation Processing
Multiple approaches to provide real-time progress feedback to users
Progress Manager for Citation Extraction Tasks
AUTO-RELOAD LIVE TEST: This change should trigger immediate restart!
"""

import os
import re
import threading

import time
import json
import logging
import requests
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from flask import Flask
import asyncio

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

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


from src.input_fetchers import fetch_url_content, preprocess_extracted_text


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

    def update(
        self, step: int, status: str, message: str, partial_results: Optional[List] = None, error: Optional[str] = None
    ):
        """Update progress and optionally add partial results"""
        # FIX DEC 2025: Prevent progress regression - only allow forward progress
        # This prevents confusing UX where progress bar goes backwards
        if step >= self.current_step:
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
            "task_id": self.task_id,
            "progress": round(progress_percent, 2),
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "status": self.status,
            "message": self.message,
            "results_count": len(self.results),
            "error_count": len(self.errors),
            "estimated_completion": self.estimated_completion,
            "timestamp": datetime.now().isoformat(),
        }

    def is_complete(self) -> bool:
        return self.status in ["completed", "failed"]


class SSEProgressManager:
    """Manages Server-Sent Events for real-time progress updates"""

    def __init__(self):
        self.active_tasks: Dict[str, ProgressTracker] = {}
        self.redis_client = None
        if REDIS_AVAILABLE and redis is not None:
            try:
                # Use REDIS_URL environment variable if available, otherwise fallback to localhost
                from src.config import REDIS_URL
                redis_url = REDIS_URL
                if redis_url.startswith("redis://"):
                    # Parse redis://:password@host:port/db format
                    import re

                    match = re.match(
                        r"redis://:(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<db>\d+)", redis_url
                    )
                    if match:
                        self.redis_client = redis.Redis(
                            host=match.group("host"),
                            port=int(match.group("port")),
                            db=int(match.group("db")),
                            password=match.group("password"),
                        )
                    else:
                        # Fallback for simple redis://host:port/db
                        match = re.match(r"redis://(?P<host>[^:]+):(?P<port>\d+)/(?P<db>\d+)", redis_url)
                        if match:
                            self.redis_client = redis.Redis(
                                host=match.group("host"), port=int(match.group("port")), db=int(match.group("db"))
                            )
                else:
                    # Direct connection fallback
                    self.redis_client = redis.Redis(host="localhost", port=6379, db=0)
            except Exception as e:
                logger.warning(f"Redis not available, using in-memory progress tracking: {e}")
                self.redis_client = None
        else:
            logger.info("Redis not installed, using in-memory progress tracking")

    def start_task(self, total_steps: int, task_id_override: str = None) -> str:
        """Start a new task and return task ID

        Args:
            total_steps: Number of steps in the task
            task_id_override: Optional custom task ID to use instead of generating UUID
        """
        task_id = task_id_override if task_id_override else str(uuid.uuid4())
        tracker = ProgressTracker(task_id, total_steps)
        self.active_tasks[task_id] = tracker

        if self.redis_client:
            self._store_progress_in_redis(task_id, tracker)

        return task_id

    def update_progress(
        self,
        task_id: str,
        step: int,
        status: str,
        message: str,
        partial_results: Optional[List] = None,
        error: Optional[str] = None,
    ):
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

        return {"error": "Task not found"}

    def get_results(self, task_id: str) -> Dict:
        """Get final results for a completed task"""
        if task_id in self.active_tasks:
            tracker = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": tracker.status,
                "results": tracker.results,
                "errors": tracker.errors,
                "progress_data": tracker.get_progress_data(),
            }
        return {"error": "Task not found"}

    def cleanup_task(self, task_id: str, keep_redis_data: bool = False):
        """Clean up completed task

        Args:
            keep_redis_data: If True, keep Redis data for polling after completion
        """
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]

        # Only delete Redis data if not keeping it for polling
        if self.redis_client and not keep_redis_data:
            self.redis_client.delete(f"progress:{task_id}")

    def _store_progress_in_redis(self, task_id: str, tracker: ProgressTracker):
        """Store progress in Redis for multi-instance support"""
        try:
            if self.redis_client is not None:
                data = tracker.get_progress_data()
                data["results"] = tracker.results
                data["errors"] = tracker.errors
                self.redis_client.setex(  # type: ignore
                    f"progress:{task_id}", 3600, json.dumps(data, default=str)  # 1 hour expiration
                )
        except Exception as e:
            logger.error(f"Failed to store progress in Redis: {e}")

    def _get_progress_from_redis(self, task_id: str) -> Dict:
        """Get progress from Redis"""
        try:
            if self.redis_client is not None:
                data = self.redis_client.get(f"progress:{task_id}")  # type: ignore
                if data:
                    return json.loads(data.decode("utf-8") if isinstance(data, bytes) else data)  # type: ignore
        except Exception as e:
            logger.error(f"Failed to get progress from Redis: {e}")
        return {"error": "Task not found"}

    def start_eta_heartbeat(
        self,
        task_id: str,
        start_pct: int,
        cap_pct: int,
        expected_seconds: float,
        message: str = "Processing...",
        interval: float = 0.8,
    ) -> None:
        """Start an ETA-based heartbeat that advances progress smoothly up to cap_pct.

        - Never decreases progress (monotonic).
        - Stops when task completes or fails.
        - Uses elapsed/expected to compute target percent in [start_pct..cap_pct].
        """
        try:
            start_time = time.time()

            def _hb():
                try:
                    while True:
                        time.sleep(interval)
                        task = self.active_tasks.get(task_id)
                        if not task:
                            break
                        status = getattr(task, "status", "")
                        if status in ("completed", "failed"):
                            break
                        elapsed = max(0.0, time.time() - start_time)
                        frac = min(1.0, elapsed / max(1.0, expected_seconds))
                        target = start_pct + int((cap_pct - start_pct) * frac)
                        # Monotonic increase: don't regress existing current_step
                        current = int(getattr(task, "current_step", 0))
                        nxt = max(current, max(start_pct, min(cap_pct, target)))
                        self.update_progress(task_id, nxt, "processing", message)
                except Exception:
                    pass

            threading.Thread(target=_hb, daemon=True).start()
        except Exception:
            pass


def estimate_citations_cheap(text: str) -> int:
    """Fast, cheap estimate of citation count without full parsing.

    Combines a few regex heuristics:
    - Reporter pattern like "123 F.3d 456" / "159 Wn.2d 700"
    - Presence of " v. " case markers (bounded to avoid overcounting)
    Returns the max of the two counts.
    """
    if not text:
        return 0
    try:
        reporter_pat = re.compile(r"\b\d{1,3}\s+[A-Z][A-Za-z\d\.]*(?:\s?[A-Za-z\d\.]*)\s+\d{1,4}\b")
        v_mark_pat = re.compile(r"\b\w[\w\.'-]{1,}\s+v\.\s+\w")
        c1 = len(reporter_pat.findall(text))
        c2 = len(v_mark_pat.findall(text))
        return max(c1, c2)
    except Exception:
        return 0


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

        self.socketio.emit("progress_update", tracker.get_progress_data(), room=f"task_{task_id}")

        return task_id

    def update_progress(
        self,
        task_id: str,
        step: int,
        status: str,
        message: str,
        partial_results: Optional[List] = None,
        error: Optional[str] = None,
    ):
        """Update progress and emit to all clients watching this task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update(step, status, message, partial_results or [], error)

            progress_data = self.active_tasks[task_id].get_progress_data()

            if partial_results:
                progress_data["partial_results"] = partial_results

            self.socketio.emit("progress_update", progress_data, room=f"task_{task_id}")


class ChunkedCitationProcessor:
    """Process citations in chunks to provide incremental progress"""

    def __init__(self, progress_manager: SSEProgressManager):
        self.progress_manager = progress_manager
        self.chunk_size = 5000  # Characters per chunk (increased to prevent citation splitting)

    async def process_document_with_progress(self, document_text: str, document_type: str = "legal_brief") -> str:
        """Process document in chunks with progress updates"""
        logger.info("\n" + "=" * 80)
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

            # CITATION-BASED PROGRESS: First do a quick citation count to determine realistic progress steps
            logger.info(f"[Task {task_id}] Counting citations for citation-based progress tracking...")
            try:
                from src.citation_extraction_endpoint import extract_citations_with_clustering

                # Do a quick extraction without verification to count citations
                quick_result = extract_citations_with_clustering(document_text, enable_verification=False)
                citation_count = len(quick_result.get("citations", []))

                # Calculate realistic total steps based on citation count
                # Base steps: initialization, extraction, clustering, verification, completion
                base_steps = 5
                # Citation processing steps: more citations = more steps
                citation_steps = max(1, min(citation_count, 100))  # Cap at 100 steps for performance
                total_steps = base_steps + citation_steps

                logger.info(
                    f"[Task {task_id}] Citation-based progress: {citation_count} citations → {total_steps} total steps"
                )
            except Exception as e:
                logger.warning(f"[Task {task_id}] Failed to count citations, using default steps: {e}")
                total_steps = 25  # Fallback to reasonable default

            tracker = ProgressTracker(task_id, total_steps=total_steps)
            logger.info(f"Initialized progress tracker with {total_steps} steps")

            self.progress_manager.active_tasks[task_id] = tracker
            logger.info(f"Stored task in active_tasks. Total active tasks: {len(self.progress_manager.active_tasks)}")

            logger.info(
                f"Redis available: {hasattr(self.progress_manager, 'redis_client') and self.progress_manager.redis_client is not None}"
            )

            logger.info("Creating background task for document processing...")

            # Submit to RQ queue instead of local asyncio task
            try:
                from rq import Queue

                # Get RQ queue
                queue = Queue("casestrainer", connection=self.progress_manager.redis_client)

                # Enqueue the async task
                job = queue.enqueue(
                    "src.rq_worker.process_citation_task_async",
                    task_id=task_id,
                    document_text=document_text,
                    document_type=document_type,
                    timeout=3600,  # 1 hour timeout
                    ttl=86400,  # Job expires after 24 hours
                    result_ttl=86400,  # Result kept for 24 hours
                    failure_ttl=3600,  # Failure info kept for 1 hour
                )

                logger.info(f"Task submitted to RQ queue: job_id={job.id}, task_id={task_id}")

            except Exception as rq_error:
                logger.error(f"Failed to submit task to RQ: {rq_error}")
                # Fallback to local asyncio task if RQ fails
                logger.info("Falling back to local asyncio task...")
                asyncio.create_task(self._process_document_async(task_id, document_text, document_type, tracker))

            logger.info("Background task created successfully")

            self.progress_manager.update_progress(
                task_id, 0, "started", "Document processing started...", partial_results=[]
            )

            return task_id

        except Exception as e:
            self.progress_manager.update_progress(task_id, 0, "failed", f"Processing failed: {str(e)}", error=str(e))
            raise

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split document into processable chunks"""
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunk = text[i : i + self.chunk_size]

            if i + self.chunk_size < len(text):
                break_points = [". ", "\n\n", "\n", ". "]
                for bp in break_points:
                    last_bp = chunk.rfind(bp)
                    if last_bp > self.chunk_size * 0.8:  # Don't make chunks too small
                        chunk = chunk[: last_bp + len(bp)]
                        break

            chunks.append(chunk)

        return chunks

    async def _preprocess_chunks(self, chunks: List[str]) -> List[str]:
        """Preprocess chunks for better citation extraction"""
        processed = []
        for chunk in chunks:
            processed_chunk = chunk.replace("  ", " ").strip()
            processed.append(processed_chunk)

        return processed

    async def _process_chunk(self, chunk: str, document_type: str) -> List[Dict]:
        """Process a single chunk for citations using the unified extraction master."""
        chunk_hash = hash(chunk) % 1000
        logger.info(f"[Chunk-{chunk_hash}] Starting chunk processing (size: {len(chunk)} chars)")

        try:
            logger.info(f"[Chunk-{chunk_hash}] Using unified extraction master...")
            from src.unified_citation_processor_v2 import extract_citations_unified

            logger.info(f"[Chunk-{chunk_hash}] Starting extract_citations_unified()...")
            start_time = time.time()

            # Extract citations using unified master
            citation_results = extract_citations_unified(chunk)
            
            logger.info(f"[Chunk-{chunk_hash}] Extracted {len(citation_results)} citations with unified master")

            # NEW: Apply verification and parallel verification to chunk results
            logger.info(f"[Chunk-{chunk_hash}] Applying verification and parallel verification to chunk results...")
            try:
                # Convert to list for verification
                citations_list = list(citation_results)

                # Import verification functions
                from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

                processor = UnifiedCitationProcessorV2()

                # First verify citations to get canonical data
                verified_citations = processor._verify_citations_sync(citations_list, chunk)
                citation_results = verified_citations
                logger.info(f"[Chunk-{chunk_hash}] Verification complete, {len(citation_results)} citations verified")

                # Apply parallel verification to the verified citations
                processor.propagate_canonical_to_cluster(citation_results)
                logger.info(f"[Chunk-{chunk_hash}] Parallel verification complete")

                # Log if parallel verification was applied
                parallel_count = sum(1 for c in citation_results if getattr(c, "true_by_parallel", False))
                if parallel_count > 0:
                    logger.info(f"[Chunk-{chunk_hash}] ✅ Applied parallel verification to {parallel_count} citations")

            except Exception as parallel_error:
                logger.warning(f"[Chunk-{chunk_hash}] Parallel verification failed (non-critical): {parallel_error}")
                import traceback

                logger.warning(f"[Chunk-{chunk_hash}] Parallel verification error details: {traceback.format_exc()}")

            process_time = time.time() - start_time
            logger.info(
                f"[Chunk-{chunk_hash}] extract_citations() completed in {process_time:.2f}s, got {len(citation_results)} citations"
            )

            # Convert CitationResult objects to dicts
            results = {"citations": []}
            for cit_obj in citation_results:
                results["citations"].append(
                    {
                        "citation": cit_obj.citation,
                        "extracted_case_name": cit_obj.extracted_case_name,
                        "extracted_date": cit_obj.extracted_date,
                        "start_index": cit_obj.start_index,
                        "end_index": cit_obj.end_index,
                        "method": cit_obj.method,
                        "confidence": cit_obj.confidence,
                        "metadata": cit_obj.metadata,
                        "verified": False,  # Verification happens later
                        "canonical_name": None,
                        "canonical_date": None,
                        "url": None,
                    }
                )

            citations = []
            raw_citations = results.get("citations", [])
            logger.info(f"[Chunk-{chunk_hash}] Converting {len(raw_citations)} citations to dicts...")

            for i, citation_dict in enumerate(raw_citations, 1):
                try:
                    citation_data = {
                        "id": len(citations) + 1,
                        "citation": citation_dict.get("citation", ""),
                        "raw_text": citation_dict.get("citation", ""),
                        "case_name": citation_dict.get("extracted_case_name") or "Unknown Case",
                        "year": citation_dict.get("extracted_date") or "No year",
                        "confidence_score": citation_dict.get("confidence_score", 0.7),
                        "chunk_index": chunk_hash,
                        "extracted_case_name": citation_dict.get("extracted_case_name"),
                        "canonical_name": citation_dict.get("canonical_name"),
                        "extracted_date": citation_dict.get("extracted_date"),
                        "canonical_date": citation_dict.get("canonical_date"),
                        "verified": citation_dict.get("verified", False),
                        "source": citation_dict.get("source", "enhanced_sync"),
                        "method": citation_dict.get("extraction_method", "enhanced_sync"),
                        "is_parallel": citation_dict.get("is_parallel", False),
                        "parallel_citations": citation_dict.get("parallel_citations", []),
                        "start_index": citation_dict.get("start_index"),
                        "end_index": citation_dict.get("end_index"),
                        "context": citation_dict.get("context"),
                        "url": citation_dict.get("url"),
                        "metadata": citation_dict.get("metadata", {}),
                    }
                    citations.append(citation_data)

                    if i <= 3:  # Only log first 3 citations to avoid log spam
                        logger.info(
                            f"[Chunk-{chunk_hash}] Citation {i}: "
                            f"Name: {citation_dict.get('extracted_case_name')} | "
                            f"Date: {citation_dict.get('extracted_date')} | "
                            f"Verified: {citation_dict.get('verified')}"
                        )
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

    async def _process_document_async(
        self, task_id: str, document_text: str, document_type: str, tracker: "ProgressTracker"
    ):
        """Background task to process document asynchronously"""
        print(f"🔥🔥🔥 _process_document_async CALLED with {len(document_text)} chars, task_id={task_id}")
        logger.info("\n" + "=" * 80)
        logger.info(f"Starting _process_document_async for task {task_id}")
        logger.info(f"Document type: {document_type}")
        logger.info(f"Document text length: {len(document_text)} characters")
        logger.info(f"Tracker status: {tracker.status if tracker else 'No tracker'}")

        try:
            if not document_text or not isinstance(document_text, str):
                error_msg = f"Invalid document text in _process_document_async. Type: {type(document_text)}"
                logger.error(error_msg)
                self.progress_manager.update_progress(task_id, 0, "failed", error_msg, error=error_msg)
                return

            logger.info(f"Document sample: {document_text[:200]}...")

            logger.info("Splitting document into chunks...")
            chunks = self._split_into_chunks(document_text)
            logger.info(f"Document split into {len(chunks)} chunks")

            logger.info("Updating progress to 10% (chunking complete)")
            self.progress_manager.update_progress(task_id, 10, "processing", "Processing document chunks...")

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
                        task_id, progress, "processing", progress_msg, partial_results=chunk_results
                    )

                except Exception as chunk_error:
                    error_msg = f"Error processing chunk {i}/{total_chunks}: {str(chunk_error)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())

                    self.progress_manager.update_progress(task_id, 0, "failed", error_msg, error=error_msg)
                    return

            logger.info("\nPerforming final analysis...")
            self.progress_manager.update_progress(task_id, 90, "processing", "Performing final analysis...")

            try:
                final_results = await self._perform_final_analysis(results)

                logger.info("Marking task as complete")
                # Store final results in tracker
                if task_id in self.progress_manager.active_tasks:
                    tracker = self.progress_manager.active_tasks[task_id]
                    tracker.results.extend(final_results)  # Use extend instead of assignment

                self.progress_manager.update_progress(
                    task_id,
                    100,
                    "completed",
                    f"Processing complete! Found {len(results)} citations.",
                    partial_results=results,  # Keep original results for partial updates
                )
                logger.info("Task completed successfully")

            except Exception as analysis_error:
                error_msg = f"Error in final analysis: {str(analysis_error)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())

                self.progress_manager.update_progress(task_id, 0, "failed", error_msg, error=error_msg)

        except Exception as e:
            error_msg = f"Unexpected error in _process_document_async: {str(e)}"
            logger.error("\n" + "!" * 80)
            logger.error("UNEXPECTED ERROR IN _process_document_async")
            logger.error("!" * 80)
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            logger.error("!" * 80 + "\n")

            try:
                self.progress_manager.update_progress(task_id, 0, "failed", error_msg, error=error_msg)
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
                citation=citation_dict.get("citation", ""),
                extracted_case_name=citation_dict.get("extracted_case_name"),
                extracted_date=citation_dict.get("extracted_date"),
                canonical_name=citation_dict.get("canonical_name"),
                canonical_date=citation_dict.get("canonical_date"),
                verified=citation_dict.get("verified", False),
                is_parallel=citation_dict.get("is_parallel", False),
                parallel_citations=citation_dict.get("parallel_citations", []),
                start_index=citation_dict.get("start_index", 0),
                end_index=citation_dict.get("end_index", 0),
                context=citation_dict.get("context", ""),
                source=citation_dict.get("source", ""),
                url=citation_dict.get("url"),
                metadata=citation_dict.get("metadata", {}),
            )
            citation_objects.append(citation_obj)

        # CRITICAL: Enable verification in clustering
        clusters = cluster_citations_unified(citations=citation_objects, enable_verification=True)

        # CRITICAL FIX: Update citation objects with cluster information
        # This must happen BEFORE serialization to ensure cluster data persists
        logger.info(f"[PROGRESS_MANAGER] Updating citations with cluster information")
        citation_to_cluster = {}
        for cluster in clusters:
            cluster_id = cluster.get("cluster_id")
            cluster_case_name = cluster.get("cluster_case_name") or cluster.get("case_name")
            cluster_citations = cluster.get("citations", [])

            # Match by citation text, not object id (clusters contain dicts, not objects)
            for cit_dict in cluster_citations:
                citation_text = (
                    cit_dict.get("citation") if isinstance(cit_dict, dict) else getattr(cit_dict, "citation", None)
                )
                if citation_text:
                    citation_to_cluster[citation_text] = (cluster_id, cluster_case_name, len(cluster_citations))

        updated_count = 0
        for citation_obj in citation_objects:
            citation_text = getattr(citation_obj, "citation", None)
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
                citation_dict["cluster_id"] = getattr(citation_obj, "cluster_id", None)
                citation_dict["cluster_case_name"] = getattr(citation_obj, "cluster_case_name", None)
                citation_dict["is_cluster"] = getattr(citation_obj, "is_cluster", False)

        logger.info(f"[PROGRESS_MANAGER] Updated {updated_count} citations with cluster information")

        return {
            "citations": citations,
            "clusters": clusters,
            "total_citations": len(citations),
            "high_confidence": len([c for c in citations if c.get("confidence_score", 0) > 0.8]),
            "needs_review": len([c for c in citations if c.get("confidence_score", 0) < 0.6]),
        }


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

    return "\n\n".join(text_parts)


def _extract_with_pdfminer(pdf_content: bytes) -> str:
    """Extract text using pdfminer."""
    try:
        from pdfminer.high_level import extract_text_to_fp
        from pdfminer.layout import LAParams
        import io

        output_string = io.StringIO()
        pdf_content_io = io.BytesIO(pdf_content)

        extract_text_to_fp(pdf_content_io, output_string, laparams=LAParams(), output_type="text", codec="utf-8")

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

        return "\n\n".join(text_parts)
    except ImportError:
        raise Exception("pdfplumber not available")


def process_citation_task_direct(task_id: str, input_type: str, input_data: dict):
    """
    DEPRECATED: Use src.rq_worker.run_citation_task (via src.rq_worker.process_citation_task_direct) instead.
    This wrapper remains only for backward compatibility and will be removed in a later release.
    Process citation task directly (for use with RQ workers).

    Args:
        task_id: Unique task ID
        input_type: Type of input ('text', 'url', 'file')
        input_data: Dictionary containing the input data

    Returns:
        Dictionary with processing results
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(
        "[DEPRECATED] progress_manager.process_citation_task_direct is deprecated. "
        "Use src.rq_worker.process_citation_task_direct (which calls run_citation_task). "
        "This wrapper will be removed in a later release."
    )
    from src.rq_worker_pipeline import run_citation_task
    return run_citation_task(task_id, input_type, input_data, logger=logger)


def setup_progress_enabled_app():
    """Complete setup example for progress-enabled citation processing"""
    app = Flask(__name__)

    logging.basicConfig(level=logging.INFO)

    progress_manager = SSEProgressManager()

    ChunkedCitationProcessor(progress_manager)

    return app


if __name__ == "__main__":
    app = setup_progress_enabled_app()
    debug_mode = os.getenv("FLASK_ENV") == "development"
    app.run(debug=debug_mode, threaded=True)  # nosec B201 - Debug mode is environment-controlled


PROGRESS_CONFIG = {
    "sse": {
        "description": "Server-Sent Events - Best for most cases",
        "pros": ["Simple to implement", "Works with load balancers", "Automatic reconnection"],
        "cons": ["HTTP/1.1 connection limit", "Some proxy issues"],
        "recommended_for": "Most web applications",
    },
    "websockets": {
        "description": "WebSocket - Best for real-time applications",
        "pros": ["Full bidirectional", "Lower latency", "More efficient"],
        "cons": ["More complex", "Load balancer challenges", "Sticky sessions needed"],
        "recommended_for": "Real-time collaborative features",
    },
    "polling": {
        "description": "HTTP Polling - Most compatible fallback",
        "pros": ["Universal compatibility", "Simple to implement", "Works everywhere"],
        "cons": ["Higher server load", "Delayed updates", "Less efficient"],
        "recommended_for": "Fallback mechanism",
    },
}
