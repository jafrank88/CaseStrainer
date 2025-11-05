"""
Comprehensive tracing system for CaseStrainer citation processing.
Tracks which code paths are actually used and provides detailed debugging information.
"""

import time
import uuid
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class TraceStep:
    step_name: str
    timestamp: float
    duration_ms: float
    data: Dict[str, Any]
    citations_count: int
    memory_usage_mb: Optional[float] = None

class CitationTracer:
    """Comprehensive tracer for citation processing pipeline."""
    
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())[:8]
        self.steps: List[TraceStep] = []
        self.start_time = time.time()
        self.active_step: Optional[str] = None
        self.step_start_time: Optional[float] = None
        
    def start_step(self, step_name: str, data: Dict[str, Any] = None) -> None:
        """Start tracing a new step."""
        if self.active_step:
            self.end_step()  # Auto-end previous step
            
        self.active_step = step_name
        self.step_start_time = time.time()
        
        logger.info(f"[TRACE-{self.trace_id}] Starting {step_name}: {data or {}}")
        
    def end_step(self, citations_count: int = 0, additional_data: Dict[str, Any] = None) -> None:
        """End the current step and record timing."""
        if not self.active_step or not self.step_start_time:
            return
            
        end_time = time.time()
        duration_ms = (end_time - self.step_start_time) * 1000
        
        # Merge initial data with additional data
        data = additional_data or {}
        
        # Create trace step
        step = TraceStep(
            step_name=self.active_step,
            timestamp=self.step_start_time,
            duration_ms=duration_ms,
            data=data,
            citations_count=citations_count,
            memory_usage_mb=self._get_memory_usage()
        )
        
        self.steps.append(step)
        
        logger.info(f"[TRACE-{self.trace_id}] Completed {self.active_step} in {duration_ms:.2f}ms - {citations_count} citations")
        
        self.active_step = None
        self.step_start_time = None
        
    def trace_step(self, step_name: str, data: Dict[str, Any] = None, citations_count: int = 0) -> None:
        """Quick trace step (start and end immediately)."""
        self.start_step(step_name, data)
        self.end_step(citations_count)
        
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive trace summary."""
        total_duration = sum(step.duration_ms for step in self.steps)
        total_citations = max(step.citations_count for step in self.steps) if self.steps else 0
        
        return {
            'trace_id': self.trace_id,
            'total_duration_ms': total_duration,
            'total_citations': total_citations,
            'steps_count': len(self.steps),
            'steps': [asdict(step) for step in self.steps],
            'bottlenecks': self._identify_bottlenecks(),
            'path_taken': [step.step_name for step in self.steps]
        }
        
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify slowest steps in the pipeline."""
        if not self.steps:
            return []
            
        sorted_steps = sorted(self.steps, key=lambda s: s.duration_ms, reverse=True)
        return [
            {
                'step': step.step_name,
                'duration_ms': step.duration_ms,
                'percentage': (step.duration_ms / sum(s.duration_ms for s in self.steps)) * 100
            }
            for step in sorted_steps[:3]  # Top 3 bottlenecks
        ]
        
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return None
            
    @contextmanager
    def trace_context(self, step_name: str, data: Dict[str, Any] = None):
        """Context manager for automatic step tracing."""
        self.start_step(step_name, data)
        try:
            yield self
        finally:
            self.end_step()
            
    def log_pipeline_summary(self) -> None:
        """Log a comprehensive summary of the entire pipeline."""
        summary = self.get_summary()
        
        logger.info(f"[TRACE-{self.trace_id}] PIPELINE SUMMARY:")
        logger.info(f"  Total duration: {summary['total_duration_ms']:.2f}ms")
        logger.info(f"  Total citations: {summary['total_citations']}")
        logger.info(f"  Steps taken: {' → '.join(summary['path_taken'])}")
        
        if summary['bottlenecks']:
            logger.info(f"  Bottlenecks:")
            for bottleneck in summary['bottlenecks']:
                logger.info(f"    {bottleneck['step']}: {bottleneck['duration_ms']:.2f}ms ({bottleneck['percentage']:.1f}%)")

# Global tracer registry for active traces
_active_tracers: Dict[str, CitationTracer] = {}

def get_tracer(trace_id: str) -> Optional[CitationTracer]:
    """Get active tracer by ID."""
    return _active_tracers.get(trace_id)

def register_tracer(tracer: CitationTracer) -> str:
    """Register a tracer and return its ID."""
    _active_tracers[tracer.trace_id] = tracer
    return tracer.trace_id

def unregister_tracer(trace_id: str) -> None:
    """Unregister a tracer."""
    _active_tracers.pop(trace_id, None)

@contextmanager
def trace_citation_processing(operation_name: str, data: Dict[str, Any] = None):
    """High-level context manager for citation processing operations."""
    tracer = CitationTracer()
    register_tracer(tracer)
    
    try:
        with tracer.trace_context(operation_name, data):
            yield tracer
    finally:
        tracer.log_pipeline_summary()
        unregister_tracer(tracer.trace_id)

# Decorator for automatic function tracing
def trace_function(step_name: Optional[str] = None):
    """Decorator to automatically trace function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate step name from function name if not provided
            name = step_name or func.__name__
            
            # Get tracer from kwargs if available
            tracer = kwargs.get('tracer')
            if not tracer:
                tracer = CitationTracer()
                
            # Extract relevant data for tracing
            trace_data = {
                'function': func.__name__,
                'args_count': len(args),
                'kwargs': list(kwargs.keys())
            }
            
            tracer.start_step(name, trace_data)
            
            try:
                result = func(*args, **kwargs)
                
                # Extract citation count from result if possible
                citations_count = 0
                if hasattr(result, '__len__'):
                    citations_count = len(result)
                elif isinstance(result, dict) and 'citations' in result:
                    citations_count = len(result['citations'])
                    
                tracer.end_step(citations_count, {'success': True})
                return result
                
            except Exception as e:
                tracer.end_step(0, {'success': False, 'error': str(e)})
                raise
                
        return wrapper
    return decorator
