#!/usr/bin/env python3
"""
Performance Monitor for CaseStrainer Brief Processing
This script monitors processing times and identifies performance bottlenecks.
"""

import os
import sys
import json
import time
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@dataclass
class ProcessingMetrics:
    """Metrics for a single processing operation."""
    filename: str
    file_size: int
    text_length: int
    processing_time: float
    citations_found: int
    clusters_created: int
    cache_hits: int
    cache_misses: int
    memory_usage: float
    cpu_usage: float
    timestamp: float
    error: Optional[str] = None

@dataclass
class PerformanceSummary:
    """Summary of performance metrics."""
    total_files_processed: int
    total_processing_time: float
    avg_processing_time: float
    total_citations_found: int
    avg_citations_per_file: float
    cache_hit_rate: float
    memory_usage_avg: float
    cpu_usage_avg: float
    slowest_files: List[Dict[str, Any]]
    fastest_files: List[Dict[str, Any]]
    error_rate: float
    bottlenecks: List[Dict[str, Any]]

class PerformanceMonitor:
    """Monitor performance of brief processing operations."""
    
    def __init__(self, output_dir: str = "performance_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Performance tracking
        self.metrics: List[ProcessingMetrics] = []
        self.metrics_lock = threading.Lock()
        
        # Real-time monitoring
        self.current_operations: Dict[str, Dict[str, Any]] = {}
        self.operation_lock = threading.Lock()
        
        # Performance thresholds
        self.slow_threshold = 30.0  # seconds
        self.memory_threshold = 80.0  # percent
        self.cpu_threshold = 90.0  # percent
        
        # Setup logging
        self.setup_logging()
        
        print(f"Performance Monitor initialized. Output directory: {self.output_dir}")
    
    def setup_logging(self):
        """Setup logging for performance monitoring."""
        log_file = self.output_dir / "performance.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("PerformanceMonitor")
    
    def start_operation(self, operation_id: str, filename: str, file_size: int = 0):
        """Start monitoring a processing operation."""
        with self.operation_lock:
            self.current_operations[operation_id] = {
                'filename': filename,
                'file_size': file_size,
                'start_time': time.time(),
                'start_memory': psutil.virtual_memory().percent,
                'start_cpu': psutil.cpu_percent(interval=0.1)
            }
        
        self.logger.info(f"Started monitoring operation {operation_id} for {filename}")
    
    def update_operation(self, operation_id: str, **kwargs):
        """Update operation with progress information."""
        with self.operation_lock:
            if operation_id in self.current_operations:
                self.current_operations[operation_id].update(kwargs)
    
    def end_operation(self, operation_id: str, **kwargs):
        """End monitoring a processing operation and record metrics."""
        with self.operation_lock:
            if operation_id not in self.current_operations:
                self.logger.warning(f"Operation {operation_id} not found in current operations")
                return
            
            operation = self.current_operations.pop(operation_id)
            end_time = time.time()
            
            # Calculate metrics
            processing_time = end_time - operation['start_time']
            current_memory = psutil.virtual_memory().percent
            current_cpu = psutil.cpu_percent(interval=0.1)
            
            # Create metrics object
            metrics = ProcessingMetrics(
                filename=operation['filename'],
                file_size=operation.get('file_size', 0),
                text_length=kwargs.get('text_length', 0),
                processing_time=processing_time,
                citations_found=kwargs.get('citations_found', 0),
                clusters_created=kwargs.get('clusters_created', 0),
                cache_hits=kwargs.get('cache_hits', 0),
                cache_misses=kwargs.get('cache_misses', 0),
                memory_usage=current_memory,
                cpu_usage=current_cpu,
                timestamp=end_time,
                error=kwargs.get('error')
            )
            
            # Add to metrics list
            with self.metrics_lock:
                self.metrics.append(metrics)
            
            # Log performance
            self.log_performance(metrics)
            
            # Check for performance issues
            self.check_performance_issues(metrics)
    
    def log_performance(self, metrics: ProcessingMetrics):
        """Log performance metrics."""
        if metrics.error:
            self.logger.error(f"Processing failed for {metrics.filename}: {metrics.error}")
        else:
            self.logger.info(
                f"Processed {metrics.filename} in {metrics.processing_time:.2f}s "
                f"({metrics.citations_found} citations, {metrics.memory_usage:.1f}% memory, {metrics.cpu_usage:.1f}% CPU)"
            )
    
    def check_performance_issues(self, metrics: ProcessingMetrics):
        """Check for performance issues and log warnings."""
        issues = []
        
        if metrics.processing_time > self.slow_threshold:
            issues.append(f"Slow processing: {metrics.processing_time:.2f}s > {self.slow_threshold}s")
        
        if metrics.memory_usage > self.memory_threshold:
            issues.append(f"High memory usage: {metrics.memory_usage:.1f}% > {self.memory_threshold}%")
        
        if metrics.cpu_usage > self.cpu_threshold:
            issues.append(f"High CPU usage: {metrics.cpu_usage:.1f}% > {self.cpu_threshold}%")
        
        if issues:
            self.logger.warning(f"Performance issues detected for {metrics.filename}: {'; '.join(issues)}")
    
    def get_current_operations(self) -> Dict[str, Dict[str, Any]]:
        """Get current operations being monitored."""
        with self.operation_lock:
            return self.current_operations.copy()
    
    def get_performance_summary(self, time_window: Optional[timedelta] = None) -> PerformanceSummary:
        """Get performance summary for the specified time window."""
        with self.metrics_lock:
            if time_window:
                cutoff_time = time.time() - time_window.total_seconds()
                recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            else:
                recent_metrics = self.metrics.copy()
        
        if not recent_metrics:
            return PerformanceSummary(
                total_files_processed=0,
                total_processing_time=0.0,
                avg_processing_time=0.0,
                total_citations_found=0,
                avg_citations_per_file=0.0,
                cache_hit_rate=0.0,
                memory_usage_avg=0.0,
                cpu_usage_avg=0.0,
                slowest_files=[],
                fastest_files=[],
                error_rate=0.0,
                bottlenecks=[]
            )
        
        # Calculate basic metrics
        total_files = len(recent_metrics)
        total_time = sum(m.processing_time for m in recent_metrics)
        avg_time = total_time / total_files
        total_citations = sum(m.citations_found for m in recent_metrics)
        avg_citations = total_citations / total_files
        
        # Calculate cache hit rate
        total_cache_ops = sum(m.cache_hits + m.cache_misses for m in recent_metrics)
        cache_hit_rate = sum(m.cache_hits for m in recent_metrics) / max(1, total_cache_ops)
        
        # Calculate resource usage
        memory_avg = sum(m.memory_usage for m in recent_metrics) / total_files
        cpu_avg = sum(m.cpu_usage for m in recent_metrics) / total_files
        
        # Find slowest and fastest files
        sorted_by_time = sorted(recent_metrics, key=lambda m: m.processing_time, reverse=True)
        slowest_files = [
            {
                'filename': m.filename,
                'processing_time': m.processing_time,
                'citations_found': m.citations_found,
                'file_size': m.file_size
            }
            for m in sorted_by_time[:5]
        ]
        
        fastest_files = [
            {
                'filename': m.filename,
                'processing_time': m.processing_time,
                'citations_found': m.citations_found,
                'file_size': m.file_size
            }
            for m in sorted_by_time[-5:]
        ]
        
        # Calculate error rate
        error_count = sum(1 for m in recent_metrics if m.error)
        error_rate = error_count / total_files
        
        # Identify bottlenecks
        bottlenecks = self.identify_bottlenecks(recent_metrics)
        
        return PerformanceSummary(
            total_files_processed=total_files,
            total_processing_time=total_time,
            avg_processing_time=avg_time,
            total_citations_found=total_citations,
            avg_citations_per_file=avg_citations,
            cache_hit_rate=cache_hit_rate,
            memory_usage_avg=memory_avg,
            cpu_usage_avg=cpu_avg,
            slowest_files=slowest_files,
            fastest_files=fastest_files,
            error_rate=error_rate,
            bottlenecks=bottlenecks
        )
    
    def identify_bottlenecks(self, metrics: List[ProcessingMetrics]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks from metrics."""
        bottlenecks = []
        
        # Check for slow processing patterns
        slow_files = [m for m in metrics if m.processing_time > self.slow_threshold]
        if slow_files:
            avg_slow_time = sum(m.processing_time for m in slow_files) / len(slow_files)
            bottlenecks.append({
                'type': 'slow_processing',
                'severity': 'high' if len(slow_files) > len(metrics) * 0.2 else 'medium',
                'description': f'{len(slow_files)} files took >{self.slow_threshold}s (avg: {avg_slow_time:.2f}s)',
                'files_affected': len(slow_files),
                'recommendation': 'Consider chunking large files or optimizing extraction algorithms'
            })
        
        # Check for memory issues
        high_memory_files = [m for m in metrics if m.memory_usage > self.memory_threshold]
        if high_memory_files:
            avg_memory = sum(m.memory_usage for m in high_memory_files) / len(high_memory_files)
            bottlenecks.append({
                'type': 'high_memory_usage',
                'severity': 'high' if avg_memory > 90 else 'medium',
                'description': f'{len(high_memory_files)} files used >{self.memory_threshold}% memory (avg: {avg_memory:.1f}%)',
                'files_affected': len(high_memory_files),
                'recommendation': 'Consider reducing chunk size or implementing memory cleanup'
            })
        
        # Check for CPU issues
        high_cpu_files = [m for m in metrics if m.cpu_usage > self.cpu_threshold]
        if high_cpu_files:
            avg_cpu = sum(m.cpu_usage for m in high_cpu_files) / len(high_cpu_files)
            bottlenecks.append({
                'type': 'high_cpu_usage',
                'severity': 'medium',
                'description': f'{len(high_cpu_files)} files used >{self.cpu_threshold}% CPU (avg: {avg_cpu:.1f}%)',
                'files_affected': len(high_cpu_files),
                'recommendation': 'Consider reducing parallel processing or optimizing algorithms'
            })
        
        # Check for cache inefficiency
        low_cache_hit_rate = [m for m in metrics if m.cache_hits + m.cache_misses > 0 and m.cache_hits / (m.cache_hits + m.cache_misses) < 0.3]
        if low_cache_hit_rate:
            bottlenecks.append({
                'type': 'low_cache_efficiency',
                'severity': 'medium',
                'description': f'{len(low_cache_hit_rate)} files had low cache hit rate (<30%)',
                'files_affected': len(low_cache_hit_rate),
                'recommendation': 'Consider improving cache key generation or increasing cache size'
            })
        
        return bottlenecks
    
    def save_metrics(self, filename: Optional[str] = None):
        """Save metrics to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with self.metrics_lock:
            metrics_data = [asdict(m) for m in self.metrics]
        
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2, default=str)
        
        self.logger.info(f"Saved {len(metrics_data)} metrics to {filepath}")
    
    def load_metrics(self, filename: str):
        """Load metrics from file."""
        filepath = self.output_dir / filename
        if not filepath.exists():
            self.logger.error(f"Metrics file not found: {filepath}")
            return
        
        with open(filepath, 'r') as f:
            metrics_data = json.load(f)
        
        with self.metrics_lock:
            self.metrics = [ProcessingMetrics(**m) for m in metrics_data]
        
        self.logger.info(f"Loaded {len(self.metrics)} metrics from {filepath}")
    
    def print_summary(self, time_window: Optional[timedelta] = None):
        """Print performance summary to console."""
        summary = self.get_performance_summary(time_window)
        
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        
        if summary.total_files_processed == 0:
            print("No files processed yet.")
            return
        
        print(f"Files Processed: {summary.total_files_processed}")
        print(f"Total Processing Time: {summary.total_processing_time:.2f}s")
        print(f"Average Processing Time: {summary.avg_processing_time:.2f}s")
        print(f"Total Citations Found: {summary.total_citations_found}")
        print(f"Average Citations per File: {summary.avg_citations_per_file:.1f}")
        print(f"Cache Hit Rate: {summary.cache_hit_rate:.1%}")
        print(f"Average Memory Usage: {summary.memory_usage_avg:.1f}%")
        print(f"Average CPU Usage: {summary.cpu_usage_avg:.1f}%")
        print(f"Error Rate: {summary.error_rate:.1%}")
        
        if summary.slowest_files:
            print(f"\nSlowest Files:")
            for file_info in summary.slowest_files[:3]:
                print(f"  {file_info['filename']}: {file_info['processing_time']:.2f}s ({file_info['citations_found']} citations)")
        
        if summary.bottlenecks:
            print(f"\nPerformance Bottlenecks:")
            for bottleneck in summary.bottlenecks:
                severity_icon = "🔴" if bottleneck['severity'] == 'high' else "🟡"
                print(f"  {severity_icon} {bottleneck['description']}")
                print(f"     Recommendation: {bottleneck['recommendation']}")
        
        print("="*60)

def main():
    """Test the performance monitor."""
    monitor = PerformanceMonitor()
    
    # Simulate some processing operations
    print("Testing Performance Monitor...")
    
    # Simulate processing operations
    for i in range(5):
        operation_id = f"test_op_{i}"
        filename = f"test_file_{i}.pdf"
        
        monitor.start_operation(operation_id, filename, file_size=1024 * 1024 * (i + 1))
        
        # Simulate processing time
        time.sleep(1 + i * 0.5)
        
        # Update with progress
        monitor.update_operation(operation_id, text_length=5000 * (i + 1))
        
        # End operation
        monitor.end_operation(
            operation_id,
            text_length=5000 * (i + 1),
            citations_found=5 + i * 2,
            clusters_created=2 + i,
            cache_hits=i,
            cache_misses=1
        )
    
    # Print summary
    monitor.print_summary()
    
    # Save metrics
    monitor.save_metrics()

if __name__ == "__main__":
    main() 