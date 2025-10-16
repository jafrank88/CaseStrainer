#!/usr/bin/env python3
"""
Enhanced PDF citation extractor with better text extraction and citation detection.
"""

import os
import re
import json
import time
import PyPDF2
import requests
from typing import Optional, Dict, Any, List, Tuple

def extract_text_from_pdf_enhanced(pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract text from a PDF file with improved handling for legal citations.
    Returns a tuple of (clean_text, raw_text).
    """
    try:
        print(f"📄 Extracting text from {os.path.basename(pdf_path)}...")
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from each page
            text_parts = []
            raw_text_parts = []
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                raw_text = page.extract_text()
                
                if raw_text:
                    # Keep the raw text
                    raw_text_parts.append(raw_text)
                    
                    # Clean the text for better citation detection
                    cleaned_text = raw_text
                    
                    # Remove headers/footers (simple heuristic)
                    lines = cleaned_text.split('\n')
                    if len(lines) > 3:  # Only if there are enough lines
                        # Remove common headers/footers (first/last few lines)
                        lines = lines[2:-2]
                    cleaned_text = '\n'.join(lines)
                    
                    # Normalize spaces and line breaks
                    cleaned_text = ' '.join(cleaned_text.split())
                    
                    # Add to our cleaned text
                    text_parts.append(cleaned_text)
                
                # Show progress
                progress = (page_num + 1) / total_pages * 100
                print(f"  Processed page {page_num + 1}/{total_pages} ({progress:.1f}%)", end='\r')
            
            print()  # New line after progress
            return ' '.join(text_parts), '\n'.join(raw_text_parts)
            
    except Exception as e:
        print(f"❌ Error extracting text from PDF: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def extract_citations_with_regex(text: str) -> List[Dict[str, str]]:
    """Extract potential citations using regex patterns."""
    # Common citation patterns
    patterns = [
        # Standard case citation: Roe v. Wade, 410 U.S. 113 (1973)
        r'(\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+(\d+\s+[A-Za-z\.\s]+\d+)\s*\((\d{4})\))',
        
        # Case with multiple parties: Doe v. Smith, 123 F.3d 456 (9th Cir. 1999)
        r'(\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[Ee]t\s+al\.)?\s+v\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+(\d+\s+[A-Za-z\.\s]+\d+)\s*\((?:\d{1,2}\s+[A-Za-z\.]+\s+)?(\d{4})\))',
        
        # Statute reference: 42 U.S.C. § 1983
        r'(\b\d+\s+U\.?\s*S\.?\s*C\.?\s*§?\s*\d+[a-z]?(?:\s*\([^)]+\))?)',
        
        # Washington Revised Code: RCW 49.58.110
        r'(\b(?:RCW|Rev\.?\s*Code\s*Wash\.?|Wash\.?\s*Rev\s*Code)\s+[0-9A-Za-z\.]+(?:\s*\([^)]+\))?)'
    ]
    
    citations = []
    seen = set()
    
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            citation = match.group(0).strip()
            
            # Skip duplicates
            if citation.lower() in seen:
                continue
                
            seen.add(citation.lower())
            
            # Try to extract case name and year
            case_name = ""
            year = ""
            
            # For case citations (first two patterns)
            if ' v. ' in citation and '(' in citation and ')' in citation:
                try:
                    # Extract case name (before the first comma or first citation number)
                    name_part = re.split(r'\d', citation, 1)[0].strip()
                    if name_part.endswith(','):
                        name_part = name_part[:-1].strip()
                    case_name = name_part
                    
                    # Extract year (last 4-digit number in parentheses)
                    year_match = re.search(r'\((\d{4})\)', citation)
                    if year_match:
                        year = year_match.group(1)
                except:
                    pass
            
            citations.append({
                'citation': citation,
                'case_name': case_name if case_name else 'N/A',
                'year': year if year else 'N/A',
                'source': 'regex_extraction'
            })
    
    return citations

def extract_citations_from_text(text: str, output_file: str = None) -> Dict[str, Any]:
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
                print(f"💾 API response saved to {output_file}")
            
            return result
        else:
            print(f"❌ API request failed with status {response.status_code}:")
            print(response.text[:1000])  # Print first 1000 chars of error
            return {"citations": [], "error": f"API request failed with status {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Error calling citation extractor API: {e}")
        return {"citations": [], "error": str(e)}

def process_pdf(pdf_path: str, output_dir: str = None) -> Dict[str, Any]:
    """Process a PDF file to extract citations using both API and regex."""
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return {"error": "File not found"}
    
    # Set up output directory
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Step 1: Extract text from PDF with enhanced extraction
    print("\n🔍 Extracting text from PDF...")
    cleaned_text, raw_text = extract_text_from_pdf_enhanced(pdf_path)
    
    if not cleaned_text or not raw_text:
        return {"error": "Failed to extract text from PDF"}
    
    # Save extracted text for debugging
    cleaned_text_path = os.path.join(output_dir or '.', f"{base_name}_cleaned.txt")
    raw_text_path = os.path.join(output_dir or '.', f"{base_name}_raw.txt")
    
    with open(cleaned_text_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    print(f"💾 Cleaned text saved to {cleaned_text_path}")
    
    with open(raw_text_path, 'w', encoding='utf-8') as f:
        f.write(raw_text)
    print(f"💾 Raw extracted text saved to {raw_text_path}")
    
    # Step 2: Try API-based extraction first
    print("\n🔄 Attempting API-based citation extraction...")
    json_output_path = os.path.join(output_dir or '.', f"{base_name}_api_citations.json")
    api_result = extract_citations_from_text(cleaned_text, json_output_path)
    
    # Step 3: Fall back to regex if API doesn't find citations
    citations = api_result.get('citations', [])
    
    if not citations:
        print("\n🔍 No citations found via API, trying regex-based extraction...")
        citations = extract_citations_with_regex(raw_text)
        
        if citations:
            print(f"✅ Found {len(citations)} potential citations using regex")
            
            # Save regex results
            regex_result = {
                "citations": citations,
                "source": "regex_extraction",
                "document_length": len(raw_text),
                "processing_time_ms": 0,
                "success": True
            }
            
            regex_json_path = os.path.join(output_dir or '.', f"{base_name}_regex_citations.json")
            with open(regex_json_path, 'w', encoding='utf-8') as f:
                json.dump(regex_result, f, indent=2)
            print(f"💾 Regex extraction results saved to {regex_json_path}")
            
            # Update the result to include regex findings
            api_result.update(regex_result)
    
    # Save all citations to a readable text file
    if citations:
        citations_text_path = os.path.join(output_dir or '.', f"{base_name}_all_citations.txt")
        with open(citations_text_path, 'w', encoding='utf-8') as f:
            f.write(f"Citations found in {os.path.basename(pdf_path)}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, cite in enumerate(citations, 1):
                citation_str = cite.get('citation', 'N/A')
                case_name = cite.get('case_name', 'N/A')
                year = cite.get('year', 'N/A')
                source = cite.get('source', 'api')
                
                f.write(f"{i}. {citation_str}\n")
                if case_name != 'N/A':
                    f.write(f"   Case: {case_name}\n")
                if year != 'N/A':
                    f.write(f"   Year: {year}\n")
                f.write(f"   Source: {source}\n\n")
        
        print(f"\n💾 All citations saved to {citations_text_path}")
    else:
        print("\nℹ️ No citations found in the document using any method.")
    
    return api_result

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract citations from a PDF file using multiple methods.')
    parser.add_argument('pdf_path', help='Path to the PDF file to process')
    parser.add_argument('-o', '--output-dir', help='Directory to save output files', default='output')
    
    args = parser.parse_args()
    
    print(f"🔍 Processing PDF: {args.pdf_path}")
    print("-" * 60)
    
    start_time = time.time()
    result = process_pdf(args.pdf_path, args.output_dir)
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
    else:
        citations = result.get('citations', [])
        if citations:
            print(f"\n✅ Found {len(citations)} citations in the document:")
            for i, cite in enumerate(citations[:5], 1):  # Show first 5 citations
                print(f"  {i}. {cite.get('citation')}")
            if len(citations) > 5:
                print(f"  ... and {len(citations) - 5} more")
        
        print(f"\n✅ Processing completed in {time.time() - start_time:.1f} seconds.")
        print(f"📂 Output files saved to: {os.path.abspath(args.output_dir)}")

if __name__ == "__main__":
    main()
