#!/usr/bin/env python3
"""
Enhanced Adaptive Processor for Case Name Extraction
Implements advanced pattern learning, context awareness, and validation
"""

import os
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import difflib
try:
    from fuzzywuzzy import fuzz  # type: ignore
except ImportError:
    # Fallback implementation if fuzzywuzzy is not available
    def fuzz_ratio(s1, s2):
        if not s1 or not s2:
            return 0
        s1, s2 = s1.lower(), s2.lower()
        if s1 == s2:
            return 100
        # Simple similarity calculation
        common_chars = sum(1 for c in s1 if c in s2)
        return int((common_chars / max(len(s1), len(s2))) * 100)
    
    class fuzz:
        @staticmethod
        def ratio(s1, s2):
            return fuzz_ratio(s1, s2)

@dataclass
class CaseNamePattern:
    """Represents a learned case name pattern"""
    pattern: str
    confidence: float
    success_count: int
    failure_count: int
    context_hints: List[str]
    document_types: List[str]
    last_used: float

@dataclass
class ExtractionResult:
    """Result of case name extraction"""
    case_name: str
    confidence: float
    context: str
    position: int
    pattern_used: str
    validation_score: float

class EnhancedAdaptiveProcessor:
    """
    Enhanced adaptive processor for case name extraction with:
    - Pattern learning from processed documents
    - Context-aware extraction
    - Validation and filtering
    - Performance optimization
    """
    
    def __init__(self, learning_data_dir: str):
        self.learning_data_dir = Path(learning_data_dir)
        self.learning_data_dir.mkdir(exist_ok=True)
        
        # Core patterns for legal case names
        self.base_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'In re\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+vs\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Matter of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+et al\.\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+and\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        # Invalid patterns (false positives)
        self.invalid_patterns = [
            'United States', 'State of', 'People of', 'Commonwealth of',
            'County of', 'City of', 'Town of', 'Village of',
            'Department of', 'Board of', 'Commission of'
        ]
        
        # Context hints for better extraction
        self.context_hints = [
            'case', 'matter', 'petition', 'appeal', 'review',
            'plaintiff', 'defendant', 'appellant', 'respondent',
            'petitioner', 'respondent', 'claimant'
        ]
        
        # Load learned patterns and data
        self.learned_patterns = self._load_learned_patterns()
        self.case_name_database = self._load_case_name_database()
        self.false_positives = self._load_false_positives()
        self.performance_metrics = defaultdict(int)
        
    def _load_learned_patterns(self) -> List[CaseNamePattern]:
        """Load learned patterns from file"""
        patterns_file = self.learning_data_dir / "learned_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                    return [CaseNamePattern(**pattern) for pattern in patterns_data]
            except Exception as e:
                print(f"Warning: Could not load learned patterns: {e}")
        return []
    
    def _save_learned_patterns(self):
        """Save learned patterns to file"""
        patterns_file = self.learning_data_dir / "learned_patterns.json"
        try:
            patterns_data = [asdict(pattern) for pattern in self.learned_patterns]
            with open(patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save learned patterns: {e}")
    
    def _load_case_name_database(self) -> Dict[str, Any]:
        """Load case name database"""
        db_file = self.learning_data_dir / "case_name_database.json"
        if db_file.exists():
            try:
                with open(db_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load case name database: {e}")
        return {"known_cases": {}, "patterns": {}, "statistics": {}}
    
    def _save_case_name_database(self):
        """Save case name database"""
        db_file = self.learning_data_dir / "case_name_database.json"
        try:
            with open(db_file, 'w') as f:
                json.dump(self.case_name_database, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save case name database: {e}")
    
    def _load_false_positives(self) -> List[str]:
        """Load false positives list"""
        fp_file = self.learning_data_dir / "false_positives.json"
        if fp_file.exists():
            try:
                with open(fp_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load false positives: {e}")
        return []
    
    def _save_false_positives(self):
        """Save false positives list"""
        fp_file = self.learning_data_dir / "false_positives.json"
        try:
            with open(fp_file, 'w') as f:
                json.dump(self.false_positives, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save false positives: {e}")
    
    def extract_case_names(self, text: str, document_name: str = "") -> List[ExtractionResult]:
        """
        Extract case names from text using enhanced adaptive learning
        """
        results = []
        lines = text.split('\n')
        
        # Preprocess text
        cleaned_text = self._preprocess_text(text)
        
        # Extract using base patterns
        base_results = self._extract_with_base_patterns(cleaned_text, lines)
        results.extend(base_results)
        
        # Extract using learned patterns
        learned_results = self._extract_with_learned_patterns(cleaned_text, lines)
        results.extend(learned_results)
        
        # Apply context-aware scoring
        context_results = self._apply_context_scoring(results, lines)
        
        # Validate and filter results
        validated_results = self._validate_results(context_results)
        
        # Learn from results
        self._learn_from_extractions(validated_results, document_name)
        
        return validated_results
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better extraction"""
        # Normalize spacing around legal terms
        text = re.sub(r'\s+v\.\s+', ' v. ', text)
        text = re.sub(r'\s+vs\.\s+', ' vs. ', text)
        text = re.sub(r'\s+et al\.\s+', ' et al. ', text)
        
        # Clean up OCR artifacts
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _extract_with_base_patterns(self, text: str, lines: List[str]) -> List[ExtractionResult]:
        """Extract case names using base patterns"""
        results = []
        
        for pattern in self.base_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                case_name = match.group(0)
                position = match.start()
                line_num = self._find_line_number(position, text)
                
                result = ExtractionResult(
                    case_name=case_name,
                    confidence=0.7,  # Base confidence
                    context=self._get_context(lines, line_num),
                    position=position,
                    pattern_used=pattern,
                    validation_score=0.0
                )
                results.append(result)
        
        return results
    
    def _extract_with_learned_patterns(self, text: str, lines: List[str]) -> List[ExtractionResult]:
        """Extract case names using learned patterns"""
        results = []
        
        for pattern_obj in self.learned_patterns:
            if pattern_obj.confidence > 0.5:  # Only use high-confidence patterns
                try:
                    matches = re.finditer(pattern_obj.pattern, text, re.IGNORECASE)
                    for match in matches:
                        case_name = match.group(0)
                        position = match.start()
                        line_num = self._find_line_number(position, text)
                        
                        result = ExtractionResult(
                            case_name=case_name,
                            confidence=pattern_obj.confidence,
                            context=self._get_context(lines, line_num),
                            position=position,
                            pattern_used=pattern_obj.pattern,
                            validation_score=0.0
                        )
                        results.append(result)
                except re.error:
                    # Skip invalid patterns
                    continue
        
        return results
    
    def _find_line_number(self, position: int, text: str) -> int:
        """Find line number for a given position in text"""
        return text[:position].count('\n') + 1
    
    def _get_context(self, lines: List[str], line_num: int) -> str:
        """Get context around a line"""
        start = max(0, line_num - 2)
        end = min(len(lines), line_num + 3)
        return ' '.join(lines[start:end])
    
    def _apply_context_scoring(self, results: List[ExtractionResult], lines: List[str]) -> List[ExtractionResult]:
        """Apply context-aware scoring to results"""
        for result in results:
            # Boost confidence for context hints
            context_lower = result.context.lower()
            for hint in self.context_hints:
                if hint in context_lower:
                    result.confidence += 0.1
            
            # Boost confidence for position (headers, first paragraphs)
            line_num = self._find_line_number(result.position, '\n'.join(lines))
            if line_num <= 5:  # First few lines
                result.confidence += 0.15
            elif line_num <= 20:  # First paragraph
                result.confidence += 0.1
            
            # Cap confidence at 1.0
            result.confidence = min(1.0, result.confidence)
        
        return results
    
    def _validate_results(self, results: List[ExtractionResult]) -> List[ExtractionResult]:
        """Validate and filter results"""
        validated = []
        
        for result in results:
            validation_score = self._calculate_validation_score(result)
            result.validation_score = validation_score
            
            # Filter out low-confidence results
            if validation_score > 0.3:
                validated.append(result)
        
        # Remove duplicates and similar results
        return self._deduplicate_results(validated)
    
    def _calculate_validation_score(self, result: ExtractionResult) -> float:
        """Calculate validation score for a result"""
        score = result.confidence
        
        # Check for invalid patterns
        case_name_lower = result.case_name.lower()
        for invalid in self.invalid_patterns:
            if invalid.lower() in case_name_lower:
                score -= 0.5
        
        # Check length constraints
        if len(result.case_name) < 10 or len(result.case_name) > 200:
            score -= 0.3
        
        # Check for common false positives
        if result.case_name in self.false_positives:
            score -= 0.4
        
        # Check for proper capitalization
        words = result.case_name.split()
        proper_caps = sum(1 for word in words if word[0].isupper())
        if proper_caps < len(words) * 0.7:
            score -= 0.2
        
        return max(0.0, score)
    
    def _deduplicate_results(self, results: List[ExtractionResult]) -> List[ExtractionResult]:
        """Remove duplicate and similar results"""
        if not results:
            return []
        
        # Sort by validation score (highest first)
        results.sort(key=lambda x: x.validation_score, reverse=True)
        
        unique_results = []
        for result in results:
            is_duplicate = False
            for existing in unique_results:
                similarity = fuzz.ratio(result.case_name.lower(), existing.case_name.lower())
                if similarity > 80:  # 80% similarity threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
        
        return unique_results
    
    def _learn_from_extractions(self, results: List[ExtractionResult], document_name: str):
        """Learn from extraction results"""
        for result in results:
            # Update pattern statistics
            self._update_pattern_statistics(result)
            
            # Add to case name database
            self._add_to_case_database(result, document_name)
            
            # Learn new patterns if high confidence
            if result.validation_score > 0.7:
                self._learn_new_pattern(result, document_name)
    
    def _update_pattern_statistics(self, result: ExtractionResult):
        """Update statistics for used patterns"""
        pattern = result.pattern_used
        
        # Find existing pattern or create new one
        pattern_obj = None
        for p in self.learned_patterns:
            if p.pattern == pattern:
                pattern_obj = p
                break
        
        if pattern_obj is None:
            pattern_obj = CaseNamePattern(
                pattern=pattern,
                confidence=0.5,
                success_count=0,
                failure_count=0,
                context_hints=[],
                document_types=[],
                last_used=time.time()
            )
            self.learned_patterns.append(pattern_obj)
        
        # Update statistics
        if result.validation_score > 0.5:
            pattern_obj.success_count += 1
        else:
            pattern_obj.failure_count += 1
        
        pattern_obj.last_used = time.time()
        pattern_obj.confidence = pattern_obj.success_count / (pattern_obj.success_count + pattern_obj.failure_count)
    
    def _add_to_case_database(self, result: ExtractionResult, document_name: str):
        """Add case name to database"""
        case_name = result.case_name
        if case_name not in self.case_name_database["known_cases"]:
            self.case_name_database["known_cases"][case_name] = {
                "first_seen": time.time(),
                "last_seen": time.time(),
                "confidence_scores": [],
                "documents": [],
                "patterns_used": []
            }
        
        # Update database entry
        entry = self.case_name_database["known_cases"][case_name]
        entry["last_seen"] = time.time()
        entry["confidence_scores"].append(result.validation_score)
        if document_name:
            entry["documents"].append(document_name)
        entry["patterns_used"].append(result.pattern_used)
    
    def _learn_new_pattern(self, result: ExtractionResult, document_name: str):
        """Learn new patterns from successful extractions"""
        # Extract potential patterns from context
        context_words = result.context.split()
        
        # Look for patterns around the case name
        case_words = result.case_name.split()
        if len(case_words) >= 2:
            # Try to find surrounding context
            for i, word in enumerate(context_words):
                if any(case_word.lower() in word.lower() for case_word in case_words):
                    # Found case name in context, extract pattern
                    start = max(0, i - 2)
                    end = min(len(context_words), i + len(case_words) + 2)
                    pattern_words = context_words[start:end]
                    
                    # Create regex pattern
                    pattern = r'\b' + r'\s+'.join(pattern_words) + r'\b'
                    
                    # Check if this pattern is new
                    existing_patterns = [p.pattern for p in self.learned_patterns]
                    if pattern not in existing_patterns and pattern not in self.base_patterns:
                        new_pattern = CaseNamePattern(
                            pattern=pattern,
                            confidence=0.6,
                            success_count=1,
                            failure_count=0,
                            context_hints=[word.lower() for word in pattern_words if word.lower() in self.context_hints],
                            document_types=[document_name] if document_name else [],
                            last_used=time.time()
                        )
                        self.learned_patterns.append(new_pattern)
    
    def process_text_optimized(self, text: str, document_name: str = "") -> Tuple[List[Dict], Dict]:
        """
        Process text with optimized extraction and return citations and learning info
        """
        start_time = time.time()
        
        # Extract case names
        extraction_results = self.extract_case_names(text, document_name)
        
        # Convert to citation format
        citations = []
        for result in extraction_results:
            citation = {
                'case_name': result.case_name,
                'confidence': result.validation_score,
                'context': result.context,
                'pattern_used': result.pattern_used
            }
            citations.append(citation)
        
        # Prepare learning information
        learning_info = {
            'clusters': self._create_clusters(citations),
            'learning_result': {
                'new_patterns_learned': len([p for p in self.learned_patterns if p.last_used > start_time]),
                'patterns_used': len(set(r.pattern_used for r in extraction_results)),
                'confidence_distribution': self._get_confidence_distribution(extraction_results)
            },
            'performance_metrics': {
                'cache_hits': self.performance_metrics['cache_hits'],
                'cache_misses': self.performance_metrics['cache_misses'],
                'processing_time': time.time() - start_time
            }
        }
        
        # Save learned data
        self._save_learned_patterns()
        self._save_case_name_database()
        self._save_false_positives()
        
        return citations, learning_info
    
    def _create_clusters(self, citations: List[Dict]) -> List[Dict]:
        """Create clusters from citations"""
        if not citations:
            return []
        
        # Simple clustering by similarity
        clusters = []
        used_indices = set()
        
        for i, citation in enumerate(citations):
            if i in used_indices:
                continue
            
            cluster = [citation]
            used_indices.add(i)
            
            # Find similar citations
            for j, other_citation in enumerate(citations[i+1:], i+1):
                if j in used_indices:
                    continue
                
                similarity = fuzz.ratio(
                    citation['case_name'].lower(),
                    other_citation['case_name'].lower()
                )
                
                if similarity > 70:  # 70% similarity threshold
                    cluster.append(other_citation)
                    used_indices.add(j)
            
            clusters.append({
                'citations': cluster,
                'canonical_name': cluster[0]['case_name'],
                'confidence': max(c['confidence'] for c in cluster)
            })
        
        return clusters
    
    def _get_confidence_distribution(self, results: List[ExtractionResult]) -> Dict[str, int]:
        """Get distribution of confidence scores"""
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for result in results:
            if result.validation_score >= 0.7:
                distribution['high'] += 1
            elif result.validation_score >= 0.4:
                distribution['medium'] += 1
            else:
                distribution['low'] += 1
        
        return distribution
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        total_patterns = len(self.learned_patterns)
        high_confidence_patterns = len([p for p in self.learned_patterns if p.confidence > 0.7])
        total_cases = len(self.case_name_database["known_cases"])
        
        return {
            'pattern_performance': {
                'total_patterns': total_patterns,
                'high_confidence_patterns': high_confidence_patterns,
                'pattern_success_rate': high_confidence_patterns / total_patterns if total_patterns > 0 else 0
            },
            'case_database': {
                'total_cases': total_cases,
                'unique_patterns_used': len(set(p.pattern for p in self.learned_patterns))
            },
            'learning_progress': {
                'patterns_learned': total_patterns,
                'cases_discovered': total_cases,
                'false_positives_tracked': len(self.false_positives)
            }
        } 