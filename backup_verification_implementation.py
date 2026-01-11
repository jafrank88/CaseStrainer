"""
Implementation of backup verification method
"""

import re
import aiohttp
from typing import Optional, Dict, Any
from urllib.parse import quote_plus

async def _verify_with_backup_search(self, citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str], timeout: float = 10.0):
    """
    Backup verification method that searches by case name + year + court
    when citation lookup fails (e.g., for very recent cases)
    """
    logger.info(f"[BACKUP-SEARCH] Starting backup search for {citation}")
    
    try:
        # Extract year from citation
        year_match = re.search(r'\((19|20)\d{2}\)', citation)
        year = year_match.group(0).strip('()') if year_match else None
        
        # Extract court from citation
        court = None
        if '2nd Cir.' in citation or '2d Cir.' in citation:
            court = 'ca2'  # Justia uses ca2 for 2nd Circuit
            court_name = '2nd Circuit'
        elif '9th Cir.' in citation or '9th Cir.' in citation:
            court = 'ca9'
            court_name = '9th Circuit'
        # Add more courts as needed
        
        if not extracted_case_name or not year or not court:
            logger.warning(f"[BACKUP-SEARCH] Missing required info: name={extracted_case_name}, year={year}, court={court}")
            return VerificationResult(citation=citation, error="Insufficient data for backup search")
        
        # Search Justia by case name + year + court
        justia_url = f"https://law.justia.com/cases/federal/appellate-courts/{court}/{year}/"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            logger.info(f"[BACKUP-SEARCH] Searching Justia: {justia_url}")
            async with session.get(justia_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Look for case name in the HTML
                    # Normalize case name for search
                    search_name = extracted_case_name.lower().replace('v.', 'v').replace('vs', 'v')
                    search_parts = search_name.split(' v ')
                    
                    if len(search_parts) >= 2:
                        # Look for both parties
                        plaintiff = search_parts[0].strip()
                        defendant = search_parts[1].strip()
                        
                        # Check if both parties appear in the HTML
                        if plaintiff in html.lower() and defendant in html.lower():
                            logger.info(f"[BACKUP-SEARCH] Found matching case on Justia")
                            
                            # Extract URL if found
                            url_pattern = f'href="(/cases/federal/appellate-courts/{court}/[^"]*)"'
                            url_matches = re.findall(url_pattern, html)
                            case_url = f"https://law.justia.com{url_matches[0]}" if url_matches else justia_url
                            
                            return VerificationResult(
                                citation=citation,
                                verified=True,
                                source="justia_backup_search",
                                url=case_url,
                                case_name=extracted_case_name,
                                decision_date=year,
                                court=court_name,
                                verification_method="Backup search (name + year + court)"
                            )
                    
                    logger.warning(f"[BACKUP-SEARCH] Case not found on Justia")
                else:
                    logger.warning(f"[BACKUP-SEARCH] Justia returned status {response.status}")
        
        # If Justia fails, try CourtListener search
        if self.api_key:
            search_query = quote_plus(f'"{extracted_case_name}" AND court:{court_name} AND decision_date:{year}')
            cl_url = f"https://www.courtlistener.com/api/rest/v4/search/?q={search_query}"
            
            logger.info(f"[BACKUP-SEARCH] Searching CourtListener: {cl_url}")
            async with session.get(cl_url, headers={'Authorization': f'Token {self.api_key}'}) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('count', 0) > 0:
                        result = data['results'][0]
                        logger.info(f"[BACKUP-SEARCH] Found matching case on CourtListener")
                        
                        return VerificationResult(
                            citation=citation,
                            verified=True,
                            source="courtlistener_backup_search",
                            url=f"https://courtlistener.com{result.get('absolute_url', '')}",
                            case_name=result.get('case_name', extracted_case_name),
                            decision_date=result.get('decision_date', year),
                            court=court_name,
                            verification_method="Backup search (name + year + court)"
                        )
        
        logger.warning(f"[BACKUP-SEARCH] No matches found for {citation}")
        return VerificationResult(citation=citation, error="No matches found in backup search")
        
    except Exception as e:
        logger.error(f"[BACKUP-SEARCH] Error during backup search: {e}")
        return VerificationResult(citation=citation, error=f"Backup search error: {str(e)}")

print("Backup verification method implementation ready to add to unified_verification_master.py")
