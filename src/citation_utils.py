import os
import traceback
import time
import logging
import sys
from typing import List, Dict, Any, Optional
from pdf_handler import PDFHandler, PDFExtractionConfig, PDFExtractionMethod

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import from config with absolute path
from src.config import ALLOWED_EXTENSIONS

# Robust import for extract_text_from_file
try:
    from file_utils import extract_text_from_file
except ImportError:

    def extract_text_from_file(file_path):
        raise NotImplementedError(
            "extract_text_from_file is not available in this environment"
        )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Setup logger (modules importing this should configure logging)
logger = logging.getLogger(__name__)

from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def log_citation_verification(citation, result):
    """
    Log the result of a citation verification attempt.
    
    Args:
        citation (str): The citation text that was verified.
        result (dict): The result of the verification process.
    """
    status = "SUCCESS" if result.get("verified", False) else "FAILED"
    logger.info(f"Citation Verification [{status}]: {citation}")
    if result.get("error", False):
        logger.error(f"Verification error: {result.get('error', 'Unknown error')}")
    elif result.get("verified", False):
        try:
            logger.info(f"Verified citation details: {result.get('source', 'No source info')}")
        except UnicodeEncodeError:
            safe_source = str(result.get('source', 'No source info')).encode('cp1252', errors='replace').decode('cp1252')
            logger.info(f"Verified citation details (safe): {safe_source}")

from src.config import COURTLISTENER_API_KEY
import re
from src.citation_format_utils import apply_washington_spacing_rules

# Updated: Use the unified verify_citation from enhanced_multi_source_verifier for all verification
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def normalize_citation_text(citation_text):
    """
    Normalize citation text to a standard format before processing.

    Handles common issues like:
    - Extra spaces in reporter abbreviations (e.g., 'F. 3d' -> 'F.3d')
    - Double periods (e.g., 'U.S..' -> 'U.S.')
    - Inconsistent spacing around v. (e.g., 'U.S. v.Caraway' -> 'U.S. v. Caraway')
    - Washington citation spacing rules (Wn.2d vs Wn. App.)

    Args:
        citation_text (str): The citation text to normalize

    Returns:
        str: The normalized citation text
    """
    if not citation_text or not isinstance(citation_text, str):
        return citation_text

    # Remove any leading/trailing whitespace
    normalized = citation_text.strip()

    # Fix double periods
    normalized = re.sub(r"\.\.+", ".", normalized)

    # Apply Washington citation spacing rules FIRST (before general reporter fixes)
    normalized = apply_washington_spacing_rules(normalized)

    # Fix spaces in reporter abbreviations (e.g., 'F. 3d' -> 'F.3d')
    # But exclude Washington citations that we just fixed
    normalized = re.sub(r"(\b[A-Za-z]+\.)\s+(\d+[a-z]*)(?!\s*Wn\.)", r"\1\2", normalized)

    # Fix spacing around 'v.'
    normalized = re.sub(r"\s+v\.\s*", " v. ", normalized, flags=re.IGNORECASE)

    # Fix common reporter abbreviations
    reporter_fixes = {
        r"\bFed\.\s*": "F.",
        r"\bFed\.\s*App\.\s*": "F. App'x",
        r"\bF\.\s*2d\b": "F.2d",
        r"\bF\.\s*3d\b": "F.3d",
        r"\bF\.\s*4th\b": "F.4th",
        r"\bU\.\s*S\.\s*": "U.S. ",
        r"\bS\.\s*Ct\.\s*": "S. Ct. ",
        r"\bL\.\s*Ed\.\s*2d\b": "L. Ed. 2d",
    }

    for pattern, replacement in reporter_fixes.items():
        normalized = re.sub(pattern, replacement, normalized)

    # Remove extra spaces
    normalized = " ".join(normalized.split())

    return normalized


def verify_citation(
    citation,
    context=None,
    logger=None,
    DEFAULT_API_KEY=None,
    thread_local=None,
    timeout=15,
    extracted_case_name=None
):
    """Verify a citation using the unified EnhancedMultiSourceVerifier workflow (verify_citation_unified_workflow)."""
    verifier = EnhancedMultiSourceVerifier()
    return verifier.verify_citation_unified_workflow(
        citation,
        extracted_case_name=extracted_case_name
    )


def extract_citations_from_file(filepath, logger=logger):
    """Extract citations from a file and return full metadata."""
    try:
        logger.info(f"[DEBUG] Starting extract_citations_from_file for: {filepath}")
        file_size = os.path.getsize(filepath)
        file_extension = os.path.splitext(filepath)[1].lower()
        logger.info(
            f"[DEBUG] File details - Size: {file_size} bytes, Extension: {file_extension}"
        )
        start_time = time.time()
        text = ""
        
        if filepath.endswith(".pdf"):
            logger.info("Detected PDF file, using PDFHandler for extraction")
            # Always use PDFMiner as the only extraction method
            handler = PDFHandler(PDFExtractionConfig(
                preferred_method=PDFExtractionMethod.PDFMINER,
                use_fallback=False,  # Only use PDFMiner
                timeout=30,  # 30 second timeout
                clean_text=True
            ))
            text = handler.extract_text(filepath)
            if text.startswith("Error:"):
                logger.error(f"PDF extraction failed: {text}")
                raise Exception(text)
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            
        elif filepath.endswith((".doc", ".docx")):
            logger.info("Detected Word document, using python-docx for extraction")
            import docx

            try:
                doc = docx.Document(filepath)
                logger.info(f"Word document has {len(doc.paragraphs)} paragraphs")
                paragraphs = [paragraph.text for paragraph in doc.paragraphs]
                text = "\n".join(paragraphs)
                logger.info(
                    f"Extracted {len(paragraphs)} paragraphs with total {len(text)} characters"
                )
            except Exception as docx_error:
                logger.error(f"Error reading Word document: {str(docx_error)}")
                raise
        else:
            logger.info(f"Using standard text file reading for {file_extension} file")
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    text = file.read()
                    logger.info(f"Read {len(text)} characters from text file")
            except UnicodeDecodeError:
                logger.warning("UTF-8 decoding failed, trying with latin-1 encoding")
                with open(filepath, "r", encoding="latin-1") as file:
                    text = file.read()
                    logger.info(
                        f"Read {len(text)} characters from text file using latin-1 encoding"
                    )
                    
        extraction_time = time.time() - start_time
        logger.info(
            f"File content extraction completed in {extraction_time:.2f} seconds"
        )
        logger.info(f"Extracted text sample (first 200 chars): {text[:200]}...")
        logger.info("Calling extract_citations_from_text with the extracted content")
        return extract_citations_from_text(text, logger=logger)
    except Exception as e:
        logger.error(f"Error extracting citations from file: {str(e)}")
        logger.error(traceback.format_exc())
        return []


def get_citation_context(text, citation_text, context_size=100):
    """
    Extract context around a citation in the text.

    Args:
        text: The full text containing the citation
        citation_text: The citation text to find in the text
        context_size: Number of characters to include before and after the citation

    Returns:
        str: The context around the citation, or None if not found
    """
    if not text or not citation_text:
        return None

    # Find the citation in the text (case insensitive)
    start = text.lower().find(citation_text.lower())
    if start == -1:
        return None

    # Calculate start and end positions for the context
    start = max(0, start - context_size)
    end = min(len(text), start + len(citation_text) + context_size)

    # Add ellipsis if not at the start/end of the text
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""

    return f"{prefix}{text[start:end]}{suffix}"


def validate_potential_citation(citation_text):
    """
    Secondary validation for citations that don't match standard patterns.
    This is a more lenient validation that looks for common elements in legal citations.
    
    Args:
        citation_text: The citation text to validate
        
    Returns:
        tuple: (is_valid, reason)
            - is_valid: Boolean indicating if the citation might be valid
            - reason: String explaining why it might be valid
    """
    # Filter out short citations early
    if isinstance(citation_text, str):
        # Check for eyecite object representations that should be filtered out
        if any(pattern in citation_text for pattern in [
            "IdCitation('Id.", 
            "IdCitation('id.", 
            "IdCitation('Ibid.", 
            "IdCitation('ibid.",
            "ShortCaseCitation(",
            "UnknownCitation(",
            "SupraCitation(",
            "InfraCitation("
        ]):
            return False, "Short form citation (Id., Ibid., etc.)"
        
        # Check for short citations with "at" before page numbers
        if re.search(r"\bat\s+\d+", citation_text, re.IGNORECASE):
            return False, "Short citation with 'at' reference"
        
        # Check for citations that start with short form indicators
        if citation_text.lower().startswith(('id.', 'ibid.', 'supra.', 'infra.')):
            return False, "Short form citation indicator"
    
    # Remove common punctuation and normalize spaces
    cleaned_text = re.sub(r'[.,;]', ' ', citation_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    # Split into words
    words = cleaned_text.split()
    
    # Must have at least 3 parts (e.g., "123 F 456")
    if len(words) < 3:
        return False, "Too few components"
        
    # Expanded list of reporter abbreviations
    reporter_abbrevs = {
        # Federal Reporters
        'U.S.', 'US', 'F.', 'F', 'F.2d', 'F2d', 'F.3d', 'F3d', 'F.4th', 'F4th',
        'S.Ct.', 'SCT', 'S.Ct', 'SCt', 'Sup.Ct.', 'Sup.Ct', 'SupCT',
        'L.Ed.', 'LED', 'L.Ed', 'L.Ed.2d', 'LED2d', 'L.Ed.3d', 'LED3d',
        'F.Supp.', 'F.Supp', 'F.Supp.2d', 'F.Supp.2d', 'F.Supp.3d', 'F.Supp.3d',
        'F.R.D.', 'FRD', 'F.R.D', 'Fed.R.', 'Fed.R', 'Fed.Rules',
        
        # State Reporters
        'Wash.', 'Wash', 'Wash.2d', 'Wash2d', 'Wash.App.', 'Wash.App', 'WashApp',
        'P.', 'P', 'P.2d', 'P2d', 'P.3d', 'P3d', 'Pac.', 'Pac',
        'N.W.', 'NW', 'N.W', 'N.W.2d', 'NW2d',
        'N.E.', 'NE', 'N.E', 'N.E.2d', 'NE2d', 'N.E.3d', 'NE3d',
        'S.E.', 'SE', 'S.E', 'S.E.2d', 'SE2d',
        'S.W.', 'SW', 'S.W', 'S.W.2d', 'SW2d', 'S.W.3d', 'SW3d',
        'A.', 'A', 'A.2d', 'A2d', 'A.3d', 'A3d', 'Atl.', 'Atl',
        'Cal.', 'Cal', 'Cal.2d', 'Cal2d', 'Cal.3d', 'Cal3d', 'Cal.4th', 'Cal4th',
        'N.Y.', 'NY', 'N.Y', 'N.Y.2d', 'NY2d', 'N.Y.3d', 'NY3d',
        'So.', 'So', 'So.2d', 'So2d', 'So.3d', 'So3d',
        'N.C.', 'NC', 'N.C', 'N.C.App.', 'NCApp',
        'Mich.', 'Mich', 'Mich.App.', 'MichApp',
        'Ill.', 'Ill', 'Ill.2d', 'Ill2d', 'Ill.App.', 'IllApp',
        'Tex.', 'Tex', 'Tex.App.', 'TexApp',
        'Mass.', 'Mass', 'Mass.App.', 'MassApp',
        'Ohio', 'Ohio App.', 'OhioApp',
        'Or.', 'Or', 'Or.App.', 'OrApp',
        'Wis.', 'Wis', 'Wis.2d', 'Wis2d',
        
        # Specialized Reporters
        'Bankr.', 'Bankr', 'B.R.', 'BR',
        'Misc.', 'Misc', 'Misc.2d', 'Misc2d',
        'App.', 'App', 'App.2d', 'App2d', 'App.3d', 'App3d',
        'Cir.', 'Cir', 'Cir.2d', 'Cir2d',
        '2d', '3d', '4th', '5th',
        
        # Additional variations
        'Rep.', 'Rep', 'Rptr.', 'Rptr', 'Rpt.', 'Rpt',
        'Supp.', 'Supp', 'Supp.2d', 'Supp2d',
        'Dist.', 'Dist', 'Dist.Ct.', 'DistCt',
        'Ct.', 'Ct', 'Cts.', 'Cts',
        'App.Div.', 'AppDiv', 'App.Div', 'App.Div.2d', 'AppDiv2d',
        'Super.', 'Super', 'Super.Ct.', 'SuperCt',
        'Comm.', 'Comm', 'Comm.Pl.', 'CommPl',
        'Mun.', 'Mun', 'Mun.Ct.', 'MunCt',
        'Mag.', 'Mag', 'Mag.Ct.', 'MagCt',
        'Juv.', 'Juv', 'Juv.Ct.', 'JuvCt',
        'Fam.', 'Fam', 'Fam.Ct.', 'FamCt',
        'Prob.', 'Prob', 'Prob.Ct.', 'ProbCt',
        'Tax', 'Tax.Ct.', 'TaxCt',
        'Workers', 'Workers.Comp.', 'WorkersComp',
        'L.R.A.', 'LRA', 'L.R.A', 'L.R.A.2d', 'LRA2d',
        'A.L.R.', 'ALR', 'A.L.R', 'A.L.R.2d', 'ALR2d', 'A.L.R.3d', 'ALR3d',
        'U.S.C.', 'USC', 'U.S.C', 'U.S.C.A.', 'USCA',
        'C.F.R.', 'CFR', 'C.F.R',
        'Fed.', 'Fed', 'Fed.Reg.', 'FedReg',
    }
    
    BLACKLISTED_REPORTERS = {'Filed', 'Page', 'Docket'}
    
    # Check if any word in the candidate is in the blacklist (e.g., 'No.', 'Page', 'Doc.'); if so, reject it.
    if any(word in BLACKLISTED_REPORTERS for word in words):
        return False, "Candidate contains a blacklisted non-reporter word (e.g., 'No.', 'Page', 'Doc.')"
    
    # Look for reporter abbreviations
    has_reporter = any(word in reporter_abbrevs for word in words)
    reporter = None
    for word in words:
        if word in reporter_abbrevs:
            reporter = word
            break
    if not has_reporter:
        # Try to find reporter abbreviations that might be split across words
        for i in range(len(words) - 1):
            combined = f"{words[i]}.{words[i+1]}"
            if combined in reporter_abbrevs:
                has_reporter = True
                reporter = combined
                break
            combined = f"{words[i]}{words[i+1]}"
            if combined in reporter_abbrevs:
                has_reporter = True
                reporter = combined
                break
    # Check for blacklisted reporter
    if reporter in BLACKLISTED_REPORTERS:
        return False, f"Invalid reporter: {reporter}"
    if not has_reporter:
        return False, "No reporter abbreviation found"
    
    # Look for numbers (volume and page numbers)
    numbers = [word for word in words if word.isdigit()]
    if len(numbers) < 2:
        return False, "Missing volume or page number"
    
    # Check for reasonable number ranges
    try:
        volume = int(numbers[0])
        page = int(numbers[1])
        # Expanded reasonable limits for legal citations
        if volume > 2000 or page > 20000:  # Increased limits to catch more valid citations
            return False, "Numbers outside reasonable range"
    except ValueError:
        return False, "Invalid number format"
    
    # Check for common citation structures
    citation_structures = [
        r'\d+\s+[A-Za-z\.]+\s+\d+',  # Basic structure: number reporter number
        r'\d+\s+[A-Za-z\.]+\s+\d+\s+[A-Za-z\.]+',  # With series: number reporter number series
        r'\d+\s+[A-Za-z\.]+\s+\d+\s*\(\d{4}\)',  # With year: number reporter number (year)
        r'\d+\s+[A-Za-z\.]+\s+\d+\s+[A-Za-z\.]+\s*\(\d{4}\)',  # With series and year
    ]
    
    # If the citation matches any common structure, it's more likely to be valid
    if any(re.search(pattern, citation_text, re.IGNORECASE) for pattern in citation_structures):
        return True, "Matches common citation structure"
    
    # If we got here, the citation has the basic elements of a legal citation
    return True, "Contains basic citation elements"


def clean_and_validate_citations(citations):
    """
    Clean and validate a list of citations before batch processing.
    Removes empty strings, malformed citations, and normalizes citation formats.
    Uses a two-step validation process for potentially malformed citations.
    
    Args:
        citations: List of citation strings or dictionaries to validate
        
    Returns:
        tuple: (cleaned_citations, validation_stats)
            - cleaned_citations: List of valid citations ready for processing
            - validation_stats: Dict with counts of removed citations by reason
    """
    if not citations:
        return [], {"empty_input": 0, "empty_strings": 0, "malformed": 0, "secondary_validated": 0, "total_removed": 0}
    
    validation_stats = {
        "empty_input": 0,
        "empty_strings": 0,
        "malformed": 0,
        "secondary_validated": 0,
        "total_removed": 0
    }
    
    cleaned_citations = []
    
    for citation in citations:
        # Handle different input formats
        if isinstance(citation, dict):
            citation_text = citation.get("text", citation.get("citation_text", ""))
        else:
            citation_text = str(citation)
            
        # Skip empty citations
        if not citation_text or not citation_text.strip():
            validation_stats["empty_strings"] += 1
            validation_stats["total_removed"] += 1
            continue
            
        # Filter out short citations early
        if isinstance(citation_text, str):
            # Check for eyecite object representations that should be filtered out
            if any(pattern in citation_text for pattern in [
                "IdCitation('Id.", 
                "IdCitation('id.", 
                "IdCitation('Ibid.", 
                "IdCitation('ibid.",
                "ShortCaseCitation(",
                "UnknownCitation(",
                "SupraCitation(",
                "InfraCitation("
            ]):
                validation_stats["malformed"] += 1
                validation_stats["total_removed"] += 1
                continue  # Skip short form citations
            
            # Check for short citations with "at" before page numbers
            if re.search(r"\bat\s+\d+", citation_text, re.IGNORECASE):
                validation_stats["malformed"] += 1
                validation_stats["total_removed"] += 1
                continue  # Skip short citations with 'at' reference
            
            # Check for citations that start with short form indicators
            if citation_text.lower().startswith(('id.', 'ibid.', 'supra.', 'infra.')):
                validation_stats["malformed"] += 1
                validation_stats["total_removed"] += 1
                continue  # Skip short form citation indicators
        
        # Basic citation format validation
        # Look for common citation patterns
        citation_patterns = [
            r"\d+\s+U\.?\s*S\.?\s+\d+",  # U.S. Reports
            r"\d+\s+F\.?(?:\s*\d*[a-z]*)?\s+\d+",  # Federal Reporter
            r"\d+\s+S\.?\s*Ct\.?\s+\d+",  # Supreme Court Reporter
            r"\d+\s+L\.?\s*Ed\.?\s*\d+",  # Lawyers Edition
            r"\d+\s+(?:Wash\.2d|Wash\.App\.|Wash\.|Wn\.2d|Wn\.App\.|Wn\.)\s+\d+",  # Washington Reports (including Wn. variants)
            r"\d+\s+P\.?\s*(?:2d|3d)?\s+\d+",  # Pacific Reporter
            r"\d+\s+N\.?\s*W\.?\s*(?:2d)?\s+\d+",  # North Western Reporter
            r"\d+\s+N\.?\s*E\.?\s*(?:2d|3d)?\s+\d+",  # North Eastern Reporter
            r"\d+\s+S\.?\s*E\.?\s*(?:2d)?\s+\d+",  # South Eastern Reporter
            r"\d+\s+S\.?\s*W\.?\s*(?:2d|3d)?\s+\d+",  # South Western Reporter
            r"\d+\s+A\.?\s*(?:2d|3d)?\s+\d+",  # Atlantic Reporter
            r"\d{4}\s+WL\s+\d+",  # Westlaw citations (e.g., 2020 WL 1234567)
        ]
        
        # Check if citation matches any known pattern
        is_valid = any(re.search(pattern, citation_text, re.IGNORECASE) for pattern in citation_patterns)
        
        if not is_valid:
            # Try secondary validation for potentially malformed citations
            is_potentially_valid, reason = validate_potential_citation(citation_text)
            if is_potentially_valid:
                logger.info(f"Citation '{citation_text}' passed secondary validation: {reason}")
                validation_stats["secondary_validated"] += 1
                cleaned_citations.append(citation)
                continue
            else:
                logger.warning(f"Citation '{citation_text}' failed validation: {reason}")
                validation_stats["malformed"] += 1
                validation_stats["total_removed"] += 1
                continue
            
        # If we got here, the citation is valid
        cleaned_citations.append(citation)
    
    return cleaned_citations, validation_stats


def batch_validate_citations_optimized(citations, api_key=None):
    """
    Optimized batch validation that stops after first successful verification.
    
    Args:
        citations: List of citation strings to validate
        api_key: Optional API key for CourtListener

    Returns:
        List of validation results
    """
    if not citations:
        return []

    # Clean and validate citations before processing
    cleaned_citations, validation_stats = clean_and_validate_citations(citations)
    
    if validation_stats["total_removed"] > 0:
        logger.warning(
            f"Removed {validation_stats['total_removed']} invalid citations before processing: "
            f"{validation_stats['empty_strings']} empty strings, "
            f"{validation_stats['malformed']} malformed citations. "
            f"Additionally, {validation_stats['secondary_validated']} citations passed secondary validation."
        )
    
    if not cleaned_citations:
        return []

    results = []
    
    # Process citations in parallel with early termination
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    # Thread-safe results list
    results_lock = threading.Lock()
    
    def validate_single_citation(citation):
        try:
            # Try primary verification method first (CourtListener API)
            result = verify_citation(citation, DEFAULT_API_KEY=api_key)
            
            # If successful, return immediately (no need to try other methods)
            if result.get("found", False):
                return {
                    "citation": citation,
                    "exists": True,
                    "method": result.get("method", "CourtListener API"),
                    "error": None,
                    "data": result,
                }
            
            # If not found, return the result without trying additional methods
            return {
                "citation": citation,
                "exists": False,
                "method": result.get("method", "CourtListener API"),
                "error": result.get("error_message", "Citation not found"),
                "data": result,
            }
            
        except Exception as e:
            logger.error(f"Error validating citation {citation}: {str(e)}")
            return {
                "citation": citation,
                "exists": False,
                "method": "error",
                "error": str(e),
                "data": None,
            }
    
    # Use ThreadPoolExecutor for parallel processing
    # Fix: Ensure max_workers is at least 1 to avoid ThreadPoolExecutor error
    max_workers = max(1, min(10, len(cleaned_citations)))  # At least 1, max 10 workers
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all validation tasks
        future_to_citation = {
            executor.submit(validate_single_citation, citation): citation
            for citation in cleaned_citations
        }
        
        # Process results as they complete
        for future in as_completed(future_to_citation):
            try:
                result = future.result()
                with results_lock:
                    results.append(result)
            except Exception as e:
                citation = future_to_citation[future]
                logger.error(f"Error processing citation {citation}: {str(e)}")
                with results_lock:
                    results.append({
                        "citation": citation,
                        "exists": False,
                        "method": "error",
                        "error": str(e),
                        "data": None,
                    })

    return results


def batch_validate_citations(citations, api_key=None):
    """
    Original batch validation function (maintained for backward compatibility).
    For better performance, use batch_validate_citations_optimized instead.
    
    Args:
        citations: List of citation strings to validate
        api_key: Optional API key for CourtListener

    Returns:
        List of validation results
    """
    if not citations:
        return []

    # Clean and validate citations before processing
    cleaned_citations, validation_stats = clean_and_validate_citations(citations)
    
    if validation_stats["total_removed"] > 0:
        logger.warning(
            f"Removed {validation_stats['total_removed']} invalid citations before processing: "
            f"{validation_stats['empty_strings']} empty strings, "
            f"{validation_stats['malformed']} malformed citations. "
            f"Additionally, {validation_stats['secondary_validated']} citations passed secondary validation."
        )
    
    if not cleaned_citations:
        return []

    results = []
    for citation in cleaned_citations:
        try:
            result = verify_citation(citation, DEFAULT_API_KEY=api_key)
            results.append(
                {
                    "citation": citation,
                    "exists": result.get("exists", False),
                    "method": result.get("method", "unknown"),
                    "error": None,
                    "data": result,
                }
            )
        except Exception as e:
            logger.error(f"Error validating citation {citation}: {str(e)}")
            results.append(
                {
                    "citation": citation,
                    "exists": False,
                    "method": "error",
                    "error": str(e),
                    "data": None,
                }
            )

    return results


# DEPRECATED: Use extract_all_citations from src.citation_extractor instead.
def extract_citations(*args, **kwargs):
    """DEPRECATED. Use extract_all_citations from src.citation_extractor instead."""
    import warnings
    warnings.warn("extract_citations is deprecated. Use extract_all_citations from src.citation_extractor instead.", DeprecationWarning)
    return []

def extract_citations_from_text(*args, **kwargs):
    """DEPRECATED. Use extract_all_citations from src.citation_extractor instead."""
    import warnings
    warnings.warn("extract_citations_from_text is deprecated. Use extract_all_citations from src.citation_extractor instead.", DeprecationWarning)
    return []

def extract_citations_from_text(text, logger=logger):
    """
    Extract potential citations from text using regex patterns and verify them using the CourtListener API.
    
    Args:
        text (str): The text to extract citations from.
        logger: Logger instance for logging information and errors.
    
    Returns:
        list: A list of verified citation results.
    """
    if not text or not isinstance(text, str):
        logger.error("Invalid input: Text must be a non-empty string.")
        return []

    logger.info("Starting citation extraction from text.")
    
    # Pattern for state supreme court and appellate court abbreviations (from University of Akron Bluebook Quick Reference)
    state_court_abbr_pattern = (
        r'\d+\s+(?:Ala\.|Alaska|Ariz\.|Ark\.|Cal\.|Colo\.|Conn\.|Del\.|D\.C\.|Fla\.|Ga\.|Haw\.|Idaho|Ill\.|Ind\.|Iowa|Kan\.|Ky\.|La\.|Me\.|Md\.|Mass\.|Mich\.|Minn\.|Miss\.|Mo\.|Mont\.|Neb\.|Nev\.|N\.H\.|N\.J\.|N\.M\.|N\.Y\.|N\.C\.|N\.D\.|Ohio|Okla\.|Or\.|Pa\.|R\.I\.|S\.C\.|S\.D\.|Tenn\.|Tex\.|Utah|Vt\.|Va\.|Wash\.|W\. Va\.|Wis\.|Wyo\.|Ala\. Civ\. App\.|Ala\. Crim\. App\.|Alaska Ct\. App\.|Ariz\. Ct\. App\.|Ark\. Ct\. App\.|Cal\. Ct\. App\.|Colo\. App\.|Conn\. App\. Ct\.|Del\. Ch\.|Fla\. Dist\. Ct\. App\.|Ga\. Ct\. App\.|Haw\. Ct\. App\.|Idaho Ct\. App\.|Ill\. App\. Ct\.|Ind\. Ct\. App\.|Iowa Ct\. App\.|Kan\. Ct\. App\.|Ky\. Ct\. App\.|La\. Ct\. App\.|Md\. App\. Ct\.|Md\. Ct\. Spec\. App\.|Mass\. App\. Ct\.|Mich\. Ct\. App\.|Minn\. Ct\. App\.|Miss\. Ct\. App\.|Mo\. Ct\. App\.|Neb\. Ct\. App\.|N\.J\. Super\. Ct\. App\. Div\.|N\.M\. Ct\. App\.|N\.Y\. App\. Div\.|N\.C\. Ct\. App\.|N\.D\. Ct\. App\.|Ohio Ct\. App\.|Okla\. Crim\. App\.|Okla\. Civ\. App\.|Or\. Ct\. App\.|Pa\. Super\. Ct\.|S\.C\. Ct\. App\.|Tenn\. Ct\. App\.|Tex\. Crim\. App\.|Tex\. App\.|Utah Ct\. App\.|Va\. Ct\. App\.|Wash\. Ct\. App\.|Wis\. Ct\. App\.)\s+\d+'
    )

    # Define regex patterns for a wide range of Bluebook-style case citation formats (federal, regional, state, and generic reporters)
    patterns = [
        state_court_abbr_pattern,
        # Regional and State Reporters - require full series indicator (2d, 3d, 4th, 5th, 6th, 7th, etc.) and page number
        r'\d+\s+A\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Atlantic Reporter, all series
        r'\d+\s+A\.\s+\d{2,}',    # Atlantic Reporter (original series, page must be at least 2 digits)
        r'\d+\s+N\.E\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Northeastern Reporter, all series
        r'\d+\s+N\.E\.\s+\d{2,}',    # Northeastern Reporter (original series)
        r'\d+\s+N\.W\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Northwestern Reporter, all series
        r'\d+\s+N\.W\.\s+\d{2,}',    # Northwestern Reporter (original series)
        r'\d+\s+S\.E\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Southeastern Reporter, all series
        r'\d+\s+S\.E\.\s+\d{2,}',    # Southeastern Reporter (original series)
        r'\d+\s+S\.W\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Southwestern Reporter, all series
        r'\d+\s+S\.W\.\s+\d{2,}',    # Southwestern Reporter (original series)
        r'\d+\s+So\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',     # Southern Reporter, all series
        r'\d+\s+So\.\s+\d{2,}',       # Southern Reporter (original series)
        r'\d+\s+P\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',      # Pacific Reporter, all series
        r'\d+\s+P\.\s+\d{2,}',        # Pacific Reporter (original series)
        # Washington (Wash. or Wn. with series and page)
        r'\d+\s+(?:Wash\.|Wn\.)\s*(?:2d|3d|4th|5th|6th|7th|8th|9th)?\s*(?:App\.)?\s+\d+',
        # California (Cal.4th, etc.)
        r'\d+\s+Cal\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',
        r'\d+\s+Cal\.\s+\d{2,}',
        # Westlaw
        r'\d{4}\s+WL\s+\d+',
    ]
    
    # Remove any pattern that could match a period and a single digit as a valid series indicator
    patterns = [pattern for pattern in patterns if not re.search(r'\.\d+$', pattern)]
    
    found = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            found.add(match.strip())
    
    # Post-processing: Normalize all Washington citations to Wash. format
    normalized_citations = []
    for citation in found:
        normalized_citation = citation
        # Normalize Wn. to Wash. for all Washington citations
        if re.search(r'\bWn\.', citation):
            # Wn.2d -> Wash. 2d
            normalized_citation = re.sub(r'\bWn\.2d\b', 'Wash. 2d', normalized_citation)
            # Wn.3d -> Wash. 3d  
            normalized_citation = re.sub(r'\bWn\.3d\b', 'Wash. 3d', normalized_citation)
            # Wn. App. -> Wash. App.
            normalized_citation = re.sub(r'\bWn\. App\.\b', 'Wash. App.', normalized_citation)
            # Wn. -> Wash.
            normalized_citation = re.sub(r'\bWn\.\b', 'Wash.', normalized_citation)
        
        # Also normalize any Wash.2d to Wash. 2d format
        normalized_citation = re.sub(r'\bWash\.2d\b', 'Wash. 2d', normalized_citation)
        normalized_citation = re.sub(r'\bWash\.3d\b', 'Wash. 3d', normalized_citation)
        
        normalized_citations.append(normalized_citation)
    
    # Remove duplicates and return normalized citations
    unique_normalized = list(set(normalized_citations))
    logger.info(f"Extracted {len(unique_normalized)} unique Washington citations (normalized to Wash. format).")
    return unique_normalized


def chunk_text_with_overlap(text, max_len=64000, overlap=40):
    """
    Split text into chunks of max_len with specified overlap.
    """
    chunks = []
    i = 0
    while i < len(text):
        start = i - overlap if i > 0 else 0
        end = min(i + max_len, len(text))
        chunks.append(text[start:end])
        i += max_len
    return chunks

def deduplicate_citations(citations):
    seen = set()
    unique = []
    for c in citations:
        key = c.get('normalized_citations', [None])[0] if c.get('normalized_citations') else c.get('citation') or c.get('citation_text')
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def extract_all_citations(text, logger=logger):
    """
    Extract all citations from text using the unified extractor.
    
    This function now delegates to the unified citation extraction system
    for consistency across the codebase.
    
    Args:
        text: The text to extract citations from
        logger: Optional logger instance
        
    Returns:
        List of citation dictionaries with metadata
    """
    from src.citation_extractor import CitationExtractor
    
    # Initialize extractor with case name extraction enabled
    extractor = CitationExtractor(
        use_eyecite=True,
        use_regex=True,
        context_window=1000,
        deduplicate=True,
        extract_case_names=True
    )
    
    return extractor.extract(text)
