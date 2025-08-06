"""
Memory Monitor for CaseStrainer
Detects and prevents memory leaks in the application
"""

import os
import sys
import time
import psutil
import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class MemoryMonitor:
    def __init__(self, threshold_mb: int = 1024, check_interval: int = 60):
        self.threshold_mb = threshold_mb
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.memory_history: List[Dict] = []
        self.max_history_size = 100
        
    def start_monitoring(self):
        """Start memory monitoring in a separate thread"""
        if self.monitoring:
            self.logger.warning("Memory monitoring already running")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info(f"Memory monitoring started (threshold: {self.threshold_mb}MB, interval: {self.check_interval}s)")
        
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        self.logger.info("Memory monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._check_memory_usage()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in memory monitoring: {e}")
                time.sleep(self.check_interval)
                
    def _check_memory_usage(self):
        """Check current memory usage and log if threshold exceeded"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # Record memory usage
        record = {
            'timestamp': datetime.now(),
            'memory_mb': memory_mb,
            'memory_percent': process.memory_percent(),
            'cpu_percent': process.cpu_percent()
        }
        
        self.memory_history.append(record)
        
        # Keep only recent history
        if len(self.memory_history) > self.max_history_size:
            self.memory_history.pop(0)
            
        # Check for memory threshold
        if memory_mb > self.threshold_mb:
            self.logger.warning(f"Memory usage exceeded threshold: {memory_mb:.1f}MB > {self.threshold_mb}MB")
            self._analyze_memory_trend()
            
        # Log memory usage periodically
        if len(self.memory_history) % 10 == 0:  # Log every 10 checks
            self.logger.info(f"Memory usage: {memory_mb:.1f}MB ({process.memory_percent():.1f}%)")
            
    def _analyze_memory_trend(self):
        """Analyze memory usage trend to detect leaks"""
        if len(self.memory_history) < 5:
            return
            
        recent = self.memory_history[-5:]
        older = self.memory_history[-10:-5] if len(self.memory_history) >= 10 else self.memory_history[:-5]
        
        if not older:
            return
            
        recent_avg = sum(r['memory_mb'] for r in recent) / len(recent)
        older_avg = sum(r['memory_mb'] for r in older) / len(older)
        
        growth_rate = (recent_avg - older_avg) / older_avg * 100
        
        if growth_rate > 10:  # 10% growth over 5 minutes
            self.logger.warning(f"Potential memory leak detected: {growth_rate:.1f}% growth over 5 minutes")
            self._suggest_recovery_actions()
            
    def _suggest_recovery_actions(self):
        """Suggest actions to recover from memory issues"""
        self.logger.info("Suggested recovery actions:")
        self.logger.info("1. Restart the application container")
        self.logger.info("2. Check for memory leaks in citation processing")
        self.logger.info("3. Reduce concurrent request limits")
        self.logger.info("4. Clear caches if available")
        
    def get_memory_stats(self) -> Dict:
        """Get current memory statistics"""
        if not self.memory_history:
            return {}
            
        latest = self.memory_history[-1]
        oldest = self.memory_history[0]
        
        return {
            'current_mb': latest['memory_mb'],
            'current_percent': latest['memory_percent'],
            'peak_mb': max(r['memory_mb'] for r in self.memory_history),
            'growth_mb': latest['memory_mb'] - oldest['memory_mb'],
            'growth_percent': ((latest['memory_mb'] - oldest['memory_mb']) / oldest['memory_mb']) * 100 if oldest['memory_mb'] > 0 else 0,
            'history_count': len(self.memory_history)
        }
        
    def force_garbage_collection(self):
        """Force garbage collection to free memory"""
        import gc
        before = psutil.Process().memory_info().rss / 1024 / 1024
        collected = gc.collect()
        after = psutil.Process().memory_info().rss / 1024 / 1024
        freed = before - after
        
        self.logger.info(f"Garbage collection freed {freed:.1f}MB (collected {collected} objects)")
        return freed

# Global memory monitor instance
memory_monitor = MemoryMonitor()

def start_memory_monitoring(threshold_mb: int = 1024, check_interval: int = 60):
    """Start memory monitoring"""
    global memory_monitor
    memory_monitor = MemoryMonitor(threshold_mb, check_interval)
    memory_monitor.start_monitoring()
    
def stop_memory_monitoring():
    """Stop memory monitoring"""
    global memory_monitor
    memory_monitor.stop_monitoring()
    
def get_memory_stats() -> Dict:
    """Get current memory statistics"""
    global memory_monitor
    return memory_monitor.get_memory_stats()
    
def force_gc():
    """Force garbage collection"""
    global memory_monitor
    return memory_monitor.force_garbage_collection()

# Memory leak detection decorator
def monitor_memory(func):
    """Decorator to monitor memory usage of functions"""
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        before_memory = process.memory_info().rss / 1024 / 1024
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            after_memory = process.memory_info().rss / 1024 / 1024
            memory_diff = after_memory - before_memory
            
            if memory_diff > 50:  # More than 50MB increase
                logging.getLogger(__name__).warning(
                    f"Function {func.__name__} used {memory_diff:.1f}MB of memory"
                )
                
    return wrapper

if __name__ == "__main__":
    # Test memory monitoring
    logging.basicConfig(level=logging.INFO)
    
    monitor = MemoryMonitor(threshold_mb=512, check_interval=10)
    monitor.start_monitoring()
    
    try:
        # Simulate memory usage
        large_list = []
        for i in range(1000000):
            large_list.append(f"item_{i}")
            if i % 100000 == 0:
                time.sleep(1)
                print(f"Added {i} items, memory: {psutil.Process().memory_info().rss / 1024 / 1024:.1f}MB")
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop_monitoring() 