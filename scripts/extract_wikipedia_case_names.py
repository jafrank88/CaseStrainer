#!/usr/bin/env python3
"""
Script to extract case names from Wikipedia's Lists of United States Supreme Court cases by volume
and add them to a CSV file for context analysis.
"""

import requests
import csv
import re
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WikipediaCaseNameExtractor:
    """Extract case names from Wikipedia Supreme Court case lists."""
    
    def __init__(self):
        self.base_url = "https://en.wikipedia.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.extracted_cases = []
        
    def get_page_content(self, url: str) -> Optional[str]:
        """Get the HTML content of a Wikipedia page."""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_case_names_from_page(self, html_content: str) -> List[Dict]:
        """Extract case names from a Wikipedia page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        cases = []
        
        # Look for case name patterns in the page
        # Case names typically appear in italics or as links
        case_patterns = [
            # Italicized case names (most common format)
            'i',
            # Links that might be case names
            'a',
            # Bold text that might be case names
            'b'
        ]
        
        for pattern in case_patterns:
            elements = soup.find_all(pattern)
            for element in elements:
                text = element.get_text().strip()
                if self._is_likely_case_name(text):
                    case_info = {
                        'case_name': text,
                        'source_url': '',  # Will be filled by caller
                        'extraction_method': f'wikipedia_{pattern}_tag',
                        'confidence': self._calculate_confidence(text),
                        'extracted_date': datetime.now().isoformat()
                    }
                    cases.append(case_info)
        
        # Also look for case names in regular text using regex patterns
        text_content = soup.get_text()
        regex_cases = self._extract_case_names_regex(text_content)
        for case_name in regex_cases:
            case_info = {
                'case_name': case_name,
                'source_url': '',
                'extraction_method': 'wikipedia_regex_pattern',
                'confidence': self._calculate_confidence(case_name),
                'extracted_date': datetime.now().isoformat()
            }
            cases.append(case_info)
        
        return cases
    
    def _is_likely_case_name(self, text: str) -> bool:
        """Check if text is likely to be a case name."""
        if not text or len(text) < 5:
            return False
        
        # Case names typically contain "v." or "vs." or "versus"
        if re.search(r'\bv\.?\s+', text, re.IGNORECASE):
            return True
        
        # In re cases
        if re.search(r'\bIn\s+re\s+', text, re.IGNORECASE):
            return True
        
        # Ex parte cases
        if re.search(r'\bEx\s+parte\s+', text, re.IGNORECASE):
            return True
        
        # Estate cases
        if re.search(r'\bEstate\s+of\s+', text, re.IGNORECASE):
            return True
        
        # State/People/United States cases
        if re.search(r'\b(State|People|United\s+States)\s+v\.\s+', text, re.IGNORECASE):
            return True
        
        # Check for proper capitalization pattern
        words = text.split()
        if len(words) >= 2:
            # At least two words, first word capitalized
            if words[0][0].isupper() and any(word[0].isupper() for word in words[1:]):
                return True
        
        return False
    
    def _extract_case_names_regex(self, text: str) -> List[str]:
        """Extract case names using regex patterns."""
        case_names = []
        
        # Common case name patterns
        patterns = [
            r'\b([A-Z][A-Za-z\'\-\s,\.]+)\s+v\.\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\b([A-Z][A-Za-z\'\-\s,\.]+)\s+vs\.\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\b([A-Z][A-Za-z\'\-\s,\.]+)\s+versus\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\bIn\s+re\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\b([A-Z][A-Za-z\'\-\s,\.]+)\s+ex\s+rel\.\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\bState\s+v\.\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\bPeople\s+v\.\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\bUnited\s+States\s+v\.\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                else:
                    case_name = match.group(0).strip()
                
                if self._is_likely_case_name(case_name):
                    case_names.append(case_name)
        
        return list(set(case_names))  # Remove duplicates
    
    def _calculate_confidence(self, case_name: str) -> float:
        """Calculate confidence score for a case name."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for common patterns
        if re.search(r'\bv\.\s+', case_name):
            confidence += 0.3
        if re.search(r'\bIn\s+re\s+', case_name):
            confidence += 0.2
        if re.search(r'\bState\s+v\.\s+', case_name):
            confidence += 0.2
        if re.search(r'\bUnited\s+States\s+v\.\s+', case_name):
            confidence += 0.2
        
        # Boost for proper length
        if 10 <= len(case_name) <= 100:
            confidence += 0.1
        
        # Penalize for suspicious patterns
        if re.search(r'\d{4}', case_name):  # Year in case name
            confidence -= 0.1
        if len(case_name) > 150:  # Too long
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def extract_from_main_page(self) -> List[Dict]:
        """Extract case names from the main Wikipedia page."""
        main_url = "https://en.wikipedia.org/wiki/Lists_of_United_States_Supreme_Court_cases_by_volume"
        html_content = self.get_page_content(main_url)
        
        if not html_content:
            return []
        
        cases = self.extract_case_names_from_page(html_content)
        
        # Add source URL to all cases
        for case in cases:
            case['source_url'] = main_url
        
        return cases
    
    def extract_from_volume_pages(self, max_volumes: int = 10) -> List[Dict]:
        """Extract case names from individual volume pages."""
        all_cases = []
        
        # Get the main page to find volume links
        main_url = "https://en.wikipedia.org/wiki/Lists_of_United_States_Supreme_Court_cases_by_volume"
        html_content = self.get_page_content(main_url)
        
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find links to volume pages
        volume_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/wiki/List_of_United_States_Supreme_Court_cases,_volume_' in href:
                volume_links.append(urljoin(self.base_url, href))
        
        logger.info(f"Found {len(volume_links)} volume links")
        
        # Process volume pages (limit to avoid overwhelming)
        for i, volume_url in enumerate(volume_links[:max_volumes]):
            logger.info(f"Processing volume {i+1}/{min(len(volume_links), max_volumes)}: {volume_url}")
            
            html_content = self.get_page_content(volume_url)
            if html_content:
                cases = self.extract_case_names_from_page(html_content)
                for case in cases:
                    case['source_url'] = volume_url
                all_cases.extend(cases)
            
            # Be respectful with rate limiting
            time.sleep(1)
        
        return all_cases
    
    def save_to_csv(self, cases: List[Dict], filename: str = None) -> str:
        """Save extracted cases to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wikipedia_case_names_{timestamp}.csv"
        
        # Ensure the data directory exists
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        
        fieldnames = ['case_name', 'source_url', 'extraction_method', 'confidence', 'extracted_date']
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for case in cases:
                writer.writerow(case)
        
        logger.info(f"Saved {len(cases)} cases to {filepath}")
        return filepath
    
    def run_extraction(self, include_volumes: bool = True, max_volumes: int = 5) -> str:
        """Run the complete extraction process."""
        logger.info("Starting Wikipedia case name extraction...")
        
        all_cases = []
        
        # Extract from main page
        logger.info("Extracting from main page...")
        main_cases = self.extract_from_main_page()
        all_cases.extend(main_cases)
        logger.info(f"Found {len(main_cases)} cases on main page")
        
        # Extract from volume pages if requested
        if include_volumes:
            logger.info("Extracting from volume pages...")
            volume_cases = self.extract_from_volume_pages(max_volumes)
            all_cases.extend(volume_cases)
            logger.info(f"Found {len(volume_cases)} cases in volume pages")
        
        # Remove duplicates based on case name
        unique_cases = []
        seen_names = set()
        for case in all_cases:
            if case['case_name'] not in seen_names:
                seen_names.add(case['case_name'])
                unique_cases.append(case)
        
        logger.info(f"Total unique cases found: {len(unique_cases)}")
        
        # Save to CSV
        csv_file = self.save_to_csv(unique_cases)
        
        return csv_file

def main():
    """Main function to run the extraction."""
    extractor = WikipediaCaseNameExtractor()
    
    # Run extraction with volume pages (limit to 5 to be respectful)
    csv_file = extractor.run_extraction(include_volumes=True, max_volumes=5)
    
    print(f"\nExtraction complete! Results saved to: {csv_file}")
    print("You can now use this CSV file for context analysis in your case trainer system.")

if __name__ == "__main__":
    main() 