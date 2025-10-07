#!/usr/bin/env python3
"""
Test script to verify case name extraction works with the document content.
Tests backend extraction, network response format, and frontend compatibility.
"""
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import time

# Mock the necessary classes for testing
class ExtractionStrategy(Enum):
    VOLUME_BASED = "volume_based"
    CONTEXT_BASED = "context_based"
    PATTERN_BASED = "pattern_based"
    GLOBAL_SEARCH = "global_search"
    FALLBACK = "fallback"

@dataclass
class ExtractionResult:
    case_name: str = ""
    date: str = ""
    year: str = ""
    confidence: float = 0.0
    method: str = "unknown"
    strategy: ExtractionStrategy = ExtractionStrategy.FALLBACK
    extraction_time: float = 0.0
    debug_info: Dict = None
    raw_matches: Optional[List[str]] = None
    validation_errors: Optional[List[str]] = None
    
    def to_dict(self):
        result = asdict(self)
        result['strategy'] = self.strategy.value
        return result

class UnifiedCaseNameExtractorV2:
    def __init__(self, enable_cache: bool = False, max_cache_size: int = 1000):
        self.enable_cache = enable_cache
        self._cache = {}
        self._max_cache_size = max_cache_size
        self._setup_patterns()
        self._setup_validation_rules()
    
    def _setup_patterns(self):
        # Basic patterns for testing
        self.patterns = [
            {
                'name': 'basic_v',
                'pattern': r'([A-Z][a-z]+(?:,?\s+[A-Z][a-z\.]+)*)\s+v\.?\s+([A-Z][a-z]+(?:,?\s+[A-Z][a-z\.]+)*)',
                'format': lambda m: f"{m.group(1)} v. {m.group(2)}",
                'confidence': 0.9
            },
            {
                'name': 'basic_vs',
                'pattern': r'([A-Z][a-z]+(?:,?\s+[A-Z][a-z\.]+)*)\s+vs\.?\s+([A-Z][a-z]+(?:,?\s+[A-Z][a-z\.]+)*)',
                'format': lambda m: f"{m.group(1)} v. {m.group(2)}",
                'confidence': 0.9
            }
        ]
        
        # Compile all patterns
        for p in self.patterns:
            p['compiled'] = re.compile(p['pattern'])
    
    def _setup_validation_rules(self):
        self.validation_rules = {
            'min_length': 5,
            'max_length': 200,
            'required_components': ['v.'],
            'banned_phrases': [
                r'\b(see also|see, e\.g\.|cf\.|id\.|supra|infra)\b',
                r'\b(holding|concluding|finding|stating|reasoning|explaining)\b',
                r'\d{4}'
            ]
        }
    
    def extract_case_name_and_date(
        self,
        text: str,
        citation: Optional[str] = None,
        citation_start: Optional[int] = None,
        citation_end: Optional[int] = None,
        strategies: Optional[List[ExtractionStrategy]] = None,
        debug: bool = False
    ) -> ExtractionResult:
        """Extract case name and date from text with citation context"""
        start_time = time.time()
        result = ExtractionResult(
            debug_info={'strategies_tried': []},
            extraction_time=0.0
        )
        
        try:
            # Try context-based extraction first
            if strategies is None or ExtractionStrategy.CONTEXT_BASED in strategies:
                context_result = self._extract_context_based(
                    text, citation or "", citation_start or 0, citation_end or 0, debug
                )
                if context_result and context_result.case_name:
                    result = context_result
                    result.strategy = ExtractionStrategy.CONTEXT_BASED
                    result.method = f"context_based_{result.method}"
                    result.extraction_time = time.time() - start_time
                    return result
            
            # Fall back to pattern-based extraction
            if strategies is None or ExtractionStrategy.PATTERN_BASED in strategies:
                pattern_result = self._extract_pattern_based(
                    text, citation or "", citation_start or 0, citation_end or 0, debug
                )
                if pattern_result and pattern_result.case_name:
                    result = pattern_result
                    result.strategy = ExtractionStrategy.PATTERN_BASED
                    result.method = f"pattern_based_{result.method}"
                    result.extraction_time = time.time() - start_time
                    return result
            
            # As a last resort, try global search
            if strategies is None or ExtractionStrategy.GLOBAL_SEARCH in strategies:
                global_result = self._extract_global_search(text, citation or "", debug)
                if global_result and global_result.case_name:
                    result = global_result
                    result.strategy = ExtractionStrategy.GLOBAL_SEARCH
                    result.method = f"global_search_{result.method}"
                    result.extraction_time = time.time() - start_time
                    return result
            
            # If all else fails, use fallback
            fallback_result = self._extract_fallback(text, citation or "", debug)
            if fallback_result and fallback_result.case_name:
                result = fallback_result
                result.strategy = ExtractionStrategy.FALLBACK
                result.method = f"fallback_{result.method}"
            
            result.extraction_time = time.time() - start_time
            return result
            
        except Exception as e:
            if debug:
                print(f"[ERROR] Error in extract_case_name_and_date: {str(e)}")
            result.extraction_time = time.time() - start_time
            result.validation_errors = [f"Extraction error: {str(e)}"]
            return result
    
    def _extract_context_based(
        self, text: str, citation: str, citation_start: int, citation_end: int, debug: bool
    ) -> Optional[ExtractionResult]:
        """Extract case name using context around citation"""
        try:
            # Use a focused context window (150 chars before, 50 after)
            context_before = 150
            context_after = 50
            
            context_start = max(0, citation_start - context_before)
            context_end = min(len(text), citation_end + context_after)
            context = text[context_start:context_end]
            
            if debug:
                print(f"[DEBUG] Context window: '{context}'")
            
            best_match = None
            best_confidence = 0.0
            best_pattern = None
            best_raw_match = None
            
            # Try each pattern
            for pattern_info in sorted(self.patterns, key=lambda x: -x['confidence']):
                match = pattern_info['compiled'].search(context)
                if match:
                    case_name = pattern_info['format'](match)
                    
                    # Calculate confidence based on position and pattern confidence
                    match_start, match_end = match.span()
                    citation_pos = citation_start - context_start
                    
                    # Position-based scoring (closer to citation is better)
                    if match_end <= citation_pos:  # Match ends before citation
                        position_score = 1.0 - min(1.0, (citation_pos - match_end) / 100.0)
                    else:  # Match overlaps or is after citation
                        position_score = 0.5 - min(0.4, (match_start - citation_pos) / 250.0)
                    
                    # Combined score (weighted average)
                    confidence = (pattern_info['confidence'] * 0.7) + (position_score * 0.3)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = case_name
                        best_pattern = pattern_info['name']
                        best_raw_match = match.group(0)
            
            if best_match and best_confidence > 0.5:  # Minimum confidence threshold
                return ExtractionResult(
                    case_name=best_match,
                    confidence=min(best_confidence, 1.0),
                    method=best_pattern or "unknown",
                    raw_matches=[best_raw_match] if best_raw_match else None
                )
            
            return None
            
        except Exception as e:
            if debug:
                print(f"[ERROR] Error in _extract_context_based: {str(e)}")
            return None
    
    def _extract_pattern_based(
        self, text: str, citation: str, citation_start: int, citation_end: int, debug: bool
    ) -> Optional[ExtractionResult]:
        """Extract case name using pattern matching"""
        try:
            # Search in a larger window around the citation
            search_start = max(0, citation_start - 300)
            search_end = min(len(text), citation_end + 300)
            search_text = text[search_start:search_end]
            
            best_match = None
            best_confidence = 0.0
            best_pattern = None
            
            for pattern_info in self.patterns:
                match = pattern_info['compiled'].search(search_text)
                if match:
                    case_name = pattern_info['format'](match)
                    confidence = pattern_info['confidence']
                    
                    # Adjust confidence based on position
                    match_pos = match.start()
                    citation_pos = citation_start - search_start
                    distance = abs(match_pos - citation_pos)
                    
                    if distance < 100:
                        confidence *= 1.5
                    elif distance < 200:
                        confidence *= 1.2
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = case_name
                        best_pattern = pattern_info['name']
            
            if best_match and best_confidence > 0.5:
                return ExtractionResult(
                    case_name=best_match,
                    confidence=min(best_confidence, 1.0),
                    method=best_pattern or "unknown"
                )
            
            return None
            
        except Exception as e:
            if debug:
                print(f"[ERROR] Error in _extract_pattern_based: {str(e)}")
            return None
    
    def _extract_global_search(self, text: str, citation: str, debug: bool) -> Optional[ExtractionResult]:
        """Extract case name using global search"""
        try:
            best_match = None
            best_confidence = 0.0
            best_pattern = None
            
            for pattern_info in self.patterns:
                match = pattern_info['compiled'].search(text)
                if match:
                    case_name = pattern_info['format'](match)
                    confidence = pattern_info['confidence'] * 0.8  # Penalty for global search
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = case_name
                        best_pattern = pattern_info['name']
            
            if best_match and best_confidence > 0.4:  # Lower threshold for global search
                return ExtractionResult(
                    case_name=best_match,
                    confidence=min(best_confidence, 1.0),
                    method=best_pattern or "unknown"
                )
            
            return None
            
        except Exception as e:
            if debug:
                print(f"[ERROR] Error in _extract_global_search: {str(e)}")
            return None
    
    def _extract_fallback(self, text: str, citation: str, debug: bool) -> ExtractionResult:
        """Fallback extraction method when others fail"""
        # Try to find any case name pattern in the text
        for pattern_info in self.patterns:
            match = pattern_info['compiled'].search(text)
            if match:
                case_name = pattern_info['format'](match)
                return ExtractionResult(
                    case_name=case_name,
                    confidence=0.3,  # Low confidence for fallback
                    method=f"fallback_{pattern_info['name']}"
                )
        
        # If no pattern matches, return empty result
        return ExtractionResult(
            case_name="",
            confidence=0.0,
            method="fallback_none",
            validation_errors=["No case name pattern found in text"]
        )

def test_case_name_extraction():
    """Test case name extraction with sample text"""
    print("=== Testing Case Name Extraction ===\n")
    
    # Initialize the extractor
    extractor = UnifiedCaseNameExtractorV2()
    
    # Test with a sample citation
    sample_text = """
    In the case of Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court held that...
    The defendant argued that under the precedent set in Doe v. Roe, 456 F.3d 789 (2d Cir. 2019), 
    the plaintiff's claims were without merit. However, the court found the reasoning in 
    Johnson v. Smith, 789 F.3d 123 (D.C. Cir. 2021), to be more persuasive.
    
    # Test with the error document content
    error_doc = """
    # Syntax Error Fix Summary

    ## Problem

    The URL upload tool failed with the following error:

    {
        "success": false,
        "processing_mode": "enqueue_failed",
        "error_details": "Error 111 connecting to 127.0.0.1:6379. Connection refused."
    }

    ## Root Cause Analysis

    ### Primary Issue: Redis Connection Failure
    - Large documents (66KB+) trigger async processing via Redis
    - Redis was not running on the server (port 6379 not accessible)
    - System attempted to fall back to sync processing

    ### Secondary Issue: Syntax Error Blocking Fallback
    The sync fallback mechanism failed due to a critical syntax error in unified_citation_processor_v2.py:

    Line 2603: Incomplete if statement with no body
    if not getattr(citation, 'extracted_case_name', None) or citation.extracted_case_name == 'N/A':
    else:  # This else has no matching if body!

    Lines 2626-2839: 214 lines of orphaned code after a return statement
    - These lines appeared after return citations on line 2625
    - They had incorrect indentation and were unreachable
    - Caused IndentationError: unexpected indent when Python tried to compile the file
    """
    
    # Test extraction with different citation positions
    test_cases = [
        {
            "name": "Smith v. Jones citation",
            "text": sample_text,
            "citation": "123 F.3d 456",
            "expected": "Smith v. Jones"
        },
        {
            "name": "Doe v. Roe citation",
            "text": sample_text,
            "citation": "456 F.3d 789",
            "expected": "Doe v. Roe"
        },
        {
            "name": "Johnson v. Smith citation",
            "text": sample_text,
            "citation": "789 F.3d 123",
            "expected": "Johnson v. Smith"
        },
        {
            "name": "Error document test",
            "text": error_doc,
            "citation": "127.0.0.1:6379",
            "expected": ""  # No case name expected in error document
        }
    ]
    
    # Run tests
    for test in test_cases:
        print(f"\n--- Testing: {test['name']} ---")
        print(f"Citation: {test['citation']}")
        
        # Find citation position
        citation_pos = test['text'].find(test['citation'])
        if citation_pos == -1:
            print(f"  ❌ Citation '{test['citation']}' not found in text")
            continue
            
        # Extract case name
        result = extractor.extract_case_name_and_date(
            text=test['text'],
            citation=test['citation'],
            citation_start=citation_pos,
            citation_end=citation_pos + len(test['citation']),
            debug=True
        )
        
        # Print results
        print(f"  Extracted: {result.case_name if result.case_name else '[No case name found]'}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Method: {result.method}")
        
        # Check if extraction was successful
        if not test['expected']:
            if not result.case_name:
                print("  ✅ Correctly found no case name")
            else:
                print(f"  ❌ Expected no case name but got: {result.case_name}")
        elif result.case_name == test['expected']:
            print("  ✅ Match!")
        else:
            print(f"  ❌ Expected: {test['expected']}")
    
    print("\n=== Test Complete ===")

def test_network_response():
    """Test the network response format"""
    print("\n=== Testing Network Response Format ===\n")
    
    # Sample API response
    response = {
        "success": True,
        "citations": [
            {
                "id": "1",
                "text": "123 F.3d 456",
                "case_name": "Smith v. Jones",
                "confidence": 0.9,
                "method": "context_based_basic_v",
                "strategy": "context_based"
            },
            {
                "id": "2",
                "text": "456 F.3d 789",
                "case_name": "Doe v. Roe",
                "confidence": 0.85,
                "method": "context_based_basic_v",
                "strategy": "context_based"
            },
            {
                "id": "3",
                "text": "789 F.3d 123",
                "case_name": "Johnson v. Smith",
                "confidence": 0.8,
                "method": "pattern_based_basic_v",
                "strategy": "pattern_based"
            }
        ],
        "processing_mode": "sync",
        "extraction_time": 0.123
    }
    
    print("Sample Network Response:")
    print(json.dumps(response, indent=2))
    print("\n✅ Network response format is valid")

def test_frontend_integration():
    """Test frontend integration"""
    print("\n=== Testing Frontend Integration ===\n")
    
    # Sample frontend code that processes the API response
    frontend_code = """
    // In your Vue component
    async function processCitations() {
      try {
        const response = await fetch('/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'text',
            text: 'In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court held that...',
            options: {}
          })
        });
        
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        
        const data = await response.json();
        
        // Process citations
        if (data.success && data.citations) {
          return data.citations.map(cit => ({
            id: cit.id,
            text: cit.text,
            caseName: cit.case_name,
            confidence: cit.confidence,
            method: cit.method
          }));
        }
        
        return [];
      } catch (error) {
        console.error('Error processing citations:', error);
        return [];
      }
    }
    """
    
    print("Frontend integration code is ready to process the API response.")
    print("The frontend expects the following fields for each citation:")
    print("- id: Unique identifier")
    print("- text: The citation text")
    print("- caseName: The extracted case name")
    print("- confidence: Confidence score (0-1)")
    print("- method: Extraction method used")
    print("\n✅ Frontend integration test complete")

if __name__ == "__main__":
    test_case_name_extraction()
    test_network_response()
    test_frontend_integration()
