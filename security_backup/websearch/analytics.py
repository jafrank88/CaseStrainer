"""
Analytics Module
Advanced analytics and performance tracking for web search operations.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict, Counter

from .cache import CacheManager

logger = logging.getLogger(__name__)


class AdvancedAnalytics:
    """Advanced analytics and performance tracking for web search operations."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.stats = {
            'search_attempts': defaultdict(list),
            'response_times': defaultdict(list),
            'success_rates': defaultdict(list),
            'error_counts': defaultdict(int),
            'cache_hits': 0,
            'cache_misses': 0,
            'recovery_attempts': 0,
            'recovery_successes': 0
        }
        
        # Performance thresholds
        self.thresholds = {
            'slow_response': 5.0,  # seconds
            'high_error_rate': 0.3,  # 30%
            'cache_miss_rate': 0.5   # 50%
        }
    
    def record_search_attempt(self, source: str, success: bool, response_time: float, 
                            citation: Optional[str] = None, error: Optional[Exception] = None):
        """Record a search attempt with detailed metrics."""
        timestamp = datetime.now()
        
        # Record basic stats
        self.stats['search_attempts'][source].append({
            'timestamp': timestamp,
            'success': success,
            'response_time': response_time,
            'citation': citation,
            'error': str(error) if error else None
        })
        
        # Record response time
        self.stats['response_times'][source].append(response_time)
        
        # Record success/failure
        self.stats['success_rates'][source].append(success)
        
        # Record errors
        if error:
            error_type = type(error).__name__
            self.stats['error_counts'][f"{source}_{error_type}"] += 1
        
        # Cache analytics data
        self._cache_analytics_data()
        
        # Log performance issues
        self._check_performance_issues(source, response_time, success)
    
    def _check_performance_issues(self, source: str, response_time: float, success: bool):
        """Check for performance issues and log warnings."""
        # Check for slow responses
        if response_time > self.thresholds['slow_response']:
            logger.warning(f"Slow response from {source}: {response_time:.2f}s")
        
        # Check for high error rates
        recent_attempts = self.stats['success_rates'][source][-10:]  # Last 10 attempts
        if len(recent_attempts) >= 5:
            error_rate = 1 - (sum(recent_attempts) / len(recent_attempts))
            if error_rate > self.thresholds['high_error_rate']:
                logger.warning(f"High error rate for {source}: {error_rate:.1%}")
    
    def record_cache_operation(self, hit: bool):
        """Record cache hit or miss."""
        if hit:
            self.stats['cache_hits'] += 1
        else:
            self.stats['cache_misses'] += 1
    
    def record_recovery_attempt(self, success: bool):
        """Record recovery attempt success or failure."""
        self.stats['recovery_attempts'] += 1
        if success:
            self.stats['recovery_successes'] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            'overall_stats': self._calculate_overall_stats(),
            'source_performance': self._calculate_source_performance(),
            'error_analysis': self._analyze_errors(),
            'cache_performance': self._calculate_cache_performance(),
            'recovery_stats': self._calculate_recovery_stats(),
            'recommendations': self._generate_recommendations()
        }
        
        return summary
    
    def _calculate_overall_stats(self) -> Dict[str, Any]:
        """Calculate overall performance statistics."""
        total_attempts = sum(len(attempts) for attempts in self.stats['search_attempts'].values())
        total_successes = sum(sum(rates) for rates in self.stats['success_rates'].values())
        
        if total_attempts == 0:
            return {'total_attempts': 0, 'success_rate': 0.0, 'avg_response_time': 0.0}
        
        success_rate = total_successes / total_attempts
        
        # Calculate average response time
        all_response_times = []
        for times in self.stats['response_times'].values():
            all_response_times.extend(times)
        
        avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0.0
        
        return {
            'total_attempts': total_attempts,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'total_sources_used': len(self.stats['search_attempts'])
        }
    
    def _calculate_source_performance(self) -> Dict[str, Dict[str, Any]]:
        """Calculate performance statistics for each source."""
        source_performance = {}
        
        for source in self.stats['search_attempts']:
            attempts = self.stats['search_attempts'][source]
            response_times = self.stats['response_times'][source]
            success_rates = self.stats['success_rates'][source]
            
            if not attempts:
                continue
            
            success_rate = sum(success_rates) / len(success_rates)
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            
            # Calculate recent performance (last 10 attempts)
            recent_rates = success_rates[-10:] if len(success_rates) >= 10 else success_rates
            recent_success_rate = sum(recent_rates) / len(recent_rates) if recent_rates else 0.0
            
            source_performance[source] = {
                'total_attempts': len(attempts),
                'success_rate': success_rate,
                'recent_success_rate': recent_success_rate,
                'avg_response_time': avg_response_time,
                'last_used': attempts[-1]['timestamp'] if attempts else None
            }
        
        return source_performance
    
    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns and frequencies."""
        error_analysis = {
            'total_errors': sum(self.stats['error_counts'].values()),
            'error_types': dict(self.stats['error_counts']),
            'most_common_errors': [],
            'error_trends': {}
        }
        
        # Get most common errors
        if self.stats['error_counts']:
            error_counter = Counter(self.stats['error_counts'])
            error_analysis['most_common_errors'] = error_counter.most_common(5)
        
        return error_analysis
    
    def _calculate_cache_performance(self) -> Dict[str, Any]:
        """Calculate cache performance metrics."""
        total_cache_ops = self.stats['cache_hits'] + self.stats['cache_misses']
        
        if total_cache_ops == 0:
            return {'hit_rate': 0.0, 'total_operations': 0}
        
        hit_rate = self.stats['cache_hits'] / total_cache_ops
        
        return {
            'hit_rate': hit_rate,
            'total_operations': total_cache_ops,
            'hits': self.stats['cache_hits'],
            'misses': self.stats['cache_misses']
        }
    
    def _calculate_recovery_stats(self) -> Dict[str, Any]:
        """Calculate recovery attempt statistics."""
        total_recoveries = self.stats['recovery_attempts']
        
        if total_recoveries == 0:
            return {'success_rate': 0.0, 'total_attempts': 0}
        
        success_rate = self.stats['recovery_successes'] / total_recoveries
        
        return {
            'success_rate': success_rate,
            'total_attempts': total_recoveries,
            'successes': self.stats['recovery_successes'],
            'failures': total_recoveries - self.stats['recovery_successes']
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        # Check cache performance
        cache_perf = self._calculate_cache_performance()
        if cache_perf['total_operations'] > 0 and cache_perf['hit_rate'] < 0.5:
            recommendations.append("Consider increasing cache TTL or improving cache keys")
        
        # Check source performance
        source_perf = self._calculate_source_performance()
        for source, perf in source_perf.items():
            if perf['success_rate'] < 0.7:
                recommendations.append(f"Consider deprecating or fixing {source} (success rate: {perf['success_rate']:.1%})")
            if perf['avg_response_time'] > 3.0:
                recommendations.append(f"Optimize {source} response time (avg: {perf['avg_response_time']:.2f}s)")
        
        # Check recovery performance
        recovery_stats = self._calculate_recovery_stats()
        if recovery_stats['total_attempts'] > 0 and recovery_stats['success_rate'] < 0.5:
            recommendations.append("Review error recovery strategies - low success rate")
        
        return recommendations
    
    def get_source_recommendations(self, citation: str, case_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get source recommendations based on historical performance."""
        source_perf = self._calculate_source_performance()
        
        # Filter sources with good recent performance
        good_sources = []
        for source, perf in source_perf.items():
            if perf['recent_success_rate'] >= 0.8 and perf['avg_response_time'] <= 2.0:
                good_sources.append({
                    'source': source,
                    'confidence': perf['recent_success_rate'],
                    'avg_response_time': perf['avg_response_time'],
                    'total_attempts': perf['total_attempts']
                })
        
        # Sort by confidence and response time
        good_sources.sort(key=lambda x: (x['confidence'], -x['avg_response_time']), reverse=True)
        
        return good_sources[:5]  # Return top 5 recommendations
    
    def _extract_citation_pattern(self, citation: str) -> str:
        """Extract citation pattern for analytics."""
        if not citation:
            return 'unknown'
        
        # Simple pattern extraction
        if 'Wn.' in citation or 'Wash.' in citation:
            return 'washington_state'
        elif 'U.S.' in citation:
            return 'federal_supreme'
        elif 'F.' in citation:
            return 'federal_circuit'
        elif 'P.' in citation:
            return 'pacific_reporter'
        else:
            return 'other'
    
    def export_analytics(self, filename: Optional[str] = None) -> str:
        """Export analytics data to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"websearch_analytics_{timestamp}.json"
        
        analytics_data = {
            'timestamp': datetime.now().isoformat(),
            'performance_summary': self.get_performance_summary(),
            'raw_stats': self.stats
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(analytics_data, f, indent=2, default=str)
            
            logger.info(f"Analytics exported to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to export analytics: {e}")
            return ""
    
    def _cache_analytics_data(self):
        """Cache analytics data for persistence."""
        try:
            self.cache.set('analytics_data', value=self.stats, ttl_hours=24)
        except Exception as e:
            logger.debug(f"Failed to cache analytics data: {e}")
    
    def load_cached_analytics(self):
        """Load analytics data from cache."""
        try:
            cached_data = self.cache.get('analytics_data')
            if cached_data:
                self.stats.update(cached_data)
                logger.info("Loaded analytics data from cache")
        except Exception as e:
            logger.debug(f"Failed to load cached analytics: {e}") 