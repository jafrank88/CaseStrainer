#!/usr/bin/env python3
"""
Scrape Washington State Courts Briefs for substantial briefs to test citation extraction.
Focuses on briefs with sufficient content for meaningful citation extraction testing.
"""

import os
import sys
import time
import requests
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional, Tuple
import argparse

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from document_processing_unified import extract_text_from_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wa_briefs_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WABriefsScraper:
    """Scraper for Washington State Courts Briefs website."""
    
    def __init__(self, output_dir: str = "wa_briefs", min_pages: int = 10, max_briefs: int = 50):
        # Use the correct WA Courts COA Division I briefs page
        self.base_url = "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A08"
        self.output_dir = Path(output_dir)
        self.min_pages = min_pages
        self.max_briefs = max_briefs
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.output_dir.mkdir(exist_ok=True)
        self.downloaded_count = 0
        self.skipped_count = 0

    def get_brief_listings(self) -> List[Dict]:
        """Get list of PDF briefs from the WA Courts page."""
        logger.info("Fetching brief listings from WA Courts page...")
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            briefs = []
            # Find all PDF links in the page
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and href.lower().endswith('.pdf'):
                    full_url = href
                    if not full_url.startswith('http'):
                        full_url = 'https://www.courts.wa.gov' + full_url
                    title = link.get_text(strip=True)
                    briefs.append({'url': full_url, 'title': title})
                    if len(briefs) >= self.max_briefs:
                        break
            logger.info(f"Found {len(briefs)} PDF briefs")
            return briefs
        except Exception as e:
            logger.error(f"Error fetching brief listings: {e}")
            return []
    
    def extract_case_info(self, link_element) -> Optional[Dict]:
        """Extract case information from a link element."""
        try:
            # Get link text and parent context
            link_text = link_element.get_text(strip=True)
            parent = link_element.parent
            
            # Look for case number patterns
            case_patterns = [
                r'(\d{4}-\d{6}-\d{3})',  # WA case number format
                r'(\d{2}-\d{4}-\d{4})',  # Alternative format
                r'(No\.?\s*\d+[-\d]*)',  # "No. 12345" format
            ]
            
            case_number = None
            for pattern in case_patterns:
                match = re.search(pattern, link_text)
                if match:
                    case_number = match.group(1)
                    break
            
            # Extract title (everything before case number)
            title = link_text
            if case_number:
                title = link_text.replace(case_number, '').strip()
            
            return {
                'title': title,
                'case_number': case_number,
                'court': self.detect_court(link_text),
                'date': self.extract_date(link_text)
            }
            
        except Exception as e:
            logger.debug(f"Error extracting case info: {e}")
            return None
    
    def detect_court(self, text: str) -> str:
        """Detect court from text."""
        text_lower = text.lower()
        if 'supreme' in text_lower:
            return 'Washington Supreme Court'
        elif 'appeals' in text_lower:
            return 'Washington Court of Appeals'
        elif 'district' in text_lower:
            return 'Washington District Court'
        else:
            return 'Unknown Court'
    
    def extract_date(self, text: str) -> str:
        """Extract date from text."""
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\w+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ''
    
    def find_pdf_links(self, brief_url: str) -> List[str]:
        """Find PDF links on a brief page."""
        logger.info(f"Searching for PDFs on: {brief_url}")
        
        try:
            response = self.session.get(brief_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            pdf_links = []
            
            # Look for PDF links
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and href.lower().endswith('.pdf'):
                    full_url = urljoin(brief_url, href)
                    pdf_links.append(full_url)
            
            # Also look for links with 'pdf' in the URL or text
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                link_text = link.get_text(strip=True).lower()
                if href and ('pdf' in href.lower() or 'pdf' in link_text):
                    full_url = urljoin(brief_url, href)
                    if full_url not in pdf_links:
                        pdf_links.append(full_url)
            
            logger.info(f"Found {len(pdf_links)} PDF links")
            return pdf_links
            
        except Exception as e:
            logger.error(f"Error finding PDF links on {brief_url}: {e}")
            return []
    
    def download_pdf(self, pdf_url: str, filename: str) -> bool:
        """Download a PDF file."""
        try:
            logger.info(f"Downloading: {pdf_url}")
            response = self.session.get(pdf_url, stream=True)
            response.raise_for_status()
            
            filepath = self.output_dir / filename
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {pdf_url}: {e}")
            return False
    
    def estimate_pdf_pages(self, pdf_path: Path) -> int:
        """Estimate number of pages in PDF."""
        try:
            # Try to extract text and count pages
            text = extract_text_from_file(str(pdf_path))
            if text:
                # Rough estimate: count page breaks or large text blocks
                lines = text.split('\n')
                non_empty_lines = [line.strip() for line in lines if line.strip()]
                
                # Estimate pages based on line count (rough heuristic)
                estimated_pages = max(1, len(non_empty_lines) // 50)
                return estimated_pages
            
            return 0
            
        except Exception as e:
            logger.debug(f"Error estimating pages for {pdf_path}: {e}")
            return 0
    
    def is_substantial_brief(self, pdf_path: Path) -> bool:
        """Check if brief is substantial enough for testing."""
        try:
            estimated_pages = self.estimate_pdf_pages(pdf_path)
            logger.info(f"Estimated pages for {pdf_path.name}: {estimated_pages}")
            return estimated_pages >= self.min_pages
            
        except Exception as e:
            logger.error(f"Error checking if brief is substantial: {e}")
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename
    
    def scrape_briefs(self):
        """Scrape and download briefs."""
        logger.info(f"Starting WA briefs scraping. Target: {self.max_briefs} briefs, min pages: {self.min_pages}")
        
        # Get list of PDF briefs
        briefs = self.get_brief_listings()
        if not briefs:
            logger.warning("No briefs found to download")
            return
        
        logger.info(f"Found {len(briefs)} PDF briefs to download")
        
        for i, brief in enumerate(briefs, 1):
            if self.downloaded_count >= self.max_briefs:
                break
                
            title = brief['title']
            pdf_url = brief['url']
            
            logger.info(f"Processing brief: {title}")
            
            # Create a safe filename
            safe_filename = self.sanitize_filename(f"{i:03d}_{title}.pdf")
            filepath = self.output_dir / safe_filename
            
            # Skip if file already exists
            if filepath.exists():
                logger.info(f"  Skipped: File already exists")
                self.skipped_count += 1
                continue
            
            # Download the PDF directly
            if self.download_pdf(pdf_url, safe_filename):
                self.downloaded_count += 1
                logger.info(f"  Downloaded: {safe_filename}")
            else:
                logger.warning(f"  Failed to download: {title}")
        
        logger.info(f"Scraping complete. Downloaded: {self.downloaded_count}, Skipped: {self.skipped_count}")
        
        # Create summary file
        self.create_summary()
    
    def create_summary(self):
        """Create a summary of downloaded briefs."""
        summary_file = self.output_dir / "download_summary.txt"
        
        with open(summary_file, 'w') as f:
            f.write("Washington State Courts Briefs Download Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total downloaded: {self.downloaded_count}\n")
            f.write(f"Total skipped (too small): {self.skipped_count}\n")
            f.write(f"Minimum pages required: {self.min_pages}\n")
            f.write(f"Output directory: {self.output_dir}\n\n")
            
            f.write("Downloaded files:\n")
            for pdf_file in self.output_dir.glob("*.pdf"):
                f.write(f"  - {pdf_file.name}\n")

def main():
    parser = argparse.ArgumentParser(description='Scrape Washington State Courts Briefs')
    parser.add_argument('--output-dir', default='wa_briefs', help='Output directory for PDFs')
    parser.add_argument('--min-pages', type=int, default=10, help='Minimum pages for substantial brief')
    parser.add_argument('--max-briefs', type=int, default=50, help='Maximum number of briefs to download')
    
    args = parser.parse_args()
    
    scraper = WABriefsScraper(
        output_dir=args.output_dir,
        min_pages=args.min_pages,
        max_briefs=args.max_briefs
    )
    
    scraper.scrape_briefs()

if __name__ == "__main__":
    main() 