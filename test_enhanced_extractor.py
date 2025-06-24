#!/usr/bin/env python3
"""
Test script for the Enhanced Case Name Extractor

This script demonstrates how the enhanced extractor uses CourtListener API v4
to improve case name extraction from documents.
"""

import sys
import os
import json
import PyPDF2
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_case_name_extractor import EnhancedCaseNameExtractor

def load_api_key():
    """Load API key from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def main():
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("No API key found in config.json")
        return
    
    print(f"Using API key: {api_key[:6]}...")
    
    # Initialize enhanced extractor
    extractor = EnhancedCaseNameExtractor(api_key=api_key, cache_results=True)
    
    # Test with the PDF file
    pdf_path = "1028814.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("Failed to extract text from PDF")
        return
    
    print(f"Extracted {len(text)} characters of text")
    print("\n" + "="*80)
    print("ENHANCED CASE NAME EXTRACTION")
    print("="*80)
    
    # Extract enhanced case names
    print("Extracting case names using enhanced method...")
    results = extractor.extract_enhanced_case_names(text)
    
    if not results:
        print("No citations found in document")
        return
    
    print(f"\nFound {len(results)} citations")
    
    # Show detailed results for first 10 citations
    print("\n" + "-"*80)
    print("DETAILED RESULTS (First 10 citations)")
    print("-"*80)
    
    for i, result in enumerate(results[:10]):
        print(f"\n{i+1}. Citation: {result['citation']}")
        print(f"   Final Case Name: {result['case_name'] or 'None'}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Method: {result['method']}")
        
        if result['canonical_name']:
            print(f"   Canonical Name (API): {result['canonical_name']}")
        
        if result['extracted_name']:
            print(f"   Extracted Name (Context): {result['extracted_name']}")
        
        if result['canonical_name'] and result['extracted_name']:
            similarity = extractor.calculate_similarity(
                result['canonical_name'], 
                result['extracted_name']
            )
            print(f"   Similarity: {similarity:.2f}")
    
    # Show statistics
    print("\n" + "-"*80)
    print("EXTRACTION STATISTICS")
    print("-"*80)
    
    stats = extractor.get_extraction_stats(results)
    print(f"Total citations: {stats['total']}")
    print(f"With case names: {stats['with_case_names']}")
    print(f"API success: {stats['api_success']}")
    print(f"Extracted success: {stats['extracted_success']}")
    print(f"High confidence (≥0.8): {stats['high_confidence']}")
    
    print("\nMethod breakdown:")
    for method, count in stats['method_breakdown'].items():
        percentage = (count / stats['total']) * 100
        print(f"  {method}: {count} ({percentage:.1f}%)")
    
    # Show some examples of different methods
    print("\n" + "-"*80)
    print("EXAMPLES BY METHOD")
    print("-"*80)
    
    method_examples = {}
    for result in results:
        method = result['method']
        if method not in method_examples:
            method_examples[method] = []
        if len(method_examples[method]) < 3:  # Show up to 3 examples per method
            method_examples[method].append(result)
    
    for method, examples in method_examples.items():
        print(f"\n{method.upper()}:")
        for example in examples:
            print(f"  {example['citation']} -> {example['case_name']}")

if __name__ == "__main__":
    main() 