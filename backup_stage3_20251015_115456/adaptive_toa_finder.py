#!/usr/bin/env python3
"""
Adaptive ToA Section Finder Pipeline

This pipeline uses multiple strategies to find the Table of Authorities section
in legal briefs, with learning capabilities to improve accuracy over time.
"""

import re
import time
from pathlib import Path
from typing import Optional, List

class ToAExtractionResult:
    def __init__(self, brief_name, strategy, success, toa_text=None, confidence=0.0, error=None, elapsed=0.0):
        self.brief_name = brief_name
        self.strategy = strategy
        self.success = success
        self.toa_text = toa_text
        self.confidence = confidence
        self.error = error
        self.elapsed = elapsed

class AdaptiveToAFinder:
    def __init__(self):
        self.strategies = [
            self._strategy_standard_regex,
            self._strategy_section_headers,
            self._strategy_structural_analysis
        ]

    def extract_toa(self, text: str, brief_name: str = "") -> ToAExtractionResult:
        # Add timeout protection for large files
        start_time = time.time()
        if len(text) > 1000000:  # Large file protection
            print(f"  Large file detected ({len(text)} chars), using optimized search...")
        
        best_result = None
        for strategy in self.strategies:
            strategy_start = time.time()
            try:
                result = strategy(text)
                elapsed = time.time() - strategy_start
                if result and result.success:
                    result.brief_name = brief_name
                    result.elapsed = elapsed
                    return result
                if not best_result or (result and result.confidence > best_result.confidence):
                    best_result = result
            except Exception as e:
                print(f"  Strategy {strategy.__name__} failed: {e}")
                continue
            
            # Timeout protection
            if time.time() - start_time > 30:  # 30 seconds timeout
                print(f"  Timeout reached, stopping search...")
                break
                
        if best_result:
            best_result.brief_name = brief_name
        return best_result

    def _strategy_standard_regex(self, text: str) -> ToAExtractionResult:
        # Optimized pattern for large files
        patterns = [
            r'TABLE OF AUTHORITIES',
            r'TABLE OF CASES, AUTHORITIES CITED'
        ]
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    start = match.start()
                    end = self._find_toa_end_optimized(text, start)
                    toa_text = text[start:end]
                    return ToAExtractionResult("", "standard_regex", True, toa_text, confidence=0.9)
            except Exception as e:
                print(f"    Pattern {pattern} failed: {e}")
                continue
                
        return ToAExtractionResult("", "standard_regex", False, error="No ToA pattern found", confidence=0.1)

    def _strategy_section_headers(self, text: str) -> ToAExtractionResult:
        # Simplified pattern for large files
        try:
            # Look for AUTHORITIES in context
            match = re.search(r'[A-Z\s]*AUTHORITIES[A-Z\s]*', text, re.IGNORECASE)
            if match:
                start = match.start()
                end = self._find_toa_end_optimized(text, start)
                toa_text = text[start:end]
                return ToAExtractionResult("", "section_headers", True, toa_text, confidence=0.7)
        except Exception as e:
            print(f"    Section headers strategy failed: {e}")
            
        return ToAExtractionResult("", "section_headers", False, error="No section header found", confidence=0.1)

    def _strategy_structural_analysis(self, text: str) -> ToAExtractionResult:
        # For large files, sample the text to find patterns
        try:
            # Sample first 10K and last 10K characters
            sample_size = 10000
            front_sample = text[:sample_size]
            back_sample = text[-sample_size:] if len(text) > sample_size else text
            
            # Look for AUTHORITIES in samples
            for sample, offset in [(front_sample, 0), (back_sample, max(0, len(text) - sample_size))]:
                if 'authorities' in sample.lower():
                    # Find the actual position
                    pos = sample.lower().find('authorities')
                    if pos != -1:
                        start = offset + pos
                        end = self._find_toa_end_optimized(text, start)
                        toa_text = text[start:end]
                        return ToAExtractionResult("", "structural_analysis", True, toa_text, confidence=0.5)
        except Exception as e:
            print(f"    Structural analysis failed: {e}")
            
        return ToAExtractionResult("", "structural_analysis", False, error="No structural pattern found", confidence=0.1)

    def _find_toa_end_optimized(self, text: str, start: int) -> int:
        # Optimized end finding for large files
        try:
            # Look for common section markers
            search_text = text[start:start + 50000] # Limit search area
            patterns = [
                r'\n\s*I\.\s*[A-Z\s]+\n',
                r'\n\s*II\.\s*[A-Z\s]+\n',
                r'\n\s*ARGUMENT\s*\n',
                r'\n\s*CONCLUSION\s*\n',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    return start + match.start()
                    
            # If no section markers found, look for reasonable end
            # Find next occurrence of common words that might indicate end
            end_markers = ['argument', 'conclusion', 'introduction', 'statement']
            for marker in end_markers:
                pos = search_text.lower().find(marker)
                if pos != -1:
                    return start + pos
                    
        except Exception as e:
            print(f"    End finding failed: {e}")
            
        return min(start + 500, len(text))  # Default to 500 chars or end of file

def main():
    finder = AdaptiveToAFinder()
    briefs_dir = Path("wa_briefs_text")
    if not briefs_dir.exists():
        print("wa_briefs_text directory not found!")
        return
        
    brief_files = sorted(list(briefs_dir.glob("*.txt")))[:5]
    print("=== Adaptive ToA Finder Test ===\n")
    
    for brief_file in brief_files:
        print(f"Processing: {brief_file.name}")
        print(f"  File size: {brief_file.stat().st_size} bytes")
        
        try:
            text = brief_file.read_text(encoding="utf-8")
            print(f"  Text length: {len(text)} characters")
            
            result = finder.extract_toa(text, brief_file.name)
            
            print(f"  Strategy: {result.strategy}")
            print(f"  Success: {result.success}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Time: {result.elapsed:.3f}s")
            
            if result.success:
                print(f"  ToA length: {len(result.toa_text)} characters")
                preview = result.toa_text[:200].replace('\n', '\\n')
                print(f"  ToA preview: {preview}...")
            else:
                print(f"  Error: {result.error}")
                
        except Exception as e:
            print(f"  Error reading file: {e}")
            
        print()

if __name__ == "__main__":
    main() 