#!/usr/bin/env python3
"""
Extract citations from CaseHOLD dataset for testing citation verification methods.
"""

import json
import re
from typing import List, Dict, Any
from datasets import load_dataset
from src.unified_citation_processor import unified_processor

def extract_citations_from_casehold():
    """Extract 1000 cases from CaseHOLD dataset and extract citations from them."""
    
    print("Loading CaseHOLD dataset...")
    try:
        # Load the dataset
        dataset = load_dataset("casehold/casehold", split="train", trust_remote_code=True)
        print(f"Loaded {len(dataset)} cases from CaseHOLD dataset")
        
        # Take first 1000 cases
        cases = dataset.select(range(min(1000, len(dataset))))
        print(f"Selected {len(cases)} cases for processing")
        
        extracted_citations = []
        
        for i, case in enumerate(cases):
            if i % 100 == 0:
                print(f"Processing case {i+1}/{len(cases)}")
            
            # Extract citations from the citing_prompt (which contains the legal text with citations)
            citing_prompt = case['citing_prompt']
            
            # Use our unified processor to extract citations
            try:
                citation_results = unified_processor.extract_citations(citing_prompt)
                
                for citation_result in citation_results:
                    extracted_citation = {
                        'casehold_id': case['example_id'],
                        'citation': citation_result.citation,
                        'case_name': citation_result.case_name,
                        'canonical_date': citation_result.canonical_date,
                        'year': citation_result.year,
                        'context': citation_result.context[:200] + "..." if len(citation_result.context) > 200 else citation_result.context,
                        'method': citation_result.method,
                        'confidence': citation_result.confidence,
                        'is_complex': citation_result.is_complex,
                        'is_parallel': citation_result.is_parallel,
                        'parallel_citations': citation_result.parallel_citations,
                        'pinpoint_pages': citation_result.pinpoint_pages
                    }
                    extracted_citations.append(extracted_citation)
                    
            except Exception as e:
                print(f"Error processing case {case['example_id']}: {e}")
                continue
        
        print(f"Extracted {len(extracted_citations)} citations from {len(cases)} cases")
        
        # Save to file
        with open('casehold_citations_1000.json', 'w', encoding='utf-8') as f:
            json.dump(extracted_citations, f, indent=2, ensure_ascii=False)
        
        print("Saved citations to casehold_citations_1000.json")
        
        # Print some statistics
        print("\nCitation Statistics:")
        print(f"Total citations extracted: {len(extracted_citations)}")
        
        # Count by method
        method_counts = {}
        for citation in extracted_citations:
            method = citation.get('method', 'unknown')
            method_counts[method] = method_counts.get(method, 0) + 1
        
        print("\nExtraction methods used:")
        for method, count in method_counts.items():
            print(f"  {method}: {count}")
        
        # Count complex citations
        complex_count = sum(1 for c in extracted_citations if c.get('is_complex', False))
        parallel_count = sum(1 for c in extracted_citations if c.get('is_parallel', False))
        
        print(f"\nComplex citations: {complex_count}")
        print(f"Parallel citations: {parallel_count}")
        
        # Show some examples
        print("\nSample citations:")
        for i, citation in enumerate(extracted_citations[:5]):
            print(f"  {i+1}. {citation['citation']} - {citation.get('case_name', 'N/A')}")
        
        return extracted_citations
        
    except Exception as e:
        print(f"Error loading CaseHOLD dataset: {e}")
        print("Make sure you have the datasets library installed: pip install datasets")
        return []

if __name__ == "__main__":
    extract_citations_from_casehold() 