#!/usr/bin/env python3
"""
Enhance case name extraction for documents without Table of Authorities.
This script focuses on improving the core extraction logic to handle
real-world legal documents that don't have structured ToA sections.
"""

import os
import sys
import json
import re
from pathlib import Path
import argparse
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from collections import Counter

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from case_name_extraction_core import extract_case_name_triple_comprehensive

class EnhancedCaseExtractor:
    """Enhanced case name extraction for documents without ToA."""
    
    def __init__(self):
        # Enhanced patterns for case name extraction
        self.case_patterns = [
            # Standard v. patterns
            r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+vs\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+versus\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            
            # Government v. patterns
            r'\bState\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            r'\bPeople\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            r'\bCommonwealth\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            r'\bUnited\s+States\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            
            # Special case patterns
            r'\bIn\s+re\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            r'\bMatter\s+of\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            r'\bEx\s+parte\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            
            # Business entity patterns
            r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s*,\s*[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s*,\s*[A-Za-z0-9&.,\'\-]+)*)\b',
            
            # Department patterns
            r'\b(Dep\'t\s+of\s+[A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
            
            # Simple patterns (fallback)
            r'\b([A-Z][a-z]+(?:\s+[A-Za-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Za-z]+)*)\b',
        ]
        
        # Context patterns to find case names near citations
        self.context_patterns = [
            # Look for case names followed by citations
            r'([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*\s+v\.\s+[A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s*,\s*\d+',
            # Look for case names in parentheses before citations
            r'\(([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*\s+v\.\s+[A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\)\s*,\s*\d+',
        ]
        
        # Common legal terms to exclude
        self.exclude_terms = {
            'Plaintiff', 'Defendant', 'Appellant', 'Appellee', 'Petitioner', 'Respondent',
            'Claimant', 'Intervenor', 'Amicus', 'Curiae', 'Court', 'Judge', 'Justice',
            'Attorney', 'Counsel', 'Lawyer', 'Solicitor', 'Barrister'
        }
        
        # Business suffixes to clean
        self.business_suffixes = [
            r'\s+Inc\.?$', r'\s+Corp\.?$', r'\s+Ltd\.?$', r'\s+LLC$', r'\s+L\.L\.C\.$',
            r'\s+Co\.?$', r'\s+Company$', r'\s+Associates$', r'\s+Partners$',
            r'\s+Group$', r'\s+Enterprises$', r'\s+Industries$', r'\s+Systems$',
            r'\s+Services$', r'\s+Solutions$', r'\s+Technologies$', r'\s+International$',
            r'\s+National$', r'\s+Federal$', r'\s+State$', r'\s+County$', r'\s+City$',
            r'\s+Town$', r'\s+Village$', r'\s+District$', r'\s+Agency$', r'\s+Department$',
            r'\s+Bureau$', r'\s+Commission$', r'\s+Board$', r'\s+Council$', r'\s+Committee$'
        ]
    
    def extract_case_names_from_text(self, text: str, citation_context: str = None) -> List[Dict[str, Any]]:
        """Extract case names from text using multiple strategies."""
        results = []
        
        # Strategy 1: Direct pattern matching
        pattern_results = self._extract_with_patterns(text)
        results.extend(pattern_results)
        
        # Strategy 2: Context-based extraction around citations
        if citation_context:
            context_results = self._extract_from_context(text, citation_context)
            results.extend(context_results)
        
        # Strategy 3: Citation-adjacent extraction
        citation_adjacent = self._extract_adjacent_to_citations(text)
        results.extend(citation_adjacent)
        
        # Strategy 4: Sentence-based extraction
        sentence_results = self._extract_from_sentences(text)
        results.extend(sentence_results)
        
        # Remove duplicates and rank by confidence
        unique_results = self._deduplicate_and_rank(results)
        
        return unique_results
    
    def _extract_with_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Extract case names using regex patterns."""
        results = []
        
        for i, pattern in enumerate(self.case_patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                case_name = self._format_case_name(match, i)
                if case_name and self._is_valid_case_name(case_name):
                    results.append({
                        'case_name': case_name,
                        'method': f'pattern_{i}',
                        'confidence': self._calculate_pattern_confidence(i),
                        'position': match.start(),
                        'context': text[max(0, match.start()-50):match.end()+50]
                    })
        
        return results
    
    def _format_case_name(self, match, pattern_index: int) -> str:
        """Format case name based on pattern type."""
        if pattern_index <= 2:  # v., vs., versus patterns
            return f"{match.group(1)} v. {match.group(2)}"
        elif pattern_index == 7:  # In re pattern
            return f"In re {match.group(1)}"
        elif pattern_index == 8:  # Matter of pattern
            return f"Matter of {match.group(1)}"
        elif pattern_index == 9:  # Ex parte pattern
            return f"Ex parte {match.group(1)}"
        elif pattern_index in [3, 4, 5, 6]:  # Government v. patterns
            return f"{match.group(0)}"
        else:
            return match.group(0)
    
    def _extract_from_context(self, text: str, citation_context: str) -> List[Dict[str, Any]]:
        """Extract case names from context around citations."""
        results = []
        
        # Find citations in text
        citation_positions = []
        for match in re.finditer(r'\d+\s+[A-Za-z.]+(?:\s+\d+)*\s*\(\d{4}\)', text):
            citation_positions.append(match.start())
        
        # Look for case names before each citation
        for pos in citation_positions:
            context_start = max(0, pos - 200)
            context = text[context_start:pos]
            
            # Look for case name patterns in context
            for pattern in self.context_patterns:
                matches = re.finditer(pattern, context, re.IGNORECASE)
                for match in matches:
                    case_name = match.group(1) if match.groups() else match.group(0)
                    if self._is_valid_case_name(case_name):
                        results.append({
                            'case_name': case_name,
                            'method': 'context_extraction',
                            'confidence': 0.8,
                            'position': context_start + match.start(),
                            'context': context
                        })
        
        return results
    
    def _extract_adjacent_to_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract case names that appear immediately before citations."""
        results = []
        
        # Look for patterns like "Case Name, 123 Wn.2d 456"
        citation_pattern = r'([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s*,\s*\d+\s+[A-Za-z.]+'
        
        matches = re.finditer(citation_pattern, text)
        for match in matches:
            case_name = match.group(1)
            if self._is_valid_case_name(case_name):
                results.append({
                    'case_name': case_name,
                    'method': 'citation_adjacent',
                    'confidence': 0.9,
                    'position': match.start(),
                    'context': text[max(0, match.start()-30):match.end()+30]
                })
        
        return results
    
    def _extract_from_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Extract case names from sentence structure."""
        results = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            # Look for case name patterns in sentence
            for pattern in self.case_patterns[:5]:  # Use only high-confidence patterns
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    case_name = self._format_case_name(match, 0)
                    if self._is_valid_case_name(case_name):
                        results.append({
                            'case_name': case_name,
                            'method': 'sentence_extraction',
                            'confidence': 0.7,
                            'position': text.find(sentence),
                            'context': sentence
                        })
        
        return results
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """Validate if a case name is reasonable."""
        if not case_name or len(case_name) < 5:
            return False
        
        # Must start with capital letter
        if not case_name[0].isupper():
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', case_name):
            return False
        
        # Must not be just common words
        common_words = {'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from'}
        if case_name.lower() in common_words:
            return False
        
        # Must not be in exclude list
        if case_name in self.exclude_terms:
            return False
        
        # Must not be too long
        if len(case_name) > 100:
            return False
        
        # Must contain at least one space (for multi-word names)
        if ' ' not in case_name and case_name.lower() not in ['state', 'people', 'commonwealth']:
            return False
        
        return True
    
    def _calculate_pattern_confidence(self, pattern_index: int) -> float:
        """Calculate confidence score based on pattern type."""
        confidence_scores = {
            0: 0.95,  # v. pattern
            1: 0.90,  # vs. pattern
            2: 0.85,  # versus pattern
            3: 0.90,  # State v. pattern
            4: 0.90,  # People v. pattern
            5: 0.90,  # Commonwealth v. pattern
            6: 0.90,  # United States v. pattern
            7: 0.80,  # In re pattern
            8: 0.75,  # Matter of pattern
            9: 0.70,  # Ex parte pattern
            10: 0.85, # Business entity pattern
            11: 0.80, # Department pattern
            12: 0.60, # Simple pattern (fallback)
        }
        
        return confidence_scores.get(pattern_index, 0.5)
    
    def _deduplicate_and_rank(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and rank by confidence."""
        # Group by case name (normalized)
        case_groups = defaultdict(list)
        
        for result in results:
            normalized_name = self._normalize_case_name(result['case_name'])
            case_groups[normalized_name].append(result)
        
        # Keep the highest confidence result for each case name
        unique_results = []
        for case_name, group in case_groups.items():
            best_result = max(group, key=lambda x: x['confidence'])
            unique_results.append(best_result)
        
        # Sort by confidence (highest first)
        unique_results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return unique_results
    
    def _normalize_case_name(self, case_name: str) -> str:
        """Normalize case name for comparison."""
        # Remove business suffixes
        normalized = case_name
        for suffix in self.business_suffixes:
            normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
        
        # Normalize whitespace and punctuation
        normalized = re.sub(r'\s+', ' ', normalized.strip())
        normalized = normalized.lower()
        
        return normalized
    
    def enhance_extraction_for_document(self, text: str) -> Dict[str, Any]:
        """Enhance case name extraction for a complete document."""
        print(f"Enhancing case name extraction for document ({len(text)} characters)")
        
        # Extract case names using multiple strategies
        case_names = self.extract_case_names_from_text(text)
        
        # Analyze extraction quality
        analysis = {
            'total_extractions': len(case_names),
            'high_confidence': len([c for c in case_names if c['confidence'] >= 0.8]),
            'medium_confidence': len([c for c in case_names if 0.6 <= c['confidence'] < 0.8]),
            'low_confidence': len([c for c in case_names if c['confidence'] < 0.6]),
            'extraction_methods': Counter([c['method'] for c in case_names]),
            'case_names': case_names
        }
        
        print(f"Found {len(case_names)} case names:")
        print(f"  High confidence: {analysis['high_confidence']}")
        print(f"  Medium confidence: {analysis['medium_confidence']}")
        print(f"  Low confidence: {analysis['low_confidence']}")
        
        return analysis
    
    def compare_with_core_function(self, text: str, citation: str = None) -> Dict[str, Any]:
        """Compare enhanced extraction with core function."""
        print("Comparing enhanced extraction with core function...")
        
        # Enhanced extraction
        enhanced_results = self.extract_case_names_from_text(text, citation)
        
        # Core function extraction
        try:
            core_case_name, core_date, core_confidence = extract_case_name_triple_comprehensive(text, citation)
            core_results = [{
                'case_name': core_case_name,
                'method': 'core_function',
                'confidence': core_confidence,
                'position': -1,
                'context': 'core_function'
            }] if core_case_name else []
        except Exception as e:
            print(f"Error in core function: {e}")
            core_results = []
        
        comparison = {
            'enhanced_extractions': len(enhanced_results),
            'core_extractions': len(core_results),
            'enhanced_case_names': [r['case_name'] for r in enhanced_results],
            'core_case_names': [r['case_name'] for r in core_results],
            'enhanced_results': enhanced_results,
            'core_results': core_results
        }
        
        print(f"Enhanced extraction found: {len(enhanced_results)} case names")
        print(f"Core function found: {len(core_results)} case names")
        
        return comparison

def main():
    parser = argparse.ArgumentParser(description='Enhance case name extraction for documents without ToA')
    parser.add_argument('--text', help='Text to analyze')
    parser.add_argument('--file', help='Text file to analyze')
    parser.add_argument('--pdf', help='PDF file to analyze')
    parser.add_argument('--compare', action='store_true', help='Compare with core function')
    parser.add_argument('--output', '-o', default='enhanced_extraction_results.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    extractor = EnhancedCaseExtractor()
    
    if args.text:
        text = args.text
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif args.pdf:
        from file_utils import extract_text_from_pdf
        text = extract_text_from_pdf(args.pdf)
    else:
        # Use sample text
        text = '''
        A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
        '''
    
    # Run enhanced extraction
    results = extractor.enhance_extraction_for_document(text)
    
    # Compare with core function if requested
    if args.compare:
        comparison = extractor.compare_with_core_function(text)
        results['comparison'] = comparison
    
    # Save results
    try:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {args.output}")
    except Exception as e:
        print(f"Error saving results: {e}")

if __name__ == "__main__":
    main() 