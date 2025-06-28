import requests
import PyPDF2
import io
import re
from typing import Set, List, Dict, Optional
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
                            f"Basic pdfminer extracted {len(page_text)} characters from page {i+1}"
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
        text = re.sub(
            r"(\d+)\s*[Ff]\.?\s*(?:2[Dd]|3[Dd]|4[Tt][Hh])?\s*(\d+)", r"\1 F. \2", text
        )  # Fix F. spacing

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
        text = re.sub(r"([A-Z])\.\s+([A-Z])", r"\1.\2", text)

        return text

    def preprocess_text(self, text: str) -> str:
        """Preprocess text to improve citation detection."""
        # First clean the text
        text = self.clean_extracted_text(text)

        # Additional preprocessing specific to citation detection
        # Fix common OCR errors in reporter names
        text = re.sub(r"([Uu]\.?\s*[Ss]\.?)", "U.S.", text)
        text = re.sub(r"([Ss]\.?\s*[Cc][Tt]\.?)", "S.Ct.", text)
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

    def validate_citation_with_courtlistener(self, citation: str) -> Dict:
        """Validate a citation with CourtListener API."""
        try:
            # Format citation for API
            formatted_citation = citation.replace(" ", "")
            api_url = (
                f"https://cite.case.law/api/rest/v4/citations/{formatted_citation}"
            )

            headers = {
                "Authorization": f"Token {COURT_LISTENER_API_KEY}",
                "Accept": "application/json",
            }

            response = requests.get(api_url, headers=headers)
            response.raise_for_status()

            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(
                f"Error validating citation {citation} with CourtListener: {str(e)}"
            )
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
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error validating citations: {str(e)}")
            return {"error": str(e)}

    def extract_citations_from_url(self, url: str) -> dict:
        logger.info(f"Processing PDF from {url}")
        print(f"Processing PDF from {url}")
        pdf_content = self.download_pdf(url)
        if not pdf_content:
            return {"error": ["Failed to download PDF"]}
        text = self.extract_text_from_pdf(pdf_content)
        if not text:
            return {"error": ["Failed to extract text from PDF"]}

        # Try eyecite first
        eyecite_citations = self.find_citations_with_eyecite(text)
        if eyecite_citations:
            citation_texts = [c["citation_text"] for c in eyecite_citations]
            print(f"[DEBUG] Citations extracted by eyecite: {citation_texts}")
        else:
            # Fallback to regex
            citation_texts = list(self.find_citations_with_regex(text))
            print(f"[DEBUG] Citations extracted by regex: {citation_texts}")

        # Join all citations into a single string for the API
        citations_str = " ".join(citation_texts)
        print(f"[DEBUG] Citations string sent to API: {citations_str}")
        validation_results = self.validate_citations_with_courtlistener_lookup(
            citations_str
        )
        print(f"[DEBUG] Raw API response: {validation_results}")
        # Use the response directly if it's a list
        if isinstance(validation_results, list):
            citations_out = validation_results
        elif isinstance(validation_results, dict) and "citations" in validation_results:
            citations_out = validation_results["citations"]
        else:
            citations_out = []
        return {
            "citations": citations_out,
            "total_pages": len(PyPDF2.PdfReader(io.BytesIO(pdf_content)).pages),
            "text_preview": text[:1000],
            "validation_raw": validation_results,
        }


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
