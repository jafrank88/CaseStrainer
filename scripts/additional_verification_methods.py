#!/usr/bin/env python3
"""
Additional Legal Database Verification Methods
Integrate these methods into enhanced_fallback_verifier.py
"""

import os
import re
import logging
from typing import Dict, Optional
import requests

logger = logging.getLogger(__name__)

# Add these methods to the EnhancedFallbackVerifier class

async def _verify_with_harvard_caselaw(self, citation_text: str, citation_info: Dict,
                                     extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                     search_query: Optional[str] = None) -> Optional[Dict]:
    """
    Verify citation with Harvard Caselaw Access Project.

    This is an academic gold standard with 40+ million cases from U.S. courts.
    Harvard Law School provides free API access for academic and research purposes.

    API: https://api.case.law/v1/
    Coverage: 40M+ cases from U.S. courts
    Access: Free for academic/research use
    """
    try:
        # Extract citation components for API query
        components = self._extract_citation_components(citation_text)

        if not components['volume'] or not components['reporter'] or not components['page']:
            logger.warning(f"Could not parse citation components for Harvard Caselaw: {citation_text}")
            return None

        # Build API query
        query_params = {
            'cite': f"{components['volume']} {components['reporter']} {components['page']}",
            'format': 'json',
            'full_case': 'false'  # Get basic case info only
        }

        # Add API key if available
        caselaw_api_key = os.getenv('CASELAW_API_KEY')
        headers = {}
        if caselaw_api_key:
            headers['Authorization'] = f'Token {caselaw_api_key}'

        url = "https://api.case.law/v1/cases/"

        self._rate_limit('api.case.law')
        response = self.session.get(url, headers=headers, params=query_params, timeout=self.WEBSEARCH_TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            if results:
                # Take the first (best) result
                case_data = results[0]

                # Extract date from decision_date field
                decision_date = case_data.get('decision_date', '')
                if decision_date:
                    # Convert from YYYY-MM-DD to just YYYY
                    year = decision_date.split('-')[0] if '-' in decision_date else decision_date

                return {
                    'verified': True,
                    'source': 'harvard_caselaw',
                    'canonical_name': case_data.get('name_abbreviation', ''),
                    'canonical_date': year,
                    'court': case_data.get('court', {}).get('name', ''),
                    'docket_number': case_data.get('docket_number', ''),
                    'url': case_data.get('frontend_url', ''),
                    'confidence': 0.95,  # Harvard Caselaw is highly authoritative
                    'parallel_citations': case_data.get('citations', [])
                }

        elif response.status_code == 404:
            logger.info(f"Citation not found in Harvard Caselaw database: {citation_text}")
        else:
            logger.warning(f"Harvard Caselaw API error {response.status_code}: {response.text[:200]}")

        return None

    except Exception as e:
        logger.warning(f"Harvard Caselaw verification failed for {citation_text}: {e}")
        return None

async def _verify_with_openjurist(self, citation_text: str, citation_info: Dict,
                                extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                search_query: Optional[str] = None) -> Optional[Dict]:
    """
    Verify citation with OpenJurist.

    OpenJurist is a free legal database providing access to federal and state court opinions.
    It has good coverage of published opinions from various jurisdictions.
    """
    try:
        if not search_query:
            search_query = citation_text
            if extracted_case_name:
                search_query += f" {extracted_case_name}"

        # OpenJurist search URL
        search_url = f"https://openjurist.org/search?q={requests.utils.quote(search_query)}"

        self._rate_limit('openjurist.org')
        response = self.session.get(search_url, timeout=self.WEBSEARCH_TIMEOUT, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            content = response.text

            # OpenJurist result patterns
            result_patterns = [
                r'href=\"([^\"]*openjurist\.org[^\"]*)\"[^>]*>([^<]*)</a>',
                r'<a[^>]*href=\"([^\"]*openjurist\.org[^\"]*)\"[^>]*>([^<]*)</a>',
            ]

            all_links = []
            for pattern in result_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                all_links.extend(matches)

            # Remove duplicates
            seen_urls = set()
            unique_links = []
            for url, title in all_links:
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_links.append((url, title))

            # Check each OpenJurist link for our case
            for url, title in unique_links:
                title_lower = title.lower()

                # Citation matching
                citation_match = False
                if 'u.s.' in citation_text.lower():
                    # Federal case - look for volume/page in title
                    us_match = re.search(r'(\d+)\s+u\.s\.\s+(\d+)', citation_text, re.IGNORECASE)
                    if us_match:
                        volume, page = us_match.groups()
                        citation_match = volume in title and page in title
                else:
                    # General citation matching
                    citation_words = re.findall(r'\b\w+\b', citation_text.lower())
                    title_words = re.findall(r'\b\w+\b', title_lower)
                    common_words = set(citation_words) & set(title_words)
                    citation_match = len(common_words) >= 2

                # Case name matching
                case_match = False
                if extracted_case_name:
                    case_lower = extracted_case_name.lower()
                    case_words = case_lower.split()
                    title_words = title_lower.split()
                    case_common = sum(1 for word in case_words if len(word) > 2 and word in title_words)
                    case_match = case_common >= 2

                if citation_match or case_match:
                    return {
                        'verified': True,
                        'source': 'openjurist',
                        'canonical_name': extracted_case_name,
                        'canonical_date': extracted_date or citation_info.get('year'),
                        'url': url if url.startswith('http') else f'https://openjurist.org{url}',
                        'confidence': 0.8  # Good confidence for OpenJurist matches
                    }

        return None

    except Exception as e:
        logger.warning(f"OpenJurist verification failed for {citation_text}: {e}")
        return None

async def _verify_with_google_books(self, citation_text: str, citation_info: Dict,
                                  extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                  search_query: Optional[str] = None) -> Optional[Dict]:
    """
    Verify citation with Google Books legal content.

    Google Books contains public domain legal texts, casebooks, and treatises.
    Useful as supplementary coverage for older cases and legal scholarship.
    """
    try:
        if not search_query:
            search_query = citation_text
            if extracted_case_name:
                search_query += f" {extracted_case_name}"

        # Google Books search URL
        search_url = f"https://books.google.com/books?q={requests.utils.quote(search_query)}+law+case"

        self._rate_limit('books.google.com')
        response = self.session.get(search_url, timeout=self.WEBSEARCH_TIMEOUT, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            content = response.text

            # Google Books result patterns
            book_patterns = [
                r'href=\"([^\"]*books\.google\.com/books[^\"]*)\"[^>]*>([^<]*)</a>',
                r'<a[^>]*href=\"([^\"]*books\.google\.com/books[^\"]*)\"[^>]*>([^<]*)</a>',
            ]

            all_links = []
            for pattern in book_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                all_links.extend(matches)

            # Remove duplicates
            seen_urls = set()
            unique_links = []
            for url, title in all_links:
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_links.append((url, title))

            # Check each Google Books link for legal relevance
            for url, title in unique_links:
                title_lower = title.lower()

                # Must contain legal keywords
                legal_keywords = ['case', 'court', 'law', 'legal', 'opinion', 'decision', 'justice']
                has_legal_content = any(keyword in title_lower for keyword in legal_keywords)

                if not has_legal_content:
                    continue

                # Citation matching (if applicable)
                citation_match = False
                citation_words = re.findall(r'\b\w+\b', citation_text.lower())
                title_words = re.findall(r'\b\w+\b', title_lower)
                common_words = set(citation_words) & set(title_words)
                citation_match = len(common_words) >= 2

                # Case name matching
                case_match = False
                if extracted_case_name:
                    case_lower = extracted_case_name.lower()
                    case_words = case_lower.split()
                    title_words = title_lower.split()
                    case_common = sum(1 for word in case_words if len(word) > 2 and word in title_words)
                    case_match = case_common >= 2

                if citation_match or case_match:
                    return {
                        'verified': True,
                        'source': 'google_books',
                        'canonical_name': extracted_case_name,
                        'canonical_date': extracted_date or citation_info.get('year'),
                        'url': url if url.startswith('http') else f'https://books.google.com{url}',
                        'confidence': 0.6,  # Lower confidence for supplementary legal content
                        'content_type': 'legal_textbook'
                    }

        return None

    except Exception as e:
        logger.warning(f"Google Books verification failed for {citation_text}: {e}")
        return None

# Update the sources list to include these new methods
# Add these to the sources list in verify_citation method:

SOURCES_UPDATE = [
    ('cornell_lii', self._verify_with_cornell_lii, 10.0),    # Cornell LII - HIGH PRIORITY, official source
    ('courtlistener_search', self._verify_with_courtlistener_search, 9.0), # CourtListener Search API v4 - EXCELLENT FALLBACK
    ('harvard_caselaw', self._verify_with_harvard_caselaw, 9.0), # Harvard Caselaw Access Project - ACADEMIC GOLD STANDARD
    ('google', self._verify_with_google_scholar, 8.0),      # Google Scholar - comprehensive academic search
    ('bing', self._verify_with_bing, 7.0),                 # Bing - good legal content indexing
    ('duckduckgo', self._verify_with_duckduckgo, 6.0),     # DuckDuckGo - privacy-focused search
    ('casemine', self._verify_with_casemine, 8.0),        # Legal database, international - FREE, HAS WASHINGTON CASES!
    ('descrybe', self._verify_with_descrybe, 8.0),        # Legal database, 3.6M U.S. cases - FREE!
    ('findlaw', self._verify_with_findlaw, 8.0),          # Legal database, good coverage - FREE!
    ('leagle', self._verify_with_leagle, 8.0),            # Legal database, comprehensive - FREE!
    ('vlex', self._verify_with_vlex, 7.0),                # Legal database with Pacific reporter affinity - FREE!
    ('openjurist', self._verify_with_openjurist, 8.0),    # OpenJurist - free federal/state court database
    ('google_books', self._verify_with_google_books, 6.0), # Google Books legal content - supplementary
    ('justia', self._verify_with_justia, 8.0),            # Legal-specific but reliable - FREE!

    ('scrapingbee', self._verify_with_scrapingbee, 4.0),  # Premium: handles JS, anti-bot bypass - LAST RESORT
]

print("Additional verification methods created!")
print("To integrate:")
print("1. Copy the three method definitions above into EnhancedFallbackVerifier class")
print("2. Update the sources list in verify_citation method with SOURCES_UPDATE")
print("3. Set CASELAW_API_KEY environment variable for Harvard Caselaw access")
