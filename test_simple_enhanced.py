#!/usr/bin/env python3
"""
Simple Enhanced Case Name Extractor Test

This script demonstrates how to use CourtListener API v4 to improve
case name extraction from documents, ensuring extracted names are always
substrings of the original document text.
"""

import sys
import os
import json
import requests
import re
import time
import PyPDF2
from difflib import SequenceMatcher

def load_api_key():
    """Load API key from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def get_canonical_case_name(api_key, citation):
    """Get canonical case name from CourtListener API v4"""
    try:
        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "CaseStrainer Enhanced Extractor"
        }
        data = {"text": citation}
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result_data = response.json()
            
            if isinstance(result_data, list) and len(result_data) > 0:
                citation_result = result_data[0]
                clusters = citation_result.get("clusters", [])
                
                if clusters:
                    cluster = clusters[0]
                    return cluster.get("case_name")
        
        return None
        
    except Exception as e:
        print(f"Error getting canonical name for {citation}: {e}")
        return None

def extract_case_name_from_context(text, citation, context_window=500):
    """Extract case name from text context around a citation"""
    citation_pos = text.find(citation)
    if citation_pos == -1:
        return None
    
    start_pos = max(0, citation_pos - context_window)
    context_before = text[start_pos:citation_pos]
    
    # Case name patterns
    case_patterns = [
        r'([A-Z][A-Za-z0-9\s&\'\.\-]{3,50}\s+v\.?\s+[A-Z][A-Za-z0-9\s&\'\.\-]{3,50})',
        r'([A-Z][A-Za-z0-9\s&\'\.\-]{3,50},\s+[A-Z][A-Za-z0-9\s&\'\.\-]{3,50})',
        r'(In\s+re\s+[A-Z][A-Za-z0-9\s&\'\.\-]{3,50})',
        r'((?:State|United\s+States)\s+v\.?\s+[A-Z][A-Za-z0-9\s&\'\.\-]{3,50})',
        r'([A-Z][A-Za-z0-9\s&\'\.\-]{3,50})',
    ]
    
    for pattern in case_patterns:
        matches = re.findall(pattern, context_before)
        if matches:
            potential_case = matches[-1].strip()
            if len(potential_case) > 3:
                return potential_case
    
    return None

def calculate_similarity(name1, name2):
    """Calculate similarity between two case names"""
    if not name1 or not name2:
        return 0.0
    
    norm1 = re.sub(r'[^\w\s]', '', name1.lower())
    norm2 = re.sub(r'[^\w\s]', '', name2.lower())
    
    return SequenceMatcher(None, norm1, norm2).ratio()

def verify_extracted_name_in_text(extracted_name, text):
    """Verify that the extracted name is actually a substring of the original text"""
    if not extracted_name:
        return False
    
    # Check if the exact extracted name exists in the text
    return extracted_name in text

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
    
    # Citation patterns
    citation_patterns = [
        r'\b(\d{1,3})\s+U\.?\s?S\.?\s+(\d{1,4})\b',
        r'\b(\d{1,3})\s+F\.?\s?(?:2d|3d)\.?\s+(\d{1,4})\b',
        r'\b(\d{1,3})\s+Wash\.?\s?(?:2d|App\.?)\.?\s+(\d{1,4})\b',
        r'\b(\d{1,3})\s+P\.?\s?(?:2d|3d)\.?\s+(\d{1,4})\b',
        r'\b(20\d{2})\s+WL\s+(\d{8})\b',
    ]
    
    # Extract citations
    all_citations = []
    for pattern in citation_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            citation = match.group(0)
            all_citations.append({
                'citation': citation,
                'start': match.start(),
                'end': match.end()
            })
    
    # Sort by position
    all_citations.sort(key=lambda x: x['start'])
    
    print(f"\nFound {len(all_citations)} citations")
    print("\n" + "="*80)
    print("ENHANCED CASE NAME EXTRACTION RESULTS")
    print("="*80)
    print("(Always returning names found in original document text)")
    print("="*80)
    
    # Process first 10 citations
    results = []
    for i, citation_info in enumerate(all_citations[:10]):
        citation = citation_info['citation']
        
        print(f"\n{i+1}. Citation: {citation}")
        
        # Get canonical name from API (for validation/guidance only)
        print("   Getting canonical name from API...")
        canonical_name = get_canonical_case_name(api_key, citation)
        
        # Extract from context (this is what we'll actually return)
        print("   Extracting from context...")
        extracted_name = extract_case_name_from_context(text, citation)
        
        # Verify extracted name is in original text
        if extracted_name:
            is_in_text = verify_extracted_name_in_text(extracted_name, text)
            print(f"   Extracted name verified in text: {is_in_text}")
        
        # Determine final case name and confidence
        final_case_name = None
        confidence = 0.0
        method = "none"
        
        if extracted_name and verify_extracted_name_in_text(extracted_name, text):
            # We have a valid extracted name from the document
            if canonical_name:
                similarity = calculate_similarity(canonical_name, extracted_name)
                print(f"   Similarity to canonical: {similarity:.2f}")
                
                if similarity > 0.7:
                    confidence = 0.95
                    method = "extracted_api_confirmed"
                else:
                    confidence = 0.8
                    method = "extracted_api_mismatch"
            else:
                confidence = 0.7
                method = "extracted_only"
            
            final_case_name = extracted_name
        elif canonical_name:
            # Only API result available, but we can't use it directly
            print("   Warning: API found canonical name but no matching text in document")
            confidence = 0.0
            method = "api_only_no_text_match"
        
        print(f"   Final Case Name: {final_case_name or 'None'}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Method: {method}")
        
        if canonical_name:
            print(f"   Canonical (API): {canonical_name}")
        if extracted_name:
            print(f"   Extracted (Document): {extracted_name}")
        
        results.append({
            'citation': citation,
            'case_name': final_case_name,
            'confidence': confidence,
            'method': method,
            'canonical_name': canonical_name,
            'extracted_name': extracted_name,
            'verified_in_text': extracted_name and verify_extracted_name_in_text(extracted_name, text)
        })
        
        # Rate limiting
        if canonical_name:
            time.sleep(0.1)
    
    # Show statistics
    print("\n" + "-"*80)
    print("EXTRACTION STATISTICS")
    print("-"*80)
    
    total = len(results)
    with_case_names = len([r for r in results if r['case_name']])
    api_success = len([r for r in results if r['canonical_name']])
    extracted_success = len([r for r in results if r['extracted_name']])
    verified_in_text = len([r for r in results if r['verified_in_text']])
    high_confidence = len([r for r in results if r['confidence'] >= 0.8])
    
    print(f"Total citations: {total}")
    print(f"With case names: {with_case_names}")
    print(f"API success: {api_success}")
    print(f"Extracted success: {extracted_success}")
    print(f"Verified in text: {verified_in_text}")
    print(f"High confidence (≥0.8): {high_confidence}")
    
    # Method breakdown
    method_counts = {}
    for result in results:
        method = result['method']
        method_counts[method] = method_counts.get(method, 0) + 1
    
    print("\nMethod breakdown:")
    for method, count in method_counts.items():
        percentage = (count / total) * 100
        print(f"  {method}: {count} ({percentage:.1f}%)")
    
    # Show examples of verified text matches
    print("\n" + "-"*80)
    print("VERIFIED TEXT MATCHES")
    print("-"*80)
    
    verified_results = [r for r in results if r['verified_in_text']]
    for result in verified_results[:5]:
        print(f"✓ {result['citation']} -> {result['case_name']}")

if __name__ == "__main__":
    main() 