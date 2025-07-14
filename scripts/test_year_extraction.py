#!/usr/bin/env python3
"""
Test script specifically for year extraction from citations in WA briefs.
Validates the year extraction logic and provides detailed analysis.
"""

import os
import sys
import json
import re
from pathlib import Path
import argparse
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import with absolute paths to avoid relative import issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessor
from src.case_name_extraction_core import extract_case_name_triple_comprehensive
from src.file_utils import extract_text_from_pdf

class YearExtractionTester:
    """Test year extraction from citations."""
    
    def __init__(self):
        self.processor = UnifiedCitationProcessor()
        self.year_patterns = [
            r'\b(19|20)\d{2}\b',  # 4-digit years
            r'\b\d{2}\b',  # 2-digit years (context dependent)
        ]
        
    def extract_years_from_text(self, text: str) -> List[Tuple[str, int]]:
        """Extract all potential years from text with context."""
        years = []
        
        # Find all 4-digit years
        for match in re.finditer(r'\b(19|20)\d{2}\b', text):
            year = int(match.group())
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 50)
            context = text[context_start:context_end]
            years.append((context.strip(), year))
        
        return years
    
    def test_citation_year_extraction(self, citation: str) -> Dict[str, Any]:
        """Test year extraction from a single citation."""
        result = {
            'citation': citation,
            'extracted_years': [],
            'extraction_method': None,
            'confidence': 0.0
        }
        
        # Method 1: Direct regex extraction
        year_matches = re.findall(r'\b(19|20)\d{2}\b', citation)
        if year_matches:
            result['extracted_years'].extend([int(year) for year in year_matches])
            result['extraction_method'] = 'regex'
            result['confidence'] = 0.9
        
        # Method 2: Use case name extraction core
        try:
            extraction_result = extract_case_name_triple_comprehensive(citation)
            if extraction_result and 'extracted_year' in extraction_result:
                extracted_year = extraction_result['extracted_year']
                if extracted_year and extracted_year not in result['extracted_years']:
                    result['extracted_years'].append(extracted_year)
                    if result['extraction_method']:
                        result['extraction_method'] += '+core'
                    else:
                        result['extraction_method'] = 'core'
                    result['confidence'] = max(result['confidence'], 0.8)
        except Exception as e:
            pass
        
        # Method 3: Look for year patterns in context
        # Common patterns like "200 Wash. 2d 72 (2022)" or "514 P.3d 643 (2022)"
        context_patterns = [
            r'\((\d{4})\)',  # Year in parentheses
            r',\s*(\d{4})\s*$',  # Year at end after comma
            r'\s+(\d{4})\s*$',  # Year at end
        ]
        
        for pattern in context_patterns:
            matches = re.findall(pattern, citation)
            for match in matches:
                year = int(match)
                if 1900 <= year <= 2030 and year not in result['extracted_years']:
                    result['extracted_years'].append(year)
                    if result['extraction_method']:
                        result['extraction_method'] += '+context'
                    else:
                        result['extraction_method'] = 'context'
                    result['confidence'] = max(result['confidence'], 0.7)
        
        # Remove duplicates and sort
        result['extracted_years'] = sorted(list(set(result['extracted_years'])))
        
        return result
    
    def analyze_year_distribution(self, citations: List[str]) -> Dict[str, Any]:
        """Analyze year distribution in citations."""
        year_results = []
        year_counts = Counter()
        extraction_methods = Counter()
        
        for citation in citations:
            result = self.test_citation_year_extraction(citation)
            year_results.append(result)
            
            for year in result['extracted_years']:
                year_counts[year] += 1
            
            if result['extraction_method']:
                extraction_methods[result['extraction_method']] += 1
        
        return {
            'year_results': year_results,
            'year_distribution': dict(year_counts.most_common()),
            'extraction_methods': dict(extraction_methods),
            'total_citations': len(citations),
            'citations_with_years': len([r for r in year_results if r['extracted_years']]),
            'year_extraction_rate': len([r for r in year_results if r['extracted_years']]) / len(citations) if citations else 0
        }
    
    def test_brief_year_extraction(self, pdf_path: str, output_file: str = None) -> Dict[str, Any]:
        """Test year extraction on a single brief."""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print(f"Error: PDF file not found: {pdf_path}")
            return {}
        
        print(f"Testing year extraction on: {pdf_path.name}")
        print("=" * 60)
        
        # Extract text
        print("1. Extracting text from PDF...")
        try:
            text = extract_text_from_pdf(str(pdf_path))
            if not text or len(text.strip()) < 100:
                print("Error: Extracted text too short")
                return {}
            
            print(f"   Extracted {len(text)} characters")
            
        except Exception as e:
            print(f"Error extracting text: {e}")
            return {}
        
        # Extract all years from text
        print("\n2. Extracting all years from text...")
        all_years = self.extract_years_from_text(text)
        print(f"   Found {len(all_years)} year occurrences in text")
        
        # Show year distribution
        year_counter = Counter([year for _, year in all_years])
        print(f"   Year distribution: {dict(year_counter.most_common(10))}")
        
        # Extract citations
        print("\n3. Extracting citations...")
        try:
            extraction_result = self.processor.extract_citations_from_text(text)
            extracted_citations = extraction_result.get('extracted_citations', [])
            print(f"   Found {len(extracted_citations)} citations")
            
        except Exception as e:
            print(f"Error extracting citations: {e}")
            return {}
        
        # Analyze year extraction from citations
        print("\n4. Analyzing year extraction from citations...")
        year_analysis = self.analyze_year_distribution(extracted_citations)
        
        print(f"   Citations with years: {year_analysis['citations_with_years']}/{year_analysis['total_citations']}")
        print(f"   Year extraction rate: {year_analysis['year_extraction_rate']:.1%}")
        print(f"   Extraction methods: {year_analysis['extraction_methods']}")
        
        # Show year distribution in citations
        if year_analysis['year_distribution']:
            print(f"   Year distribution in citations: {year_analysis['year_distribution']}")
        
        # Show examples of year extraction
        print("\n5. Year extraction examples:")
        examples_shown = 0
        for result in year_analysis['year_results']:
            if result['extracted_years'] and examples_shown < 5:
                print(f"   Citation: {result['citation'][:80]}...")
                print(f"   Extracted years: {result['extracted_years']}")
                print(f"   Method: {result['extraction_method']}")
                print()
                examples_shown += 1
        
        # Prepare results
        results = {
            'filename': pdf_path.name,
            'text_length': len(text),
            'total_years_in_text': len(all_years),
            'year_distribution_in_text': dict(year_counter.most_common()),
            'citation_analysis': year_analysis,
            'extracted_citations': extracted_citations[:10],  # First 10 for reference
        }
        
        # Save results
        if output_file:
            print(f"\n6. Saving results to {output_file}...")
            try:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"   Results saved successfully")
            except Exception as e:
                print(f"Error saving results: {e}")
        
        print("\n" + "=" * 60)
        print("Year extraction test completed!")
        print(f"Summary: {year_analysis['citations_with_years']} citations with years extracted")
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Test year extraction from citations')
    parser.add_argument('pdf_file', help='Path to PDF file to test')
    parser.add_argument('--output', '-o', help='Output JSON file for results')
    
    args = parser.parse_args()
    
    tester = YearExtractionTester()
    results = tester.test_brief_year_extraction(args.pdf_file, args.output)
    
    if not results:
        sys.exit(1)

if __name__ == "__main__":
    main() 