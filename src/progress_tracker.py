"""
Progress Tracking System for CaseStrainer
Provides real-time progress updates for both sync and async processing
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ProgressStep:
    """Represents a single step in the processing pipeline."""
    name: str
    progress: int = 0
    status: str = 'pending'  # pending, in_progress, completed, failed
    message: str = ''
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def start(self, message: str = ''):
        """Mark step as started."""
        self.status = 'in_progress'
        self.progress = 0
        self.message = message
        self.start_time = time.time()
        
    def update(self, progress: int, message: str = ''):
        """Update step progress."""
        self.progress = min(100, max(0, progress))
        if message:
            self.message = message
            
    def complete(self, message: str = ''):
        """Mark step as completed."""
        self.status = 'completed'
        self.progress = 100
        self.message = message or f'{self.name} completed'
        self.end_time = time.time()
        
    def fail(self, message: str = ''):
        """Mark step as failed."""
        self.status = 'failed'
        self.message = message or f'{self.name} failed'
        self.end_time = time.time()

class ProgressTracker:
    """Tracks progress for citation processing tasks."""
    
    def __init__(self, task_id: str, total_steps: int = 6):
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
        self.end_time = None
        self.status = 'initializing'
        self.overall_progress = 0
        
        # Define standard processing steps
        self.steps = [
            ProgressStep('Initializing', 0, 'pending', 'Starting processing...'),
            ProgressStep('Extract', 0, 'pending', 'Extracting citations from text'),
            ProgressStep('Analyze', 0, 'pending', 'Analyzing and normalizing citations'),
            ProgressStep('Extract Names', 0, 'pending', 'Extracting case names and years'),
            ProgressStep('Cluster', 0, 'pending', 'Clustering parallel citations'),
            ProgressStep('Verify', 0, 'pending', 'Verifying citations with external sources')
        ]
        
        # Callbacks for progress updates
        self.update_callbacks: List[Callable] = []
        
        logger.info(f"[ProgressTracker {task_id}] Initialized with {total_steps} steps")
        
    def add_update_callback(self, callback: Callable):
        """Add a callback function to be called on progress updates."""
        self.update_callbacks.append(callback)
        
    def _notify_callbacks(self):
        """Notify all registered callbacks of progress update."""
        progress_data = self.get_progress_data()
        for callback in self.update_callbacks:
            try:
                callback(progress_data)
            except Exception as e:
                logger.error(f"[ProgressTracker {self.task_id}] Callback error: {e}")
    
    def start_step(self, step_index: int, message: str = ''):
        """Start a specific step."""
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            self.steps[step_index].start(message)
            self._update_overall_progress()
            self._notify_callbacks()
            logger.info(f"[ProgressTracker {self.task_id}] Started step {step_index}: {self.steps[step_index].name}")
    
    def update_step(self, step_index: int, progress: int, message: str = ''):
        """Update progress for a specific step."""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index].update(progress, message)
            self._update_overall_progress()
            self._notify_callbacks()
    
    def complete_step(self, step_index: int, message: str = ''):
        """Mark a step as completed."""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index].complete(message)
            self._update_overall_progress()
            self._notify_callbacks()
            logger.info(f"[ProgressTracker {self.task_id}] Completed step {step_index}: {self.steps[step_index].name}")
    
    def fail_step(self, step_index: int, message: str = ''):
        """Mark a step as failed."""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index].fail(message)
            self.status = 'failed'
            self._notify_callbacks()
            logger.error(f"[ProgressTracker {self.task_id}] Failed step {step_index}: {message}")
    
    def _update_overall_progress(self):
        """Update overall progress based on step progress."""
        if not self.steps:
            self.overall_progress = 0
            return
            
        total_progress = sum(step.progress for step in self.steps)
        # FIXED: Use float division to avoid integer division issues
        self.overall_progress = min(100, int(total_progress / len(self.steps)))
        
        # Update status based on progress
        if self.overall_progress == 100:
            self.status = 'completed'
            self.end_time = time.time()
        elif any(step.status == 'failed' for step in self.steps):
            self.status = 'failed'
        elif any(step.status == 'in_progress' for step in self.steps):
            self.status = 'processing'
        else:
            self.status = 'initializing'
    
    def get_progress_data(self) -> Dict[str, Any]:
        """Get current progress data for API responses."""
        elapsed_time = max(0.0, time.time() - self.start_time)  # Ensure non-negative
        
        return {
            'task_id': self.task_id,
            'status': self.status,
            'overall_progress': self.overall_progress,
            'current_step': self.current_step,
            'total_steps': len(self.steps),
            'elapsed_time': elapsed_time,
            'current_message': self.steps[self.current_step].message if self.current_step < len(self.steps) else 'Processing...',
            'start_time': self.start_time,
            'end_time': self.end_time,
            'steps': [
                {
                    'name': step.name,
                    'progress': step.progress,
                    'status': step.status,
                    'message': step.message,
                    'start_time': step.start_time,
                    'end_time': step.end_time
                }
                for step in self.steps
            ]
        }
    
    def complete_all(self, message: str = 'Processing completed successfully'):
        """Mark all processing as completed."""
        for i, step in enumerate(self.steps):
            if step.status != 'completed':
                self.complete_step(i, f'{step.name} completed')
        
        self.status = 'completed'
        self.overall_progress = 100
        self.end_time = time.time()
        self._notify_callbacks()
        
        total_time = self.end_time - self.start_time
        logger.info(f"[ProgressTracker {self.task_id}] All processing completed in {total_time:.2f}s")

# Global progress tracker registry
_progress_trackers: Dict[str, ProgressTracker] = {}
_tracker_lock = threading.Lock()

def create_progress_tracker(task_id: str, total_steps: int = 6) -> ProgressTracker:
    """Create and register a new progress tracker."""
    with _tracker_lock:
        tracker = ProgressTracker(task_id, total_steps)
        _progress_trackers[task_id] = tracker
        return tracker

def get_progress_tracker(task_id: str) -> Optional[ProgressTracker]:
    """Get an existing progress tracker."""
    with _tracker_lock:
        return _progress_trackers.get(task_id)

def remove_progress_tracker(task_id: str):
    """Remove a progress tracker from registry."""
    with _tracker_lock:
        if task_id in _progress_trackers:
            del _progress_trackers[task_id]

def get_progress_data(task_id: str) -> Optional[Dict[str, Any]]:
    """Get progress data for a task.
    
    FIX #21: Check Redis if not found in memory (async workers run in different process!)
    FIX #23 (Sync Progress): Return completed status for sync tasks not in memory
    """
    # First check in-memory (for sync processing)
    tracker = get_progress_tracker(task_id)
    if tracker:
        return tracker.get_progress_data()
    
    # FIX #21: If not in memory, check Redis (async workers write here)
    try:
        from redis import Redis
        from src.config import REDIS_URL
        import json
        
        redis_conn = Redis.from_url(REDIS_URL)
        redis_data = redis_conn.get(f"progress:{task_id}")
        
        if redis_data:
            progress_data = json.loads(redis_data.decode('utf-8') if isinstance(redis_data, bytes) else redis_data)
            logger.info(f"✅ FIX #21: Retrieved progress from Redis for {task_id}: {progress_data.get('progress')}%")
            return progress_data
            
    except Exception as e:
        logger.error(f"Failed to get progress from Redis: {e}")
    
    # FIX #23: If task not found anywhere, it might be a completed sync task
    # Return a default "completed" status so frontend knows to stop polling
    logger.debug(f"Task {task_id} not found in memory or Redis, assuming completed sync task")
    return {
        'task_id': task_id,
        'status': 'completed',
        'overall_progress': 100,
        'current_step': 6,
        'total_steps': 6,
        'elapsed_time': 0,
        'current_message': 'Processing completed',
        'steps': []
    }

# Cleanup old trackers periodically
def cleanup_old_trackers(max_age_hours: int = 24):
    """Remove trackers older than max_age_hours."""
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    with _tracker_lock:
        to_remove = []
        for task_id, tracker in _progress_trackers.items():
            if current_time - tracker.start_time > max_age_seconds:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del _progress_trackers[task_id]
            
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old progress trackers")
