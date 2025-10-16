#!/usr/bin/env python3
"""
Final Citation Extractor - Extracts and organizes legal citations from PDFs.
"""

import os
import re
import json
import time
import PyPDF2
import requests
from typing import Optional, Dict, Any, List, Set, Tuple
from collections import defaultdict

class CitationExtractor:
    def __init__(self):
        self.citation_patterns = [
            # Standard case citation: Roe v. Wade, 410 U.S. 113 (1973)
            {
                'name': 'standard_case_citation',
                'pattern': r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+(\d+\s+[A-Za-z\.\s]+\d+)\s*\((\d{4})\)',
                'type': 'case'
            },
            # Case with multiple parties: Doe v. Smith, 123 F.3d 456 (9th Cir. 1999)
            {
                'name': 'complex_case_citation',
                'pattern': r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[Ee]t\s+al\.)?\s+v\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+(\d+\s+[A-Za-z\.\s]+\d+)\s*(?:\(\d{1,2}\s+[A-Za-z\.]+\s+)?\((\d{4})\)',
                'type': 'case'
            },
            # Washington Revised Code: RCW 49.58.110
            {
                'name': 'washington_rcw',
                'pattern': r'\b(RCW\s+[0-9A-Za-z\.]+(?:\s*\([^)]+\))?)',
                'type': 'statute'
            },
            # U.S. Code: 42 U.S.C. § 1983
            {
                'name': 'us_code',
                'pattern': r'\b(\d+\s+U\.?\s*S\.?\s*C\.?\s*§?\s*\d+[a-z]?(?:\s*\([^)]+\))?)',
                'type': 'statute'
            },
            # Federal Reporter: 123 F.3d 456
            {
                'name': 'federal_reporter',
                'pattern': r'\b(\d+\s+F\.?\s*(?:2d|3d|4th)?\s*\d+)',
                'type': 'reporter'
            },
            # Supreme Court Reporter: 123 S. Ct. 1234
            {
                'name': 'supreme_court_reporter',
                'pattern': r'\b(\d+\s+S\.?\s*Ct\.?\s*\d+)',
                'type': 'reporter'
            }
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract text from PDF with improved handling."""
        try:
            print(f"📄 Extracting text from {os.path.basename(pdf_path)}...")
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                raw_text_parts = []
                total_pages = len(pdf_reader.pages)
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    raw_text = page.extract_text()
                    
                    if raw_text:
                        raw_text_parts.append(raw_text)
                        
                        # Clean the text
                        cleaned_text = raw_text
                        
                        # Remove headers/footers (simple heuristic)
                        lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
                        if len(lines) > 3:
                            lines = lines[2:-2]  # Remove first 2 and last 2 lines
                        
                        cleaned_text = ' '.join(lines)
                        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize spaces
                        text_parts.append(cleaned_text)
                    
                    print(f"  Processed page {page_num + 1}/{total_pages} ({(page_num + 1)/total_pages*100:.1f}%)", end='\r')
                
                print()
                return ' '.join(text_parts), '\n'.join(raw_text_parts)
                
        except Exception as e:
            print(f"❌ Error extracting text from PDF: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def extract_citations(self, text: str) -> List[Dict[str, str]]:
        """Extract citations using regex patterns."""
        citations = []
        seen = set()
        
        for pattern_info in self.citation_patterns:
            for match in re.finditer(pattern_info['pattern'], text):
                citation = match.group(0).strip()
                
                # Skip duplicates and very short matches
                if len(citation) < 5 or citation.lower() in seen:
                    continue
                
                seen.add(citation.lower())
                
                # Extract metadata
                citation_data = {
                    'citation': citation,
                    'type': pattern_info['type'],
                    'source': 'regex_extraction'
                }
                
                # For case citations, try to extract case name and year
                if pattern_info['type'] == 'case':
                    try:
                        # Extract case name (before the first comma or first citation number)
                        name_part = re.split(r'\d', citation, 1)[0].strip()
                        if name_part.endswith(','):
                            name_part = name_part[:-1].strip()
                        citation_data['case_name'] = name_part
                        
                        # Extract year (last 4-digit number in parentheses)
                        year_match = re.search(r'\((\d{4})\)', citation)
                        if year_match:
                            citation_data['year'] = year_match.group(1)
                    except:
                        pass
                
                citations.append(citation_data)
        
        return citations
    
    def clean_citations(self, citations: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Clean and normalize citations."""
        cleaned = []
        seen = set()
        
        for cite in citations:
            # Normalize the citation for deduplication
            norm_cite = cite['citation'].lower()
            norm_cite = re.sub(r'[\s\n]+', ' ', norm_cite)  # Normalize whitespace
            norm_cite = re.sub(r'[\.,;]$', '', norm_cite)  # Remove trailing punctuation
            
            # Skip if we've seen this citation before
            if norm_cite in seen:
                continue
                
            seen.add(norm_cite)
            
            # Clean up the citation
            cleaned_cite = cite.copy()
            cleaned_cite['citation'] = re.sub(r'\s+', ' ', cite['citation'].strip())
            
            # Clean up case names if present
            if 'case_name' in cleaned_cite:
                cleaned_cite['case_name'] = re.sub(r'\s+', ' ', cleaned_cite['case_name'].strip())
            
            cleaned.append(cleaned_cite)
        
        return cleaned
    
    def categorize_citations(self, citations: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Categorize citations by type."""
        categorized = defaultdict(list)
        
        for cite in citations:
            categorized[cite['type']].append(cite)
        
        # Sort each category
        for cat in categorized:
            categorized[cat].sort(key=lambda x: x.get('citation', '').lower())
        
        return dict(categorized)
    
    def generate_report(self, citations: List[Dict[str, str]], output_dir: str, pdf_name: str) -> str:
        """Generate a markdown report of the citations."""
        # Clean and categorize citations
        cleaned = self.clean_citations(citations)
        categorized = self.categorize_citations(cleaned)
        
        # Create markdown content
        lines = [
            f"# Legal Citations in {pdf_name}",
            f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total unique citations found: {len(cleaned)}\n"
        ]
        
        # Add sections for each citation type
        for cat in sorted(categorized.keys()):
            cat_cites = categorized[cat]
            lines.append(f"## {cat.capitalize()} Citations ({len(cat_cites)})\n")
            
            for i, cite in enumerate(cat_cites, 1):
                lines.append(f"{i}. **{cite['citation']}**")
                if 'case_name' in cite and cite['case_name']:
                    lines.append(f"   - Case: {cite['case_name']}")
                if 'year' in cite and cite['year']:
                    lines.append(f"   - Year: {cite['year']}")
                lines.append("")
        
        # Save the report
        report_path = os.path.join(output_dir, f"{os.path.splitext(pdf_name)[0]}_citations.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return report_path

def process_pdf(pdf_path: str, output_dir: str = 'output') -> Dict[str, Any]:
    """Process a PDF and extract citations."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize extractor
    extractor = CitationExtractor()
    
    # Extract text
    cleaned_text, raw_text = extractor.extract_text_from_pdf(pdf_path)
    if not cleaned_text or not raw_text:
        return {"error": "Failed to extract text from PDF"}
    
    # Save extracted text
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    with open(os.path.join(output_dir, f"{base_name}_cleaned.txt"), 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    
    # Extract citations
    print("🔍 Extracting citations...")
    citations = extractor.extract_citations(raw_text)
    
    if not citations:
        return {"error": "No citations found in the document"}
    
    # Generate report
    print("📝 Generating citation report...")
    report_path = extractor.generate_report(citations, output_dir, os.path.basename(pdf_path))
    
    # Prepare result
    cleaned = extractor.clean_citations(citations)
    categorized = extractor.categorize_citations(cleaned)
    
    # Count citations by type
    counts = {cat: len(items) for cat, items in categorized.items()}
    
    return {
        "success": True,
        "total_citations": len(cleaned),
        "citation_counts": counts,
        "report_path": report_path,
        "citations": cleaned
    }

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract legal citations from PDF documents.')
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
        print(f"\n✅ Found {result['total_citations']} unique citations:")
        for cat, count in result['citation_counts'].items():
            print(f"   - {cat.capitalize()}: {count}")
        
        print(f"\n📄 Report generated: {result['report_path']}")
        print(f"⏱️  Processing time: {time.time() - start_time:.1f} seconds")

if __name__ == "__main__":
    main()
