"""
Performance Monitor for CaseStrainer Optimization

This module monitors the performance of the simplified vs legacy processors
to ensure optimization goals are met.
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor performance metrics for citation processing."""

    def __init__(self):
        self.metrics = {
            "simplified": {
                "requests": 0,
                "total_time": 0.0,
                "errors": 0,
                "citations_processed": 0,
                "verification_rate": 0.0,
            },
            "legacy": {
                "requests": 0,
                "total_time": 0.0,
                "errors": 0,
                "citations_processed": 0,
                "verification_rate": 0.0,
            },
        }
        self.start_time = datetime.now()

    def record_request(
        self, processor_type: str, duration: float, success: bool, citation_count: int, verification_rate: float = 0.0
    ):
        """Record a processing request."""
        if processor_type not in self.metrics:
            processor_type = "legacy"  # Default to legacy

        self.metrics[processor_type]["requests"] += 1
        self.metrics[processor_type]["total_time"] += duration
        self.metrics[processor_type]["citations_processed"] += citation_count
        self.metrics[processor_type]["verification_rate"] += verification_rate

        if not success:
            self.metrics[processor_type]["errors"] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}

        for processor_type, data in self.metrics.items():
            if data["requests"] > 0:
                avg_time = data["total_time"] / data["requests"]
                error_rate = data["errors"] / data["requests"]
                avg_citations = data["citations_processed"] / data["requests"]
                avg_verification = data["verification_rate"] / data["requests"]
            else:
                avg_time = error_rate = avg_citations = avg_verification = 0

            summary[processor_type] = {
                "requests": data["requests"],
                "avg_time": avg_time,
                "error_rate": error_rate,
                "avg_citations": avg_citations,
                "avg_verification_rate": avg_verification,
            }

        # Calculate improvements
        if summary["legacy"]["requests"] > 0 and summary["simplified"]["requests"] > 0:
            time_improvement = (summary["legacy"]["avg_time"] - summary["simplified"]["avg_time"]) / summary["legacy"][
                "avg_time"
            ]
            error_improvement = (summary["legacy"]["error_rate"] - summary["simplified"]["error_rate"]) / max(
                summary["legacy"]["error_rate"], 0.01
            )

            summary["improvements"] = {
                "time_reduction_percent": time_improvement * 100,
                "error_reduction_percent": error_improvement * 100,
            }

        summary["uptime"] = str(datetime.now() - self.start_time)
        return summary

    def log_metrics(self):
        """Log current metrics."""
        summary = self.get_summary()

        logger.info("=== Performance Metrics ===")
        for processor_type, data in summary.items():
            if processor_type != "improvements" and processor_type != "uptime":
                logger.info(f"{processor_type.capitalize()}:")
                logger.info(f"  Requests: {data['requests']}")
                logger.info(f"  Avg time: {data['avg_time']:.2f}s")
                logger.info(f"  Error rate: {data['error_rate']:.2%}")
                logger.info(f"  Avg citations: {data['avg_citations']:.1f}")

        if "improvements" in summary:
            logger.info(f"Improvements:")
            logger.info(f"  Time reduction: {summary['improvements']['time_reduction_percent']:.1f}%")
            logger.info(f"  Error reduction: {summary['improvements']['error_reduction_percent']:.1f}%")

    def save_metrics(self, filename: str = None):
        """Save metrics to file."""
        if filename is None:
            filename = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        summary = self.get_summary()
        summary["timestamp"] = datetime.now().isoformat()

        with open(filename, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Metrics saved to: {filename}")


# Global monitor instance
_monitor = None


def get_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def monitor_performance(processor_type: str):
    """Decorator to monitor function performance."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_monitor()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                success = True

                # Extract metrics from result if available
                citation_count = 0
                verification_rate = 0.0

                if isinstance(result, dict):
                    citation_count = len(result.get("citations", []))
                    verification_results = result.get("verification_results", {})
                    if isinstance(verification_results, dict):
                        verified_count = verification_results.get("verified_count", 0)
                        total_count = verification_results.get("total_citations", 1)
                        verification_rate = verified_count / max(total_count, 1)

            except Exception as e:
                success = False
                result = None
                logger.error(f"Performance monitor caught error: {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                monitor.record_request(processor_type, duration, success, citation_count, verification_rate)

            return result

        return wrapper

    return decorator


if __name__ == "__main__":
    # Test the performance monitor
    monitor = PerformanceMonitor()

    # Simulate some requests
    monitor.record_request("simplified", 2.5, True, 10, 0.8)
    monitor.record_request("legacy", 3.2, True, 10, 0.8)
    monitor.record_request("simplified", 2.1, True, 8, 0.75)
    monitor.record_request("legacy", 3.5, False, 8, 0.0)

    monitor.log_metrics()
    monitor.save_metrics()
