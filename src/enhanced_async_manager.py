"""
Enhanced Async Job Manager for CaseStrainer

This module provides advanced async job management with concurrent processing,
job queuing, progress tracking, and result caching.
"""

import asyncio
import logging
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import redis
from concurrent.futures import ThreadPoolExecutor
import pickle
import threading

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobInfo:
    """Job information data class."""
    job_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    current_step: str = ""
    total_steps: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    worker_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobInfo':
        """Create from dictionary."""
        # Convert ISO strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data['started_at']:
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data['completed_at']:
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        # Convert status string back to enum
        if isinstance(data['status'], str):
            data['status'] = JobStatus(data['status'])
        
        return cls(**data)


class EnhancedAsyncManager:
    """Enhanced async job manager with concurrent processing capabilities."""
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379/0",
                 max_concurrent_jobs: int = 10,
                 job_timeout: int = 300,
                 result_ttl: int = 3600):
        
        self.redis_url = redis_url
        self.max_concurrent_jobs = max_concurrent_jobs
        self.job_timeout = job_timeout
        self.result_ttl = result_ttl
        
        # Redis connection
        self.redis_client = None
        self._connect_redis()
        
        # Job tracking
        self.active_jobs: Dict[str, JobInfo] = {}
        self.job_semaphore = asyncio.Semaphore(max_concurrent_jobs)
        
        # Thread pool for CPU-intensive tasks
        self.thread_executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs)
        
        # Background tasks
        self.cleanup_task = None
        self.running = False
        
        # Event handlers
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self.completion_callbacks: Dict[str, List[Callable]] = {}
        
        logger.info(f"EnhancedAsyncManager initialized: max_concurrent={max_concurrent_jobs}, timeout={job_timeout}s")
    
    def _connect_redis(self):
        """Connect to Redis with fallback."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Using in-memory storage.")
            self.redis_client = None
    
    async def start(self):
        """Start the async manager and background tasks."""
        if self.running:
            return
        
        self.running = True
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_old_jobs())
        
        logger.info("EnhancedAsyncManager started")
    
    async def stop(self):
        """Stop the async manager and cleanup resources."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Wait for active jobs to complete or cancel them
        for job_id, job_info in list(self.active_jobs.items()):
            if job_info.status == JobStatus.RUNNING:
                await self.cancel_job(job_id)
        
        # Shutdown thread executor
        self.thread_executor.shutdown(wait=True)
        
        logger.info("EnhancedAsyncManager stopped")
    
    async def submit_job(self, 
                        input_data: Dict[str, Any],
                        processor_func: Callable,
                        job_id: str = None,
                        priority: int = 0) -> str:
        """Submit a new job for processing."""
        
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        # Create job info
        job_info = JobInfo(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            input_data=input_data
        )
        
        # Store job info
        await self._store_job_info(job_info)
        
        # Submit job for processing
        task = asyncio.create_task(
            self._process_job(job_id, input_data, processor_func)
        )
        
        logger.info(f"Job {job_id} submitted for processing")
        return job_id
    
    async def _process_job(self, 
                          job_id: str, 
                          input_data: Dict[str, Any],
                          processor_func: Callable):
        """Process a single job with timeout and progress tracking."""
        
        # Acquire semaphore to limit concurrent jobs
        async with self.job_semaphore:
            try:
                # Update job status to running
                job_info = await self._get_job_info(job_id)
                if job_info:
                    job_info.status = JobStatus.RUNNING
                    job_info.started_at = datetime.now()
                    job_info.worker_id = f"worker_{threading.get_ident()}"
                    await self._store_job_info(job_info)
                
                # Process with timeout
                result = await asyncio.wait_for(
                    self._run_processor_with_progress(job_id, input_data, processor_func),
                    timeout=self.job_timeout
                )
                
                # Update job with success result
                job_info = await self._get_job_info(job_id)
                if job_info:
                    job_info.status = JobStatus.COMPLETED
                    job_info.completed_at = datetime.now()
                    job_info.progress = 100.0
                    job_info.result = result
                    job_info.processing_time = (job_info.completed_at - job_info.started_at).total_seconds()
                    await self._store_job_info(job_info)
                
                # Call completion callbacks
                await self._call_completion_callbacks(job_id, result, None)
                
                logger.info(f"Job {job_id} completed successfully")
                
            except asyncio.TimeoutError:
                # Handle timeout
                job_info = await self._get_job_info(job_id)
                if job_info:
                    job_info.status = JobStatus.FAILED
                    job_info.completed_at = datetime.now()
                    job_info.error = f"Job timed out after {self.job_timeout} seconds"
                    job_info.processing_time = (job_info.completed_at - job_info.started_at).total_seconds()
                    await self._store_job_info(job_info)
                
                await self._call_completion_callbacks(job_id, None, job_info.error)
                logger.error(f"Job {job_id} timed out")
                
            except Exception as e:
                # Handle other errors
                job_info = await self._get_job_info(job_id)
                if job_info:
                    job_info.status = JobStatus.FAILED
                    job_info.completed_at = datetime.now()
                    job_info.error = str(e)
                    job_info.processing_time = (job_info.completed_at - job_info.started_at).total_seconds() if job_info.started_at else None
                    await self._store_job_info(job_info)
                
                await self._call_completion_callbacks(job_id, None, str(e))
                logger.error(f"Job {job_id} failed: {str(e)}")
            
            finally:
                # Remove from active jobs
                self.active_jobs.pop(job_id, None)
    
    async def _run_processor_with_progress(self, 
                                          job_id: str, 
                                          input_data: Dict[str, Any], 
                                          processor_func: Callable) -> Dict[str, Any]:
        """Run processor function with progress tracking."""
        
        # Create progress callback
        async def progress_callback(progress: float, step: str, message: str):
            await self.update_job_progress(job_id, progress, step, message)
        
        # Check if processor function is async
        if asyncio.iscoroutinefunction(processor_func):
            if 'progress_callback' in processor_func.__code__.co_varnames:
                result = await processor_func(input_data, progress_callback=progress_callback)
            else:
                result = await processor_func(input_data)
        else:
            # Run sync function in thread pool
            if 'progress_callback' in processor_func.__code__.co_varnames:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.thread_executor,
                    processor_func,
                    input_data,
                    progress_callback
                )
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.thread_executor,
                    processor_func,
                    input_data
                )
        
        return result
    
    async def update_job_progress(self, 
                                 job_id: str, 
                                 progress: float, 
                                 step: str = "", 
                                 message: str = ""):
        """Update job progress and call callbacks."""
        
        job_info = await self._get_job_info(job_id)
        if job_info and job_info.status == JobStatus.RUNNING:
            job_info.progress = min(100.0, max(0.0, progress))
            job_info.current_step = f"{step}: {message}" if message else step
            await self._store_job_info(job_info)
            
            # Call progress callbacks
            await self._call_progress_callbacks(job_id, progress, step, message)
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and information."""
        job_info = await self._get_job_info(job_id)
        if job_info:
            return job_info.to_dict()
        return None
    
    async def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job result if completed."""
        job_info = await self._get_job_info(job_id)
        if job_info and job_info.status == JobStatus.COMPLETED:
            return job_info.result
        return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        job_info = await self._get_job_info(job_id)
        if job_info and job_info.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job_info.status = JobStatus.CANCELLED
            job_info.completed_at = datetime.now()
            job_info.error = "Job was cancelled"
            await self._store_job_info(job_info)
            
            # Remove from active jobs
            self.active_jobs.pop(job_id, None)
            
            logger.info(f"Job {job_id} cancelled")
            return True
        return False
    
    async def list_jobs(self, 
                       status: Optional[JobStatus] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """List jobs with optional status filter."""
        
        if self.redis_client:
            try:
                # Get all job keys
                job_keys = self.redis_client.keys(f"job:*")
                jobs = []
                
                for job_key in job_keys[:limit]:
                    job_data = self.redis_client.get(job_key)
                    if job_data:
                        job_info = pickle.loads(job_data)
                        if status is None or job_info.status == status:
                            jobs.append(job_info.to_dict())
                
                # Sort by creation time (newest first)
                jobs.sort(key=lambda x: x['created_at'], reverse=True)
                return jobs
                
            except Exception as e:
                logger.error(f"Error listing jobs from Redis: {str(e)}")
        
        # Fallback to active jobs
        jobs = []
        for job_info in self.active_jobs.values():
            if status is None or job_info.status == status:
                jobs.append(job_info.to_dict())
        
        return jobs[:limit]
    
    async def add_progress_callback(self, job_id: str, callback: Callable):
        """Add progress callback for a job."""
        if job_id not in self.progress_callbacks:
            self.progress_callbacks[job_id] = []
        self.progress_callbacks[job_id].append(callback)
    
    async def add_completion_callback(self, job_id: str, callback: Callable):
        """Add completion callback for a job."""
        if job_id not in self.completion_callbacks:
            self.completion_callbacks[job_id] = []
        self.completion_callbacks[job_id].append(callback)
    
    async def _call_progress_callbacks(self, job_id: str, progress: float, step: str, message: str):
        """Call all progress callbacks for a job."""
        callbacks = self.progress_callbacks.get(job_id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(job_id, progress, step, message)
                else:
                    callback(job_id, progress, step, message)
            except Exception as e:
                logger.error(f"Progress callback error for job {job_id}: {str(e)}")
    
    async def _call_completion_callbacks(self, job_id: str, result: Optional[Dict[str, Any]], error: Optional[str]):
        """Call all completion callbacks for a job."""
        callbacks = self.completion_callbacks.get(job_id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(job_id, result, error)
                else:
                    callback(job_id, result, error)
            except Exception as e:
                logger.error(f"Completion callback error for job {job_id}: {str(e)}")
        
        # Clean up callbacks
        self.progress_callbacks.pop(job_id, None)
        self.completion_callbacks.pop(job_id, None)
    
    async def _store_job_info(self, job_info: JobInfo):
        """Store job information in Redis or memory."""
        if self.redis_client:
            try:
                job_key = f"job:{job_info.job_id}"
                job_data = pickle.dumps(job_info)
                self.redis_client.setex(job_key, self.result_ttl, job_data)
            except Exception as e:
                logger.error(f"Error storing job info in Redis: {str(e)}")
        
        # Always store in memory for active jobs
        if job_info.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            self.active_jobs[job_info.job_id] = job_info
    
    async def _get_job_info(self, job_id: str) -> Optional[JobInfo]:
        """Get job information from Redis or memory."""
        
        # Check active jobs first
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # Check Redis
        if self.redis_client:
            try:
                job_key = f"job:{job_id}"
                job_data = self.redis_client.get(job_key)
                if job_data:
                    return pickle.loads(job_data)
            except Exception as e:
                logger.error(f"Error getting job info from Redis: {str(e)}")
        
        return None
    
    async def _cleanup_old_jobs(self):
        """Background task to clean up old completed jobs."""
        while self.running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                if self.redis_client:
                    # Clean up old jobs from Redis
                    cutoff_time = datetime.now() - timedelta(seconds=self.result_ttl)
                    job_keys = self.redis_client.keys(f"job:*")
                    
                    for job_key in job_keys:
                        job_data = self.redis_client.get(job_key)
                        if job_data:
                            job_info = pickle.loads(job_data)
                            if (job_info.completed_at and 
                                job_info.completed_at < cutoff_time):
                                self.redis_client.delete(job_key)
                                logger.debug(f"Cleaned up old job {job_info.job_id}")
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        
        # Count jobs by status
        status_counts = {status.value: 0 for status in JobStatus}
        
        if self.redis_client:
            try:
                job_keys = self.redis_client.keys(f"job:*")
                for job_key in job_keys:
                    job_data = self.redis_client.get(job_key)
                    if job_data:
                        job_info = pickle.loads(job_data)
                        status_counts[job_info.status.value] += 1
            except Exception as e:
                logger.error(f"Error getting stats from Redis: {str(e)}")
        
        # Add active jobs
        for job_info in self.active_jobs.values():
            status_counts[job_info.status.value] += 1
        
        return {
            'total_jobs': sum(status_counts.values()),
            'active_jobs': status_counts[JobStatus.RUNNING.value],
            'pending_jobs': status_counts[JobStatus.PENDING.value],
            'completed_jobs': status_counts[JobStatus.COMPLETED.value],
            'failed_jobs': status_counts[JobStatus.FAILED.value],
            'cancelled_jobs': status_counts[JobStatus.CANCELLED.value],
            'max_concurrent_jobs': self.max_concurrent_jobs,
            'redis_connected': self.redis_client is not None
        }


# Global instance for easy access
_global_manager = None


async def get_async_manager(redis_url: str = "redis://localhost:6379/0",
                           max_concurrent_jobs: int = 10,
                           job_timeout: int = 300) -> EnhancedAsyncManager:
    """Get or create global async manager instance."""
    global _global_manager
    
    if _global_manager is None:
        _global_manager = EnhancedAsyncManager(
            redis_url=redis_url,
            max_concurrent_jobs=max_concurrent_jobs,
            job_timeout=job_timeout
        )
        await _global_manager.start()
    
    return _global_manager


# Utility functions for quick usage
async def submit_processing_job(input_data: Dict[str, Any],
                               processor_func: Callable,
                               job_id: str = None) -> str:
    """Submit a processing job and return job ID."""
    manager = await get_async_manager()
    return await manager.submit_job(input_data, processor_func, job_id)


async def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status."""
    manager = await get_async_manager()
    return await manager.get_job_status(job_id)


async def get_job_result(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job result."""
    manager = await get_async_manager()
    return await manager.get_job_result(job_id)


async def wait_for_job(job_id: str, timeout: int = None) -> Optional[Dict[str, Any]]:
    """Wait for job completion and return result."""
    manager = await get_async_manager()
    
    start_time = time.time()
    check_interval = 1.0
    
    while True:
        job_info = await manager.get_job_info(job_id)
        if not job_info:
            return None
        
        if job_info.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return job_info.to_dict()
        
        if timeout and (time.time() - start_time) > timeout:
            logger.warning(f"Timeout waiting for job {job_id}")
            return None
        
        await asyncio.sleep(check_interval)
