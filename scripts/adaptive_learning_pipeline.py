#!/usr/bin/env python3
"""
Adaptive Learning Pipeline for Citation Extraction
This pipeline learns from failed extractions to continuously improve the tool.
"""

import sys
import os
import json
import time
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import argparse
import logging
from collections import Counter, defaultdict
import re
from dataclasses import dataclass, asdict

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.document_processing_unified import extract_text_from_file
from src.toa_parser import ToAParser
from difflib import SequenceMatcher

@dataclass
class LearningResult:
    """Result of learning from a processing attempt."""
    filename: str
    total_citations: int
    successful_extractions: int
    failed_extractions: int
    new_patterns_learned: int
    confidence_improvements: int
    processing_time: float
    timestamp: float

@dataclass
class FailedExtraction:
    """Represents a failed extraction attempt."""
    text_context: str
    expected_citation: str
    extraction_method: str
    confidence: float
    error_type: str
    suggested_pattern: Optional[str] = None
    timestamp: float = None

@dataclass
class PatternLearning:
    """Represents a learned pattern."""
    pattern: str
    success_count: int
    failure_count: int
    confidence_threshold: float
    context_examples: List[str]
    last_updated: float

class AdaptiveCitationProcessor:
    """Citation processor that learns from failed extractions."""
    
    def __init__(self, learning_data_dir: str = "learning_data"):
        self.learning_data_dir = Path(learning_data_dir)
        self.learning_data_dir.mkdir(exist_ok=True)
        
        # Initialize the base processor
        self.base_processor = UnifiedCitationProcessorV2()
        
        # Learning components
        self.failed_extractions: List[FailedExtraction] = []
        self.learned_patterns: Dict[str, PatternLearning] = {}
        self.case_name_database: Dict[str, List[str]] = defaultdict(list)
        self.confidence_thresholds: Dict[str, float] = defaultdict(lambda: 0.5)
        
        # Load existing learning data
        self.load_learning_data()
        
        # Track processing statistics
        self.total_processed = 0
        self.total_improvements = 0
        self.learning_history: List[LearningResult] = []
    
    def load_learning_data(self):
        """Load existing learning data from files."""
        try:
            # Load failed extractions
            failed_file = self.learning_data_dir / "failed_extractions.pkl"
            if failed_file.exists():
                with open(failed_file, 'rb') as f:
                    self.failed_extractions = pickle.load(f)
                print(f"Loaded {len(self.failed_extractions)} failed extractions")
            
            # Load learned patterns
            patterns_file = self.learning_data_dir / "learned_patterns.pkl"
            if patterns_file.exists():
                with open(patterns_file, 'rb') as f:
                    self.learned_patterns = pickle.load(f)
                print(f"Loaded {len(self.learned_patterns)} learned patterns")
            
            # Load case name database
            case_names_file = self.learning_data_dir / "case_name_database.json"
            if case_names_file.exists():
                with open(case_names_file, 'r') as f:
                    self.case_name_database = defaultdict(list, json.load(f))
                print(f"Loaded case name database with {len(self.case_name_database)} entries")
            
            # Load confidence thresholds
            thresholds_file = self.learning_data_dir / "confidence_thresholds.json"
            if thresholds_file.exists():
                with open(thresholds_file, 'r') as f:
                    self.confidence_thresholds = defaultdict(lambda: 0.5, json.load(f))
                print(f"Loaded confidence thresholds for {len(self.confidence_thresholds)} methods")
                
        except Exception as e:
            print(f"Warning: Could not load learning data: {e}")
    
    def save_learning_data(self):
        """Save learning data to files."""
        try:
            # Save failed extractions
            with open(self.learning_data_dir / "failed_extractions.pkl", 'wb') as f:
                pickle.dump(self.failed_extractions, f)
            
            # Save learned patterns
            with open(self.learning_data_dir / "learned_patterns.pkl", 'wb') as f:
                pickle.dump(self.learned_patterns, f)
            
            # Save case name database
            with open(self.learning_data_dir / "case_name_database.json", 'w') as f:
                json.dump(dict(self.case_name_database), f, indent=2)
            
            # Save confidence thresholds
            with open(self.learning_data_dir / "confidence_thresholds.json", 'w') as f:
                json.dump(dict(self.confidence_thresholds), f, indent=2)
                
        except Exception as e:
            print(f"Error saving learning data: {e}")
    
    def analyze_failed_extractions(self) -> Dict[str, Any]:
        """Analyze failed extractions to identify patterns and improvement opportunities."""
        if not self.failed_extractions:
            return {"error_types": {}, "suggested_improvements": []}
        
        # Analyze error types
        error_types = Counter()
        method_failures = Counter()
        context_patterns = []
        
        for failure in self.failed_extractions:
            error_types[failure.error_type] += 1
            method_failures[failure.extraction_method] += 1
            
            # Extract context patterns
            context_words = re.findall(r'\b[A-Z][a-z]+\b', failure.text_context)
            context_patterns.extend(context_words[:5])  # First 5 capitalized words
        
        # Identify common failure patterns
        common_contexts = Counter(context_patterns).most_common(10)
        
        # Generate improvement suggestions
        suggestions = []
        
        if error_types.get('pattern_mismatch', 0) > 5:
            suggestions.append({
                'type': 'pattern_learning',
                'description': f"High pattern mismatch errors ({error_types['pattern_mismatch']}). Consider learning new patterns.",
                'priority': 'high'
            })
        
        if error_types.get('low_confidence', 0) > 10:
            suggestions.append({
                'type': 'confidence_adjustment',
                'description': f"Many low confidence extractions ({error_types['low_confidence']}). Consider adjusting confidence thresholds.",
                'priority': 'medium'
            })
        
        if method_failures.get('regex', 0) > method_failures.get('eyecite', 0):
            suggestions.append({
                'type': 'method_optimization',
                'description': "Regex method failing more than eyecite. Consider improving regex patterns.",
                'priority': 'medium'
            })
        
        return {
            'total_failures': len(self.failed_extractions),
            'error_types': dict(error_types),
            'method_failures': dict(method_failures),
            'common_contexts': common_contexts,
            'suggested_improvements': suggestions
        }
    
    def learn_from_failures(self) -> int:
        """Learn new patterns and improve confidence thresholds from failed extractions."""
        improvements = 0
        
        # Group failures by error type
        pattern_failures = [f for f in self.failed_extractions if f.error_type == 'pattern_mismatch']
        confidence_failures = [f for f in self.failed_extractions if f.error_type == 'low_confidence']
        
        # Learn new patterns from pattern failures
        for failure in pattern_failures:
            if failure.suggested_pattern:
                pattern_key = f"learned_{len(self.learned_patterns)}"
                if pattern_key not in self.learned_patterns:
                    self.learned_patterns[pattern_key] = PatternLearning(
                        pattern=failure.suggested_pattern,
                        success_count=0,
                        failure_count=1,
                        confidence_threshold=0.6,
                        context_examples=[failure.text_context[:100]],
                        last_updated=time.time()
                    )
                    improvements += 1
        
        # Adjust confidence thresholds based on confidence failures
        for failure in confidence_failures:
            method = failure.extraction_method
            current_threshold = self.confidence_thresholds[method]
            
            # Lower threshold if we're missing too many extractions
            if failure.confidence > current_threshold * 0.8:
                self.confidence_thresholds[method] = current_threshold * 0.9
                improvements += 1
        
        return improvements
    
    def extract_with_learning(self, text: str, filename: str = "unknown") -> Tuple[List, Dict[str, Any]]:
        """Extract citations with learning from failures."""
        start_time = time.time()
        
        # First pass: Use base processor
        base_results = self.base_processor.process_text(text)
        
        # Analyze results and identify potential failures
        potential_failures = []
        successful_extractions = 0
        
        for citation in base_results:
            # Check if this looks like a failed extraction
            if citation.confidence < self.confidence_thresholds.get(citation.method, 0.5):
                # This might be a failure - analyze context
                context = self._extract_context_around_citation(text, citation)
                
                potential_failure = FailedExtraction(
                    text_context=context,
                    expected_citation=citation.citation,
                    extraction_method=citation.method,
                    confidence=citation.confidence,
                    error_type='low_confidence',
                    suggested_pattern=self._suggest_pattern_from_context(context),
                    timestamp=time.time()
                )
                potential_failures.append(potential_failure)
            else:
                successful_extractions += 1
        
        # Learn from potential failures
        if potential_failures:
            self.failed_extractions.extend(potential_failures)
            improvements = self.learn_from_failures()
            self.total_improvements += improvements
        else:
            improvements = 0
        
        # Create learning result
        learning_result = LearningResult(
            filename=filename,
            total_citations=len(base_results),
            successful_extractions=successful_extractions,
            failed_extractions=len(potential_failures),
            new_patterns_learned=improvements,
            confidence_improvements=improvements,
            processing_time=time.time() - start_time,
            timestamp=time.time()
        )
        
        self.learning_history.append(learning_result)
        self.total_processed += 1
        
        # Save learning data periodically
        if self.total_processed % 10 == 0:
            self.save_learning_data()
        
        return base_results, {
            'learning_result': asdict(learning_result),
            'potential_failures': len(potential_failures),
            'improvements': improvements
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
        """Suggest a new pattern based on context analysis."""
        # Look for citation-like patterns in the context
        citation_patterns = [
            r'\b\d+\s+[A-Za-z]+\.\s*\d+[a-z]*\s+\d+\b',  # Basic citation pattern
            r'\b\d+\s+[A-Za-z]+\s+\d+\b',  # Simplified pattern
            r'\b[A-Z][a-z]+\.\s*\d+[a-z]*\s+\d+\b',  # Reporter pattern
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, context)
            if matches:
                return pattern
        
        return None
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of learning progress."""
        failure_analysis = self.analyze_failed_extractions()
        
        return {
            'total_processed': self.total_processed,
            'total_improvements': self.total_improvements,
            'learned_patterns': len(self.learned_patterns),
            'failed_extractions': len(self.failed_extractions),
            'case_name_database_size': len(self.case_name_database),
            'failure_analysis': failure_analysis,
            'recent_improvements': [
                asdict(result) for result in self.learning_history[-5:]
            ]
        }

class AdaptiveLearningPipeline:
    """Main pipeline for adaptive learning."""
    
    def __init__(self, briefs_dir: str = "wa_briefs", output_dir: str = "adaptive_results"):
        self.briefs_dir = Path(briefs_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize adaptive processor
        self.adaptive_processor = AdaptiveCitationProcessor()
        
        # Track results
        self.results = []
    
    def process_briefs_with_learning(self):
        """Process all briefs with adaptive learning."""
        print("Starting Adaptive Learning Pipeline")
        print("=" * 50)
        
        pdf_files = list(self.briefs_dir.glob("*.pdf"))
        if not pdf_files:
            print("No PDF files found to process")
            return
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\nProcessing {i}/{len(pdf_files)}: {pdf_path.name}")
            
            try:
                # Extract text
                text = extract_text_from_file(str(pdf_path))
                if not text or len(text.strip()) < 100:
                    print(f"  Skipped: Text too short")
                    continue
                
                # Process with learning
                citations, learning_info = self.adaptive_processor.extract_with_learning(
                    text, pdf_path.name
                )

                # --- ToA Extraction and Comparison Logic ---
                toa_parser = ToAParser()
                toa_section = toa_parser.detect_toa_section(text)
                toa_entries = []
                if toa_section:
                    start, end = toa_section
                    toa_text = text[start:end]
                    toa_entries = toa_parser.parse_toa_section(toa_text)

                # Prepare ToA entries as dicts for easier matching
                toa_dicts = [
                    {
                        'case_name': entry.case_name,
                        'citations': entry.citations,
                        'years': entry.years
                    } for entry in toa_entries
                ]

                def compare_fields(field1, field2):
                    if field1 == field2:
                        return "exact"
                    elif field1 and field2 and SequenceMatcher(None, field1, field2).ratio() > 0.8:
                        return "partial"
                    else:
                        return "mismatch"

                def find_best_toa_match(extracted, toa_dicts):
                    # Try to match by citation first
                    for toa in toa_dicts:
                        if extracted['citation'] in toa['citations']:
                            return toa
                    # Fallback: best fuzzy match on case name
                    best_ratio = 0
                    best_toa = None
                    for toa in toa_dicts:
                        ratio = SequenceMatcher(None, extracted['case_name'], toa['case_name']).ratio()
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_toa = toa
                    return best_toa

                # Build extracted citation dicts for comparison
                extracted_dicts = []
                for c in citations:
                    extracted_dicts.append({
                        'case_name': getattr(c, 'extracted_case_name', None) or getattr(c, 'case_name', None) or '',
                        'citation': getattr(c, 'citation', None) or '',
                        'year': getattr(c, 'extracted_date', None) or getattr(c, 'year', None) or ''
                    })

                comparison_results = []
                summary_stats = {'case_name': {'exact': 0, 'partial': 0, 'mismatch': 0, 'no_match': 0},
                                 'citation': {'exact': 0, 'partial': 0, 'mismatch': 0, 'no_match': 0},
                                 'year': {'exact': 0, 'partial': 0, 'mismatch': 0, 'no_match': 0}}

                for extracted in extracted_dicts:
                    toa = find_best_toa_match(extracted, toa_dicts) if toa_dicts else None
                    if toa:
                        # For year, compare to any year in ToA entry
                        year_status = "no_match"
                        if extracted['year'] and toa['years']:
                            if extracted['year'] in toa['years']:
                                year_status = "exact"
                            elif any(SequenceMatcher(None, extracted['year'], y).ratio() > 0.8 for y in toa['years']):
                                year_status = "partial"
                            else:
                                year_status = "mismatch"
                        elif not extracted['year'] and not toa['years']:
                            year_status = "exact"
                        else:
                            year_status = "no_match"
                        match_status = {
                            'case_name': compare_fields(extracted['case_name'], toa['case_name']),
                            'citation': "exact" if extracted['citation'] in toa['citations'] else "mismatch",
                            'year': year_status
                        }
                    else:
                        match_status = {'case_name': 'no_match', 'citation': 'no_match', 'year': 'no_match'}
                        toa = {'case_name': '', 'citations': [], 'years': []}
                    for k in ['case_name', 'citation', 'year']:
                        summary_stats[k][match_status[k]] += 1
                    comparison_results.append({
                        'extracted': extracted,
                        'toa': toa,
                        'match_status': match_status
                    })

                # Store results
                result = {
                    'filename': pdf_path.name,
                    'citations_count': len(citations),
                    'learning_info': learning_info,
                    'comparison_results': comparison_results,
                    'summary_stats': summary_stats,
                    'timestamp': time.time()
                }
                self.results.append(result)
                # Save detailed comparison for this file
                comp_file = self.output_dir / f"comparison_{pdf_path.stem}.json"
                with open(comp_file, 'w', encoding='utf-8') as f:
                    json.dump({'comparison_results': comparison_results, 'summary_stats': summary_stats}, f, indent=2, ensure_ascii=False)
                print(f"  Extracted {len(citations)} citations")
                print(f"  Learning: {learning_info['improvements']} improvements")
                print(f"  Comparison: {summary_stats}")
                
            except Exception as e:
                print(f"  Error processing {pdf_path.name}: {e}")
        
        # Final learning summary
        self.save_results()
        self.print_learning_summary()
    
    def save_results(self):
        """Save processing results and learning data."""
        # Save results
        results_file = self.output_dir / "adaptive_processing_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Save learning summary
        learning_summary = self.adaptive_processor.get_learning_summary()
        summary_file = self.output_dir / "learning_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(learning_summary, f, indent=2, default=str)
        
        # Save learning data
        self.adaptive_processor.save_learning_data()
        
        print(f"\nResults saved to {self.output_dir}")
    
    def print_learning_summary(self):
        """Print a summary of learning progress."""
        summary = self.adaptive_processor.get_learning_summary()
        
        print("\n" + "=" * 50)
        print("ADAPTIVE LEARNING SUMMARY")
        print("=" * 50)
        print(f"Total briefs processed: {summary['total_processed']}")
        print(f"Total improvements made: {summary['total_improvements']}")
        print(f"Learned patterns: {summary['learned_patterns']}")
        print(f"Failed extractions analyzed: {summary['failed_extractions']}")
        print(f"Case name database entries: {summary['case_name_database_size']}")
        
        # Show failure analysis
        failure_analysis = summary['failure_analysis']
        if failure_analysis['total_failures'] > 0:
            print(f"\nFailure Analysis:")
            print(f"  Total failures: {failure_analysis['total_failures']}")
            print(f"  Error types: {failure_analysis['error_types']}")
            print(f"  Suggested improvements: {len(failure_analysis['suggested_improvements'])}")
            
            for suggestion in failure_analysis['suggested_improvements']:
                print(f"    - {suggestion['description']} (Priority: {suggestion['priority']})")

def main():
    parser = argparse.ArgumentParser(description='Adaptive Learning Pipeline for Citation Extraction')
    parser.add_argument('--briefs-dir', default='wa_briefs', help='Directory containing brief PDFs')
    parser.add_argument('--output-dir', default='adaptive_results', help='Output directory for results')
    parser.add_argument('--learning-data-dir', default='learning_data', help='Directory for learning data')
    
    args = parser.parse_args()
    
    pipeline = AdaptiveLearningPipeline(args.briefs_dir, args.output_dir)
    pipeline.process_briefs_with_learning()

if __name__ == "__main__":
    main() 