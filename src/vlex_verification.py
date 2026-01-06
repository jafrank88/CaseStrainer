#!/usr/bin/env python3
"""
VLex verification implementation for CaseStrainer
"""

import re
import logging
from typing import Optional, Dict, Any
from urllib.parse import quote
import requests

from src.unified_verification_master import VerificationResult

logger = logging.getLogger(__name__)


async def verify_with_vlex(
    self, 
    citation: str, 
    extracted_case_name: Optional[str], 
    extracted_date: Optional[str], 
    timeout: float
) -> VerificationResult:
    """Verify citation using VLex legal database."""
    logger.info(f"🔍 [VLEX] Verifying {citation}")
    
    try:
        # VLex search URL
        base_url = "https://vlex.com"
        
        # Build search query
        search_query = citation
        if extracted_case_name and extracted_case_name != "N/A":
            search_query += f" {extracted_case_name}"
        
        # VLex search URL pattern
        search_url = f"{base_url}/search?query={quote(search_query)}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        logger.debug(f"[VLEX] Searching: {search_url}")
        
        response = self.session.get(search_url, headers=headers, timeout=min(timeout, 10))
        
        if response.status_code == 200:
            content = response.text
            
            # Look for case links in VLex search results
            # VLex case URLs follow pattern: https://case-law.vlex.com/vid/[case-name]-[id]/
            case_link_pattern = r'href="(https://case-law\.vlex\.com/vid/[^"]+)"'
            matches = re.findall(case_link_pattern, content, re.IGNORECASE)
            
            if not matches:
                # Try alternative pattern for VLex links
                case_link_pattern = r'href="(/vid/[^"]+)"'
                alt_matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                matches = [f"{base_url}{match}" for match in alt_matches]
            
            for case_url in matches[:3]:  # Check first 3 results
                try:
                    logger.debug(f"[VLEX] Checking case: {case_url}")
                    
                    # Visit the case page
                    case_response = self.session.get(case_url, headers=headers, timeout=min(8, timeout))
                    
                    if case_response.status_code == 200:
                        case_content = case_response.text
                        
                        # Extract case name from VLex page
                        name_patterns = [
                            r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>',
                            r'<title>([^<]+)\s*-\s*VLex</title>',
                            r'<meta\s+property="og:title"\s+content="([^"]+)"',
                            r'<h2[^>]*>([^<]+v\.?[^<]+)</h2>',
                        ]
                        
                        canonical_name = None
                        for pattern in name_patterns:
                            match = re.search(pattern, case_content, re.IGNORECASE)
                            if match:
                                canonical_name = match.group(1).strip()
                                # Clean up the name
                                canonical_name = re.sub(r'\s+', ' ', canonical_name)
                                canonical_name = canonical_name.replace(' | VLex', '')
                                break
                        
                        # Extract date
                        date_patterns = [
                            r'<meta\s+name="citation_date"\s+content="([^"]+)"',
                            r'<span[^>]*class="[^"]*date[^"]*"[^>]*>([^<]+)</span>',
                            r'(\d{1,2}\s+\w+\s+\d{4})',
                        ]
                        
                        canonical_date = None
                        for pattern in date_patterns:
                            match = re.search(pattern, case_content, re.IGNORECASE)
                            if match:
                                canonical_date = match.group(1).strip()
                                break
                        
                        # Check if citation appears on page
                        citation_found = False
                        if citation.replace(" ", "").lower() in case_content.replace(" ", "").lower():
                            citation_found = True
                        
                        # Also check for reporter match
                        reporter_match = re.search(r'F\.4th\s+' + citation.split()[0], case_content, re.IGNORECASE)
                        if reporter_match:
                            citation_found = True
                        
                        if citation_found and canonical_name:
                            logger.info(f"✅ [VLEX] Found case: {canonical_name}")
                            return VerificationResult(
                                citation=citation,
                                verified=True,
                                canonical_name=canonical_name,
                                canonical_date=canonical_date,
                                canonical_url=case_url,
                                source="VLex",
                                confidence=0.9,
                                method="vlex_search",
                            )
                        elif canonical_name:
                            logger.info(f"🔶 [VLEX] Found possible match: {canonical_name}")
                            return VerificationResult(
                                citation=citation,
                                verified=False,
                                possible_match=True,
                                canonical_name=canonical_name,
                                canonical_date=canonical_date,
                                canonical_url=case_url,
                                source="VLex",
                                confidence=0.7,
                                method="vlex_search",
                            )
                
                except Exception as e:
                    logger.debug(f"[VLEX] Error checking case page: {e}")
                    continue
            
            logger.warning(f"⚠️  [VLEX] No matching cases found for {citation}")
            return VerificationResult(
                citation=citation, 
                verified=False, 
                error="No matching cases found on VLex"
            )
        
        elif response.status_code == 429:
            logger.warning(f"⚠️  [VLEX] Rate limited for {citation}")
            return VerificationResult(
                citation=citation, 
                verified=False, 
                error="VLex rate limit exceeded"
            )
        else:
            logger.warning(f"⚠️  [VLEX] HTTP {response.status_code} for {citation}")
            return VerificationResult(
                citation=citation, 
                verified=False, 
                error=f"VLex returned status {response.status_code}"
            )
    
    except Exception as e:
        logger.error(f"❌ [VLEX] Error verifying {citation}: {e}")
        return VerificationResult(
            citation=citation, 
            verified=False, 
            error=f"VLex error: {str(e)}"
        )
