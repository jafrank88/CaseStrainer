"""
URL content fetching and text preprocessing for citation extraction.

Moved from progress_manager to separate progress tracking from input acquisition.
Used by: progress_manager (re-export), unified_input_processor, vue_api_endpoints_updated.
"""

import json
import logging
import os
import re
import tempfile
import time
import traceback

import requests

from src.config import DEFAULT_REQUEST_TIMEOUT

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)
logger = logging.getLogger(__name__)

__all__ = ["fetch_url_content", "preprocess_extracted_text"]


def preprocess_extracted_text(text: str) -> str:
    """
    FIX #13: Preprocess extracted text to remove markers that break context isolation.

    This MUST happen before eyecite parses the text, so it's done immediately
    after PDF extraction in fetch_url_content().

    Removes endnote/footnote markers that separate case names from citations.
    Example: "Acres Bonusing, Inc. v. Marston [Endnote 18], 17 F.4th 901"
    Becomes: "Acres Bonusing, Inc. v. Marston, 17 F.4th 901"
    
    Also removes "Cite as:" headers that contain dates, which can contaminate date extraction.
    Example: "Cite as: 594 U. S. ____ (2021)" -> removed
    """
    if not text:
        return text

    original_length = len(text)

    # CRITICAL FIX: Remove "Cite as:" headers that contaminate extraction (e.g. Milkovich -> 594 U.S. _)
    # REQUIRE \n in match to avoid eating entire document when PDF has no newline after header
    # (e.g. "Cite as: 594 U. S. _ (2021)" + page content with no \n -> [^\n]*(?:\n|$) matched to EOF)
    cite_as_pattern = r"(?:^|\n)\s*Cite\s+as:?\s*[^\n]{0,100}(?:\([^)]*\d{4}[^)]*\)|_{1,4}\s*\(\d{4}\)|\(\d{4}\))[^\n]{0,50}\n"
    text, count_cite_as = re.subn(cite_as_pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    # Mid-line: "text. Cite as: 594 U. S. _ (scotus 2021)\n" - require newline to avoid eating doc
    cite_as_midline = r"\s+Cite\s+as:?\s*\d+\s+U\.?\s*S\.?\s*_{1,4}[^\n]{0,80}\([^)]*\d{4}[^)]*\)[^\n]{0,50}\n"
    text, count_midline = re.subn(cite_as_midline, "", text, flags=re.IGNORECASE)
    count_cite_as += count_midline
    # Also remove standalone "Cite as:" lines (placeholder only). Require \n to avoid eating doc.
    cite_as_simple = r"(?:^|\n)\s*Cite\s+as:?\s*[^\n]{0,50}\d+\s+U\.?\s*S\.?\s*_{1,4}[^\n]{0,80}\n"
    text, count_cite_as_simple = re.subn(cite_as_simple, "", text, flags=re.IGNORECASE | re.MULTILINE)

    # Fallback: Remove inline "Cite as: 594 U. S. _ (2021)" when NO newline (PDF page break).
    # Cap to ~70 chars so we never eat document content.
    cite_as_inline = r"Cite\s+as:?\s*\d+\s+U\.?\s*S\.?\s*_{1,4}\s*\([^)]*\d{4}[^)]*\)"
    text, count_inline = re.subn(cite_as_inline, "", text, flags=re.IGNORECASE)
    count_cite_as += count_inline

    # Pattern 1: [Endnote N] with optional surrounding whitespace
    text, count1 = re.subn(r"\s*\[(?:Endnote|Footnote|FN|n\.?)\s*\d+\]\s*", " ", text, flags=re.IGNORECASE)

    # Pattern 2: Endnote markers without brackets (less common but possible)
    text, count2 = re.subn(r"\s+(?:Endnote|Footnote|FN)\s+\d+\s+", " ", text, flags=re.IGNORECASE)

    # Pattern 3: Remove standalone footnote superscripts/numbers between text
    # Be conservative - only remove if it looks like a footnote (small number between words)
    # This catches: "argument that\n\n18\n\nMarston" -> "argument that Marston"
    #
    # IMPORTANT: Require a newline in the gap between the letter and the digits. If the gap is
    # only horizontal whitespace (e.g. "F.3d 460 Unverified" after later line collapse), treating
    # the reporter page number as a footnote strips the page and breaks extraction (UI paste of
    # CaseStrainer output is a real case).
    def _strip_orphan_footnote_num(m: re.Match) -> str:
        letter, gap, digits = m.group(1), m.group(2), m.group(3)
        if "\n" not in gap:
            return m.group(0)
        try:
            n = int(digits)
        except ValueError:
            return m.group(0)
        # Reporter pages are often 3 digits; vertical layout can break "F.3d" and page across lines.
        if n >= 100:
            return m.group(0)
        idx = m.start(1)
        if letter in "dD" and idx > 0 and text[idx - 1].isdigit():
            return m.group(0)
        return letter + " "

    text = re.sub(
        r"([A-Za-z])(\s+)(\d{1,3})(\s+)(?=[A-Z][a-z])",
        _strip_orphan_footnote_num,
        text,
    )

    # Pattern 3b: Remove orphan numbers after "v." in case names
    # This catches: "Inc. v. 15 Marston" -> "Inc. v. Marston"
    text = re.sub(r"(v\.\s+)\d{1,3}\s+(?=[A-Z])", r"\1", text, flags=re.IGNORECASE)

    total_removed = count1 + count2 + count_cite_as + count_cite_as_simple
    if total_removed > 0:
        logger.info(
            f"[PREPROCESSING] Removed {total_removed} markers ({count_cite_as + count_cite_as_simple} 'Cite as:' headers, "
            f"{count1 + count2} endnote/footnote markers) ({original_length} -> {len(text)} chars)"
        )

    # Strip OSCN "Citationize" citation index section.
    # OSCN opinions append a citation table that eyecite misreads as real in-text citations,
    # producing false-positive case cards and broken clusters.
    # Pattern A: "Citationize" is OSCN's proprietary label — safe to strip everything after it.
    oscn_m = re.search(r'(?:^|\n)\s*Citationize\b', text, re.IGNORECASE)
    if oscn_m:
        stripped = len(text) - oscn_m.start()
        text = text[:oscn_m.start()].rstrip()
        logger.info(f"[PREPROCESSING] Removed OSCN Citationize section ({stripped} chars)")
    else:
        # Pattern B fallback: "Cite Name Level" column header immediately followed by
        # an OK-reporter citation — this combination cannot appear in genuine brief text.
        oscn_m2 = re.search(
            r'\bCite\s+Name\s+Level\b\s{0,20}\d+\s+(?:OK\b|P\.\s*\d?d\s)',
            text, re.IGNORECASE
        )
        if oscn_m2:
            # Walk back up to 300 chars to find the enclosing section header and strip from there.
            preamble_start = max(0, oscn_m2.start() - 300)
            preamble = text[preamble_start:oscn_m2.start()]
            hdr = re.search(
                r'\b(?:Oklahoma\s+(?:Supreme|Court|Civil)|Court\s+Cases|Citationize)\b',
                preamble, re.IGNORECASE
            )
            strip_from = preamble_start + hdr.start() if hdr else oscn_m2.start()
            stripped = len(text) - strip_from
            text = text[:strip_from].rstrip()
            logger.info(f"[PREPROCESSING] Removed OSCN citation table via 'Cite Name Level' pattern ({stripped} chars)")

    # Clean up whitespace created by removals. Preserve newlines - collapsing all \s+ to space
    # can merge lines and break citation parsing / date extraction (regression: fewer citations).
    text = re.sub(r"[ \t]+", " ", text)  # Collapse horizontal whitespace only
    text = re.sub(r"\n{3,}", "\n\n", text)  # Collapse 3+ newlines to 2

    # Clean up double commas
    text = re.sub(r",\s*,", ",", text)

    return text



def fetch_url_content(url: str) -> str:
    """Fetch content from a URL with proper error handling and user agent."""
    try:
        logger.info(f"Fetching URL: {url}")
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # OPTIMIZATION: For CourtListener opinion URLs, convert to API endpoint
        # Web URLs return 202, but API endpoint returns JSON immediately with full text
        # Store original URL for fallback if API is rate-limited
        original_url = url
        courtlistener_api_attempted = False

        if "courtlistener.com" in url.lower() and "/opinion/" in url and "/api/" not in url:
            import re

            # Extract opinion ID from URL: /opinion/10460933/robert-cassell-v-state...
            opinion_match = re.search(r"/opinion/(\d+)/", url)
            if opinion_match:
                opinion_id = opinion_match.group(1)
                # Convert to API endpoint
                api_url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
                logger.info("[CONVERT] Converting CourtListener opinion URL to API endpoint")
                logger.info(f"   Opinion ID: {opinion_id}")
                logger.info(f"   API URL: {api_url}")
                url = api_url
                courtlistener_api_attempted = True
                # Add API headers
                from src.config import COURTLISTENER_API_KEY

                if COURTLISTENER_API_KEY:
                    headers["Authorization"] = f"Token {COURTLISTENER_API_KEY}"
                    headers["Accept"] = "application/json"
                    logger.info("[OK] Added CourtListener API authorization header")
                else:
                    logger.warning("COURTLISTENER_API_KEY is not set")
            else:
                logger.warning("[WARNING]  Could not extract opinion ID from URL")

        # API search disabled for CourtListener opinion URLs (see above)
        # This avoids rate limit errors and is faster

        if url.lower().endswith(".pdf"):
            headers["Accept"] = "application/pdf,application/x-pdf,application/octet-stream"
        elif url.lower().endswith((".docx", ".doc")):
            headers["Accept"] = (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword,application/octet-stream"
            )
        elif url.lower().endswith(".rtf"):
            headers["Accept"] = "application/rtf,text/rtf,application/octet-stream"
        elif url.lower().endswith((".md", ".markdown")):
            headers["Accept"] = "text/markdown,text/plain,application/octet-stream"
        elif url.lower().endswith((".txt", ".html", ".htm", ".xml", ".xhtml")):
            headers["Accept"] = "text/html,text/xml,text/plain,application/xhtml+xml,application/xml"

        # Handle 202 (Accepted) and 429 (Rate Limit) responses with retry
        # CourtListener sometimes returns 202 while page is being generated or 429 when rate limited
        import time

        max_attempts = 4
        retry_delay = 5  # Start with 5 seconds

        for attempt in range(max_attempts):
            # Try with SSL verification first, then fallback to unverified if SSL fails
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=DEFAULT_REQUEST_TIMEOUT,  # 30 second timeout
                    allow_redirects=True,
                    stream=True,  # Stream the response for large files
                    verify=True,  # Try SSL verification first
                )
            except requests.exceptions.SSLError as ssl_error:
                logger.warning(
                    f"SSL verification failed for {url} (attempt {attempt + 1}), trying without verification: {ssl_error}"
                )
                try:
                    # Suppress SSL warnings for unverified requests
                    import urllib3

                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

                    response = requests.get(
                        url,
                        headers=headers,
                        timeout=DEFAULT_REQUEST_TIMEOUT,
                        allow_redirects=True,
                        stream=True,
                        verify=False,  # nosec - Disable SSL verification as fallback after SSL fails
                    )
                    logger.info(f"Successfully fetched {url} without SSL verification")
                except Exception as e:
                    logger.error(f"Failed to fetch {url} even without SSL verification: {e}")
                    raise

            logger.info(f"Response status: {response.status_code}")

            # Handle 202 (Accepted) - page still generating
            if response.status_code == 202:
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"[WARNING]  Got 202 Accepted - page still generating, retrying in {retry_delay}s (attempt {attempt + 1}/{max_attempts})"
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Still getting 202 after {max_attempts} attempts")

            # Handle 429 (Too Many Requests) - rate limited
            elif response.status_code == 429:
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"[WARNING]  Rate limited (429), retrying in {retry_delay}s (attempt {attempt + 1}/{max_attempts})"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"Still rate limited after {max_attempts} attempts")
                    # FALLBACK: If this was a CourtListener API endpoint, try HTML scraping instead
                    if courtlistener_api_attempted and original_url != url:
                        logger.warning("[CONVERT] Falling back to HTML scraping from original URL")
                        logger.info(f"   Original URL: {original_url}")
                        url = original_url
                        # Reset headers for HTML scraping
                        headers.pop("Authorization", None)
                        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                        # Try one more time with the original URL
                        response = requests.get(
                            url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT, allow_redirects=True, stream=True
                        )
                        logger.info(f"Fallback response status: {response.status_code}")
                        if response.status_code != 429:
                            response.raise_for_status()
                            break
                        else:
                            logger.error("HTML fallback also rate limited")
                    # If not CourtListener or fallback failed, raise the error
                    response.raise_for_status()

            response.raise_for_status()
            break

        content_type = response.headers.get("content-type", "").lower()
        logger.info(f"Content type: {content_type}")

        if "pdf" in content_type or url.lower().endswith(".pdf"):
            # USER FIX: Use the same PDF extraction pipeline as file uploads for consistency
            # Save PDF content to temporary file and use extract_text_from_pdf_smart()
            import tempfile
            import os

            try:
                # Save PDF content to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                    temp_pdf.write(response.content)
                    temp_pdf_path = temp_pdf.name

                try:
                    logger.info("Extracting PDF from URL using extract_text_from_pdf_smart()")
                    from src.robust_pdf_extractor import extract_text_from_pdf_smart

                    result = extract_text_from_pdf_smart(temp_pdf_path)

                    if result and len(result.strip()) > 0:
                        logger.info(f"Successfully extracted {len(result)} characters from URL PDF")
                        # FIX #13: Preprocess text to remove endnote markers BEFORE eyecite sees it
                        result = preprocess_extracted_text(result)
                        logger.info(f"After preprocessing: {len(result)} characters")
                        return result
                    else:
                        logger.error("PDF extraction returned empty content")
                        raise Exception("The PDF document appears to be empty or unreadable")

                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_pdf_path)
                    except OSError:
                        pass

            except Exception as e:
                logger.error(f"PDF extraction from URL failed: {str(e)}")
                raise Exception(
                    f"The PDF document could not be processed: {str(e)}. It may be corrupted, password-protected, or in an unsupported format."
                )

        elif (
            "word" in content_type
            or "openxmlformats" in content_type
            or url.lower().endswith(".docx")
            or url.lower().endswith(".doc")
        ):
            # Handle Word documents (DOCX and DOC)
            import tempfile
            import os

            try:
                # Determine file extension from URL or content type
                if url.lower().endswith(".docx") or "openxmlformats" in content_type:
                    file_ext = "docx"
                elif url.lower().endswith(".doc") or "msword" in content_type:
                    file_ext = "doc"
                else:
                    # Default to docx for modern Word documents
                    file_ext = "docx"

                # Save document content to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_doc:
                    temp_doc.write(response.content)
                    temp_doc_path = temp_doc.name

                try:
                    logger.info(f"Extracting {file_ext.upper()} from URL using unified_text_extractor")
                    from src.unified_text_extractor import UnifiedTextExtractor

                    extractor = UnifiedTextExtractor(verbose=True)
                    result, method = extractor.extract_text_from_file(temp_doc_path)

                    if result and len(result.strip()) > 0:
                        logger.info(
                            f"Successfully extracted {len(result)} characters from URL {file_ext.upper()} using {method}"
                        )
                        # Preprocess text to clean artifacts
                        result = preprocess_extracted_text(result)
                        logger.info(f"After preprocessing: {len(result)} characters")
                        return result
                    else:
                        logger.error(f"{file_ext.upper()} extraction returned empty content")
                        raise Exception(f"The {file_ext.upper()} document appears to be empty or unreadable")

                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_doc_path)
                    except OSError:
                        pass

            except Exception as e:
                logger.error(f"{file_ext.upper()} extraction from URL failed: {str(e)}")
                raise Exception(
                    f"The Word document could not be processed: {str(e)}. It may be corrupted, password-protected, or in an unsupported format."
                )

        elif "rtf" in content_type or url.lower().endswith(".rtf"):
            # Handle Rich Text Format (RTF) files
            import tempfile
            import os

            try:
                # Save RTF content to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".rtf") as temp_rtf:
                    temp_rtf.write(response.content)
                    temp_rtf_path = temp_rtf.name

                try:
                    logger.info("Extracting RTF from URL using unified_text_extractor")
                    from src.unified_text_extractor import UnifiedTextExtractor

                    extractor = UnifiedTextExtractor(verbose=True)
                    result, method = extractor.extract_text_from_file(temp_rtf_path)

                    if result and len(result.strip()) > 0:
                        logger.info(f"Successfully extracted {len(result)} characters from URL RTF using {method}")
                        # Preprocess text to clean artifacts
                        result = preprocess_extracted_text(result)
                        logger.info(f"After preprocessing: {len(result)} characters")
                        return result
                    else:
                        logger.error("RTF extraction returned empty content")
                        raise Exception("The RTF document appears to be empty or unreadable")

                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_rtf_path)
                    except OSError:
                        pass

            except Exception as e:
                logger.error(f"RTF extraction from URL failed: {str(e)}")
                raise Exception(
                    f"The RTF document could not be processed: {str(e)}. It may be corrupted or in an unsupported format."
                )

        elif "json" in content_type or "application/json" in content_type:
            # Handle JSON responses (e.g., from CourtListener API)
            logger.info("Processing JSON response from API")
            try:
                import json

                data = response.json()

                # Extract text from CourtListener API opinion response
                # Check plain_text first, but only if it actually contains content
                if "plain_text" in data and data["plain_text"] and len(data["plain_text"].strip()) > 0:
                    text = data["plain_text"]
                    logger.info(f"[OK] Extracted opinion plain_text: {len(text)} characters")
                    return text
                elif (
                    "html_with_citations" in data
                    and data["html_with_citations"]
                    and len(data["html_with_citations"].strip()) > 0
                ):
                    # Fallback to HTML version with citations
                    from bs4 import BeautifulSoup

                    html = data["html_with_citations"]
                    soup = BeautifulSoup(html, "html.parser")
                    text = soup.get_text(separator=" ", strip=True)
                    logger.info(f"[OK] Extracted from html_with_citations: {len(text)} characters")
                    return text
                elif "html" in data and data["html"] and len(data["html"].strip()) > 0:
                    from bs4 import BeautifulSoup

                    html = data["html"]
                    soup = BeautifulSoup(html, "html.parser")
                    text = soup.get_text(separator=" ", strip=True)
                    logger.info(f"[OK] Extracted from html field: {len(text)} characters")
                    return text
                else:
                    # Return JSON as formatted string
                    logger.warning("[WARNING]  JSON response doesn't contain expected text fields")
                    logger.warning(f"   Available fields: {list(data.keys())}")
                    return json.dumps(data, indent=2)
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return response.text

        elif (
            "html" in content_type
            or "xml" in content_type
            or url.lower().endswith(".html")
            or url.lower().endswith(".htm")
            or url.lower().endswith(".xml")
            or url.lower().endswith(".xhtml")
        ):
            # Handle HTML and XML content
            logger.info(f"Processing {'HTML' if 'html' in content_type else 'XML'} content")
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(response.text, "html.parser")
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                # Get text
                text = soup.get_text(separator=" ", strip=True)
                logger.info(
                    f"[OK] Extracted text from {'HTML' if 'html' in content_type else 'XML'}: {len(text)} characters"
                )
                text = preprocess_extracted_text(text)
                return text
            except Exception as e:
                logger.warning(f"Failed to parse {'HTML' if 'html' in content_type else 'XML'} with BeautifulSoup: {e}")
                logger.info(f"Returning raw content, length: {len(response.text)}")
                return response.text

        elif (
            "text/plain" in content_type
            or "text/markdown" in content_type
            or url.lower().endswith(".txt")
            or url.lower().endswith(".md")
            or url.lower().endswith(".markdown")
        ):
            # Handle plain text and markdown files
            logger.info(f"Processing {'plain text' if 'text/plain' in content_type else 'markdown'} content")
            text = response.text

            # Basic markdown cleanup for .md files
            if url.lower().endswith(".md") or "markdown" in content_type:
                # Remove common markdown syntax that might interfere with citation extraction
                import re

                # Remove markdown links [text](url) -> text
                text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
                # Remove markdown headers (# ## ###)
                text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
                # Remove bold/italic markers
                text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
                text = re.sub(r"\*([^*]+)\*", r"\1", text)
                text = re.sub(r"__([^_]+)__", r"\1", text)
                text = re.sub(r"_([^_]+)_", r"\1", text)
                logger.info(f"[OK] Cleaned markdown content: {len(text)} characters")
            else:
                logger.info(f"[OK] Plain text content: {len(text)} characters")

            return text

        else:
            try:
                logger.info(f"Attempting to decode unknown content type: {content_type}")
                text = response.text

                # Try to detect if it's HTML and parse it
                if text.strip().startswith("<!DOCTYPE html") or text.strip().startswith("<html"):
                    logger.info("Detected HTML in unknown content type, attempting to parse")
                    try:
                        from bs4 import BeautifulSoup

                        soup = BeautifulSoup(text, "html.parser")
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        # Get text
                        parsed_text = soup.get_text(separator=" ", strip=True)
                        logger.info(f"[OK] Extracted text from HTML: {len(parsed_text)} characters")
                        return parsed_text
                    except Exception as e:
                        logger.warning(f"Failed to parse as HTML: {e}")

                return text
            except UnicodeDecodeError:
                logger.warning(f"Could not decode content as text: {content_type}")
                return f"[Binary content from {url} - cannot be processed as text]"

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching URL {url}")
        raise Exception("The URL took too long to respond. Please check if the URL is accessible and try again.")

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error fetching URL {url}: {str(e)}")
        if "Name or service not known" in str(e) or "nodename nor servname provided" in str(e):
            raise Exception("The URL could not be found. Please check that the URL is correct and accessible.")
        elif "Connection refused" in str(e):
            raise Exception("The server refused the connection. The URL may be temporarily unavailable.")
        else:
            raise Exception("Could not connect to the URL. Please check your internet connection and try again.")

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else None
        logger.error(f"HTTP error fetching URL {url}: {status_code} - {str(e)}")

        if status_code == 404:
            raise Exception(
                "The document was not found at this URL (404 error). Please check that the URL is correct."
            )
        elif status_code == 403:
            # Check if this is a Cloudflare protection issue
            response_text = ""
            if e.response:
                try:
                    response_text = e.response.text[:500].lower()  # Get first 500 chars
                except Exception:
                    response_text = ""

            # Detect anti-bot protection indicators
            protection_indicators = [
                "cloudflare",
                "just a moment",
                "checking your browser",
                "cf-mitigated",
                "cf-ray",
                "ddos protection",
                "security check",
                "incapsula",
                "sucuri",
                "akamai",
                "bot protection",
                "access denied",
                "blocked by",
                "please wait",
                "verifying you are human",
            ]

            is_protected = any(indicator in response_text for indicator in protection_indicators)

            if is_protected:
                # Determine if this is likely a PDF or HTML page
                is_pdf = url.lower().endswith(".pdf") or "pdf" in url.lower()
                "PDF file" if is_pdf else "web page"
                action = (
                    "download the PDF file manually from the URL and upload it directly to the tool"
                    if is_pdf
                    else "copy the text content from the web page and paste it into the tool"
                )

                raise Exception(
                    f"This website is protected by anti-bot protection and blocks automated access. "
                    f"Please {action} instead. "
                    f"This will allow the citation extraction to work properly."
                )
            else:
                raise Exception(
                    "Access to this document is forbidden (403 error). The document may require special permissions."
                )
        elif status_code == 500:
            raise Exception("The server encountered an error (500 error). Please try again later.")
        elif status_code and 400 <= status_code < 500:
            raise Exception(
                f"There was a problem with the request ({status_code} error). Please check the URL and try again."
            )
        elif status_code and status_code >= 500:
            raise Exception(f"The server is experiencing problems ({status_code} error). Please try again later.")
        else:
            # If we can't determine the status code, check the error message for anti-bot protection indicators
            error_message = str(e).lower()
            protection_indicators = [
                "cloudflare",
                "just a moment",
                "checking your browser",
                "cf-mitigated",
                "cf-ray",
                "ddos protection",
                "security check",
                "incapsula",
                "sucuri",
                "akamai",
                "bot protection",
                "access denied",
                "blocked by",
                "please wait",
                "verifying you are human",
                "403 client error: forbidden",
            ]

            is_protected = any(indicator in error_message for indicator in protection_indicators)

            if is_protected:
                # Determine if this is likely a PDF or HTML page
                is_pdf = url.lower().endswith(".pdf") or "pdf" in url.lower()
                "PDF file" if is_pdf else "web page"
                action = (
                    "download the PDF file manually from the URL and upload it directly to the tool"
                    if is_pdf
                    else "copy the text content from the web page and paste it into the tool"
                )

                raise Exception(
                    f"This website is protected by anti-bot protection and blocks automated access. "
                    f"Please {action} instead. "
                    f"This will allow the citation extraction to work properly."
                )
            else:
                raise Exception(f"The URL returned an error ({status_code}). Please check the URL and try again.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {str(e)}\n{traceback.format_exc()}")
        raise Exception(f"Failed to fetch the URL: {str(e)}. Please check that the URL is accessible and try again.")

    except Exception as e:
        logger.error(f"Unexpected error fetching URL {url}: {str(e)}\n{traceback.format_exc()}")
        if "PDF extraction" in str(e):
            raise Exception(
                "The PDF document could not be processed. It may be corrupted, password-protected, or in an unsupported format."
            )
        else:
            raise Exception(f"An unexpected error occurred while processing the URL: {str(e)}")
