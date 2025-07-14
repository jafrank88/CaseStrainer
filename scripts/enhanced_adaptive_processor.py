#!/usr/bin/env python3
"""
Enhanced Adaptive Processor that applies learned patterns and improvements.
This extends the base processor with learned patterns and confidence adjustments.
"""

import os
import sys
import json
import re
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import time
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, CitationResult

@dataclass
class LearnedPattern:
    """A learned citation pattern with success metrics."""
    pattern: str
    regex: re.Pattern
    success_count: int
    failure_count: int
    confidence_threshold: float
    context_examples: List[str]
    last_updated: float
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

class EnhancedAdaptiveProcessor:
    """Enhanced citation processor that applies learned patterns and improvements."""
    
    def __init__(self, learning_data_dir: str = "learning_data"):
        self.learning_data_dir = Path(learning_data_dir)
        
        # Initialize base processor
        self.base_processor = UnifiedCitationProcessorV2()
        
        # Learning components
        self.learned_patterns: Dict[str, LearnedPattern] = {}
        self.confidence_thresholds: Dict[str, float] = defaultdict(lambda: 0.5)
        self.case_name_database: Dict[str, List[str]] = defaultdict(list)
        
        # Load learned data
        self.load_learned_data()
        
        # Apply learned improvements to base processor
        self.apply_learned_improvements()
    
    def load_learned_data(self):
        """Load learned patterns and improvements."""
        try:
            # Load learned patterns
            patterns_file = self.learning_data_dir / "learned_patterns.pkl"
            if patterns_file.exists():
                with open(patterns_file, 'rb') as f:
                    raw_patterns = pickle.load(f)
                
                # Convert to LearnedPattern objects
                for key, pattern_data in raw_patterns.items():
                    try:
                        regex = re.compile(pattern_data.pattern, re.IGNORECASE)
                        self.learned_patterns[key] = LearnedPattern(
                            pattern=pattern_data.pattern,
                            regex=regex,
                            success_count=pattern_data.success_count,
                            failure_count=pattern_data.failure_count,
                            confidence_threshold=pattern_data.confidence_threshold,
                            context_examples=pattern_data.context_examples,
                            last_updated=pattern_data.last_updated
                        )
                    except Exception as e:
                        print(f"Warning: Could not load pattern {key}: {e}")
                
                print(f"Loaded {len(self.learned_patterns)} learned patterns")
            
            # Load confidence thresholds
            thresholds_file = self.learning_data_dir / "confidence_thresholds.json"
            if thresholds_file.exists():
                with open(thresholds_file, 'r') as f:
                    self.confidence_thresholds = defaultdict(lambda: 0.5, json.load(f))
                print(f"Loaded confidence thresholds for {len(self.confidence_thresholds)} methods")
            
            # Load case name database
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
            if learned_pattern.success_rate > 0.6:  # Only use patterns with good success rate
                pattern_name = f"learned_{key}"
                self.base_processor.citation_patterns[pattern_name] = learned_pattern.regex
                print(f"Applied learned pattern: {pattern_name} (success rate: {learned_pattern.success_rate:.2f})")
        
        # Adjust confidence thresholds in the base processor
        for method, threshold in self.confidence_thresholds.items():
            if hasattr(self.base_processor, 'config'):
                # Update the processor's confidence threshold
                self.base_processor.config.min_confidence = min(
                    self.base_processor.config.min_confidence,
                    threshold
                )
                print(f"Adjusted confidence threshold for {method}: {threshold}")
    
    def extract_with_learned_patterns(self, text: str) -> List[CitationResult]:
        """Extract citations using both base patterns and learned patterns."""
        # First, use the base processor
        base_results = self.base_processor.process_text(text)
        
        # Then, apply learned patterns for additional extractions
        learned_results = self.apply_learned_patterns(text)
        
        # Combine and deduplicate results
        all_results = base_results + learned_results
        deduplicated_results = self.deduplicate_results(all_results)
        
        # Apply learned confidence adjustments
        adjusted_results = self.apply_confidence_adjustments(deduplicated_results)
        
        return adjusted_results
    
    def apply_learned_patterns(self, text: str) -> List[CitationResult]:
        """Apply learned patterns to extract additional citations."""
        learned_results = []
        
        for key, learned_pattern in self.learned_patterns.items():
            if learned_pattern.success_rate < 0.5:
                continue  # Skip patterns with poor success rate
            
            matches = learned_pattern.regex.finditer(text)
            for match in matches:
                citation_text = match.group(0)
                
                # Check if this citation is already found by base processor
                if not self.is_citation_already_found(citation_text, text):
                    # Create new citation result
                    citation_result = CitationResult(
                        citation=citation_text,
                        method=f"learned_{key}",
                        confidence=learned_pattern.confidence_threshold,
                        start_index=match.start(),
                        end_index=match.end(),
                        pattern=learned_pattern.pattern
                    )
                    
                    # Extract context
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(text), match.end() + 100)
                    citation_result.context = text[context_start:context_end]
                    
                    learned_results.append(citation_result)
        
        return learned_results
    
    def is_citation_already_found(self, citation_text: str, text: str) -> bool:
        """Check if a citation is already found by the base processor."""
        # Simple check: look for the citation text in the original text
        # This is a basic deduplication check
        return citation_text in text
    
    def deduplicate_results(self, results: List[CitationResult]) -> List[CitationResult]:
        """Remove duplicate citations from results."""
        seen_citations = set()
        deduplicated = []
        
        for result in results:
            # Normalize citation for comparison
            normalized = self.normalize_citation_for_comparison(result.citation)
            
            if normalized not in seen_citations:
                seen_citations.add(normalized)
                deduplicated.append(result)
        
        return deduplicated
    
    def normalize_citation_for_comparison(self, citation: str) -> str:
        """Normalize citation text for deduplication comparison."""
        # Remove extra whitespace and convert to lowercase
        normalized = re.sub(r'\s+', ' ', citation.strip()).lower()
        # Remove common punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return normalized
    
    def apply_confidence_adjustments(self, results: List[CitationResult]) -> List[CitationResult]:
        """Apply learned confidence adjustments to results."""
        for result in results:
            method = result.method
            if method in self.confidence_thresholds:
                # Adjust confidence based on learned threshold
                if result.confidence < self.confidence_thresholds[method]:
                    result.confidence = self.confidence_thresholds[method]
            
            # Apply case name database improvements
            if result.extracted_case_name:
                improved_case_name = self.improve_case_name_with_database(result.extracted_case_name)
                if improved_case_name:
                    result.extracted_case_name = improved_case_name
        
        return results
    
    def improve_case_name_with_database(self, case_name: str) -> Optional[str]:
        """Improve case name using the learned database."""
        # Look for similar case names in the database
        for canonical_name, variations in self.case_name_database.items():
            if case_name in variations:
                return canonical_name
            
            # Check for similarity
            if self.calculate_similarity(case_name, canonical_name) > 0.8:
                return canonical_name
        
        return None
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names."""
        # Simple similarity calculation
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def update_learning_data(self, results: List[CitationResult], text: str):
        """Update learning data based on processing results."""
        # Update pattern success/failure counts
        for result in results:
            if result.method.startswith('learned_'):
                pattern_key = result.method.replace('learned_', '')
                if pattern_key in self.learned_patterns:
                    pattern = self.learned_patterns[pattern_key]
                    
                    # Determine if this was a successful extraction
                    # (This is a simplified heuristic - in practice you'd want more sophisticated validation)
                    if result.confidence > 0.7:
                        pattern.success_count += 1
                    else:
                        pattern.failure_count += 1
                    
                    pattern.last_updated = time.time()
        
        # Update case name database
        for result in results:
            if result.extracted_case_name and result.canonical_name:
                self.case_name_database[result.canonical_name].append(result.extracted_case_name)
    
    def save_learning_data(self):
        """Save updated learning data."""
        try:
            # Save learned patterns
            patterns_data = {}
            for key, pattern in self.learned_patterns.items():
                patterns_data[key] = {
                    'pattern': pattern.pattern,
                    'success_count': pattern.success_count,
                    'failure_count': pattern.failure_count,
                    'confidence_threshold': pattern.confidence_threshold,
                    'context_examples': pattern.context_examples,
                    'last_updated': pattern.last_updated
                }
            
            with open(self.learning_data_dir / "learned_patterns.pkl", 'wb') as f:
                pickle.dump(patterns_data, f)
            
            # Save confidence thresholds
            with open(self.learning_data_dir / "confidence_thresholds.json", 'w') as f:
                json.dump(dict(self.confidence_thresholds), f, indent=2)
            
            # Save case name database
            with open(self.learning_data_dir / "case_name_database.json", 'w') as f:
                json.dump(dict(self.case_name_database), f, indent=2)
                
        except Exception as e:
            print(f"Error saving learning data: {e}")
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about the learning system."""
        total_patterns = len(self.learned_patterns)
        successful_patterns = sum(1 for p in self.learned_patterns.values() if p.success_rate > 0.6)
        
        return {
            'total_learned_patterns': total_patterns,
            'successful_patterns': successful_patterns,
            'pattern_success_rate': successful_patterns / total_patterns if total_patterns > 0 else 0.0,
            'confidence_thresholds': dict(self.confidence_thresholds),
            'case_name_database_size': len(self.case_name_database),
            'pattern_details': [
                {
                    'key': key,
                    'pattern': pattern.pattern,
                    'success_rate': pattern.success_rate,
                    'success_count': pattern.success_count,
                    'failure_count': pattern.failure_count
                }
                for key, pattern in self.learned_patterns.items()
            ]
        }

def main():
    """Test the enhanced adaptive processor."""
    processor = EnhancedAdaptiveProcessor()
    
    # Test text
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    """
    
    print("Testing Enhanced Adaptive Processor")
    print("=" * 40)
    
    # Extract with learned patterns
    results = processor.extract_with_learned_patterns(test_text)
    
    print(f"Found {len(results)} citations:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.citation} (method: {result.method}, confidence: {result.confidence:.2f})")
    
    # Show learning stats
    stats = processor.get_learning_stats()
    print(f"\nLearning Statistics:")
    print(f"  Total learned patterns: {stats['total_learned_patterns']}")
    print(f"  Successful patterns: {stats['successful_patterns']}")
    print(f"  Pattern success rate: {stats['pattern_success_rate']:.2f}")
    print(f"  Case name database size: {stats['case_name_database_size']}")

if __name__ == "__main__":
    main() 