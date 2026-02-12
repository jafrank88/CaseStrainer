"""
Verification Sources Module
============================

Individual source verifiers (CourtListener, Justia, Cornell LII, etc.)
"""

import re
import html
import asyncio
import logging
from typing import Optional, Dict, Any
from urllib.parse import quote

from src.utils.fallback_verification_utils import URLBuilder, HTMLExtractor, NameValidator, HTTPClient

logger = logging.getLogger(__name__)


class CourtListenerVerifier:
    """Verifier for CourtListener API."""
    
    def __init__(self, api_key: Optional[str] = None, session=None):
        self.api_key = api_key
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
        self.session = session
        self.base_url = "https://www.courtlistener.com/api/rest/v4"
    
    async def verify(self, citation: str, timeout: float = 10.0, extracted_case_name: Optional[str] = None) -> Dict[str, Any]:
        """Verify citation using CourtListener lookup API."""
        if not self.api_key:
            return {"verified": False, "error": "No API key"}
        
        url = f"{self.base_url}/citation-lookup/"
        headers = {"Authorization": f"Token {self.api_key}"}
        
        try:
            resp = self.session.post(
                url, 
                json={"text": citation}, 
                headers=headers, 
                timeout=min(timeout, 10)
            )
            
            if resp.status_code == 200:
                data = resp.json()
                # Process results
                if data and len(data) > 0:
                    result = data[0] if isinstance(data, list) else data
                    if result.get("clusters"):
                        cluster = self._select_best_cluster(result["clusters"], extracted_case_name)
                        return {
                            "verified": True,
                            "canonical_name": cluster.get("case_name") or cluster.get("caseName"),
                            "canonical_date": self._extract_year(cluster),
                            "canonical_url": f"https://www.courtlistener.com{cluster.get('absolute_url', '')}",
                            "source": "CourtListener",
                            "confidence": 0.95,
                        }
                
                return {"verified": False, "error": "No results"}
            
            elif resp.status_code == 429:
                return {"verified": False, "error": "Rate limited"}
            else:
                return {"verified": False, "error": f"HTTP {resp.status_code}"}
                
        except Exception as e:
            logger.warning(f"CourtListener lookup failed: {e}")
            return {"verified": False, "error": str(e)}
    
    def _select_best_cluster(self, clusters: list, extracted_case_name: Optional[str] = None) -> Dict:
        """Select the cluster whose case_name best matches extracted_case_name."""
        if not clusters:
            return {}
        if len(clusters) == 1 or not extracted_case_name or extracted_case_name == "N/A":
            return clusters[0]
        
        ecn_lower = extracted_case_name.lower().strip()
        ecn_parts = re.split(r"\s+v\.?\s+", ecn_lower, maxsplit=1)
        ecn_first = ecn_parts[0].strip().split()[-1] if ecn_parts else ""
        
        best_cluster = clusters[0]
        best_score = -1
        for cluster in clusters:
            cn = (cluster.get("case_name") or cluster.get("caseName") or "").lower().strip()
            if not cn:
                continue
            score = 0
            if ecn_lower in cn or cn in ecn_lower:
                score += 10
            cn_parts = re.split(r"\s+v\.?\s+", cn, maxsplit=1)
            cn_first = cn_parts[0].strip().split()[-1] if cn_parts else ""
            if ecn_first and cn_first and ecn_first == cn_first:
                score += 5
            ecn_words = set(re.findall(r"[a-z]+", ecn_lower)) - {"v", "the", "of", "and", "inc", "llc"}
            cn_words = set(re.findall(r"[a-z]+", cn)) - {"v", "the", "of", "and", "inc", "llc"}
            if ecn_words and cn_words:
                overlap = len(ecn_words & cn_words) / max(len(ecn_words | cn_words), 1)
                score += overlap * 3
            if score > best_score:
                best_score = score
                best_cluster = cluster
        
        if best_score > 0 and best_cluster != clusters[0]:
            logger.info(
                f"[CL-CLUSTER-SELECT] Selected '{best_cluster.get('case_name','')}' over "
                f"'{clusters[0].get('case_name','')}' for ecn='{extracted_case_name}'"
            )
        return best_cluster

    def _extract_year(self, cluster: Dict) -> Optional[str]:
        """Extract year from cluster data."""
        date_filed = cluster.get("date_filed") or cluster.get("dateFiled", "")
        if date_filed:
            match = re.search(r"(\d{4})", date_filed)
            if match:
                return match.group(1)
        return None


class JustiaVerifier:
    """Verifier for Justia legal database."""
    
    def __init__(self, session=None):
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
        self.session = session
    
    async def verify(
        self, 
        citation: str, 
        extracted_case_name: Optional[str] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Verify using Justia direct URL construction."""
        
        direct_url = URLBuilder.build_justia_url(citation)
        if not direct_url:
            return {"verified": False, "error": "Cannot build URL"}
        
        try:
            headers = HTTPClient.get_headers()
            response = self.session.get(direct_url, headers=headers, timeout=min(timeout, 10))
            
            if response.status_code == 200:
                content = response.text
                canonical_name = HTMLExtractor.extract_case_name(content)
                
                if canonical_name:
                    canonical_date = HTMLExtractor.extract_date(content)
                    
                    # Validate name match
                    if extracted_case_name:
                        is_valid, overlap, warning = NameValidator.validate_match(
                            extracted_case_name, canonical_name, min_overlap=0.3
                        )
                        if not is_valid:
                            return {
                                "verified": False,
                                "canonical_name": canonical_name,
                                "canonical_date": canonical_date,
                                "canonical_url": direct_url,
                                "source": "Justia",
                                "confidence": 0.5,
                                "validation_warning": warning,
                            }
                    
                    confidence = 0.85 if overlap >= 0.3 else 0.60
                    
                    return {
                        "verified": True,
                        "canonical_name": canonical_name,
                        "canonical_date": canonical_date,
                        "canonical_url": direct_url,
                        "source": "Justia",
                        "confidence": confidence,
                    }
            
            return {"verified": False, "error": f"HTTP {response.status_code}"}
            
        except Exception as e:
            logger.warning(f"Justia verification failed: {e}")
            return {"verified": False, "error": str(e)}


class CornellLIIVerifier:
    """Verifier for Cornell Legal Information Institute."""
    
    def __init__(self, session=None):
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
        self.session = session
    
    async def verify(
        self, 
        citation: str,
        extracted_case_name: Optional[str] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Verify using Cornell LII direct URL."""
        
        direct_url = URLBuilder.build_cornell_lii_url(citation)
        if not direct_url:
            return {"verified": False, "error": "Cannot build URL"}
        
        try:
            headers = HTTPClient.get_headers()
            response = self.session.get(direct_url, headers=headers, timeout=min(timeout, 10))
            
            if response.status_code == 200:
                content = response.text
                canonical_name = HTMLExtractor.extract_case_name(content)
                
                if canonical_name:
                    canonical_date = HTMLExtractor.extract_year(content)
                    
                    # Validate
                    if extracted_case_name:
                        is_valid, overlap, warning = NameValidator.validate_match(
                            extracted_case_name, canonical_name, min_overlap=0.3
                        )
                        if not is_valid:
                            return {
                                "verified": False,
                                "canonical_name": canonical_name,
                                "canonical_date": canonical_date,
                                "canonical_url": direct_url,
                                "source": "Cornell LII",
                                "confidence": 0.5,
                                "validation_warning": warning,
                            }
                    
                    confidence = 0.90 if overlap >= 0.5 else 0.75
                    
                    return {
                        "verified": True,
                        "canonical_name": canonical_name,
                        "canonical_date": canonical_date,
                        "canonical_url": direct_url,
                        "source": "Cornell LII",
                        "confidence": confidence,
                    }
            
            return {"verified": False, "error": f"HTTP {response.status_code}"}
            
        except Exception as e:
            logger.warning(f"Cornell LII verification failed: {e}")
            return {"verified": False, "error": str(e)}


class OpenJuristVerifier:
    """Verifier for OpenJurist."""
    
    def __init__(self, session=None):
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
        self.session = session
    
    async def verify(
        self, 
        citation: str,
        extracted_case_name: Optional[str] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Verify using OpenJurist direct URL."""
        
        direct_url = URLBuilder.build_openjurist_url(citation)
        if not direct_url:
            return {"verified": False, "error": "Cannot build URL"}
        
        try:
            headers = HTTPClient.get_headers()
            response = self.session.get(direct_url, headers=headers, timeout=min(timeout, 10))
            
            if response.status_code == 200:
                content = response.text
                canonical_name = HTMLExtractor.extract_case_name(content)
                
                if canonical_name:
                    # Clean up: "410 US 113 Roe v. Wade" -> "Roe v. Wade"
                    canonical_name = re.sub(r"^\d+\s+[A-Z\.]+\s+\d+\s+", "", canonical_name).strip()
                    
                    if "v" in canonical_name.lower():
                        canonical_date = HTMLExtractor.extract_year(content)
                        
                        # Validate
                        if extracted_case_name:
                            is_valid, overlap, warning = NameValidator.validate_match(
                                extracted_case_name, canonical_name, min_overlap=0.3
                            )
                            if not is_valid:
                                return {
                                    "verified": False,
                                    "canonical_name": canonical_name,
                                    "canonical_date": canonical_date,
                                    "canonical_url": direct_url,
                                    "source": "OpenJurist",
                                    "confidence": 0.5,
                                    "validation_warning": warning,
                                }
                        
                        confidence = 0.85
                        
                        return {
                            "verified": True,
                            "canonical_name": canonical_name,
                            "canonical_date": canonical_date,
                            "canonical_url": direct_url,
                            "source": "OpenJurist",
                            "confidence": confidence,
                        }
            
            return {"verified": False, "error": f"HTTP {response.status_code}"}
            
        except Exception as e:
            logger.warning(f"OpenJurist verification failed: {e}")
            return {"verified": False, "error": str(e)}


class GoogleScholarVerifier:
    """Verifier for Google Scholar case law (scholar.google.com).

    Google Scholar has excellent coverage for all US case law — federal appellate,
    Supreme Court, and state courts.  The search page returns server-rendered HTML
    with ``/scholar_case`` links and case titles.  We visit the first result to
    extract the canonical name, year, and confirm the citation appears on the page.
    """

    def __init__(self, session=None):
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
        self.session = session

    @staticmethod
    def _clean_citation_for_search(citation: str) -> str:
        """Strip pinpoint pages, footnotes, and parentheticals for cleaner search.
        
        E.g. 'Trichell v. Midland Credit Mgmt., Inc., 964 F.3d 990, 999, n. 2 (2020) (sitting by designation)'
        becomes '964 F.3d 990'.
        """
        # Try to extract just the volume-reporter-page core
        m = re.search(r'(\d+)\s+([A-Za-z][A-Za-z.\s]*\d*[a-z]{0,2}\.?)\s+(\d+)', citation)
        if m:
            return f"{m.group(1)} {m.group(2).strip()} {m.group(3)}"
        # Fallback: strip parentheticals
        cleaned = re.sub(r'\([^)]*\)', '', citation).strip()
        return cleaned

    async def verify(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Verify using Google Scholar case law search."""
        try:
            search_citation = self._clean_citation_for_search(citation)
            search_url = (
                f"https://scholar.google.com/scholar"
                f"?hl=en&as_sdt=2006&q={quote(search_citation)}"
            )

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }

            logger.debug(f"[SCHOLAR] Searching: {search_citation[:60]}")
            response = self.session.get(
                search_url, headers=headers, timeout=min(timeout, 10)
            )

            if response.status_code != 200:
                return {"verified": False, "error": f"HTTP {response.status_code}"}

            content = response.text

            # Detect captcha / rate-limit
            if "captcha" in content.lower() or "unusual traffic" in content.lower():
                logger.warning(f"[SCHOLAR] Captcha / rate-limit detected for: {search_citation[:60]}")
                return {"verified": False, "error": "Scholar rate-limited"}

            # Extract scholar_case links with titles
            results = re.findall(
                r'href="(/scholar_case\?[^"]+)"[^>]*>([^<]+)</a>',
                content,
            )
            # Deduplicate by link (keep first occurrence)
            seen = set()
            unique_results = []
            for link, title in results:
                link_clean = link.replace("&amp;", "&")
                # Skip "about" links (they are duplicates)
                if "about=" in link_clean:
                    continue
                if link_clean not in seen:
                    seen.add(link_clean)
                    unique_results.append((link_clean, title.strip()))

            if not unique_results:
                logger.debug(f"[SCHOLAR] No results for: {search_citation[:60]}")
                return {"verified": False, "error": "No results on Google Scholar"}

            # Visit the first result
            for rel_link, search_title in unique_results[:2]:
                case_url = f"https://scholar.google.com{rel_link}"
                try:
                    page = self.session.get(
                        case_url, headers=headers, timeout=min(8, timeout)
                    )
                    if page.status_code != 200:
                        continue
                    page_content = page.text

                    # Extract canonical name from <title>
                    canonical_name = None
                    title_match = re.search(
                        r"<title>([^<]+)</title>", page_content, re.IGNORECASE
                    )
                    if title_match:
                        raw_title = html.unescape(title_match.group(1).strip())
                        # Strip " - Google Scholar" suffix
                        canonical_name = re.sub(
                            r"\s*-\s*Google Scholar.*$", "", raw_title
                        ).strip()
                        # Strip trailing citation info: ", 573 US 149 - Supreme Court 2014"
                        # Keep just the case name part
                        name_match = re.match(
                            r"^(.+?),\s+\d+\s+", canonical_name
                        )
                        if name_match:
                            canonical_name = name_match.group(1).strip()

                    if not canonical_name:
                        # Fallback to search result title
                        canonical_name = search_title

                    # Check if citation appears on the page (try full text, then base citation)
                    page_lower = page_content.lower().replace(" ", "")
                    citation_on_page = (
                        citation.lower().replace(" ", "") in page_lower
                    )
                    if not citation_on_page:
                        # Try with just the base citation (volume-reporter-page)
                        citation_on_page = (
                            search_citation.lower().replace(" ", "") in page_lower
                        )
                    if not citation_on_page:
                        continue

                    # Extract year from page content (early in the document)
                    canonical_date = None
                    year_match = re.search(
                        r"\b(18|19|20)\d{2}\b", page_content[:5000]
                    )
                    if year_match:
                        canonical_date = year_match.group(0)

                    # Validate name match if we have an extracted name
                    if extracted_case_name and extracted_case_name != "N/A":
                        is_valid, overlap, warning = NameValidator.validate_match(
                            extracted_case_name, canonical_name, min_overlap=0.25
                        )
                        if not is_valid:
                            logger.debug(
                                f"[SCHOLAR] Name mismatch: extracted='{extracted_case_name}' "
                                f"canonical='{canonical_name}' overlap={overlap:.2f}"
                            )
                            continue

                    logger.info(f"[SCHOLAR] Verified: {canonical_name}")
                    return {
                        "verified": True,
                        "canonical_name": canonical_name,
                        "canonical_date": canonical_date,
                        "canonical_url": case_url,
                        "source": "Google Scholar",
                        "confidence": 0.90,
                    }

                except Exception as e:
                    logger.debug(f"[SCHOLAR] Error checking case page: {e}")
                    continue

            logger.debug(f"[SCHOLAR] No matching case page for: {search_citation[:60]}")
            return {"verified": False, "error": "No matching case on Google Scholar"}

        except Exception as e:
            logger.warning(f"Google Scholar verification failed: {e}")
            return {"verified": False, "error": str(e)}
