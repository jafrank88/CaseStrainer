#!/usr/bin/env python3
"""
Enhanced Adaptive Processor with Performance Optimizations
This processor learns from failed extractions and applies performance optimizations.
"""

import sys
import os
import json
import time
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from collections import Counter, defaultdict
import re
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.document_processing_unified import extract_text_from_file

@dataclass
class LearnedPattern:
    """A learned citation pattern with performance metrics."""
    regex: str
    success_count: int = 0
    failure_count: int = 0
    avg_processing_time: float = 0.0
    last_used: float = 0.0
    context_examples: List[str] = None
    
    def __post_init__(self):
        if self.context_examples is None:
            self.context_examples = []
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def is_performant(self) -> bool:
        return self.success_rate > 0.6 and self.avg_processing_time < 0.1

@dataclass
class PerformanceMetrics:
    """Performance metrics for processing."""
    total_processing_time: float = 0.0
    citations_found: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    parallel_processing_time: float = 0.0
    early_terminations: int = 0

class EnhancedAdaptiveProcessor:
    """Enhanced citation processor that applies learned patterns and improvements with performance optimizations."""
    
    def __init__(self, learning_data_dir: str = "learning_data"):
        self.learning_data_dir = Path(learning_data_dir)
        
        # Initialize base processor
        self.base_processor = UnifiedCitationProcessorV2()
        
        # Learning components
        self.learned_patterns: Dict[str, LearnedPattern] = {}
        self.confidence_thresholds: Dict[str, float] = defaultdict(lambda: 0.5)
        self.case_name_database: Dict[str, List[str]] = defaultdict(list)
        
        # PERFORMANCE OPTIMIZATION: In-memory cache for frequently accessed patterns
        self.pattern_cache = {}
        self.cache_size_limit = 1000
        self.cache_hits = 0
        self.cache_misses = 0
        
        # PERFORMANCE OPTIMIZATION: Thread-safe collections
        self.cache_lock = threading.Lock()
        self.patterns_lock = threading.Lock()
        
        # Load learned data
        self.load_learned_data()
        
        # Apply learned improvements to base processor
        self.apply_learned_improvements()
        
        # Performance tracking
        self.performance_metrics = PerformanceMetrics()
        
        print(f"Enhanced Adaptive Processor initialized with {len(self.learned_patterns)} learned patterns")
    
    def load_learned_data(self):
        """Load learned patterns and data from disk."""
        try:
            patterns_file = self.learning_data_dir / "learned_patterns.pkl"
            if patterns_file.exists():
                with open(patterns_file, 'rb') as f:
                    self.learned_patterns = pickle.load(f)
                print(f"Loaded {len(self.learned_patterns)} learned patterns")
            
            thresholds_file = self.learning_data_dir / "confidence_thresholds.json"
            if thresholds_file.exists():
                with open(thresholds_file, 'r') as f:
                    self.confidence_thresholds = defaultdict(lambda: 0.5, json.load(f))
                print(f"Loaded confidence thresholds for {len(self.confidence_thresholds)} methods")
            
            case_names_file = self.learning_data_dir / "case_name_database.json"
            if case_names_file.exists():
                with open(case_names_file, 'r') as f:
                    self.case_name_database = defaultdict(list, json.load(f))
                print(f"Loaded case name database with {len(self.case_name_database)} entries")
                
        except Exception as e:
            print(f"Warning: Could not load learned data: {e}")
    
    def apply_learned_improvements(self):
        """Apply learned improvements to the base processor."""
        # Add learned patterns to the base processor's patterns
        for key, learned_pattern in self.learned_patterns.items():
            if learned_pattern.is_performant:  # Only use performant patterns
                pattern_name = f"learned_{key}"
                self.base_processor.citation_patterns[pattern_name] = learned_pattern.regex
                print(f"Applied learned pattern: {pattern_name} (success rate: {learned_pattern.success_rate:.2f}, avg time: {learned_pattern.avg_processing_time:.3f}s)")
        
        # Adjust confidence thresholds in the base processor
        for method, threshold in self.confidence_thresholds.items():
            if hasattr(self.base_processor, 'config'):
                # Update the processor's confidence threshold
                self.base_processor.config.min_confidence = min(
                    self.base_processor.config.min_confidence,
                    threshold
                )
                print(f"Adjusted confidence threshold for {method}: {threshold}")
    
    def process_text_optimized(self, text: str, filename: str = "unknown") -> Tuple[List, Dict[str, Any]]:
        """
        Process text with performance optimizations and learning.
        OPTIMIZED: Added intelligent caching, early termination, and parallel processing.
        """
        start_time = time.time()
        
        # PERFORMANCE OPTIMIZATION: Early termination for very short text
        if len(text.strip()) < 100:
            self.performance_metrics.early_terminations += 1
            return [], {
                'learning_result': {
                    'filename': filename,
                    'total_citations': 0,
                    'successful_extractions': 0,
                    'failed_extractions': 0,
                    'new_patterns_learned': 0,
                    'confidence_improvements': 0,
                    'processing_time': time.time() - start_time,
                    'timestamp': time.time(),
                    'early_termination': True
                },
                'performance_metrics': asdict(self.performance_metrics)
            }
        
        # PERFORMANCE OPTIMIZATION: Check cache for similar text patterns
        cache_key = self._generate_cache_key(text)
        with self.cache_lock:
            if cache_key in self.pattern_cache:
                self.cache_hits += 1
                self.performance_metrics.cache_hits += 1
                cached_result = self.pattern_cache[cache_key]
                # Update cache access time
                cached_result['last_accessed'] = time.time()
                return cached_result['citations'], {
                    'learning_result': {
                        'filename': filename,
                        'total_citations': len(cached_result['citations']),
                        'successful_extractions': len(cached_result['citations']),
                        'failed_extractions': 0,
                        'new_patterns_learned': 0,
                        'confidence_improvements': 0,
                        'processing_time': time.time() - start_time,
                        'timestamp': time.time(),
                        'cache_hit': True
                    },
                    'performance_metrics': asdict(self.performance_metrics)
                }
            else:
                self.cache_misses += 1
                self.performance_metrics.cache_misses += 1
        
        # PERFORMANCE OPTIMIZATION: Process text in parallel chunks for large documents
        if len(text) > 50000:  # Large document threshold
            parallel_start = time.time()
            citations = self._process_large_text_parallel(text)
            self.performance_metrics.parallel_processing_time = time.time() - parallel_start
        else:
            # Standard processing for smaller documents
            citations = self.base_processor.process_text(text)
        
        # Learn from results
        learning_info = self._learn_from_results(citations, text, filename)
        
        # PERFORMANCE OPTIMIZATION: Cache results for future use
        with self.cache_lock:
            if len(self.pattern_cache) < self.cache_size_limit:
                self.pattern_cache[cache_key] = {
                    'citations': citations,
                    'last_accessed': time.time()
                }
        
        processing_time = time.time() - start_time
        self.performance_metrics.total_processing_time += processing_time
        self.performance_metrics.citations_found += len(citations)
        
        return citations, {
            'learning_result': learning_info,
            'performance_metrics': asdict(self.performance_metrics)
        }
    
    def _process_large_text_parallel(self, text: str) -> List:
        """
        Process large text in parallel chunks for better performance.
        """
        chunk_size = 10000  # Optimized chunk size
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        all_citations = []
        citations_lock = threading.Lock()
        
        def process_chunk(chunk):
            try:
                return self.base_processor.process_text(chunk)
            except Exception as e:
                print(f"Error processing chunk: {e}")
                return []
        
        # Use ThreadPoolExecutor for parallel processing
        max_workers = min(4, len(chunks))  # Limit workers to avoid overwhelming system
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {executor.submit(process_chunk, chunk): chunk for chunk in chunks}
            
            for future in as_completed(future_to_chunk):
                try:
                    chunk_citations = future.result()
                    with citations_lock:
                        all_citations.extend(chunk_citations)
                except Exception as e:
                    print(f"Error collecting chunk results: {e}")
        
        return all_citations
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate a cache key for the text."""
        # Use hash of first 1000 characters and length for cache key
        text_sample = text[:1000] if len(text) > 1000 else text
        return f"{hash(text_sample)}_{len(text)}"
    
    def _learn_from_results(self, citations: List, text: str, filename: str) -> Dict[str, Any]:
        """Learn from processing results and update patterns."""
        start_time = time.time()
        improvements = 0
        
        # Analyze citations for learning opportunities
        for citation in citations:
            if hasattr(citation, 'confidence') and citation.confidence < 0.7:
                # Low confidence citation - potential learning opportunity
                context = self._extract_context_around_citation(text, citation)
                new_pattern = self._suggest_pattern_from_context(context)
                
                if new_pattern and new_pattern not in self.learned_patterns:
                    # Create new learned pattern
                    pattern_key = f"pattern_{len(self.learned_patterns)}"
                    self.learned_patterns[pattern_key] = LearnedPattern(
                        regex=new_pattern,
                        context_examples=[context[:200]]  # Store first 200 chars of context
                    )
                    improvements += 1
        
        # Update performance metrics for patterns
        with self.patterns_lock:
            for pattern_key, pattern in self.learned_patterns.items():
                if pattern_key.startswith('learned_'):
                    # Update pattern usage
                    pattern.last_used = time.time()
        
        # Save learning data periodically
        if improvements > 0:
            self.save_learning_data()
        
        return {
            'filename': filename,
            'total_citations': len(citations),
            'successful_extractions': len([c for c in citations if hasattr(c, 'confidence') and c.confidence > 0.7]),
            'failed_extractions': len([c for c in citations if hasattr(c, 'confidence') and c.confidence <= 0.7]),
            'new_patterns_learned': improvements,
            'confidence_improvements': improvements,
            'processing_time': time.time() - start_time,
            'timestamp': time.time()
        }
    
    def _extract_context_around_citation(self, text: str, citation) -> str:
        """Extract context around a citation for analysis using isolation-aware logic."""
        start = citation.start_index or 0
        end = citation.end_index or len(text)

        # Use a larger window and avoid cross-contamination
        context_start = max(0, start - 300)
        context_end = min(len(text), end + 100)
        context_text = text[context_start:context_end]

        # Look for citation patterns that might indicate other cases
        import re
        citation_patterns = [
            r'\b\d+\s+[A-Za-z.]+(?:\s+\d+)?\b',  # Basic citation pattern
            r'\b\d+\s+(?:Wash\.|Wn\.|P\.|A\.|S\.|N\.|F\.|U\.S\.)\b',  # Common reporters
        ]
        last_citation_pos = 0
        for pattern in citation_patterns:
            matches = list(re.finditer(pattern, context_text))
            for match in matches:
                if match.end() < (start - context_start):
                    last_citation_pos = max(last_citation_pos, match.end())
        if last_citation_pos > 0:
            sentence_pattern = re.compile(r'\.\s+[A-Z]')
            sentence_matches = list(sentence_pattern.finditer(context_text, last_citation_pos))
            if sentence_matches:
                adjusted_start = context_start + sentence_matches[0].start() + 1
                context_start = max(context_start, adjusted_start)
            else:
                context_start = max(context_start, context_start + last_citation_pos)
        return text[context_start:context_end]
    
    def _suggest_pattern_from_context(self, context: str) -> Optional[str]:
        """Suggest a new regex pattern from context."""
        # Look for citation-like patterns in context
        citation_patterns = [
            r'\b\d+\s+[A-Za-z]+\.?\s+\d+\b',  # Basic citation pattern
            r'\b\d+\s+[A-Za-z]+\s+\d+\s+[A-Za-z]+\b',  # Multi-part citation
            r'\b[A-Za-z]+\s+v\.?\s+[A-Za-z]+\b',  # Case name pattern
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, context)
            if matches:
                # Return the most specific pattern that matches
                return pattern
        
        return None
    
    def save_learning_data(self):
        """Save learned patterns and data to disk."""
        try:
            self.learning_data_dir.mkdir(exist_ok=True)
            
            # Save learned patterns
            patterns_file = self.learning_data_dir / "learned_patterns.pkl"
            with open(patterns_file, 'wb') as f:
                pickle.dump(self.learned_patterns, f)
            
            # Save confidence thresholds
            thresholds_file = self.learning_data_dir / "confidence_thresholds.json"
            with open(thresholds_file, 'w') as f:
                json.dump(dict(self.confidence_thresholds), f, indent=2)
            
            # Save case name database
            case_names_file = self.learning_data_dir / "case_name_database.json"
            with open(case_names_file, 'w') as f:
                json.dump(dict(self.case_name_database), f, indent=2)
            
            print(f"Saved learning data: {len(self.learned_patterns)} patterns, {len(self.confidence_thresholds)} thresholds")
            
        except Exception as e:
            print(f"Error saving learning data: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary and recommendations."""
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        
        # Analyze pattern performance
        performant_patterns = [p for p in self.learned_patterns.values() if p.is_performant]
        avg_processing_time = self.performance_metrics.total_processing_time / max(1, self.performance_metrics.citations_found)
        
        return {
            'cache_performance': {
                'hit_rate': cache_hit_rate,
                'hits': self.cache_hits,
                'misses': self.cache_misses
            },
            'processing_performance': {
                'total_processing_time': self.performance_metrics.total_processing_time,
                'avg_time_per_citation': avg_processing_time,
                'parallel_processing_time': self.performance_metrics.parallel_processing_time,
                'early_terminations': self.performance_metrics.early_terminations
            },
            'learning_performance': {
                'total_patterns': len(self.learned_patterns),
                'performant_patterns': len(performant_patterns),
                'pattern_success_rate': sum(p.success_rate for p in self.learned_patterns.values()) / max(1, len(self.learned_patterns))
            },
            'recommendations': self._generate_performance_recommendations()
        }
    
    def _generate_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        # Cache recommendations
        cache_hit_rate = self.cache_hits / max(1, self.cache_hits + self.cache_misses)
        if cache_hit_rate < 0.3:
            recommendations.append({
                'type': 'cache_optimization',
                'priority': 'high',
                'description': f'Low cache hit rate ({cache_hit_rate:.1%}). Consider increasing cache size or improving cache key generation.',
                'impact': 'medium'
            })
        
        # Pattern recommendations
        slow_patterns = [p for p in self.learned_patterns.values() if p.avg_processing_time > 0.1]
        if slow_patterns:
            recommendations.append({
                'type': 'pattern_optimization',
                'priority': 'medium',
                'description': f'{len(slow_patterns)} patterns are slow (>0.1s avg). Consider optimizing or removing slow patterns.',
                'impact': 'high'
            })
        
        # Parallel processing recommendations
        if self.performance_metrics.parallel_processing_time > 0:
            parallel_efficiency = self.performance_metrics.parallel_processing_time / max(1, self.performance_metrics.total_processing_time)
            if parallel_efficiency > 0.5:
                recommendations.append({
                    'type': 'parallel_optimization',
                    'priority': 'medium',
                    'description': f'High parallel processing overhead ({parallel_efficiency:.1%}). Consider adjusting chunk size or worker count.',
                    'impact': 'medium'
                })
        
        return recommendations

def main():
    """Test the enhanced adaptive processor."""
    processor = EnhancedAdaptiveProcessor()
    
    # Test with sample text
    test_text = """
    The court held in Smith v. Jones, 123 Wash. 2d 456, 789 P.3d 123 (2020) that 
    the plaintiff's claim was valid. This was consistent with the earlier decision 
    in Brown v. State, 456 Wash. 2d 789, 123 P.3d 456 (2019).
    """
    
    print("Testing Enhanced Adaptive Processor...")
    start_time = time.time()
    
    citations, learning_info = processor.process_text_optimized(test_text, "test_file.txt")
    
    processing_time = time.time() - start_time
    print(f"Processing completed in {processing_time:.3f}s")
    print(f"Found {len(citations)} citations")
    print(f"Learning info: {learning_info}")
    
    # Get performance summary
    performance_summary = processor.get_performance_summary()
    print(f"Performance summary: {json.dumps(performance_summary, indent=2)}")

if __name__ == "__main__":
    main() 