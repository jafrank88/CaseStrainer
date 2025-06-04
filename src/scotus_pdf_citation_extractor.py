import os
import re
import io
import requests
import PyPDF2
from typing import Set, List, Dict, Optional

# Configure logging
import logging

logger = logging.getLogger(__name__)
import logging
import sys
import json
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

# Set up logging to output to console at INFO level
logging.basicConfig(
    stream=sys.stdout, level=logging.INFO, format="%(levelname)s:%(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration
try:
    with open("config.json", "r") as f:
        config = json.load(f)
    COURT_LISTENER_API_KEY = config.get("COURTLISTENER_API_KEY")
    COURT_LISTENER_API_URL = config.get(
        "COURTLISTENER_API_URL", "https://cite.case.law/api/rest/v4/citations/"
    )
    LOG_LEVEL = config.get("LOG_LEVEL", "INFO")
    LOG_FILE = config.get("LOG_FILE", "logs/casestrainer.log")

    # Set up file logging if LOG_FILE is specified
    if LOG_FILE:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)

    # Set log level from config
    logger.setLevel(getattr(logging, LOG_LEVEL))

    if not COURT_LISTENER_API_KEY:
        logger.warning("CourtListener API key not found in config.json")
except Exception as e:
    logger.error(f"Error loading config.json: {str(e)}")
    COURT_LISTENER_API_KEY = None
    COURT_LISTENER_API_URL = "https://cite.case.law/api/rest/v4/citations/"

# Try to import eyecite
try:
    from eyecite import get_citations
    from eyecite.tokenizers import HyperscanTokenizer, AhocorasickTokenizer

    EYECITE_AVAILABLE = True
    logger.info("Successfully imported eyecite for citation extraction")
except ImportError:
    EYECITE_AVAILABLE = False
    logger.warning(
        "Eyecite not installed. Will use regex patterns for citation extraction."
    )


class SCOTUSPDFCitationExtractor:
    """A class to extract citations from Supreme Court PDF opinions."""

    def __init__(self):
        print(f"[DEBUG] Loaded SCOTUSPDFCitationExtractor from {__file__}")
        # Fallback regex patterns if eyecite is not available
        self.citation_patterns = [
            r"\b(\d+)\s+U\.?\s*S\.?\s+(\d+)\b",  # U.S. Reports
            r"\b(\d+)\s+S\.?\s*Ct\.?\s+(\d+)\b",  # Supreme Court Reporter
            r"\b(\d+)\s+L\.?\s*Ed\.?\s+(\d+)\b",  # Lawyers Edition
            r"\b(\d+)\s+U\.?\s*S\.?\s+C\.?\s+(\d+)\b",  # U.S. Court of Appeals
            r"\b(\d+)\s+F\.?\s*(?:2d|3d|4th)?\s+(\d+)\b",  # Federal Reporter
            r"\b(\d+)\s+F\.?\s*Supp\.?\s*(?:2d|3d)?\s+(\d+)\b",  # Federal Supplement
            # Add more flexible patterns
            r"\b(\d+)\s*U\.?\s*S\.?\s*C\.?\s*(\d+)\b",  # More flexible U.S.C.
            r"\b(\d+)\s*F\.?\s*(?:2d|3d|4th)?\s*App\.?\s*(\d+)\b",  # Federal Appendix
            r"\b(\d+)\s*F\.?\s*R\.?\s*D\.?\s*(\d+)\b",  # Federal Rules Decisions
            r"\b(\d+)\s*F\.?\s*Supp\.?\s*(?:2d|3d)?\s*(\d+)\b",  # More flexible F.Supp.
            r"\b(\d+)\s*S\.?\s*E\.?\s*(?:2d)?\s*(\d+)\b",  # South Eastern Reporter
            r"\b(\d+)\s*N\.?\s*E\.?\s*(?:2d|3d)?\s*(\d+)\b",  # North Eastern Reporter
            r"\b(\d+)\s*N\.?\s*W\.?\s*(?:2d)?\s*(\d+)\b",  # North Western Reporter
            r"\b(\d+)\s*S\.?\s*W\.?\s*(?:2d|3d)?\s*(\d+)\b",  # South Western Reporter
            r"\b(\d+)\s*P\.?\s*(?:2d|3d)?\s*(\d+)\b",  # Pacific Reporter
            r"\b(\d+)\s*A\.?\s*(?:2d|3d)?\s*(\d+)\b",  # Atlantic Reporter
        ]

    def download_pdf(self, url: str) -> Optional[bytes]:
        """Download a PDF from a URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading PDF: {str(e)}")
            print(f"Error downloading PDF: {str(e)}")
            return None

    def extract_text_from_pdf(self, pdf_content: bytes) -> Optional[str]:
        """Extract text from PDF content using multiple methods for better accuracy."""
        try:
            pdf_file = io.BytesIO(pdf_content)

            # First try with enhanced pdfminer settings
            try:
                # Configure pdfminer for better text extraction
                laparams = LAParams(
                    line_margin=0.5,  # Reduce line margin to better handle line breaks
                    word_margin=0.1,  # Reduce word margin to better handle word breaks
                    char_margin=2.0,  # Increase char margin to better handle character spacing
                    boxes_flow=0.5,  # Adjust flow of text boxes
                    detect_vertical=True,  # Enable vertical text detection
                )

                resource_manager = PDFResourceManager()
                text_output = io.StringIO()
                converter = TextConverter(
                    resource_manager, text_output, laparams=laparams
                )
                interpreter = PDFPageInterpreter(resource_manager, converter)

                # Process each page
                for page in PDFPage.get_pages(pdf_file):
                    interpreter.process_page(page)

                text = text_output.getvalue()
                converter.close()
                text_output.close()

                if text and len(text.strip()) > 0:
                    logger.info(
                        "Successfully extracted text using enhanced pdfminer settings"
                    )
                    return self.clean_extracted_text(text)
            except Exception as e:
                logger.error(f"Enhanced pdfminer extraction failed: {str(e)}")

            # Reset file pointer
            pdf_file.seek(0)

            # Try PyPDF2 as backup
            reader = PyPDF2.PdfReader(pdf_file)
            all_text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text is None or not page_text.strip():
                    # Reset file pointer before using basic pdfminer
                    pdf_file.seek(0)
                    try:
                        page_text = pdfminer_extract_text(pdf_file, page_numbers=[i])
                        logger.info(
                            f"Basic pdfminer extracted {len(page_text)} characters "
                            f"from page {i+1}"
                        )
                    except Exception as e:
                        logger.error(f"Basic pdfminer failed on page {i+1}: {e}")
                        page_text = ""
                else:
                    logger.info(
                        f"PyPDF2 extracted {len(page_text)} characters from page {i+1}"
                    )

                if page_text:
                    all_text += page_text + "\n"

            return self.clean_extracted_text(all_text)

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            print(f"Error extracting text from PDF: {str(e)}")
            return None

    def clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text to improve citation detection."""
        # Remove non-printable characters but preserve citation patterns
        text = "".join(
            char for char in text if char.isprintable() or char in ".,;:()[]{}"
        )

        # Fix common OCR errors in citations
        text = re.sub(
            r"(\d+)\s*[Uu]\.?\s*[Ss]\.?\s*(\d+)", r"\1 U.S. \2", text
        )  # Fix U.S. spacing
        text = re.sub(
            r"(\d+)\s*[Ss]\.?\s*[Cc][Tt]\.?\s*(\d+)", r"\1 S.Ct. \2", text
        )  # Fix S.Ct. spacing
        text = re.sub(
            r"(\d+)\s*[Ll]\.?\s*[Ee][Dd]\.?\s*(\d+)", r"\1 L.Ed. \2", text
        )  # Fix L.Ed. spacing
        # Fix F. spacing
        text = re.sub(
            r"(\d+)\s*[Ff]\.?\s*(2d|3d|4th)?\s*(\d+)",
            lambda m: f"{m.group(1)} F.{' ' + m.group(2) if m.group(2) else ''} {m.group(3)}",
            text,
        )

        # Fix line breaks within citations
        text = re.sub(r"(\d+)\s*U\.?\s*S\.?\s*\n\s*(\d+)", r"\1 U.S. \2", text)
        text = re.sub(r"(\d+)\s*S\.?\s*Ct\.?\s*\n\s*(\d+)", r"\1 S.Ct. \2", text)
        text = re.sub(r"(\d+)\s*L\.?\s*Ed\.?\s*\n\s*(\d+)", r"\1 L.Ed. \2", text)
        text = re.sub(r"(\d+)\s*F\.?\s*(?:2d|3d|4th)?\s*\n\s*(\d+)", r"\1 F. \2", text)

        # Fix page breaks within citations
        text = re.sub(
            r"(\d+)\s*U\.?\s*S\.?\s*-\s*(\d+)", r"\1 U.S. \2", text
        )  # Fix page break markers
        text = re.sub(r"(\d+)\s*S\.?\s*Ct\.?\s*-\s*(\d+)", r"\1 S.Ct. \2", text)
        text = re.sub(r"(\d+)\s*L\.?\s*Ed\.?\s*-\s*(\d+)", r"\1 L.Ed. \2", text)
        text = re.sub(r"(\d+)\s*F\.?\s*(?:2d|3d|4th)?\s*-\s*(\d+)", r"\1 F. \2", text)

        # Normalize whitespace while preserving citation patterns
        text = re.sub(r"\s+", " ", text)

        # Fix spacing in abbreviations
        text = re.sub(r"([Ll]\.?\s*[Ee][Dd]\.?)", "L.Ed.", text)
        text = re.sub(r"([Ff]\.?\s*(?:2[Dd]|3[Dd]|4[Tt][Hh])?)", "F.", text)

        # Fix spacing around citations
        text = re.sub(r"(\d+)\s*U\.?\s*S\.?\s*(\d+)", r"\1 U.S. \2", text)
        text = re.sub(r"(\d+)\s*S\.?\s*Ct\.?\s*(\d+)", r"\1 S.Ct. \2", text)
        text = re.sub(r"(\d+)\s*L\.?\s*Ed\.?\s*(\d+)", r"\1 L.Ed. \2", text)
        text = re.sub(r"(\d+)\s*F\.?\s*(?:2d|3d|4th)?\s*(\d+)", r"\1 F. \2", text)

        return text

    def format_citation(self, match: re.Match) -> str:
        """Format a citation match with proper spacing and punctuation."""
        groups = match.groups()
        if len(groups) == 2:
            volume, page = groups
            if "U.S." in match.group():
                return f"{volume} U.S. {page}"
            elif "S.Ct." in match.group():
                return f"{volume} S.Ct. {page}"
            elif "L.Ed." in match.group():
                return f"{volume} L.Ed. {page}"
            elif "F." in match.group():
                if "Supp." in match.group():
                    return f"{volume} F.Supp. {page}"
                else:
                    return f"{volume} F. {page}"
        return match.group()

    def find_citations_with_eyecite(self, text: str) -> List[Dict]:
        """Find citations using eyecite."""
        if not EYECITE_AVAILABLE:
            return []

        try:
            # Preprocess text
            text = self.preprocess_text(text)

            # Debug: Print length and type of text
            logger.info(f"Text length: {len(text)}, type: {type(text)}")

            # Try a small known string if text is valid
            if text and len(text) > 0:
                test_text = "See United States v. Detroit Timber & Lumber Co., 200 U.S. 321, 337."
                logger.info(f"Testing eyecite with known string: {test_text}")
                test_citations = get_citations(
                    test_text, tokenizer=AhocorasickTokenizer()
                )
                logger.info(f"Test citations: {test_citations}")

            # Try to use the faster HyperscanTokenizer first
            try:
                tokenizer = HyperscanTokenizer()
            except Exception:
                logger.info("Falling back to AhocorasickTokenizer...")
                tokenizer = AhocorasickTokenizer()

            # Process text in larger chunks with overlap to avoid missing citations at boundaries
            chunk_size = 50000  # Increased chunk size
            overlap = 1000  # Overlap between chunks to catch citations at boundaries
            all_citations = []

            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i : i + chunk_size]
                logger.info(
                    f"Processing chunk {i//(chunk_size-overlap) + 1} of length {len(chunk)}"
                )
                try:
                    citations = get_citations(chunk, tokenizer=tokenizer)
                    all_citations.extend(citations)
                except Exception as e:
                    logger.error(
                        f"Error processing chunk {i//(chunk_size-overlap) + 1}: {e}"
                    )

            # Remove duplicate citations while preserving order
            seen = set()
            unique_citations = []
            for citation in all_citations:
                citation_text = citation.matched_text()
                if citation_text not in seen:
                    seen.add(citation_text)
                    unique_citations.append(citation)

            # Format citations with metadata
            formatted_citations = []
            for citation in unique_citations:
                citation_info = {
                    "citation_text": citation.matched_text(),
                    "corrected_citation": (
                        citation.corrected_citation()
                        if hasattr(citation, "corrected_citation")
                        else None
                    ),
                    "citation_type": str(citation.type()),
                    "metadata": {
                        "reporter": getattr(citation, "reporter", None),
                        "volume": getattr(citation, "volume", None),
                        "page": getattr(citation, "page", None),
                        "year": getattr(citation, "year", None),
                        "court": getattr(citation, "court", None),
                    },
                }
                formatted_citations.append(citation_info)

            return formatted_citations
        except Exception as e:
            logger.error(f"Error using eyecite: {str(e)}")
            print(f"Error using eyecite: {str(e)}")
            import traceback

            traceback.print_exc()
            return []

    def find_citations_with_regex(self, text: str) -> Set[str]:
        """Find citations using regex patterns as fallback."""
        found_citations = set()
        for pattern in self.citation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                citation = self.format_citation(match)
                found_citations.add(citation)
        return found_citations

    def validate_citation_with_courtlistener(
        self, citation_text: str, case_name: str = None
    ) -> Dict:
        """Validate a citation with CourtListener API.

        Args:
            citation_text: The citation text to validate (e.g., "123 F.3d 456")
            case_name: Optional case name to help with validation

        Returns:
            dict: Validation results including verification status and metadata
        """
        if not self.courtlistener_api_key:
            logger.warning("No CourtListener API key provided, skipping validation")
            return {
                "verified": False,
                "error": "No CourtListener API key provided",
                "validation_method": "none",
                "confidence": "none",
            }

        try:
            # First try to find the case by citation
            response = requests.get(
                f"{self.COURTLISTENER_API_BASE}/api/rest/v4/opinion-cites/find-citations/",
                params={"citation__cite": citation_text},
                headers={"Authorization": f"Token {self.courtlistener_api_key}"},
                timeout=10,
            )

            if response.status_code == 200 and response.json().get("count", 0) > 0:
                result = response.json()["results"][0]
                return {
                    "verified": True,
                    "case_name": result.get("caseName", ""),
                    "citation": result.get("citation", ""),
                    "parallel_citations": result.get("parallel_citations", []),
                    "reporter_type": (
                        result.get("reporter", "").split()[-1]
                        if result.get("reporter")
                        else ""
                    ),
                    "court": result.get("court", ""),
                    "date_filed": result.get("date_filed", ""),
                    "docket_number": result.get("docket_number", ""),
                    "url": result.get("absolute_url", ""),
                    "validation_method": "CourtListener API",
                    "confidence": "high",
                    "source": "courtlistener",
                }

            # If not found by citation, try searching by case name if provided
            if case_name and case_name.strip() and case_name != "§":
                search_response = requests.get(
                    f"{self.COURTLISTENER_API_BASE}/api/rest/v4/search/",
                    params={"q": f'"{case_name}"', "type": "opinion"},
                    headers={"Authorization": f"Token {self.courtlistener_api_key}"},
                    timeout=10,
                )

                if (
                    search_response.status_code == 200
                    and search_response.json().get("count", 0) > 0
                ):
                    result = search_response.json()["results"][0]
                    return {
                        "verified": True,
                        "case_name": result.get("caseName", ""),
                        "citation": result.get("citation", ""),
                        "parallel_citations": (
                            result.get("citation", "").split("; ")
                            if result.get("citation")
                            else []
                        ),
                        "reporter_type": (
                            result.get("citation", "").split()[-1]
                            if result.get("citation")
                            else ""
                        ),
                        "court": result.get("court", ""),
                        "date_filed": result.get("date_filed", ""),
                        "docket_number": result.get("docket_number", ""),
                        "url": result.get("absolute_url", ""),
                        "validation_method": "CourtListener API (by case name)",
                        "confidence": "medium",
                        "source": "courtlistener",
                    }

            # If we get here, the citation wasn't found
            return {
                "verified": False,
                "error": "Citation not found in CourtListener",
                "validation_method": "CourtListener API",
                "confidence": "high",
                "citation": citation_text,
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating citation with CourtListener: {str(e)}")
            return {
                "verified": False,
                "error": str(e),
                "validation_method": "error",
                "confidence": "none",
                "citation": citation_text,
            }
            return {"error": str(e)}
        except Exception as e:
            logging.error(f"Unexpected error validating citation {citation}: {str(e)}")
            return {"error": str(e)}

    def validate_citations_with_courtlistener_lookup(self, text: str) -> dict:
        """Validate citations using the CourtListener citation-lookup API (batch, POST, form data)."""
        if not COURT_LISTENER_API_KEY:
            logger.error("CourtListener API key not configured")
            return {"error": "API key not configured"}

        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        headers = {"Authorization": f"Token {COURT_LISTENER_API_KEY}"}
        data = {"text": text}
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            logger.info(
                "Successfully validated citations with CourtListener citation-lookup API"
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error validating citations with CourtListener citation-lookup: {str(e)}"
            )

    def extract_citations_from_url(
        self, url: str, verify_citations: bool = True
    ) -> dict:
        """Extract and verify citations from a PDF at the given URL or local file path.

        Args:
            url: Either a URL to download a PDF from, or a local file path
            verify_citations: If True, verify citations using CourtListener API

        Returns:
            dict: Dictionary containing extracted citations, verification results, and metadata
        """
        from reusable_results import ReusableResults

        result = ReusableResults(
            operation="pdf_citation_extraction",
            source=url,
            metadata={"source_type": "file" if os.path.isfile(url) else "url"},
        )

        try:
            pdf_content = None

            # Check if the input is a local file path
            if os.path.isfile(url):
                logger.info(f"[extract_citations_from_url] Reading local file: {url}")
                try:
                    with open(url, "rb") as f:
                        pdf_content = f.read()
                except Exception as e:
                    error_msg = f"Error reading local file {url}: {str(e)}"
                    logger.error(error_msg)
                    result.add_error(error_msg)
                    return result.to_dict()
            else:
                # Treat as URL
                logger.info(f"[extract_citations_from_url] Downloading PDF from {url}")
                pdf_content = self.download_pdf(url)

            if not pdf_content:
                error_msg = f"Failed to get PDF content from {url}"
                result.add_error(error_msg)
                return result.to_dict()

            # Extract text from PDF
            logger.info("[extract_citations_from_url] Extracting text from PDF")
            text = self.extract_text_from_pdf(pdf_content)
            if not text or not text.strip():
                error_msg = "Failed to extract text from PDF"
                result.add_error(error_msg)
                return result.to_dict()

            # Extract citations
            logger.info("[extract_citations_from_url] Finding citations")
            if EYECITE_AVAILABLE:
                citations = self.find_citations_with_eyecite(text)
            else:
                citations = list(self.find_citations_with_regex(text))

            logger.info(
                f"[extract_citations_from_url] Found {len(citations)} citations"
            )

            # Add citations to result
            result.add_data("citations", citations)

            # Add metadata
            result.metadata.update(
                {
                    "total_pages": (
                        len(PyPDF2.PdfReader(io.BytesIO(pdf_content)).pages)
                        if pdf_content
                        else 0
                    ),
                    "text_preview": text[:1000] if text else "",
                }
            )

            # Verify citations if requested
            if verify_citations and citations:
                logger.info(
                    f"[extract_citations_from_url] Verifying {len(citations)} citations with CourtListener"
                )
                validation_results = []
                verified_citations = []

                for citation in citations:
                    try:
                        if isinstance(citation, dict):
                            citation_text = citation.get("citation_text", "")
                            case_name = citation.get("case_name", "")
                        else:
                            citation_text = str(citation)
                            case_name = ""

                        if (
                            not citation_text or citation_text == "§"
                        ):  # Skip invalid citations
                            continue

                        # Validate the citation
                        validation = self.validate_citation_with_courtlistener(
                            citation_text, case_name
                        )

                        # Update citation with validation status
                        if isinstance(citation, dict):
                            citation.update(
                                {
                                    "validation_status": (
                                        "verified"
                                        if validation.get("verified")
                                        else "not_found"
                                    ),
                                    "validation_details": validation,
                                }
                            )

                            # Only include verified citations in the main results
                            if validation.get("verified"):
                                verified_citations.append(citation)

                        validation_results.append(
                            {
                                "citation": citation_text,
                                "case_name": case_name,
                                "validation": validation,
                            }
                        )

                    except Exception as e:
                        logger.error(f"Error validating citation {citation}: {str(e)}")
                        validation_results.append(
                            {
                                "citation": str(citation),
                                "error": str(e),
                                "validation": {
                                    "verified": False,
                                    "error": str(e),
                                    "validation_method": "error",
                                    "confidence": "none",
                                },
                            }
                        )

                # Combine all citations with their validation status
                all_citations = []
                for citation_data in validation_results:
                    citation = citation_data.copy()
                    validation = citation.pop("validation", {})

                    # Create a unified citation object with all necessary fields
                    unified_citation = {
                        "citation_text": citation.get("citation", ""),
                        "case_name": citation.get("case_name", ""),
                        "verified": validation.get("verified", False),
                        "validation_method": validation.get(
                            "validation_method", "unknown"
                        ),
                        "confidence": validation.get("confidence", "none"),
                        "metadata": {
                            "court": validation.get("court", ""),
                            "year": (
                                validation.get("date_filed", "")[:4]
                                if validation.get("date_filed")
                                else ""
                            ),
                            "source": validation.get("source", "unknown"),
                        },
                        "contexts": (
                            [
                                {
                                    "text": citation.get("context", ""),
                                    "source": "extracted",
                                }
                            ]
                            if citation.get("context")
                            else []
                        ),
                        "validation_details": validation,
                    }

                    # Add any additional fields from the original citation
                    if isinstance(citation, dict):
                        for key, value in citation.items():
                            if key not in unified_citation and not key.startswith("_"):
                                unified_citation[key] = value

                    all_citations.append(unified_citation)

                # Update the results with all citations
                result.add_data("citations", all_citations)

                # Add statistics
                verified_count = sum(
                    1 for c in all_citations if c.get("verified", False)
                )
                result.metadata.update(
                    {
                        "verified_citations": verified_count,
                        "total_citations": len(all_citations),
                        "verification_rate": (
                            f"{(verified_count / len(all_citations) * 100):.1f}%"
                            if all_citations
                            else "0%"
                        ),
                        "verification_timestamp": datetime.now(
                            timezone.utc
                        ).isoformat(),
                    }
                )

            return result.to_dict()

        except Exception as e:
            error_msg = f"Unexpected error in extract_citations_from_url: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result.add_error(error_msg)
            return result.to_dict()


def main():
    """Main function to demonstrate usage."""
    print("Starting SCOTUSPDFCitationExtractor main()...")
    extractor = SCOTUSPDFCitationExtractor()
    url = "https://www.courts.wa.gov/opinions/pdf/1029403.pdf"
    try:
        results = extractor.extract_citations_from_url(url)
    except Exception as e:
        print(f"Exception in main: {e}")
        import traceback

        traceback.print_exc()
        return
    if "error" in results:
        print(f"Error: {results['error'][0]}")
        return
    print(f"\nPDF has {results['total_pages']} pages")
    print("\nText preview:")
    print(results["text_preview"])
    print("\nCitations from CourtListener citation-lookup API:")
    for citation in results["citations"]:
        print(f"- {citation}")
    print("\nRaw validation response:")
    print(results["validation_raw"])


if __name__ == "__main__":
    main()
