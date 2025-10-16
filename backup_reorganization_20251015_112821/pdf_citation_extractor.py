#!/usr/bin/env python3
"""
Extract citations from a PDF file by first converting it to text and then using the API.
"""

import os
import json
import time
import PyPDF2
import requests
from typing import Optional, Dict, Any, List

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extract text from a PDF file."""
    try:
        print(f"📄 Extracting text from {os.path.basename(pdf_path)}...")
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from each page
            text_parts = []
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    text_parts.append(text)
                
                # Show progress
                progress = (page_num + 1) / total_pages * 100
                print(f"  Extracted page {page_num + 1}/{total_pages} ({progress:.1f}%)", end='\r')
            
            print()  # New line after progress
            return "\n".join(text_parts)
            
    except Exception as e:
        print(f"❌ Error extracting text from PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_citations_from_text(text: str, output_file: str = None) -> Optional[Dict[str, Any]]:
    """Send text to the API for citation extraction."""
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    data = {
        "text": text,
        "options": {
            "track_progress": False,
            "processing_strategy": "unified_v2_direct"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print("🚀 Sending text to citation extractor API...")
        response = requests.post(url, json=data, headers=headers, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            # Save the response if output file is specified
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                print(f"💾 Full API response saved to {output_file}")
            
            return result
        else:
            print(f"❌ API request failed with status {response.status_code}:")
            print(response.text[:1000])  # Print first 1000 chars of error
            return None
            
    except Exception as e:
        print(f"❌ Error calling citation extractor API: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_pdf(pdf_path: str, output_dir: str = None) -> Optional[Dict[str, Any]]:
    """Process a PDF file to extract citations."""
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return None
    
    # Set up output directory
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Step 1: Extract text from PDF
    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        return None
    
    # Save extracted text for debugging
    text_output_path = os.path.join(output_dir or '.', f"{base_name}_extracted.txt")
    with open(text_output_path, 'w', encoding='utf-8') as f:
        f.write(extracted_text)
    print(f"💾 Extracted text saved to {text_output_path}")
    
    # Step 2: Send text to citation extractor
    json_output_path = os.path.join(output_dir or '.', f"{base_name}_citations.json") if output_dir else None
    result = extract_citations_from_text(extracted_text, json_output_path)
    
    if result and 'citations' in result:
        citations = result['citations']
        print(f"\n✅ Found {len(citations)} citations in the document:")
        
        # Save citations to a readable text file
        citations_text_path = os.path.join(output_dir or '.', f"{base_name}_citations.txt")
        with open(citations_text_path, 'w', encoding='utf-8') as f:
            f.write(f"Citations found in {os.path.basename(pdf_path)}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, cite in enumerate(citations, 1):
                citation_str = cite.get('citation', 'N/A')
                case_name = cite.get('case_name', 'N/A')
                year = cite.get('year', 'N/A')
                
                # Print to console
                print(f"  {i}. {citation_str}")
                if case_name != 'N/A':
                    print(f"     Case: {case_name}")
                if year != 'N/A':
                    print(f"     Year: {year}")
                print()
                
                # Write to file
                f.write(f"{i}. {citation_str}\n")
                if case_name != 'N/A':
                    f.write(f"   Case: {case_name}\n")
                if year != 'N/A':
                    f.write(f"   Year: {year}\n")
                f.write("\n")
        
        print(f"\n💾 Citations saved to {citations_text_path}")
    
    return result

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract citations from a PDF file.')
    parser.add_argument('pdf_path', help='Path to the PDF file to process')
    parser.add_argument('-o', '--output-dir', help='Directory to save output files', default='output')
    
    args = parser.parse_args()
    
    print(f"🔍 Processing PDF: {args.pdf_path}")
    print("-" * 60)
    
    start_time = time.time()
    result = process_pdf(args.pdf_path, args.output_dir)
    
    if result is None:
        print("\n❌ Failed to process the PDF.")
    else:
        print(f"\n✅ Processing completed in {time.time() - start_time:.1f} seconds.")

if __name__ == "__main__":
    main()
