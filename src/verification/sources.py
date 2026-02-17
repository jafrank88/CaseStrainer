"""
Verification Sources Module
============================

Individual source verifiers (CourtListener, Justia, Cornell LII, etc.)
"""

import re
import html
import asyncio
import logging
import os
import random
import time
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import quote

from src.utils.fallback_verification_utils import URLBuilder, HTMLExtractor, NameValidator, HTTPClient

logger = logging.getLogger(__name__)


class BaseURLVerifier:
    """
    Base class for verifiers that: build URL from citation, fetch page, extract name via
    HTMLExtractor, validate via NameValidator, and return a result dict.
    Subclasses override build_url(), source_name, and optionally extract_date_from_content()
    and post_process_canonical_name().
    """

    source_name: str = "Base"
    confidence_high: float = 0.85
    confidence_low: float = 0.60
    min_overlap: float = 0.3

    def __init__(self, session=None):
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
        self.session = session

    def build_url(self, citation: str) -> Optional[str]:
        """Return the URL to fetch for this citation, or None if not buildable. Subclasses must override."""
        return None

    def extract_date_from_content(self, content: str) -> Optional[str]:
        """Extract date/year from page content. Default: HTMLExtractor.extract_year."""
        return HTMLExtractor.extract_year(content)

    def post_process_canonical_name(self, canonical_name: str, content: str) -> str:
        """Optional cleanup of extracted case name (e.g. strip leading citation). Default: identity."""
        return canonical_name

    def _confidence_for_overlap(self, overlap: float) -> float:
        return self.confidence_high if overlap >= self.min_overlap else self.confidence_low

    async def verify(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Common flow: build URL, fetch, extract name/date, validate, return result."""
        direct_url = self.build_url(citation)
        if not direct_url:
            return {"verified": False, "error": "Cannot build URL"}

        try:
            headers = HTTPClient.get_headers()
            response = self.session.get(direct_url, headers=headers, timeout=min(timeout, 10))

            if response.status_code != 200:
                return {"verified": False, "error": f"HTTP {response.status_code}"}

            content = response.text
            canonical_name = HTMLExtractor.extract_case_name(content)

            if not canonical_name:
                return {"verified": False, "error": "No case name on page"}

            canonical_name = self.post_process_canonical_name(canonical_name, content)
            canonical_date = self.extract_date_from_content(content)

            if extracted_case_name:
                is_valid, overlap, warning = NameValidator.validate_match(
                    extracted_case_name, canonical_name, min_overlap=self.min_overlap
                )
                if not is_valid:
                    return {
                        "verified": False,
                        "canonical_name": canonical_name,
                        "canonical_date": canonical_date,
                        "canonical_url": direct_url,
                        "source": self.source_name,
                        "confidence": 0.5,
                        "validation_warning": warning,
                    }
                confidence = self._confidence_for_overlap(overlap)
            else:
                confidence = self.confidence_high

            return {
                "verified": True,
                "canonical_name": canonical_name,
                "canonical_date": canonical_date,
                "canonical_url": direct_url,
                "source": self.source_name,
                "confidence": confidence,
            }

        except Exception as e:
            logger.warning(f"{self.source_name} verification failed: {e}")
            return {"verified": False, "error": str(e)}


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


class JustiaVerifier(BaseURLVerifier):
    """Verifier for Justia legal database."""

    source_name = "Justia"
    confidence_high = 0.85
    confidence_low = 0.60

    def build_url(self, citation: str) -> Optional[str]:
        return URLBuilder.build_justia_url(citation)

    def extract_date_from_content(self, content: str) -> Optional[str]:
        return HTMLExtractor.extract_date(content)


class CornellLIIVerifier(BaseURLVerifier):
    """Verifier for Cornell Legal Information Institute."""

    source_name = "Cornell LII"
    confidence_high = 0.90
    confidence_low = 0.75
    min_overlap = 0.5

    def build_url(self, citation: str) -> Optional[str]:
        return URLBuilder.build_cornell_lii_url(citation)


class OpenJuristVerifier(BaseURLVerifier):
    """Verifier for OpenJurist."""

    source_name = "OpenJurist"
    confidence_high = 0.85
    confidence_low = 0.85

    def build_url(self, citation: str) -> Optional[str]:
        return URLBuilder.build_openjurist_url(citation)

    def post_process_canonical_name(self, canonical_name: str, content: str) -> str:
        # "410 US 113 Roe v. Wade" -> "Roe v. Wade"
        return re.sub(r"^\d+\s+[A-Z\.]+\s+\d+\s+", "", canonical_name).strip()

    async def verify(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        result = await super().verify(citation, extracted_case_name, timeout)
        # Original only returned success when "v" in canonical_name (avoid non-case pages)
        if result.get("verified") and result.get("canonical_name"):
            if "v" not in result["canonical_name"].lower():
                return {"verified": False, "error": "No case name (v.) on page"}
        return result


class GoogleScholarVerifier:
    """Verifier for Google Scholar case law (scholar.google.com).

    Google Scholar has excellent coverage for all US case law — federal appellate,
    Supreme Court, and state courts.  The search page returns server-rendered HTML
    with ``/scholar_case`` links and case titles.  We visit the first result to
    extract the canonical name, year, and confirm the citation appears on the page.

    Anti-rate-limiting measures:
    - Random delays (2-4s + jitter) between requests
    - Cookie persistence via a dedicated requests.Session
    - Rotating User-Agent strings to mimic different browsers
    - Proxy rotation via SCHOLAR_PROXY_LIST env var (comma-separated)
    """

    # Rotating User-Agent pool to mimic different browsers
    _USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    ]

    # Class-level state shared across instances for rate-limiting
    _last_request_time: float = 0.0
    _scholar_session: Optional[requests.Session] = None
    _proxy_list: Optional[List[str]] = None
    _proxy_index: int = 0

    def __init__(self, session=None):
        # Keep the passed session as a fallback but prefer a dedicated Scholar session
        self._fallback_session = session
        self._init_scholar_session()
        self._init_proxies()

    def _init_scholar_session(self):
        """Create a dedicated session with cookie persistence for Scholar."""
        if GoogleScholarVerifier._scholar_session is None:
            s = requests.Session()
            # Pre-set headers that look like a real browser
            s.headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            })
            GoogleScholarVerifier._scholar_session = s
            logger.debug("[SCHOLAR] Created dedicated session with cookie persistence")

    def _init_proxies(self):
        """Load proxy list from SCHOLAR_PROXY_LIST env var (comma-separated URLs)."""
        if GoogleScholarVerifier._proxy_list is None:
            proxy_env = os.environ.get("SCHOLAR_PROXY_LIST", "")
            if proxy_env.strip():
                GoogleScholarVerifier._proxy_list = [
                    p.strip() for p in proxy_env.split(",") if p.strip()
                ]
                logger.info(f"[SCHOLAR] Loaded {len(GoogleScholarVerifier._proxy_list)} proxies")
            else:
                GoogleScholarVerifier._proxy_list = []

    def _get_next_proxy(self) -> Optional[Dict[str, str]]:
        """Rotate to the next proxy. Returns None if no proxies configured."""
        if not GoogleScholarVerifier._proxy_list:
            return None
        proxy_url = GoogleScholarVerifier._proxy_list[
            GoogleScholarVerifier._proxy_index % len(GoogleScholarVerifier._proxy_list)
        ]
        GoogleScholarVerifier._proxy_index += 1
        return {"http": proxy_url, "https": proxy_url}

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with a randomly selected User-Agent."""
        ua = random.choice(self._USER_AGENTS)
        return {
            "User-Agent": ua,
            "Referer": "https://scholar.google.com/",
        }

    async def _throttle(self):
        """Enforce a random delay between Scholar requests to avoid rate-limiting."""
        now = time.time()
        elapsed = now - GoogleScholarVerifier._last_request_time
        # Base delay 2-4 seconds with random jitter
        min_delay = 2.0 + random.uniform(0, 2.0)
        if elapsed < min_delay:
            wait = min_delay - elapsed
            logger.debug(f"[SCHOLAR] Throttling: waiting {wait:.1f}s")
            await asyncio.sleep(wait)
        GoogleScholarVerifier._last_request_time = time.time()

    def _scholar_get(self, url: str, timeout: float) -> requests.Response:
        """Make a GET request using the Scholar session with proxy rotation."""
        session = GoogleScholarVerifier._scholar_session or self._fallback_session
        headers = self._get_headers()
        proxies = self._get_next_proxy()
        kwargs: Dict[str, Any] = {
            "headers": headers,
            "timeout": min(timeout, 10),
        }
        if proxies:
            kwargs["proxies"] = proxies
            logger.debug(f"[SCHOLAR] Using proxy: {proxies.get('https', 'none')[:40]}")
        return session.get(url, **kwargs)

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

            # Throttle before the search request
            await self._throttle()

            logger.debug(f"[SCHOLAR] Searching: {search_citation[:60]}")
            response = self._scholar_get(search_url, timeout)

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

            # Visit the first result (with throttle between requests)
            for rel_link, search_title in unique_results[:2]:
                case_url = f"https://scholar.google.com{rel_link}"
                try:
                    # Throttle before visiting case page
                    await self._throttle()

                    page = self._scholar_get(case_url, timeout)
                    if page.status_code != 200:
                        continue
                    page_content = page.text

                    # Detect captcha on case page too
                    if "captcha" in page_content.lower() or "unusual traffic" in page_content.lower():
                        logger.warning(f"[SCHOLAR] Captcha on case page: {case_url[:60]}")
                        continue

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


class FindLawVerifier:
    """Verifier for FindLaw (caselaw.findlaw.com).

    FindLaw has excellent coverage for recent federal and state cases,
    often indexing opinions within days of publication.  This makes it
    a valuable fallback for very recent citations that CourtListener
    and Google Scholar have not yet indexed.

    Uses FindLaw's search endpoint to locate cases by citation text,
    then visits the case page to extract canonical name and date.
    """

    def __init__(self, session=None):
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
        self.session = session

    async def verify(
        self,
        citation: str,
        extracted_case_name: Optional[str] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Verify using FindLaw case law search."""
        try:
            # Build search query: use citation + case name if available
            search_query = citation
            if extracted_case_name and extracted_case_name != "N/A":
                search_query = f"{extracted_case_name} {citation}"

            search_url = (
                f"https://caselaw.findlaw.com/search"
                f"?q={quote(search_query)}"
            )

            headers = HTTPClient.get_headers()
            logger.debug(f"[FINDLAW] Searching: {search_query[:60]}")
            response = self.session.get(
                search_url, headers=headers, timeout=min(timeout, 10)
            )

            if response.status_code != 200:
                return {"verified": False, "error": f"HTTP {response.status_code}"}

            content = response.text

            # Extract case links from search results
            # FindLaw search results have links like /court/us-dis-crt-d-mas/116931955.html
            case_links = re.findall(
                r'href="(https?://caselaw\.findlaw\.com/court/[^"]+)"[^>]*>\s*([^<]+)',
                content,
            )
            if not case_links:
                # Try relative links
                case_links = re.findall(
                    r'href="(/court/[^"]+)"[^>]*>\s*([^<]+)',
                    content,
                )
                case_links = [
                    (f"https://caselaw.findlaw.com{link}", title)
                    for link, title in case_links
                ]

            if not case_links:
                logger.debug(f"[FINDLAW] No results for: {search_query[:60]}")
                return {"verified": False, "error": "No results on FindLaw"}

            # Visit top results to find a match
            for case_url, search_title in case_links[:3]:
                try:
                    page = self.session.get(
                        case_url, headers=headers, timeout=min(8, timeout)
                    )
                    if page.status_code != 200:
                        continue
                    page_content = page.text

                    # Extract canonical name from og:description or title
                    canonical_name = None
                    og_match = re.search(
                        r'<meta\s+(?:property|name)="og:description"\s+content="Case opinion for[^"]*?([A-Z][^"]*?v\.?\s+[^"]+?)\.?\s*Read',
                        page_content, re.IGNORECASE,
                    )
                    if og_match:
                        canonical_name = og_match.group(1).strip()
                    if not canonical_name:
                        title_match = re.search(
                            r"<title>\s*([^<]+?)\s*(?:\(\d{4}\))?\s*\|",
                            page_content, re.IGNORECASE,
                        )
                        if title_match:
                            canonical_name = html.unescape(title_match.group(1).strip())
                    if not canonical_name:
                        canonical_name = html.unescape(search_title.strip())

                    # Check if citation appears on the page
                    page_lower = page_content.lower().replace(" ", "")
                    citation_normalized = citation.lower().replace(" ", "")
                    if citation_normalized not in page_lower:
                        # Try with periods removed too
                        citation_no_dots = citation.lower().replace(".", "").replace(" ", "")
                        page_no_dots = page_content.lower().replace(".", "").replace(" ", "")
                        if citation_no_dots not in page_no_dots:
                            continue

                    # Extract year
                    canonical_date = None
                    date_match = re.search(
                        r"Decided:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",
                        page_content,
                    )
                    if date_match:
                        year_m = re.search(r"(\d{4})", date_match.group(1))
                        if year_m:
                            canonical_date = year_m.group(1)
                    if not canonical_date:
                        year_match = re.search(r"\b(20\d{2})\b", page_content[:5000])
                        if year_match:
                            canonical_date = year_match.group(1)

                    # Validate name match
                    if extracted_case_name and extracted_case_name != "N/A" and canonical_name:
                        is_valid, overlap, warning = NameValidator.validate_match(
                            extracted_case_name, canonical_name, min_overlap=0.25
                        )
                        if not is_valid:
                            logger.debug(
                                f"[FINDLAW] Name mismatch: extracted='{extracted_case_name}' "
                                f"canonical='{canonical_name}' overlap={overlap:.2f}"
                            )
                            continue

                    logger.info(f"[FINDLAW] Verified: {canonical_name}")
                    return {
                        "verified": True,
                        "canonical_name": canonical_name,
                        "canonical_date": canonical_date,
                        "canonical_url": case_url,
                        "source": "FindLaw",
                        "confidence": 0.85,
                    }

                except Exception as e:
                    logger.debug(f"[FINDLAW] Error checking case page: {e}")
                    continue

            logger.debug(f"[FINDLAW] No matching case page for: {search_query[:60]}")
            return {"verified": False, "error": "No matching case on FindLaw"}

        except Exception as e:
            logger.warning(f"FindLaw verification failed: {e}")
            return {"verified": False, "error": str(e)}
