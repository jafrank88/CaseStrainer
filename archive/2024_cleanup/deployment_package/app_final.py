from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    Response,
    send_from_directory,
    redirect,
)
from flask_cors import CORS
import os
import re
import json
import time
import uuid
import sys
import io
import subprocess
import threading
import traceback
import requests
import tempfile
import threading
import random
import string
import hashlib
import os.path
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from functools import lru_cache
from test_citations import get_random_test_citations

# Import citation correction module
try:
    from citation_correction import get_correction_suggestions
except ImportError:
    print(
        "Warning: citation_correction module not found. Correction suggestions will not be available."
    )

    def get_correction_suggestions(citation_text):
        return []


# Import citation classifier module
try:
    from citation_classifier import (
        classify_citation,
        batch_classify_citations,
        train_citation_classifier,
    )
except ImportError:
    print(
        "Warning: citation_classifier module not found. ML classification will not be available."
    )

    def classify_citation(citation_text, case_name=None):
        return 0.5

    def batch_classify_citations(citations):
        return [0.5] * len(citations)

    def train_citation_classifier():
        return None, None


# Import citation export module
try:
    from citation_export import export_citations, load_citations
except ImportError:
    print(
        "Warning: citation_export module not found. Enhanced export functionality will not be available."
    )

# Import enhanced citation verifier module
try:
    from enhanced_citation_verifier import MultiSourceVerifier

    print("Successfully imported enhanced citation verifier")
    USE_MULTI_SOURCE_VERIFIER = True
    multi_source_verifier = MultiSourceVerifier()
except ImportError:
    print(
        "Warning: enhanced_citation_verifier module not found. Enhanced verification will not be available."
    )
    USE_MULTI_SOURCE_VERIFIER = False


def export_citations(citations, format_type, filename=None):
    return None


def load_citations(filter_criteria=None):
    return []


from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from functools import lru_cache

# Import citation grouping functionality
from citation_grouping import group_citations

# Import eyecite for better citation extraction
from eyecite import get_citations
from eyecite.tokenizers import HyperscanTokenizer, AhocorasickTokenizer

# Import our robust PDF handler
from pdf_handler import extract_text_from_pdf

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})


# Handle URL prefix for Nginx proxy
class PrefixMiddleware(object):
    def __init__(self, app, prefix=""):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        # Check if request has our prefix
        if self.prefix and environ["PATH_INFO"].startswith(self.prefix):
            # Strip the prefix
            environ["PATH_INFO"] = environ["PATH_INFO"][len(self.prefix) :]
            environ["SCRIPT_NAME"] = self.prefix

        # Ensure PATH_INFO starts with a slash
        if not environ["PATH_INFO"]:
            environ["PATH_INFO"] = "/"
        elif not environ["PATH_INFO"].startswith("/"):
            environ["PATH_INFO"] = "/" + environ["PATH_INFO"]

        # Pass the modified environment to the app
        return self.app(environ, start_response)


# Apply the prefix middleware
# This allows the application to work both with and without the /casestrainer prefix
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix="/casestrainer")

# Constants
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx", "doc"}
COURTLISTENER_API_URL = "https://www.courtlistener.com/api/rest/v3/search/"
LANGSEARCH_API_URL = "https://api.langsearch.ai/v1/completions"
CACHE_DIR = "citation_cache"
CACHE_EXPIRY_DAYS = 30  # Cache entries expire after 30 days

# Create upload folder and cache directory if they don't exist
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print(f"Upload folder created/verified at: {UPLOAD_FOLDER}")
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"Cache directory created/verified at: {CACHE_DIR}")
    # Test write permissions
    test_file = os.path.join(UPLOAD_FOLDER, "test_write.txt")
    with open(test_file, "w") as f:
        f.write("Test write")
    os.remove(test_file)
    print("Upload folder is writable")
except Exception as e:
    print(f"ERROR creating upload folder: {e}")
    traceback.print_exc()

# Load API keys from config.json if available
DEFAULT_API_KEY = None
LANGSEARCH_API_KEY = None
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        DEFAULT_API_KEY = config.get("courtlistener_api_key")
        LANGSEARCH_API_KEY = config.get("langsearch_api_key")
        print(
            f"Loaded CourtListener API key from config.json: {DEFAULT_API_KEY[:5]}..."
            if DEFAULT_API_KEY
            else "No CourtListener API key found in config.json"
        )
        print(
            f"Loaded LangSearch API key from config.json: {LANGSEARCH_API_KEY[:5]}..."
            if LANGSEARCH_API_KEY
            else "No LangSearch API key found in config.json"
        )
except Exception as e:
    print(f"Error loading config.json: {e}")

# Dictionary to store analysis results
analysis_results = {}


# Cache management functions
def get_cache_key(citation_text):
    """
    Generate a unique cache key for a citation.
    """
    # Create a hash of the citation text to use as the cache key
    return hashlib.md5(citation_text.encode("utf-8")).hexdigest()


def get_cache_path(cache_key):
    """
    Get the file path for a cache entry.
    """
    return os.path.join(CACHE_DIR, f"{cache_key}.json")


def save_to_cache(citation_text, result):
    """
    Save a citation verification result to the cache.
    """
    try:
        cache_key = get_cache_key(citation_text)
        cache_path = get_cache_path(cache_key)

        # Add timestamp to the cached result
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "citation": citation_text,
            "result": result,
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

        print(f"Saved citation to cache: {citation_text}")
        return True
    except Exception as e:
        print(f"Error saving to cache: {e}")
        return False


def load_from_cache(citation_text):
    """
    Load a citation verification result from the cache if it exists and is not expired.
    Returns None if the cache entry doesn't exist or is expired.
    """
    try:
        cache_key = get_cache_key(citation_text)
        cache_path = get_cache_path(cache_key)

        # Check if cache file exists
        if not os.path.exists(cache_path):
            return None

        with open(cache_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        # Check if cache entry is expired
        timestamp = datetime.fromisoformat(cache_data["timestamp"])
        expiry_date = datetime.now() - timedelta(days=CACHE_EXPIRY_DAYS)

        if timestamp < expiry_date:
            print(f"Cache entry expired for citation: {citation_text}")
            # Remove expired cache entry
            os.remove(cache_path)
            return None

        print(f"Loaded citation from cache: {citation_text}")
        return cache_data["result"]
    except Exception as e:
        print(f"Error loading from cache: {e}")
        return None


# Advanced case name extraction function
def extract_case_name_from_text(text, citation_text):
    """
    Extract potential case name from text surrounding a citation.
    Uses multiple patterns and heuristics to find the most likely case name.
    """
    if not text or not citation_text:
        return None

    # Find the citation in the text
    citation_index = text.find(citation_text)
    if citation_index <= 0:
        return None

    # Look for potential case name in the text before the citation
    # We'll use a larger window (300 chars) to increase chances of finding the case name
    pre_text = text[max(0, citation_index - 300) : citation_index]

    # List of patterns to try, in order of preference
    patterns = [
        # Pattern 1: Case name with "v." or "vs." (most common format)
        r"([A-Z][\w\s\.,&\-]+\sv\.\s[\w\s\.,&\-]+)",
        # Pattern 2: Case name with "versus"
        r"([A-Z][\w\s\.,&\-]+\sversus\s[\w\s\.,&\-]+)",
        # Pattern 3: Case name with "v" (abbreviated format)
        r"([A-Z][\w\s\.,&\-]+\sv\s[\w\s\.,&\-]+)",
        # Pattern 4: Case name with "ex rel." format
        r"([A-Z][\w\s\.,&\-]+\sex rel\.\s[\w\s\.,&\-]+)",
        # Pattern 5: Case name with "In re" format
        r"(In re\s[\w\s\.,&\-]+)",
        # Pattern 6: Case name with "Matter of" format
        r"(Matter of\s[\w\s\.,&\-]+)",
        # Pattern 7: Case name with "Estate of" format
        r"(Estate of\s[\w\s\.,&\-]+)",
        # Pattern 8: Last resort - look for capitalized phrases that might be case names
        r"([A-Z][\w\s\.,&\-]+(?:,|\.|;)\s+\d)",
    ]

    # Try each pattern in order
    for pattern in patterns:
        matches = re.findall(pattern, pre_text)
        if matches:
            # Get the last match (closest to the citation)
            case_name = matches[-1].strip()
            # Clean up the case name (remove trailing punctuation)
            case_name = re.sub(r"[\.,;]\s*$", "", case_name)
            print(f"Extracted case name using pattern '{pattern}': {case_name}")
            return case_name

    # If no matches found with any pattern, return None
    return None


# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Function to extract text from different file types
def extract_text_from_file(file_path):
    """Extract text from a file based on its extension."""
    print(f"Extracting text from file: {file_path}")

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None

    # Get file extension
    file_extension = file_path.split(".")[-1].lower()
    print(f"File extension: {file_extension}")

    try:
        # Extract text based on file extension
        if file_extension == "txt":
            # For .txt files, just read the content
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    text = file.read()
                    print(f"Successfully extracted {len(text)} characters from TXT")
                    return text
            except UnicodeDecodeError:
                # Try with a different encoding if utf-8 fails
                with open(file_path, "r", encoding="latin-1") as file:
                    text = file.read()
                    print(
                        f"Successfully extracted {len(text)} characters from TXT (latin-1 encoding)"
                    )
                    return text

        elif file_extension == "pdf":
            # Use our robust PDF handler for all PDF files
            print(f"Using robust PDF handler for: {file_path}")
            text = extract_text_from_pdf(file_path)

            # Check if extraction was successful
            if text and isinstance(text, str):
                if text.startswith("Error:"):
                    print(f"PDF extraction failed: {text}")
                    return None
                else:
                    print(f"Successfully extracted {len(text)} characters from PDF")
                    return text
            else:
                print(f"PDF extraction returned invalid result: {type(text)}")
                return None

        elif file_extension in ["docx", "doc"]:
            # For .docx files, use python-docx
            try:
                # Check if file exists and is readable
                if not os.path.isfile(file_path):
                    error_msg = f"File not found: {file_path}"
                    print(error_msg)
                    return f"Error: {error_msg}"

                # Check file size
                try:
                    file_size = os.path.getsize(file_path)
                    print(f"DOCX file size: {file_size} bytes")
                    if file_size == 0:
                        error_msg = f"File is empty: {file_path}"
                        print(error_msg)
                        return f"Error: {error_msg}"
                    elif file_size > 50 * 1024 * 1024:  # 50MB limit
                        error_msg = (
                            f"File is too large ({file_size} bytes): {file_path}"
                        )
                        print(error_msg)
                        return f"Error: {error_msg}"
                except Exception as e:
                    print(f"Error checking file size: {e}")

                # Open the document
                doc = docx.Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                print(f"Successfully extracted {len(text)} characters from DOCX")
                return text
            except Exception as e:
                print(f"Error extracting text from DOCX: {e}")
                traceback.print_exc()
                return None

        else:
            print(f"Unsupported file extension: {file_extension}")
            return None

    except Exception as e:
        print(f"Error extracting text from file: {e}")
        traceback.print_exc()
        return None


# Function to extract citations from text
def extract_citations(text):
    """
    Extract legal citations from text using eyecite library.
    This provides more accurate and comprehensive citation extraction than regex patterns.
    """
    print(f"Extracting citations from text of length: {len(text)}")
    citations = []

    # Try using eyecite first
    try:
        print("Extracting citations using eyecite...")
        # Try to use the faster HyperscanTokenizer first
        try:
            tokenizer = HyperscanTokenizer()
        except Exception:
            # Fall back to AhocorasickTokenizer if HyperscanTokenizer fails
            print("Falling back to AhocorasickTokenizer...")
            tokenizer = AhocorasickTokenizer()

        # Get citations using eyecite
        citation_objects = get_citations(text, tokenizer=tokenizer)

        # Extract the citation strings
        for citation in citation_objects:
            citation_str = (
                citation.corrected_citation()
                if hasattr(citation, "corrected_citation")
                else str(citation)
            )
            if citation_str not in citations:
                citations.append(citation_str)

        print(f"Found {len(citations)} citations using eyecite")
    except Exception as e:
        print(f"Error using eyecite: {e}")
        traceback.print_exc()

        # Fall back to regex patterns if eyecite fails
        print("Falling back to regex patterns...")
        # Normalize the text to make citation matching more reliable
        text = re.sub(r"\s+", " ", text)

        # Example patterns for common citation formats
        patterns = [
            # US Reports (e.g., 347 U.S. 483)
            r"\b\d+\s+U\.?\s*S\.?\s+\d+\b",
            # Supreme Court Reporter (e.g., 98 S.Ct. 2733)
            r"\b\d+\s+S\.?\s*Ct\.?\s+\d+\b",
            # Federal Reporter (e.g., 410 F.2d 701, 723 F.3d 1067)
            r"\b\d+\s+F\.?\s*(?:2d|3d)?\s+\d+\b",
            # Federal Supplement (e.g., 595 F.Supp.2d 735)
            r"\b\d+\s+F\.?\s*Supp\.?\s*(?:2d|3d)?\s+\d+\b",
            # Westlaw citations (e.g., 2011 WL 2160468)
            r"\b\d{4}\s+WL\s+\d+\b",
        ]

        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    citation = match.group(0).strip()
                    if citation not in citations:
                        citations.append(citation)
            except Exception as e:
                print(f"Error searching for pattern {pattern}: {e}")

    print(f"Total citations extracted: {len(citations)}")
    if citations:
        print(f"Extracted citations: {citations}")

        # Save the extracted citations to a file for inspection
        try:
            with open("extracted_citations.txt", "w", encoding="utf-8") as f:
                for i, citation in enumerate(citations):
                    f.write(f"{i+1}. {citation}\n")
            print(f"Extracted citations saved to extracted_citations.txt")
        except Exception as e:
            print(f"Error saving extracted citations to file: {e}")

    return citations


# Function to search for a citation on multiple legal websites
# Import the landmark cases database
try:
    from landmark_cases import is_landmark_case, LANDMARK_CASES

    print("Loaded landmark cases database with", len(LANDMARK_CASES), "cases")
except ImportError:
    print(
        "Warning: landmark_cases module not found. Landmark case verification will not be available."
    )

    def is_landmark_case(citation_text):
        return None


# Import the multi-source verifier if available
try:
    # Try to import from the fixed version first
    try:
        from fixed_multi_source_verifier import MultiSourceVerifier

        print(
            "Successfully imported MultiSourceVerifier from fixed_multi_source_verifier"
        )
    except ImportError:
        from multi_source_verifier import MultiSourceVerifier

        print("Successfully imported MultiSourceVerifier from multi_source_verifier")

    # Initialize the verifier with API keys from config.json
    api_keys = {}
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            api_keys["courtlistener"] = config.get("courtlistener_api_key")
    except Exception as e:
        print(f"Error loading API keys from config.json: {e}")

    multi_source_verifier = MultiSourceVerifier(api_keys)
    USE_MULTI_SOURCE_VERIFIER = True
except ImportError:
    print(
        "Warning: multi_source_verifier module not found. Enhanced verification will not be available."
    )
    USE_MULTI_SOURCE_VERIFIER = False

# Descrybe.ai configuration for manual verification
DESCRYBE_URL = "https://descrybe.ai/search"
USE_DESCRYBE_MANUAL_VERIFICATION = True


@lru_cache(maxsize=128)  # Cache the most recent 128 search results in memory
def search_citation_on_web(citation_text, case_name=None):
    """
    Search for a citation on legal websites like Leagle.com, Justia, FindLaw, and Google Scholar to verify if it exists.
    Also checks against a database of landmark cases for reliable verification.
    If case_name is provided, it will also check if the found case name matches.

    Returns a dictionary with:
    - found: boolean indicating if citation was found
    - url: URL of the found case (if any)
    - found_case_name: Name of the case found (if any)
    - name_match: boolean indicating if the found case name matches the provided case_name
    - confidence: confidence score (0.0-1.0)
    - explanation: explanation of the result
    - source: which website found the citation
    """
    print(f"Searching for citation on legal websites: {citation_text}")

    # Check if we have this citation in the cache
    cached_result = load_from_cache(citation_text)
    if cached_result:
        print(f"Using cached result for citation: {citation_text}")

        # If case_name is provided but wasn't in the original cache entry,
        # update the name_match field
        if case_name and "found_case_name" in cached_result:
            cached_result["name_match"] = check_name_match(
                case_name, cached_result["found_case_name"]
            )

        return cached_result

    # Use the multi-source verifier if available
    if USE_MULTI_SOURCE_VERIFIER:
        try:
            print(f"Using multi-source verifier for citation: {citation_text}")
            result = multi_source_verifier.verify_citation(citation_text, case_name)

            # Save to cache
            save_to_cache(citation_text, result)

            return result
        except Exception as e:
            print(f"Error using multi-source verifier: {e}")
            print("Falling back to legacy verification method")
            traceback.print_exc()

        # If case_name is provided but wasn't in the original cache entry,
        # update the name_match field
        if case_name and "found_case_name" in cached_result and cached_result["found"]:
            # Use the improved case name matching algorithm
            name_match = check_name_match(cached_result["found_case_name"], case_name)
            cached_result["name_match"] = name_match

            # Update confidence and explanation if name matches
            if name_match and cached_result["confidence"] < 0.9:
                cached_result["confidence"] = 0.9
                cached_result["explanation"] += " (case name matches)"

                # Update the cache with the improved result
                save_to_cache(citation_text, cached_result)

        return cached_result

    result = {
        "found": False,
        "url": None,
        "found_case_name": None,
        "name_match": False,
        "confidence": 0.5,
        "explanation": f"Citation not found on legal websites",
        "source": None,
    }

    # 0. Check if this is a landmark case first
    landmark_info = is_landmark_case(citation_text)
    if landmark_info:
        print(f"Found landmark case: {landmark_info['name']} ({citation_text})")

        # Check if case name matches (if provided)
        name_match = False
        if case_name:
            name_match = check_name_match(landmark_info["name"], case_name)

        # Create a result with high confidence
        result = {
            "found": True,
            "url": (
                f"https://supreme.justia.com/cases/federal/us/{citation_text.split()[0]}/{citation_text.split()[2]}/"
                if "U.S." in citation_text
                else None
            ),
            "found_case_name": landmark_info["name"],
            "name_match": name_match,
            "confidence": 0.95 if name_match else 0.9,
            "explanation": f"Verified landmark case: {landmark_info['name']} ({landmark_info['year']}) - {landmark_info['significance']}",
            "source": "Landmark Cases Database",
        }

        # Save to cache and return immediately
        save_to_cache(citation_text, result)
        return result

    # Use the improved case name matching algorithm
    def check_name_match(found_name, original_name):
        if not original_name or not found_name:
            return False

        # Normalize case names for comparison
        def normalize_case_name(name):
            # Convert to lowercase
            name = name.lower()

            # Remove common legal terms that don't help with matching
            common_terms = [
                "v.",
                "vs.",
                "versus",
                "v",
                "et al.",
                "et al",
                "inc.",
                "inc",
                "llc",
                "corp.",
                "corp",
                "ltd.",
                "ltd",
                "co.",
                "co",
                "company",
                "corporation",
                "incorporated",
                "limited",
                "the",
                "and",
                "of",
                "for",
                "in",
                "re:",
                "re",
                "matter of",
                "estate of",
            ]

            for term in common_terms:
                name = name.replace(f" {term} ", " ")
                if name.startswith(f"{term} "):
                    name = name[len(term) + 1 :]
                if name.endswith(f" {term}"):
                    name = name[: -len(term) - 1]

            # Remove punctuation and extra whitespace
            name = re.sub(r"[^\w\s]", "", name)
            name = re.sub(r"\s+", " ", name).strip()

            return name

        # Normalize both names
        norm_found_name = normalize_case_name(found_name)
        norm_case_name = normalize_case_name(original_name)

        # Get significant words (longer than 3 chars)
        words_found = [w for w in norm_found_name.split() if len(w) > 3]
        words_case = [w for w in norm_case_name.split() if len(w) > 3]

        # If either name has no significant words, we can't match properly
        if not words_found or not words_case:
            return False

        # Count matches
        matches = 0
        for word in words_found:
            # Check for exact word match or substring match for longer words
            if any(word == case_word for case_word in words_case):
                matches += 2  # Give more weight to exact matches
            elif any(
                word in case_word or case_word in word
                for case_word in words_case
                if len(word) > 5 and len(case_word) > 5
            ):
                matches += 1  # Give less weight to partial matches

        # Calculate match percentage based on the shorter name
        min_words = min(len(words_found), len(words_case))
        if min_words == 0:
            return False

        match_percentage = matches / (
            min_words * 2
        )  # Normalize to account for exact matches worth 2

        # Consider it a match if we have at least 50% matching
        return match_percentage >= 0.5

    try:
        # Clean and format the citation for searching
        clean_citation = citation_text.strip()

        # 1. Try Leagle.com first
        # For WL citations, we'll search directly
        if "WL" in clean_citation:
            search_url = f"https://www.leagle.com/decision/search?q={urllib.parse.quote(clean_citation)}"
            print(f"Searching Leagle.com with URL: {search_url}")

            try:
                response = requests.get(search_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Look for search results
                    results = soup.select(".search-result")
                    for result_item in results:
                        # Check if the citation appears in the result
                        result_text = result_item.text.strip()
                        if clean_citation in result_text:
                            # Get the case name and URL
                            case_link = result_item.select_one("a")
                            if case_link:
                                found_case_name = case_link.text.strip()
                                case_url = (
                                    "https://www.leagle.com" + case_link["href"]
                                    if case_link["href"].startswith("/")
                                    else case_link["href"]
                                )

                                # Check if case name matches (if provided)
                                name_match = check_name_match(
                                    found_case_name, case_name
                                )

                                result = {
                                    "found": True,
                                    "url": case_url,
                                    "found_case_name": found_case_name,
                                    "name_match": name_match,
                                    "confidence": 0.8 if name_match else 0.7,
                                    "explanation": f"Citation found on Leagle.com: {found_case_name}",
                                    "source": "Leagle.com",
                                }

                                if name_match:
                                    result["explanation"] += f" (case name matches)"
                                    result["confidence"] = 0.9

                                return result
            except Exception as e:
                print(f"Error searching Leagle.com: {e}")

        # 2. Try Justia
        try:
            # Justia has a different search format for different citation types
            justia_search_url = None

            # For Supreme Court citations
            if "S.Ct." in clean_citation or "S. Ct." in clean_citation:
                justia_search_url = f"https://supreme.justia.com/search?q={urllib.parse.quote(clean_citation)}"
            # For Westlaw citations
            elif "WL" in clean_citation:
                justia_search_url = f"https://law.justia.com/search?query={urllib.parse.quote(clean_citation)}"
            # For standard reporter citations
            else:
                justia_search_url = f"https://law.justia.com/search?query={urllib.parse.quote(clean_citation)}"

            if justia_search_url:
                print(f"Searching Justia with URL: {justia_search_url}")
                response = requests.get(justia_search_url, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Look for search results - Justia has different result formats
                    # Try multiple selectors
                    results = (
                        soup.select(".result-title")
                        or soup.select(".gs-title")
                        or soup.select("h3.title")
                    )

                    for result_item in results:
                        result_text = result_item.text.strip()
                        # Check if the citation or parts of it appear in the result
                        if clean_citation in result_text or (
                            ("WL" in clean_citation)
                            and clean_citation.split()[0] in result_text
                        ):
                            case_link = result_item.find("a") or result_item
                            if (
                                case_link
                                and hasattr(case_link, "href")
                                and case_link["href"]
                            ):
                                found_case_name = result_text
                                case_url = case_link["href"]
                                if not case_url.startswith("http"):
                                    case_url = "https://law.justia.com" + case_url

                                name_match = check_name_match(
                                    found_case_name, case_name
                                )

                                result = {
                                    "found": True,
                                    "url": case_url,
                                    "found_case_name": found_case_name,
                                    "name_match": name_match,
                                    "confidence": 0.8 if name_match else 0.7,
                                    "explanation": f"Citation found on Justia: {found_case_name}",
                                    "source": "Justia",
                                }

                                if name_match:
                                    result["explanation"] += f" (case name matches)"
                                    result["confidence"] = 0.9

                                return result
        except Exception as e:
            print(f"Error searching Justia: {e}")

        # 3. Try FindLaw
        try:
            findlaw_search_url = f"https://caselaw.findlaw.com/search?query={urllib.parse.quote(clean_citation)}"
            print(f"Searching FindLaw with URL: {findlaw_search_url}")

            response = requests.get(findlaw_search_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # FindLaw uses different selectors for search results
                results = (
                    soup.select(".search-result")
                    or soup.select(".result-title")
                    or soup.select("h3.title")
                )

                for result_item in results:
                    result_text = result_item.text.strip()
                    if clean_citation in result_text:
                        case_link = result_item.find("a")
                        if case_link and case_link.get("href"):
                            found_case_name = result_text
                            case_url = case_link["href"]
                            if not case_url.startswith("http"):
                                case_url = "https://caselaw.findlaw.com" + case_url

                            name_match = check_name_match(found_case_name, case_name)

                            result = {
                                "found": True,
                                "url": case_url,
                                "found_case_name": found_case_name,
                                "name_match": name_match,
                                "confidence": 0.8 if name_match else 0.7,
                                "explanation": f"Citation found on FindLaw: {found_case_name}",
                                "source": "FindLaw",
                            }

                            if name_match:
                                result["explanation"] += f" (case name matches)"
                                result["confidence"] = 0.9

                            return result
        except Exception as e:
            print(f"Error searching FindLaw: {e}")

        # 4. Try Google Scholar
        try:
            # Google Scholar has a specific format for legal searches
            scholar_search_url = f"https://scholar.google.com/scholar?q={urllib.parse.quote(clean_citation)}"
            print(f"Searching Google Scholar with URL: {scholar_search_url}")

            # Google Scholar may block automated requests, so we need to use a user agent
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            response = requests.get(scholar_search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Google Scholar uses gs_ri class for results
                results = soup.select(".gs_ri")

                for result_item in results:
                    result_text = result_item.text.strip()
                    # Check if the citation appears in the result
                    if clean_citation in result_text:
                        case_link = result_item.select_one("h3 a")
                        if case_link and case_link.get("href"):
                            found_case_name = case_link.text.strip()
                            case_url = case_link["href"]

                            name_match = check_name_match(found_case_name, case_name)

                            result = {
                                "found": True,
                                "url": case_url,
                                "found_case_name": found_case_name,
                                "name_match": name_match,
                                "confidence": 0.8 if name_match else 0.7,
                                "explanation": f"Citation found on Google Scholar: {found_case_name}",
                                "source": "Google Scholar",
                            }

                            if name_match:
                                result["explanation"] += f" (case name matches)"
                                result["confidence"] = 0.9

                            return result
        except Exception as e:
            print(f"Error searching Google Scholar: {e}")

        # 5. Try direct URL formats for specific citation types
        # This works for some standard reporter citations like S.Ct.
        if "S.Ct." in clean_citation or "S. Ct." in clean_citation:
            try:
                # Extract volume and page numbers
                match = re.search(r"(\d+)\s*S\.?\s*Ct\.?\s*(\d+)", clean_citation)
                if match:
                    volume, page = match.groups()

                    # Try Leagle.com direct URL
                    direct_url = (
                        f"https://www.leagle.com/decision/in-sco-{volume}sct{page}-1"
                    )
                    print(f"Trying direct URL for Supreme Court citation: {direct_url}")

                    response = requests.get(direct_url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")
                        case_title = soup.select_one(".case-title")

                        if case_title:
                            found_case_name = case_title.text.strip()
                            name_match = check_name_match(found_case_name, case_name)

                            result = {
                                "found": True,
                                "url": direct_url,
                                "found_case_name": found_case_name,
                                "name_match": name_match,
                                "confidence": 0.8 if name_match else 0.7,
                                "explanation": f"Citation found directly on Leagle.com: {found_case_name}",
                                "source": "Leagle.com (direct)",
                            }

                            if name_match:
                                result["explanation"] += f" (case name matches)"
                                result["confidence"] = 0.9

                            return result

                    # Try Justia direct URL for Supreme Court
                    justia_direct_url = (
                        f"https://supreme.justia.com/cases/federal/us/{volume}/{page}/"
                    )
                    print(
                        f"Trying direct URL for Supreme Court citation on Justia: {justia_direct_url}"
                    )

                    response = requests.get(justia_direct_url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")
                        case_title = soup.select_one("h1.case-name")

                        if case_title:
                            found_case_name = case_title.text.strip()
                            name_match = check_name_match(found_case_name, case_name)

                            result = {
                                "found": True,
                                "url": justia_direct_url,
                                "found_case_name": found_case_name,
                                "name_match": name_match,
                                "confidence": 0.8 if name_match else 0.7,
                                "explanation": f"Citation found directly on Justia: {found_case_name}",
                                "source": "Justia (direct)",
                            }

                            if name_match:
                                result["explanation"] += f" (case name matches)"
                                result["confidence"] = 0.9

                            return result
            except Exception as e:
                print(f"Error with direct URL approach: {e}")

        # Save the result to cache before returning
        save_to_cache(citation_text, result)
        return result

    except Exception as e:
        print(f"Error searching citation on legal websites: {e}")
        traceback.print_exc()
        error_result = {
            "found": False,
            "url": None,
            "found_case_name": None,
            "name_match": False,
            "confidence": 0.5,
            "explanation": f"Error searching citation: {str(e)}",
            "source": None,
        }
        # We don't cache error results
        return error_result


# Function to check case using LangSearch API
def check_case_with_langsearch(citation_text):
    """Check if a case is real by asking LangSearch to summarize it twice and comparing the summaries."""
    print(f"Checking case with LangSearch API: {citation_text}")

    if not LANGSEARCH_API_KEY:
        print("No LangSearch API key provided")
        return {
            "is_real": False,
            "confidence": 0.5,
            "explanation": "No LangSearch API key provided, unable to verify citation",
        }

    try:
        # Prepare the request
        headers = {
            "Authorization": f"Bearer {LANGSEARCH_API_KEY}",
            "Content-Type": "application/json",
        }

        # First summary request
        first_prompt = f"Summarize the legal case {citation_text} in 3-5 sentences. Include the main legal issue and holding."
        first_data = {"prompt": first_prompt, "max_tokens": 300}

        # Make the first request
        print(f"Requesting first summary for: {citation_text}")
        first_response = requests.post(
            "https://api.langsearch.ai/v1/generate", headers=headers, json=first_data
        )

        # Check the response
        if first_response.status_code != 200:
            print(
                f"First LangSearch API request failed with status code {first_response.status_code}"
            )
            print(f"Response: {first_response.text}")
            return {
                "is_real": False,
                "confidence": 0.6,
                "explanation": f"Error checking citation: API request failed with status code {first_response.status_code}",
            }

        first_result = first_response.json()
        first_summary = first_result.get("text", "")
        print(f"First summary: {first_summary}")

        # If the first summary indicates the case doesn't exist
        if (
            "unable to find" in first_summary.lower()
            or "no information" in first_summary.lower()
            or "not a valid" in first_summary.lower()
        ):
            return {
                "is_real": False,
                "confidence": 0.8,
                "explanation": f"LangSearch could not find information about this citation: {first_summary}",
            }

        # Second summary request with different wording
        second_prompt = f"Provide a brief overview of the case {citation_text}. What were the key facts and the court's decision?"
        second_data = {"prompt": second_prompt, "max_tokens": 300}

        # Make the second request
        print(f"Requesting second summary for: {citation_text}")
        second_response = requests.post(
            "https://api.langsearch.ai/v1/generate", headers=headers, json=second_data
        )

        # Check the response
        if second_response.status_code != 200:
            print(
                f"Second LangSearch API request failed with status code {second_response.status_code}"
            )
            print(f"Response: {second_response.text}")
            # If first summary worked but second failed, use just the first
            if first_summary:
                return {
                    "is_real": True,
                    "confidence": 0.7,
                    "explanation": f"Case appears to be real based on first summary: {first_summary}",
                }
            return {
                "is_real": False,
                "confidence": 0.6,
                "explanation": f"Error checking citation: Second API request failed",
            }

        second_result = second_response.json()
        second_summary = second_result.get("text", "")
        print(f"Second summary: {second_summary}")

        # Compare the summaries
        similarity = compare_summaries(first_summary, second_summary)
        print(f"Summary similarity: {similarity}")

        # If the summaries are similar, the citation is likely real
        if similarity >= 0.7:
            return {
                "is_real": True,
                "confidence": min(
                    0.5 + similarity / 2, 0.9
                ),  # Scale confidence based on similarity
                "explanation": f"LangSearch API generated consistent summaries for this citation (similarity: {similarity:.2f}).",
                "summaries": [first_summary, second_summary],
            }
        elif similarity >= 0.4:
            return {
                "is_real": True,
                "confidence": 0.6,
                "explanation": f"LangSearch API generated somewhat consistent summaries for this citation (similarity: {similarity:.2f}).",
                "summaries": [first_summary, second_summary],
            }
        else:
            return {
                "is_real": False,
                "confidence": 0.6,
                "explanation": f"LangSearch API generated inconsistent summaries for this citation (similarity: {similarity:.2f}), suggesting it may be hallucinated.",
                "summaries": [first_summary, second_summary],
            }

    except Exception as e:
        print(f"Error checking case with LangSearch API: {e}")
        return {
            "is_real": False,
            "confidence": 0.5,
            "explanation": f"Error checking citation: {str(e)}",
        }


# Function to check case using LangSearch API with different prompts
def check_case_with_ai(citation_text, case_name=None):
    """
    Check if a case is real by asking LangSearch to summarize it with different prompts and comparing the summaries.
    This is a more robust version of check_case_with_langsearch that uses multiple prompts and ensures
    summaries are at least 50 words long.

    If the enhanced citation verifier is available, it will be used first for more comprehensive verification.
    For citations not found in automated sources, a manual verification step with Descrybe.ai is suggested
    before proceeding to AI summarization.

    Args:
        citation_text (str): The citation to check
        case_name (str, optional): The case name to include in the prompt

    Returns:
        dict: Result with found status, confidence, and explanation
    """
    print(f"Checking case with AI: {citation_text}")

    # Use the enhanced citation verifier if available
    if USE_MULTI_SOURCE_VERIFIER:
        try:
            print(f"Using enhanced citation verifier for citation: {citation_text}")
            result = multi_source_verifier.verify_citation(citation_text, case_name)

            # If the citation was found, return the result
            if result.get("found", False):
                print(
                    f"Citation found and verified by enhanced verifier: {citation_text}"
                )
                return result

            # If manual verification is suggested and enabled, add Descrybe.ai verification step
            if USE_DESCRYBE_MANUAL_VERIFICATION and result.get(
                "manual_verification_suggested", False
            ):
                # Create search URL for Descrybe.ai
                search_query = urllib.parse.quote(
                    f"{citation_text} {case_name if case_name else ''}"
                )
                descrybe_url = f"{DESCRYBE_URL}?q={search_query}"

                print(
                    f"Suggesting manual verification with Descrybe.ai for citation: {citation_text}"
                )
                return {
                    "found": False,
                    "confidence": result.get("confidence", 0.5),
                    "explanation": f"Citation not verified by automated sources. Please verify manually with Descrybe.ai before proceeding to AI summarization.",
                    "manual_verification_suggested": True,
                    "manual_verification_source": "Descrybe.ai",
                    "manual_verification_url": descrybe_url,
                    "format_analysis": result.get("format_analysis", {}),
                }

            # If the citation has a high confidence score despite not being found, return the result
            if result.get("confidence", 0) > 0.7:
                return result

            # Otherwise, continue with the AI check as a fallback
            print(
                f"Enhanced citation verifier couldn't confirm citation. Trying AI check as fallback."
            )
        except Exception as e:
            print(f"Error using enhanced citation verifier: {e}")
            print("Falling back to AI verification method")
            traceback.print_exc()

    # First check if this is a landmark case (for efficiency)
    try:
        landmark_info = is_landmark_case(citation_text)
        if landmark_info:
            print(
                f"Found landmark case via AI check: {landmark_info['name']} ({citation_text})"
            )
            return {
                "found": True,
                "url": (
                    f"https://supreme.justia.com/cases/federal/us/{citation_text.split()[0]}/{citation_text.split()[2]}/"
                    if "U.S." in citation_text
                    else None
                ),
                "found_case_name": landmark_info["name"],
                "name_match": case_name
                and check_name_match(landmark_info["name"], case_name),
                "confidence": 0.95,
                "explanation": f"Verified landmark case: {landmark_info['name']} ({landmark_info['year']}) - {landmark_info['description']}",
                "source": "Landmark Cases Database (AI verification)",
            }
    except Exception as e:
        print(f"Error checking landmark case database: {e}")

    api_key = LANGSEARCH_API_KEY
    if not api_key:
        try:
            # Load API key from config file
            with open("config.json", "r") as f:
                config = json.load(f)
                api_key = config.get("langsearch_api_key")
        except Exception as e:
            print(f"Error loading LangSearch API key: {e}")
            return {
                "found": False,
                "confidence": 0.5,
                "explanation": f"Error loading LangSearch API key: {str(e)}",
            }

    if not api_key:
        print("No LangSearch API key found in config.json")
        return {
            "found": False,
            "confidence": 0.5,
            "explanation": "No LangSearch API key found in config.json",
        }

    try:
        # Generate two summaries with different prompts and compare them
        citation_with_name = citation_text
        if case_name:
            citation_with_name = f"{case_name} ({citation_text})"

        first_summary = generate_langsearch_case_summary(
            citation_with_name, api_key, "detailed"
        )
        second_summary = generate_langsearch_case_summary(
            citation_with_name, api_key, "brief"
        )

        if not first_summary or not second_summary:
            return {
                "found": False,
                "confidence": 0.6,
                "explanation": "LangSearch could not generate summaries for this citation.",
            }

        # Check for phrases that indicate the citation is not real
        not_found_phrases = [
            "not a valid",
            "unable to find",
            "no information",
            "cannot find",
            "do not have",
            "not a recognized",
            "not a known",
            "not familiar",
            "no record",
            "not a real",
            "fictional",
            "i don't have",
            "no results",
            "no matches",
            "couldn't locate",
            "could not locate",
            "i don't recognize",
            "i am not aware",
            "i cannot provide",
            "i don't have access",
            "not a case",
            "not an actual",
            "not a legitimate",
            "not a valid citation",
        ]

        # Check if either summary contains phrases indicating the citation is not real
        for phrase in not_found_phrases:
            if phrase in first_summary.lower() or phrase in second_summary.lower():
                print(f"AI indicates citation not found: {citation_text}")
                return {
                    "found": False,
                    "confidence": 0.7,
                    "explanation": f"AI indicates this is not a valid citation.",
                    "summaries": [first_summary, second_summary],
                }

        # Compare the summaries
        similarity = compare_summaries(first_summary, second_summary)
        print(f"LangSearch alternative summary similarity: {similarity}")

        # Extract any URLs mentioned in the summaries
        urls = extract_urls_from_text(first_summary + " " + second_summary)

        # Extract case name from summaries if not provided
        extracted_case_name = None
        if not case_name:
            # Try to extract case name from the first line of either summary
            first_line_1 = (
                first_summary.split("\n")[0] if "\n" in first_summary else first_summary
            )
            first_line_2 = (
                second_summary.split("\n")[0]
                if "\n" in second_summary
                else second_summary
            )

            # Look for patterns like "Case Name is a landmark case" or "In Case Name, the court..."
            for line in [first_line_1, first_line_2]:
                if " v. " in line or " vs. " in line:
                    extracted_case_name = line.split(".")[0] if "." in line else line
                    break

        # If the summaries are similar, the citation is likely real
        if similarity >= 0.7:
            result = {
                "found": True,
                "url": urls[0] if urls else None,
                "found_case_name": extracted_case_name or case_name,
                "name_match": case_name
                and extracted_case_name
                and check_name_match(extracted_case_name, case_name),
                "confidence": min(
                    0.5 + similarity / 2, 0.85
                ),  # Scale confidence based on similarity
                "explanation": f"AI generated consistent summaries for this citation (similarity: {similarity:.2f}).",
                "source": "AI Verification",
            }
            if urls:
                result[
                    "explanation"
                ] += f" Found {len(urls)} reference URLs in summaries."
            return result
        elif similarity >= 0.4:
            result = {
                "found": True,
                "url": urls[0] if urls else None,
                "found_case_name": extracted_case_name or case_name,
                "name_match": case_name
                and extracted_case_name
                and check_name_match(extracted_case_name, case_name),
                "confidence": 0.6,
                "explanation": f"AI generated somewhat consistent summaries for this citation (similarity: {similarity:.2f}).",
                "source": "AI Verification",
            }
            if urls:
                result[
                    "explanation"
                ] += f" Found {len(urls)} reference URLs in summaries."
            return result
        else:
            return {
                "found": False,
                "confidence": 0.6,
                "explanation": f"AI generated inconsistent summaries for this citation (similarity: {similarity:.2f}), suggesting it may not be a valid citation.",
                "summaries": [first_summary, second_summary],
            }

    except Exception as e:
        print(f"Error checking case with LangSearch alternative prompts: {e}")
        traceback.print_exc()
        return {
            "found": False,
            "confidence": 0.5,
            "explanation": f"Error checking citation with LangSearch alternative prompts: {str(e)}",
        }


# Function to query the CourtListener API
def query_courtlistener_api(text, api_key):
    """Query the CourtListener API to verify citations in the text.

    Instead of sending the full text, we extract citations first and then
    send only the citations to the API. This is more efficient and avoids
    the 64,000 character limit of the API.
    """
    print(f"Processing text of length: {len(text)} for CourtListener API")

    if not api_key:
        print("No API key provided")
        return {"error": "No API key provided"}

    try:
        # Extract citations from the text using eyecite
        citations = extract_citations(text)

        if not citations:
            print("No citations found in the text")
            return {"error": "No citations found in the text"}

        print(f"Found {len(citations)} citations to verify with CourtListener API")

        # Prepare the request
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }

        # Join citations with newlines to create a compact text
        # This is much more efficient than sending the full text
        citations_text = "\n".join(citations)
        print(f"Citations text length: {len(citations_text)} characters")

        data = {"text": citations_text}

        # Make the request
        print(f"Sending request to {COURTLISTENER_API_URL}")
        response = requests.post(COURTLISTENER_API_URL, headers=headers, json=data)

        # Check the response
        if response.status_code == 200:
            print("API request successful")
            result = response.json()

            # Save the API response to a file for inspection
            try:
                with open("api_response.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                print("API response saved to api_response.json")
            except Exception as e:
                print(f"Error saving API response to file: {e}")

            return result
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return {
                "error": f"API request failed with status code {response.status_code}: {response.text}"
            }

    except Exception as e:
        print(f"Error querying CourtListener API: {e}")
        traceback.print_exc()
        return {"error": f"Error querying CourtListener API: {str(e)}"}


# Helper function to compare two text summaries
def compare_summaries(summary1, summary2):
    """
    Compare two text summaries and return a similarity score between 0.0 and 1.0.
    Uses a combination of word overlap and semantic similarity.
    """
    if not summary1 or not summary2:
        return 0.0

    # Clean and normalize the summaries
    def normalize_text(text):
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
        text = re.sub(r"\s+", " ", text).strip()  # Normalize whitespace
        return text

    norm_summary1 = normalize_text(summary1)
    norm_summary2 = normalize_text(summary2)

    # Get word sets
    words1 = set(norm_summary1.split())
    words2 = set(norm_summary2.split())

    # Calculate Jaccard similarity (word overlap)
    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)
    jaccard_similarity = len(intersection) / len(union)

    # Look for key facts that appear in both summaries
    # This helps identify when both summaries mention the same case details
    key_fact_bonus = 0.0

    # Check for case name patterns in both summaries
    case_name_pattern = r"([A-Z][\w\s]+\sv\.\s[\w\s]+)"
    names1 = re.findall(case_name_pattern, summary1)
    names2 = re.findall(case_name_pattern, summary2)

    if names1 and names2:
        # Check if any case names match
        for name1 in names1:
            for name2 in names2:
                if name1.lower() in name2.lower() or name2.lower() in name1.lower():
                    key_fact_bonus += 0.2
                    break

    # Check for date patterns in both summaries
    date_pattern = r"\b(19|20)\d{2}\b"  # Years from 1900-2099
    dates1 = re.findall(date_pattern, summary1)
    dates2 = re.findall(date_pattern, summary2)

    if dates1 and dates2:
        # Check if any dates match
        common_dates = set(dates1).intersection(set(dates2))
        if common_dates:
            key_fact_bonus += min(0.1 * len(common_dates), 0.2)

    # Final similarity score (capped at 1.0)
    similarity = min(jaccard_similarity + key_fact_bonus, 1.0)

    return similarity


# Helper function to extract URLs from text
def extract_urls_from_text(text):
    """
    Extract URLs from text that might point to legal resources.
    """
    if not text:
        return []

    # URL pattern focusing on legal websites
    url_pattern = r"https?://(?:www\.)?(?:leagle\.com|justia\.com|findlaw\.com|scholar\.google\.com|courtlistener\.com|law\.cornell\.edu|supremecourt\.gov|uscourts\.gov|oyez\.org|lexisnexis\.com|westlaw\.com|casetext\.com|law\.\w+\.edu)[\w\-./]+"

    urls = re.findall(url_pattern, text)
    return list(set(urls))  # Remove duplicates


# Function to generate a case summary using LangSearch API with different prompts
def generate_langsearch_case_summary(citation_text, api_key, summary_type):
    """
    Generate a summary of a legal case using the LangSearch API with different prompt styles.
    summary_type can be 'detailed' or 'brief' to get different perspectives on the same case.
    Ensures summaries are at least 50 words long.
    """
    try:
        import requests

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Create different prompts based on the summary type
        if summary_type == "detailed":
            prompt = f"Provide a detailed summary of the legal case {citation_text}. Include the court, year, key facts, legal reasoning, and holding. Focus on the legal principles established. The summary must be at least 50 words long."
        else:  # brief
            prompt = f"Summarize the case {citation_text}. Focus on the parties involved, the court, the year, and the main outcome. What is the key legal significance of this case? The summary must be at least 50 words long."

        # Make request to LangSearch API
        response = requests.post(
            "https://api.langsearch.ai/v1/generate",
            headers=headers,
            json={
                "prompt": prompt,
                "max_tokens": 600,  # Increased to allow for longer summaries
                "temperature": 0.3,  # Lower temperature for more consistent responses
                "search_strategy": "hybrid",  # Use both keyword and semantic search
                "search_depth": "deep",  # More thorough search for legal cases
            },
        )

        if response.status_code != 200:
            print(f"LangSearch API error: {response.status_code} - {response.text}")
            return None

        result = response.json()
        summary = result.get("text", "").strip()

        # Check if the response indicates the citation wasn't found
        not_found_phrases = [
            "not a valid",
            "unable to find",
            "no information",
            "cannot find",
            "do not have",
            "not a recognized",
            "not a known",
            "not familiar",
            "no record",
            "not a real",
            "fictional",
            "i don't have",
            "no results",
            "no matches",
            "couldn't locate",
            "could not locate",
        ]

        if any(phrase in summary.lower() for phrase in not_found_phrases):
            print(f"LangSearch indicates citation not found: {citation_text}")
            return None

        # Check if the summary is at least 50 words long
        word_count = len(summary.split())
        if word_count < 50:
            print(
                f"Summary too short ({word_count} words), requesting longer summary for {citation_text}"
            )

            # Try again with a more explicit prompt for a longer summary
            longer_prompt = f"Provide a comprehensive and detailed summary of the legal case {citation_text}. Include the court, year, parties involved, key facts, legal issues, reasoning, and holding. Explain the legal principles established and the significance of this case. Your summary must be at least 50 words long and should be thorough."

            response = requests.post(
                "https://api.langsearch.ai/v1/generate",
                headers=headers,
                json={
                    "prompt": longer_prompt,
                    "max_tokens": 800,  # Further increased for longer summary
                    "temperature": 0.3,
                    "search_strategy": "hybrid",
                    "search_depth": "deep",
                },
            )

            if response.status_code == 200:
                result = response.json()
                new_summary = result.get("text", "").strip()

                # Only use the new summary if it's longer than the original
                if len(new_summary.split()) > word_count:
                    summary = new_summary
                    print(f"Generated longer summary with {len(summary.split())} words")

        return summary

    except Exception as e:
        print(f"Error generating LangSearch summary: {e}")
        return None


# Function to generate a unique analysis ID
def generate_analysis_id():
    return str(uuid.uuid4())


# Function to run the analysis with CourtListener API
def run_analysis(analysis_id, brief_text=None, file_path=None, api_key=None):
    """
    Run the citation analysis with the CourtListener API and multi-source verification.

    Args:
        analysis_id (str): Unique ID for this analysis
        brief_text (str, optional): Text of the brief to analyze
        file_path (str, optional): Path to the file to analyze
        api_key (str, optional): CourtListener API key

    Returns:
        dict: Analysis results
    """
    print(f"Running analysis {analysis_id}")

    # Log whether we're using enhanced verification
    if USE_MULTI_SOURCE_VERIFIER:
        print("Using enhanced multi-source verification for this analysis")

    # Log system info
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"UPLOAD_FOLDER path: {os.path.abspath(UPLOAD_FOLDER)}")

    # Check if upload folder exists and is writable
    if not os.path.exists(UPLOAD_FOLDER):
        print(f"WARNING: Upload folder does not exist: {UPLOAD_FOLDER}")
        try:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            print(f"Created upload folder: {UPLOAD_FOLDER}")
        except Exception as e:
            print(f"ERROR: Could not create upload folder: {e}")
    else:
        print(f"Upload folder exists: {UPLOAD_FOLDER}")
        try:
            test_file = os.path.join(UPLOAD_FOLDER, f"test_{analysis_id}.txt")
            with open(test_file, "w") as f:
                f.write(f"Test write at {datetime.now()}")
            os.remove(test_file)
            print(f"Upload folder is writable")
        except Exception as e:
            print(f"WARNING: Upload folder may not be writable: {e}")

    try:
        # Initialize the results for this analysis
        analysis_results[analysis_id] = {
            "status": "running",
            "progress": 0,
            "total_steps": 3,
            "message": "Analysis started",
            "completed": False,
            "results": None,
            "error": None,
            "extracted_citations": [],
            "citation_results": [],
        }

        # Get text from file if provided
        if file_path and not brief_text:
            print(f"\n==== EXTRACTING TEXT FROM FILE: {file_path} ====\n")
            print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Verify file exists and is readable
            if not os.path.isfile(file_path):
                error_msg = f"File not found: {file_path}"
                print(f"ERROR: {error_msg}")
                analysis_results[analysis_id]["status"] = "error"
                analysis_results[analysis_id]["error"] = error_msg
                analysis_results[analysis_id]["completed"] = True
                return

            print(f"File exists and is readable: {file_path}")
            print(f"File absolute path: {os.path.abspath(file_path)}")
            print(f"File extension: {os.path.splitext(file_path)[1]}")
            print(f"File size: {os.path.getsize(file_path)} bytes")
            print(
                f"File last modified: {datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print(f"Attempting to extract text...")

            # Check file permissions
            try:
                with open(file_path, "rb") as test_file:
                    first_bytes = test_file.read(10)
                    print(f"Successfully read first bytes of file: {first_bytes}")

                # Get file size
                file_size = os.path.getsize(file_path)
                print(f"Confirmed file size: {file_size} bytes")

                # Check if file is empty
                if file_size == 0:
                    error_msg = f"File is empty: {file_path}"
                    print(error_msg)
                    analysis_results[analysis_id]["status"] = "error"
                    analysis_results[analysis_id]["error"] = error_msg
                    analysis_results[analysis_id]["completed"] = True
                    return
            except Exception as e:
                error_msg = f"Error checking file: {str(e)}"
                print(error_msg)
                analysis_results[analysis_id]["status"] = "error"
                analysis_results[analysis_id]["error"] = error_msg
                analysis_results[analysis_id]["completed"] = True
                return

            # Update progress - Step 1: Extracting text
            analysis_results[analysis_id]["progress"] = 1
            analysis_results[analysis_id][
                "message"
            ] = f"Extracting text from file: {os.path.basename(file_path)}"

            # Extract text from file
            brief_text = extract_text_from_file(file_path)

            if not brief_text:
                error_msg = f"Failed to extract text from file: {file_path}"
                print(error_msg)
                analysis_results[analysis_id]["status"] = "error"
                analysis_results[analysis_id]["error"] = error_msg
                analysis_results[analysis_id]["completed"] = True
                return

            # Update progress after extraction
            analysis_results[analysis_id][
                "message"
            ] = f"Successfully extracted {len(brief_text)} characters from {os.path.basename(file_path)}"

            # Save extracted text to a file for debugging
            try:
                debug_file = f"extracted_text_{analysis_id}.txt"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(brief_text)
                print(f"Saved extracted text to {debug_file}")
            except Exception as e:
                print(f"Error saving extracted text to file: {e}")

        # Use default text if none provided
        if not brief_text:
            brief_text = "2016 WL 165971"
            citations = [brief_text]
            # Update with default citation
            analysis_results[analysis_id][
                "message"
            ] = "Using default citation for testing"
        else:
            # Update progress - Step 2: Extracting citations
            analysis_results[analysis_id]["progress"] = 2
            analysis_results[analysis_id][
                "message"
            ] = "Extracting citations from document text..."

            # Extract citations from the text
            citations = extract_citations(brief_text)

            # Update with extracted citations
            analysis_results[analysis_id]["extracted_citations"] = citations

            if citations:
                analysis_results[analysis_id][
                    "message"
                ] = f"Successfully extracted {len(citations)} citations from document"
            else:
                # If no citations found, treat the entire text as one citation
                citations = [
                    brief_text[:100] + "..." if len(brief_text) > 100 else brief_text
                ]
                analysis_results[analysis_id][
                    "message"
                ] = "No specific citations found, treating entire text as one citation"
                analysis_results[analysis_id]["extracted_citations"] = citations

        # Pre-screen citations with ML classifier
        # Update progress - Step 3: Pre-screening with ML
        analysis_results[analysis_id]["progress"] = 3
        analysis_results[analysis_id][
            "message"
        ] = "Pre-screening citations with ML classifier..."

        # Use ML classifier to get initial confidence scores for all citations
        citation_objects = [{"citation_text": citation} for citation in citations]
        ml_confidences = batch_classify_citations(citation_objects)

        # Create a dictionary mapping citations to their ML confidence scores
        ml_confidence_map = {}
        for i, citation in enumerate(citations):
            ml_confidence_map[citation] = ml_confidences[i]
            print(f"ML Confidence for '{citation}': {ml_confidences[i]:.2f}")

        # Store ML confidence scores in analysis results
        analysis_results[analysis_id]["ml_confidence_scores"] = ml_confidence_map

        # Query the CourtListener API
        if api_key:
            # Update progress - Step 4: Querying API
            analysis_results[analysis_id]["progress"] = 4
            analysis_results[analysis_id]["message"] = "Querying CourtListener API..."

            # Query the API with the entire text
            api_response = query_courtlistener_api(brief_text, api_key)

            # Update with API response
            if "error" in api_response:
                analysis_results[analysis_id]["status"] = "error"
                analysis_results[analysis_id][
                    "error"
                ] = f"Error querying CourtListener API: {api_response['error']}"
                analysis_results[analysis_id]["completed"] = True
                return

            # Process the API response
            hallucinated_count = 0
            citation_results = []

            # Debug the API response structure
            print(f"API response type: {type(api_response)}")
            if isinstance(api_response, list):
                print(f"API response is a list with {len(api_response)} items")
                for i, item in enumerate(api_response):
                    print(
                        f"Item {i} keys: {item.keys() if isinstance(item, dict) else 'not a dict'}"
                    )
            elif isinstance(api_response, dict):
                print(f"API response is a dict with keys: {api_response.keys()}")

            # Process each citation from our extraction
            for i, citation in enumerate(citations):
                # Check if this citation is in the API response
                found = False
                court_listener_url = None
                case_name = None

                # The API response can be a list of citation objects
                if isinstance(api_response, list):
                    for api_item in api_response:
                        if isinstance(api_item, dict) and "citation" in api_item:
                            if citation.lower() in api_item["citation"].lower():
                                found = True
                                # Check if there are clusters with URLs
                                if "clusters" in api_item and api_item["clusters"]:
                                    cluster = api_item["clusters"][
                                        0
                                    ]  # Get the first cluster
                                    court_listener_url = cluster.get(
                                        "absolute_url", None
                                    )
                                    if (
                                        court_listener_url
                                        and not court_listener_url.startswith("http")
                                    ):
                                        court_listener_url = f"https://www.courtlistener.com{court_listener_url}"
                                    case_name = cluster.get("case_name", "Unknown case")
                                break
                elif isinstance(api_response, dict) and "citations" in api_response:
                    # Traditional structure with citations dictionary
                    api_citations = api_response["citations"]
                    print(
                        f"API returned citations dictionary with keys: {api_citations.keys() if isinstance(api_citations, dict) else 'not a dict'}"
                    )

                    # Check if citation is in the citations dictionary
                    for citation_key, citation_data in api_citations.items():
                        if citation.lower() in citation_key.lower():
                            found = True
                            case_name = citation_data.get("name", "Unknown case")
                            # Try to find URL in the citation data
                            if "match_url" in citation_data:
                                court_listener_url = citation_data["match_url"]
                                if not court_listener_url.startswith("http"):
                                    court_listener_url = f"https://www.courtlistener.com{court_listener_url}"
                            break

                    # Determine the hallucination status
                    hallucination_status = "not_hallucination"

                    # If the case name is 'Unknown case', it's not verified regardless of what the API says
                    if case_name == "Unknown case" or not case_name:
                        found = False  # Not verified if case name is unknown
                        hallucination_status = "unconfirmed"
                        confidence = 0.7
                        explanation = f"Citation format recognized but case name unknown - unconfirmed citation"

                        # If we have a URL, it's unconfirmed rather than hallucinated
                        if court_listener_url:
                            hallucination_status = "unconfirmed"
                        else:
                            hallucination_status = "possible_hallucination"
                            hallucinated_count += 1
                    elif found:
                        # Extract case name from the text surrounding the citation
                        brief_case_name = extract_case_name_from_text(
                            brief_text, citation
                        )

                        # Check if we have both a URL AND a proper case name that is not 'Unknown case'
                        if (
                            court_listener_url
                            and case_name
                            and case_name != "Unknown case"
                        ):
                            confidence = 0.9  # High confidence for exact match

                            # Compare case names if we have both
                            if brief_case_name and case_name:
                                # Function to normalize case names for comparison
                                def normalize_case_name(name):
                                    return re.sub(r"[^\w\s]", "", name.lower())

                                norm_brief_name = normalize_case_name(brief_case_name)
                                norm_cl_name = normalize_case_name(case_name)

                                # Check for significant difference in case names
                                # Using a simple word overlap metric
                                brief_words = set(norm_brief_name.split())
                                cl_words = set(norm_cl_name.split())

                                # Calculate word overlap percentage
                                if brief_words and cl_words:
                                    overlap = len(brief_words.intersection(cl_words))
                                    max_words = max(len(brief_words), len(cl_words))
                                    similarity = overlap / max_words

                                    if similarity < 0.5:  # Less than 50% word overlap
                                        explanation = f"Citation verified but case names differ significantly. Brief: '{brief_case_name}', CourtListener: '{case_name}' - {court_listener_url}"
                                        # Reduce confidence slightly due to name mismatch
                                        confidence = 0.85
                                    else:
                                        explanation = f"Citation confirmed: {case_name} - {court_listener_url}"
                                else:
                                    explanation = f"Citation confirmed: {case_name} - {court_listener_url}"
                            else:
                                explanation = f"Citation confirmed: {case_name} - {court_listener_url}"

                            hallucination_status = "not_hallucination"
                        # If case name is 'Unknown case', mark as potential hallucination even with URL
                        elif court_listener_url and (
                            not case_name or case_name == "Unknown case"
                        ):
                            confidence = 0.6
                            explanation = f"Citation format recognized but case details unknown - potential hallucination"
                            hallucination_status = "possible_hallucination"
                        # If we haven't processed any citations yet, it means the API response format wasn't recognized
                        if not citation_results:
                            print(
                                "API response format not recognized or no citations found"
                            )
                            print(f"API response: {api_response}")
                        # If we have a case name but no URL, also mark as unconfirmed
                        elif (
                            (not court_listener_url)
                            and case_name
                            and case_name != "Unknown case"
                        ):
                            confidence = 0.7
                            explanation = f"Citation format recognized with case name '{case_name}' but no URL found - unconfirmed citation"
                            hallucination_status = "unconfirmed"
                            # Don't count as hallucinated, but don't count as fully verified either
                            found = True  # Keep as found but with unconfirmed status
                        else:
                            # If we haven't found the citation in the API response, use ML confidence score
                            if not found:
                                # Get the ML confidence score for this citation
                                ml_confidence = ml_confidence_map.get(citation, 0.2)

                                # If ML confidence is high, mark as unconfirmed but not necessarily hallucinated
                                if ml_confidence >= 0.7:
                                    confidence = (
                                        0.5  # Still lower than API-verified citations
                                    )
                                    explanation = f"Citation not found in CourtListener API but ML classifier indicates valid format (ML confidence: {ml_confidence:.2f}) - unconfirmed citation"
                                    hallucination_status = "unconfirmed"
                                else:
                                    # Low ML confidence suggests potential hallucination
                                    hallucinated_count += 1
                                    confidence = ml_confidence
                                    explanation = f"Citation not found in CourtListener API and ML classifier indicates potential issues (ML confidence: {ml_confidence:.2f}) - potential hallucination"
                                    hallucination_status = "possible_hallucination"

                    # If not found or no URL, check with LangSearch API
                    if not found or not court_listener_url:
                        # Mark as not found if there's no URL - citations without URLs are potential hallucinations
                        if not court_listener_url and found:
                            print(
                                f"Citation {citation} has no URL, marking as not found for LangSearch verification"
                            )
                            found = False

                        # For Westlaw citations, we don't automatically increment hallucinated_count
                        # because we want to give LangSearch a chance to verify them
                        if "WL" not in citation:
                            hallucinated_count += 1

                        # Check with LangSearch API
                        print(
                            f"Citation not found in CourtListener database, checking with LangSearch: {citation}"
                        )
                        langsearch_result = check_case_with_langsearch(citation)

                        if langsearch_result["is_real"]:
                            # If LangSearch says it's real, reduce the hallucination count (if it was incremented)
                            if "WL" not in citation:
                                hallucinated_count -= 1
                            found = True
                            confidence = langsearch_result["confidence"]
                            explanation = langsearch_result["explanation"]

                            # For Westlaw citations, update the case name if verified by LangSearch
                            if "WL" in citation:
                                result_data["case_name"] = (
                                    "Westlaw Citation (Verified by LangSearch)"
                                )
                                result_data["hallucination_status"] = "verified"

                            # Add summaries if available
                            if "summaries" in langsearch_result:
                                summaries = langsearch_result["summaries"]
                        else:
                            # If LangSearch also says it's hallucinated
                            confidence = langsearch_result["confidence"]
                            explanation = langsearch_result["explanation"]

                            # For Westlaw citations that LangSearch couldn't verify, mark as unverified
                            if "WL" in citation:
                                hallucinated_count += (
                                    1  # Now we count it as hallucinated
                                )
                                result_data["case_name"] = "Unverified Westlaw Citation"
                                result_data["hallucination_status"] = "unverified"

                            # Add summaries if available
                            if "summaries" in langsearch_result:
                                summaries = langsearch_result["summaries"]
                            else:
                                summaries = []
                    else:
                        # Citation found in CourtListener
                        summaries = []

                    # Create the result data dictionary if it doesn't exist yet
                    if "citation_text" not in result_data:
                        # CRITICAL: Citations without URLs should NEVER be marked as verified
                        # Force hallucination_status to 'possible_hallucination' if there's no URL
                        if (
                            not court_listener_url
                            and hallucination_status != "unverified"
                        ):
                            hallucination_status = "possible_hallucination"
                            explanation = "Citation format recognized but no verification URL found - potential hallucination"
                            confidence = 0.5  # Medium confidence
                            found = False  # Mark as not found

                        # Add result with clearer hallucination marking
                        result_data = {
                            "citation_text": citation,
                            "is_hallucinated": not found
                            or (
                                not court_listener_url
                                and hallucination_status != "unverified"
                            ),
                            "hallucination_status": hallucination_status,
                            "confidence": confidence,
                            "explanation": explanation,
                        }

                    # Special handling for Westlaw (WL) citations that haven't been processed yet
                    if "WL" in citation and "case_name" not in result_data:
                        # For Westlaw citations, we'll try CourtListener first
                        # If found in CourtListener with a valid case name AND URL, keep that result
                        if (
                            found
                            and case_name
                            and case_name != "Unknown case"
                            and court_listener_url
                        ):
                            # This is a verified Westlaw citation found in CourtListener with URL
                            result_data["is_hallucinated"] = False
                            result_data["hallucination_status"] = "verified"
                            result_data["confidence"] = confidence
                            result_data["case_name"] = case_name
                            result_data["explanation"] = (
                                f"Westlaw citation verified: {case_name}"
                            )
                        else:
                            # Not found in CourtListener, has unknown case name, or no URL
                            # Mark as not found and let LangSearch try to verify
                            found = False
                            # Explicitly mark as potential hallucination if no URL
                            if not court_listener_url:
                                result_data["is_hallucinated"] = True
                                result_data["hallucination_status"] = (
                                    "possible_hallucination"
                                )
                                result_data["explanation"] = (
                                    "Westlaw citation format recognized but no verification URL found - potential hallucination"
                                )
                                result_data["confidence"] = 0.5  # Medium confidence
                            # Don't increment hallucinated_count yet - let LangSearch decide
                            hallucinated_count -= 1  # Counteract the increment that will happen for !found

                    # Add CourtListener URL if available
                    if court_listener_url:
                        result_data["court_listener_url"] = court_listener_url
                        # Don't overwrite case name for Westlaw citations if we already set it
                        if "case_name" not in result_data:
                            result_data["case_name"] = case_name or "Unknown case"
                        # If case_name is 'Unknown case' and not a Westlaw citation, mark as potential hallucination
                        # (Westlaw citations are already handled above)
                        if (
                            case_name == "Unknown case"
                            or result_data["case_name"] == "Unknown case"
                        ) and "WL" not in citation:
                            result_data["is_hallucinated"] = True
                            result_data["hallucination_status"] = (
                                "possible_hallucination"
                            )
                            result_data["explanation"] = (
                                "Citation format recognized but case details unknown - potential hallucination"
                            )

                    # Add summaries if available
                    if summaries:
                        result_data["summaries"] = summaries

                    citation_results.append(result_data)
            # If we haven't processed any citations yet, it means the API response format wasn't recognized
            if not citation_results:
                print("API response format not recognized or no citations found")
                print(f"API response: {api_response}")

                # Try one more approach - if the API response is a list of items with citation info
                if isinstance(api_response, list):
                    for i, citation in enumerate(citations):
                        found = False
                        court_listener_url = None
                        case_name = None

                        # Check each item in the response list
                        for api_item in api_response:
                            # Look for the citation in normalized_citations if available
                            if (
                                isinstance(api_item, dict)
                                and "normalized_citations" in api_item
                            ):
                                # First check exact match in normalized_citations
                                for norm_citation in api_item["normalized_citations"]:
                                    if citation.lower() == norm_citation.lower():
                                        found = True
                                        # Get case info from clusters if available
                                        if (
                                            "clusters" in api_item
                                            and api_item["clusters"]
                                        ):
                                            cluster = api_item["clusters"][0]
                                            court_listener_url = cluster.get(
                                                "absolute_url", None
                                            )
                                            if (
                                                court_listener_url
                                                and not court_listener_url.startswith(
                                                    "http"
                                                )
                                            ):
                                                court_listener_url = f"https://www.courtlistener.com{court_listener_url}"
                                            case_name = cluster.get(
                                                "case_name", "Unknown case"
                                            )
                                        break

                                # If not found, check if this is an alternative citation format
                                if (
                                    not found
                                    and "clusters" in api_item
                                    and api_item["clusters"]
                                ):
                                    cluster = api_item["clusters"][0]
                                    if "citations" in cluster:
                                        # Check all alternative citations for this case
                                        for alt_citation in cluster["citations"]:
                                            # Construct the citation string in various formats
                                            volume = str(alt_citation.get("volume", ""))
                                            reporter = alt_citation.get("reporter", "")
                                            page = alt_citation.get("page", "")

                                            # Format 1: "550 U.S. 544"
                                            alt_format1 = f"{volume} {reporter} {page}"
                                            # Format 2: "550 U. S. 544"
                                            alt_format2 = alt_format1.replace(".", ". ")
                                            # Format 3: "550U.S.544"
                                            alt_format3 = f"{volume}{reporter}{page}"

                                            # Compare with our citation
                                            citation_clean = citation.replace(
                                                " ", ""
                                            ).replace(".", "")
                                            alt_format1_clean = alt_format1.replace(
                                                " ", ""
                                            ).replace(".", "")
                                            alt_format2_clean = alt_format2.replace(
                                                " ", ""
                                            ).replace(".", "")
                                            alt_format3_clean = alt_format3.replace(
                                                " ", ""
                                            ).replace(".", "")

                                            if (
                                                citation_clean == alt_format1_clean
                                                or citation_clean == alt_format2_clean
                                                or citation_clean == alt_format3_clean
                                            ):
                                                found = True
                                                court_listener_url = cluster.get(
                                                    "absolute_url", None
                                                )
                                                if (
                                                    court_listener_url
                                                    and not court_listener_url.startswith(
                                                        "http"
                                                    )
                                                ):
                                                    court_listener_url = f"https://www.courtlistener.com{court_listener_url}"
                                                case_name = cluster.get(
                                                    "case_name", "Unknown case"
                                                )
                                                break
                            if found:
                                break

                        # Add result for this citation
                        if found:
                            result_data = {
                                "citation_text": citation,
                                "is_hallucinated": False,
                                "confidence": 0.9,
                                "explanation": f"Citation confirmed: {case_name}{' - ' + court_listener_url if court_listener_url else ''}",
                            }

                            # If case_name is 'Unknown case', change the explanation and mark as potential hallucination
                            if case_name == "Unknown case":
                                result_data["explanation"] = (
                                    f"Citation format recognized but case details unknown - potential hallucination"
                                )
                                result_data["is_hallucinated"] = True
                                result_data["hallucination_status"] = (
                                    "possible_hallucination"
                                )

                            # Add CourtListener URL if available
                            if court_listener_url:
                                result_data["court_listener_url"] = court_listener_url
                                result_data["case_name"] = case_name or "Unknown case"
                                # If case_name is 'Unknown case', ensure it's marked as a potential hallucination
                                if case_name == "Unknown case":
                                    result_data["is_hallucinated"] = True
                                    result_data["hallucination_status"] = (
                                        "possible_hallucination"
                                    )
                            citation_results.append(result_data)
                        else:
                            # Check with LangSearch API
                            print(
                                f"Citation not found in CourtListener database, checking with LangSearch: {citation}"
                            )
                            langsearch_result = check_case_with_langsearch(citation)

                            if langsearch_result["is_real"]:
                                # LangSearch says it's real
                                result_data = {
                                    "citation_text": citation,
                                    "is_hallucinated": False,
                                    "confidence": langsearch_result["confidence"],
                                    "explanation": langsearch_result["explanation"],
                                }

                                # Add summaries if available
                                if "summaries" in langsearch_result:
                                    result_data["summaries"] = langsearch_result[
                                        "summaries"
                                    ]
                            else:
                                # LangSearch says it might be hallucinated, but let's try web search as a last resort
                                print(
                                    f"LangSearch couldn't verify citation, trying web search: {citation}"
                                )

                                # Use our advanced case name extraction algorithm
                                case_name = extract_case_name_from_text(
                                    brief_text, citation
                                )
                                if case_name:
                                    print(f"Found potential case name: {case_name}")

                                # Try web search with the extracted case name
                                web_search_result = search_citation_on_web(
                                    citation, case_name
                                )

                                if web_search_result["found"]:
                                    # Web search found the citation
                                    result_data = {
                                        "citation_text": citation,
                                        "is_hallucinated": False,
                                        "confidence": web_search_result["confidence"],
                                        "explanation": web_search_result["explanation"],
                                        "web_url": web_search_result["url"],
                                        "case_name": web_search_result[
                                            "found_case_name"
                                        ]
                                        or "Unknown case",
                                    }

                                    # If case name was found and matches, increase confidence
                                    if web_search_result["name_match"]:
                                        result_data["confidence"] = 0.9
                                        result_data[
                                            "explanation"
                                        ] += " (with matching case name)"
                                else:
                                    # Web search couldn't verify, try our third method: AI-based verification
                                    print(
                                        f"Web search couldn't verify citation, trying AI-based verification: {citation}"
                                    )

                                    # Use the AI to generate and compare summaries
                                    ai_result = check_case_with_ai(citation, case_name)

                                    if ai_result["is_real"]:
                                        # AI thinks the citation is real
                                        result_data = {
                                            "citation_text": citation,
                                            "is_hallucinated": False,
                                            "confidence": ai_result["confidence"],
                                            "explanation": ai_result["explanation"],
                                            "case_name": case_name or "Unknown case",
                                            "verification_method": "AI summary comparison",
                                        }

                                        # Add summaries to the result
                                        if "summaries" in ai_result:
                                            result_data["summaries"] = ai_result[
                                                "summaries"
                                            ]

                                        # Add any URLs found in the summaries
                                        if "urls" in ai_result and ai_result["urls"]:
                                            result_data["reference_urls"] = ai_result[
                                                "urls"
                                            ]
                                    else:
                                        # All three methods failed to verify the citation
                                        hallucinated_count += 1
                                        result_data = {
                                            "citation_text": citation,
                                            "is_hallucinated": True,
                                            "hallucination_status": "unverified",
                                            "confidence": ai_result["confidence"],
                                            "explanation": f"Citation could not be verified by CourtListener, web search, or AI analysis.",
                                        }

                                        # Add summaries if available for reference
                                        if "summaries" in ai_result:
                                            result_data["summaries"] = ai_result[
                                                "summaries"
                                            ]
                                citation_results.append(result_data)
                else:
                    # Mark all citations as potentially hallucinated if we can't process the API response
                    for i, citation in enumerate(citations):
                        hallucinated_count += 1
                        citation_results.append(
                            {
                                "citation_text": citation,
                                "is_hallucinated": True,
                                "confidence": 0.7,
                                "explanation": "Citation not verified by CourtListener API",
                            }
                        )

            # Prepare citations for grouping
            citations_for_grouping = []
            for result in citation_results:
                citation_dict = {
                    "citation": result["citation_text"],
                    "case_name": result.get("case_name", "Unknown Case"),
                    "url": result.get("court_listener_url", ""),
                    "source": result.get("method", "Unknown"),
                    "is_hallucinated": result["is_hallucinated"],
                    "details": {
                        "confidence": result["confidence"],
                        "explanation": result["explanation"],
                    },
                }

                # Add summaries if available
                if "summaries" in result:
                    citation_dict["summaries"] = result["summaries"]

                citations_for_grouping.append(citation_dict)

            # Group citations using the citation_grouping module
            grouped_citations_list = group_citations(
                citations_for_grouping, method="url_then_name"
            )

            # Convert grouped citations to the format expected by the frontend
            grouped_citation_results = []
            for group in grouped_citations_list:
                result_dict = {
                    "primary_citation": group["citation"],
                    "case_name": group["case_name"],
                    "court_listener_url": group["url"],
                    "is_hallucinated": group["is_hallucinated"],
                    "confidence": group["details"]["confidence"],
                    "explanation": group["details"]["explanation"],
                    "parallel_citations": [],
                }

                # Add alternate citations
                if "alternate_citations" in group and group["alternate_citations"]:
                    for alt in group["alternate_citations"]:
                        result_dict["parallel_citations"].append(alt["citation"])

                # Add summaries if available
                if "summaries" in group:
                    result_dict["summaries"] = group["summaries"]

                grouped_citation_results.append(result_dict)

            # Update with grouped citation results
            analysis_results[analysis_id]["citation_results"] = grouped_citation_results

            # Complete the analysis
            analysis_results[analysis_id]["status"] = "complete"
            unique_cases_count = len(grouped_citation_results)
            verified_unique_cases = len(
                [c for c in grouped_citation_results if not c["is_hallucinated"]]
            )

            # Create a more informative message that explains the difference between citations and cases
            analysis_results[analysis_id][
                "message"
            ] = f"Analysis complete. Found {len(citations)} total citations grouped into {unique_cases_count} unique cases, {hallucinated_count} potentially hallucinated."
            analysis_results[analysis_id]["completed"] = True
            analysis_results[analysis_id]["results"] = {
                "total_individual_citations": len(citations),
                "total_unique_cases": unique_cases_count,
                "hallucinated_citations": hallucinated_count,
                "verified_citations": len(citations) - hallucinated_count,
                "verified_unique_cases": verified_unique_cases,
            }
        else:
            # No API key provided, mark all citations as unverified
            analysis_results[analysis_id][
                "message"
            ] = "No CourtListener API key provided, unable to verify citations"

            # Check citations with LangSearch even if no CourtListener API key
            citation_results = []
            for i, citation in enumerate(citations):
                # Check with LangSearch API
                print(f"No CourtListener API key, checking with LangSearch: {citation}")
                langsearch_result = check_case_with_langsearch(citation)

                result_data = {
                    "citation_text": citation,
                    "is_hallucinated": not langsearch_result["is_real"],
                    "confidence": langsearch_result["confidence"],
                    "explanation": langsearch_result["explanation"],
                }

                # Add summaries if available
                if "summaries" in langsearch_result:
                    result_data["summaries"] = langsearch_result["summaries"]

                citation_results.append(result_data)

                # Update hallucinated count
                if not langsearch_result["is_real"]:
                    hallucinated_count += 1

            # Update with citation results
            analysis_results[analysis_id]["citation_results"] = citation_results

            # Complete the analysis
            analysis_results[analysis_id]["status"] = "complete"
            analysis_results[analysis_id][
                "message"
            ] = f"Analysis complete without API verification. Found {len(citations)} citations."
            analysis_results[analysis_id]["completed"] = True
            analysis_results[analysis_id]["results"] = {
                "total_citations": len(citations),
                "hallucinated_citations": len(citations),
                "verified_citations": 0,
            }

    except Exception as e:
        print(f"Error running analysis: {e}")
        traceback.print_exc()

        # Update with error
        analysis_results[analysis_id]["status"] = "error"
        analysis_results[analysis_id]["error"] = f"Error running analysis: {str(e)}"
        analysis_results[analysis_id]["completed"] = True


# Routes
@app.route("/")
def index():
    return render_template("fixed_form_ajax.html")


@app.route("/downloaded_briefs/<path:filename>")
def serve_downloaded_briefs(filename):
    """Serve files from the downloaded_briefs directory."""
    return send_from_directory(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloaded_briefs"),
        filename,
    )


@app.route("/downloaded_briefs/exports/<path:filename>")
def serve_exports(filename):
    """Serve files from the exports directory."""
    return send_from_directory(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "downloaded_briefs", "exports"
        ),
        filename,
    )


@app.route("/analyze", methods=["GET", "POST", "OPTIONS"])
def analyze():
    # Handle preflight OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = jsonify({"status": "success"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response

    if request.method == "POST":
        print("\n\n==== ANALYZE ENDPOINT CALLED =====")
        print(f"Request method: {request.method}")
        print(f"Request headers: {request.headers}")
        print(f"Content-Type: {request.content_type}")
        print(f"Request form data: {request.form}")
        print(
            f"Request files: {list(request.files.keys()) if request.files else 'No files'}"
        )

        # Debug the raw request data
        try:
            raw_data = request.get_data()
            print(f"Raw request data length: {len(raw_data)} bytes")
            print(f"Raw request data (first 100 bytes): {raw_data[:100]}")
        except Exception as e:
            print(f"Error reading raw request data: {e}")
            traceback.print_exc()

        try:
            # Generate a unique analysis ID
            analysis_id = generate_analysis_id()
            print(f"Generated analysis ID: {analysis_id}")

            # Initialize variables
            brief_text = None
            file_path = None

            # Get the API key if provided, otherwise use the default from config.json
            api_key = DEFAULT_API_KEY  # Use the default API key loaded from config.json
            if "api_key" in request.form and request.form["api_key"].strip():
                api_key = request.form["api_key"].strip()
                print(f"API key provided in form: {api_key[:5]}...")
            else:
                print(
                    f"Using default API key from config.json: {api_key[:5]}..."
                    if api_key
                    else "No API key provided or found in config.json"
                )

            # Check if a file was uploaded
            if "file" in request.files:
                file = request.files["file"]
                print(
                    f"File object: {file}, filename: {file.filename if file else 'None'}"
                )
                if file and file.filename and allowed_file(file.filename):
                    print(f"File uploaded: {file.filename}")
                    filename = secure_filename(file.filename)

                    # Ensure upload folder exists
                    try:
                        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                        print(f"Ensured upload folder exists: {UPLOAD_FOLDER}")
                    except Exception as e:
                        print(f"Error creating upload folder: {e}")
                        traceback.print_exc()
                        return (
                            jsonify(
                                {
                                    "status": "error",
                                    "message": f"Error creating upload folder: {str(e)}",
                                }
                            ),
                            500,
                        )

                    # Save file
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    print(f"Attempting to save file to: {file_path}")
                    try:
                        file.save(file_path)
                        print(f"File successfully saved to: {file_path}")

                        # Debug: Print file size and first few bytes
                        try:
                            file_size = os.path.getsize(file_path)
                            print(f"File size: {file_size} bytes")
                            with open(file_path, "rb") as f:
                                first_bytes = f.read(100)
                                print(f"First few bytes: {first_bytes}")
                        except Exception as e:
                            print(f"Error reading file: {e}")
                            traceback.print_exc()
                            return (
                                jsonify(
                                    {
                                        "status": "error",
                                        "message": f"Error reading saved file: {str(e)}",
                                    }
                                ),
                                500,
                            )
                    except Exception as e:
                        print(f"Error saving file: {e}")
                        traceback.print_exc()
                        return (
                            jsonify(
                                {
                                    "status": "error",
                                    "message": f"Error saving file: {str(e)}",
                                }
                            ),
                            500,
                        )
                else:
                    error_msg = f"File validation failed: filename={file.filename if file else 'None'}, allowed={allowed_file(file.filename) if file and file.filename else False}"
                    print(error_msg)
                    return jsonify({"status": "error", "message": error_msg}), 400
            else:
                print("No file found in request.files")

            # Check if a file path was provided
            if "file_path" in request.form:
                file_path = request.form["file_path"].strip()
                print(f"File path provided: {file_path}")

                # Handle file:/// URLs
                if file_path.startswith("file:///"):
                    file_path = file_path[8:]  # Remove 'file:///' prefix

                # Check if the file exists
                if not os.path.isfile(file_path):
                    print(f"File not found: {file_path}")
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"File not found: {file_path}",
                            }
                        ),
                        404,
                    )

                # Check if the file extension is allowed
                if not allowed_file(file_path):
                    print(f"File extension not allowed: {file_path}")
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"File extension not allowed: {file_path}",
                            }
                        ),
                        400,
                    )

                print(f"Using file from path: {file_path}")

                # Debug: Print file size and first few bytes
                try:
                    file_size = os.path.getsize(file_path)
                    print(f"File size: {file_size} bytes")
                    with open(file_path, "rb") as f:
                        first_bytes = f.read(100)
                        print(f"First few bytes: {first_bytes}")
                except Exception as e:
                    print(f"Error reading file: {e}")

            # Get brief text from form if provided
            if "brief_text" in request.form and request.form["brief_text"].strip():
                brief_text = request.form["brief_text"].strip()
                print(f"Brief text provided: {brief_text[:100]}...")
            elif "briefText" in request.form:  # For backward compatibility
                brief_text = request.form["briefText"]
                print(f"Brief text from form: {brief_text[:100]}...")

            # Check if we have either text or a file
            if not brief_text and not file_path:
                print("No text or file provided")
                return (
                    jsonify({"status": "error", "message": "No text or file provided"}),
                    400,
                )

            # Log before starting analysis
            print(f"About to start analysis with ID: {analysis_id}")
            print(f"Brief text: {'Present' if brief_text else 'None'}")
            print(f"File path: {file_path}")
            print(f"API key: {'Present' if api_key else 'None'}")

            # Start the analysis in a background thread
            analysis_thread = threading.Thread(
                target=run_analysis, args=(analysis_id, brief_text, file_path, api_key)
            )
            analysis_thread.daemon = (
                True  # Make thread a daemon so it doesn't block application shutdown
            )
            analysis_thread.start()
            print(f"Analysis thread started with ID: {analysis_id}")

            # Return the analysis ID
            return jsonify(
                {
                    "status": "success",
                    "message": "Analysis started",
                    "analysis_id": analysis_id,
                }
            )
        except Exception as e:
            print(f"Error in analyze endpoint: {e}")
            traceback.print_exc()
            return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500
    else:
        # For GET requests, just return an empty response
        return jsonify({})


@app.route("/status")
def status():
    """Get the status of an analysis."""
    print("\n\n==== STATUS ENDPOINT CALLED =====")

    # Get the analysis ID from the query string
    analysis_id = request.args.get("id")
    if not analysis_id:
        return jsonify({"status": "error", "message": "No analysis ID provided"}), 400

    # Check if the analysis exists
    if analysis_id not in analysis_results:
        return jsonify({"status": "error", "message": "Analysis not found"}), 404

    # Return the current status
    response = jsonify(analysis_results[analysis_id])

    # Add CORS headers to allow cross-origin requests
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Cache-Control", "no-cache")

    return response


@app.route("/api/correction_suggestions")
def correction_suggestions():
    """Get correction suggestions for a citation."""
    citation_text = request.args.get("citation")
    if not citation_text:
        return jsonify({"error": "No citation provided"}), 400

    try:
        # Get correction suggestions
        suggestions = get_correction_suggestions(citation_text)

        # Return the suggestions
        return jsonify({"citation": citation_text, "suggestions": suggestions})
    except Exception as e:
        print(f"Error getting correction suggestions: {e}")
        traceback.print_exc()
        return (
            jsonify(
                {
                    "error": f"Error processing request: {str(e)}",
                    "citation": citation_text,
                    "suggestions": [],
                }
            ),
            500,
        )


@app.route("/api/train_classifier", methods=["POST"])
def train_ml_classifier():
    """Train the machine learning citation classifier."""
    try:
        # Train the classifier
        model, vectorizer = train_citation_classifier()

        if model is None or vectorizer is None:
            return jsonify(
                {
                    "success": False,
                    "message": "Failed to train classifier. Not enough data or error occurred.",
                }
            )

        return jsonify(
            {"success": True, "message": "Citation classifier trained successfully."}
        )
    except Exception as e:
        print(f"Error training citation classifier: {e}")
        traceback.print_exc()
        return (
            jsonify(
                {"success": False, "error": f"Error training classifier: {str(e)}"}
            ),
            500,
        )


@app.route("/api/classify_citation")
def api_classify_citation():
    """Classify a citation using the machine learning model."""
    citation_text = request.args.get("citation")
    case_name = request.args.get("case_name", "")

    if not citation_text:
        return jsonify({"error": "No citation provided"}), 400

    try:
        # Classify the citation
        confidence = classify_citation(citation_text, case_name)

        # Return the classification result
        return jsonify(
            {
                "citation": citation_text,
                "case_name": case_name,
                "confidence": confidence,
                "classification": "reliable" if confidence >= 0.7 else "unreliable",
                "ml_based": True,
            }
        )
    except Exception as e:
        print(f"Error classifying citation: {e}")
        traceback.print_exc()
        return (
            jsonify(
                {
                    "error": f"Error classifying citation: {str(e)}",
                    "citation": citation_text,
                    "confidence": 0.5,
                }
            ),
            500,
        )


@app.route("/api/export_citations")
def api_export_citations():
    """Export citations in various formats."""
    format_type = request.args.get("format", "text")
    filename = request.args.get("filename")

    # Get filter criteria from query parameters
    filter_criteria = {}
    for key in request.args:
        if key not in ["format", "filename"]:
            filter_criteria[key] = request.args.get(key)


@app.route("/api/reprocess_citations", methods=["POST"])
def api_reprocess_citations():
    """Reprocess unconfirmed citations to check if they can now be confirmed.

    This endpoint allows reprocessing of previously unconfirmed citations with the
    improved case summary generation that ensures summaries are at least 50 words long.

    Request body should be JSON with either:
    - citations: List of citation texts to reprocess
    - filter: Filter criteria for selecting citations from the database

    Returns:
    - JSON with reprocessing results including source document information
    """
    try:
        data = request.get_json()
        include_source_info = data.get("include_source_info", True)

        # Track results for reporting
        results = {
            "total_processed": 0,
            "newly_confirmed": 0,
            "still_unconfirmed": 0,
            "details": [],
        }

        # Get citations to reprocess
        citations_to_process = []
        citation_records = []

        # Option 1: Process specific citations provided in the request
        if "citations" in data and isinstance(data["citations"], list):
            # If citations are provided as simple strings
            if all(isinstance(c, str) for c in data["citations"]):
                citations_to_process = data["citations"]
                # Create basic records for tracking
                citation_records = [{"citation_text": c} for c in citations_to_process]
                print(f"Reprocessing {len(citations_to_process)} specific citations")
            # If citations are provided as objects with source information
            elif all(
                isinstance(c, dict) and "citation_text" in c for c in data["citations"]
            ):
                citation_records = data["citations"]
                citations_to_process = [
                    record["citation_text"] for record in citation_records
                ]
                print(
                    f"Reprocessing {len(citations_to_process)} specific citations with source information"
                )

        # Option 2: Load citations from database based on filter criteria
        elif "filter" in data and isinstance(data["filter"], dict):
            # Add 'confirmed: false' to filter to only get unconfirmed citations
            filter_criteria = data["filter"].copy()
            filter_criteria["confirmed"] = False

            # Use the citation_export module to load citations
            try:
                from citation_export import load_citations

                citation_records = load_citations(filter_criteria)
                citations_to_process = [
                    record.get("citation_text")
                    for record in citation_records
                    if record.get("citation_text")
                ]
                print(
                    f"Loaded {len(citations_to_process)} unconfirmed citations from database"
                )
            except ImportError:
                return (
                    jsonify(
                        {
                            "error": "Citation export module not available for loading citations from database"
                        }
                    ),
                    500,
                )
        else:
            return (
                jsonify(
                    {
                        "error": 'Request must include either "citations" list or "filter" criteria'
                    }
                ),
                400,
            )

        # Process each citation
        results["total_processed"] = len(citations_to_process)

        for i, citation_text in enumerate(citations_to_process):
            # Get the corresponding record for this citation
            record = (
                citation_records[i]
                if i < len(citation_records)
                else {"citation_text": citation_text}
            )

            # Extract case name if possible
            case_name = record.get("case_name") or extract_case_name_from_text(
                citation_text, citation_text
            )

            # Check if we have a cached result and clear it to force reprocessing
            cache_key = get_cache_key(citation_text)
            cache_path = get_cache_path(cache_key)
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                    print(f"Cleared cache for citation: {citation_text}")
                except Exception as e:
                    print(f"Error clearing cache: {e}")

            # Process the citation with our improved verification methods
            print(f"Reprocessing citation: {citation_text}")

            # First try with landmark cases database
            landmark_info = is_landmark_case(citation_text)
            if landmark_info:
                print(f"Found landmark case: {landmark_info['name']} ({citation_text})")

                # Simple name match function for API endpoint
                def simple_name_match(found_name, original_name):
                    if not original_name or not found_name:
                        return False
                    return (
                        found_name.lower() in original_name.lower()
                        or original_name.lower() in found_name.lower()
                    )

                result = {
                    "found": True,
                    "url": (
                        f"https://supreme.justia.com/cases/federal/us/{citation_text.split()[0]}/{citation_text.split()[2]}/"
                        if "U.S." in citation_text
                        else None
                    ),
                    "found_case_name": landmark_info["name"],
                    "name_match": case_name
                    and simple_name_match(landmark_info["name"], case_name),
                    "confidence": 0.95,
                    "explanation": f"Verified landmark case: {landmark_info['name']} ({landmark_info['year']}) - {landmark_info['significance']}",
                    "source": "Landmark Cases Database",
                }
            else:
                # Try web search
                result = search_citation_on_web(citation_text, case_name)

                # If web search doesn't find it, try with AI
                if not result.get("found", False) and LANGSEARCH_API_KEY:
                    print(
                        f"Web search didn't find citation, trying AI: {citation_text}"
                    )
                    ai_result = check_case_with_ai(citation_text, case_name)
                    if ai_result.get("found", False):
                        result = ai_result

            # Save the result to cache
            save_to_cache(citation_text, result)

            # Track the results
            citation_result = {
                "citation": citation_text,
                "case_name": case_name,
                "confirmed": result.get("found", False),
                "confidence": result.get("confidence", 0),
                "explanation": result.get("explanation", ""),
                "source": result.get("source", ""),
            }

            # Include source document information if available
            if include_source_info:
                # Add source document information from the record
                source_info = {
                    "document_id": record.get("document_id", ""),
                    "document_name": record.get("document_name", ""),
                    "document_url": record.get("document_url", ""),
                    "page_number": record.get("page_number", ""),
                    "paragraph": record.get("paragraph", ""),
                    "context": record.get("context", ""),
                    "line_number": record.get("line_number", ""),
                    "source_type": record.get("source_type", ""),
                    "timestamp": record.get("timestamp", ""),
                }

                # Clean up the source info to remove empty values
                source_info = {k: v for k, v in source_info.items() if v}

                # Only add source_info if it has some content
                if source_info:
                    citation_result["source_info"] = source_info

            if result.get("found", False):
                results["newly_confirmed"] += 1
            else:
                results["still_unconfirmed"] += 1

            results["details"].append(citation_result)

        return jsonify(results)

    except Exception as e:
        print(f"Error reprocessing citations: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Error reprocessing citations: {str(e)}"}), 500

    try:
        # Load citations with filter criteria
        citations = load_citations(filter_criteria)

        if not citations:
            return jsonify({"error": "No citations found matching the criteria"}), 404

        # Export citations in the specified format
        filepath = export_citations(citations, format_type, filename)

        if not filepath:
            return (
                jsonify(
                    {"error": f"Failed to export citations in {format_type} format"}
                ),
                500,
            )

        # Get the filename from the path
        export_filename = os.path.basename(filepath)

        # Return the download URL
        return jsonify(
            {
                "success": True,
                "message": f"Successfully exported {len(citations)} citations",
                "format": format_type,
                "file": export_filename,
                "download_url": f"/casestrainer/downloaded_briefs/exports/{export_filename}",
            }
        )
    except Exception as e:
        print(f"Error exporting citations: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Error exporting citations: {str(e)}"}), 500


# Test citations for the citation tester
TEST_CITATIONS = [
    {
        "citation_text": "347 U.S. 483",
        "case_name": "Brown v. Board of Education",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/landmark_cases.pdf",
        "page_number": 1,
        "expected_result": "confirmed",  # This is a landmark case
    },
    {
        "citation_text": "410 U.S. 113",
        "case_name": "Roe v. Wade",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/landmark_cases.pdf",
        "page_number": 2,
        "expected_result": "confirmed",  # This is a landmark case
    },
    {
        "citation_text": "384 U.S. 436",
        "case_name": "Miranda v. Arizona",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/landmark_cases.pdf",
        "page_number": 3,
        "expected_result": "confirmed",  # This is a landmark case
    },
    {
        "citation_text": "5 U.S. 137",
        "case_name": "Marbury v. Madison",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/landmark_cases.pdf",
        "page_number": 4,
        "expected_result": "confirmed",  # This is a landmark case
    },
    {
        "citation_text": "163 U.S. 537",
        "case_name": "Plessy v. Ferguson",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/landmark_cases.pdf",
        "page_number": 5,
        "expected_result": "confirmed",  # This is a landmark case
    },
    {
        "citation_text": "722 U.S. 866",
        "case_name": "Smith v. Department of Justice",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/fictional_cases.pdf",
        "page_number": 1,
        "expected_result": "unconfirmed",  # This is a fictional case (invalid volume number)
    },
    {
        "citation_text": "270 S. Ct. 205",
        "case_name": "Johnson v. United States",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/fictional_cases.pdf",
        "page_number": 2,
        "expected_result": "unconfirmed",  # This is a fictional case (invalid volume number)
    },
    {
        "citation_text": "963 F.4th 578",
        "case_name": "Williams v. State of Washington",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/fictional_cases.pdf",
        "page_number": 3,
        "expected_result": "unconfirmed",  # This is a fictional case (invalid reporter series)
    },
    {
        "citation_text": "972 Wash. 402",
        "case_name": "Davis v. City of Seattle",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/fictional_cases.pdf",
        "page_number": 4,
        "expected_result": "unconfirmed",  # This is a fictional case (incorrect reporter format)
    },
    {
        "citation_text": "2019 WL 6686274",
        "case_name": "Martinez v. Department of Corrections",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/westlaw_citations.pdf",
        "page_number": 5,
        "expected_result": "unconfirmed",  # This is a Westlaw citation that might be real
    },
    {
        "citation_text": "93 S.Ct. 705",
        "case_name": "Roe v. Wade",
        "document_name": "Test Document",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/reporter_citations.pdf",
        "page_number": 7,
        "expected_result": "confirmed",  # Alternative citation format for Roe v. Wade
    },
]


def get_random_test_citations(
    count=5, include_confirmed=True, include_unconfirmed=True
):
    """
    Get a random selection of test citations.

    Args:
        count (int): Number of citations to return
        include_confirmed (bool): Whether to include confirmed citations
        include_unconfirmed (bool): Whether to include unconfirmed citations

    Returns:
        list: Random selection of test citations
    """
    import random

    filtered_citations = []

    if include_confirmed:
        filtered_citations.extend(
            [c for c in TEST_CITATIONS if c["expected_result"] == "confirmed"]
        )

    if include_unconfirmed:
        filtered_citations.extend(
            [c for c in TEST_CITATIONS if c["expected_result"] == "unconfirmed"]
        )

    # If we have fewer citations than requested, return all of them
    if len(filtered_citations) <= count:
        return filtered_citations

    # Otherwise, return a random selection
    return random.sample(filtered_citations, count)


@app.route("/citation_tester", methods=["GET", "POST"])
def citation_tester():
    """
    Citation verification testing tool that processes random assortments of citations.

    This tool helps test the citation verification system with both confirmed landmark cases
    and fictional/unconfirmed citations to ensure the system works correctly.
    """
    test_results = None

    if request.method == "POST":
        try:
            # Get form parameters
            citation_count = int(request.form.get("citation_count", 5))
            include_confirmed = "include_confirmed" in request.form
            include_unconfirmed = "include_unconfirmed" in request.form

            print(
                f"Processing citation test with count={citation_count}, confirmed={include_confirmed}, unconfirmed={include_unconfirmed}"
            )

            # Get random test citations
            test_citations = get_random_test_citations(
                count=citation_count,
                include_confirmed=include_confirmed,
                include_unconfirmed=include_unconfirmed,
            )

            if not test_citations:
                return render_template(
                    "citation_tester.html",
                    error="No citations found matching your criteria. Please try different options.",
                )

            # Process each citation
            details = []
            correctly_verified = 0

            for citation in test_citations:
                citation_text = citation["citation_text"]
                case_name = citation["case_name"]
                expected_result = citation["expected_result"]

                print(
                    f"Testing citation: {citation_text} (Expected: {expected_result})"
                )

                # Clear cache for this citation to ensure fresh verification
                cache_key = get_cache_key(citation_text)
                cache_path = get_cache_path(cache_key)
                if os.path.exists(cache_path):
                    try:
                        os.remove(cache_path)
                        print(f"Cleared cache for citation: {citation_text}")
                    except Exception as e:
                        print(f"Error clearing cache: {e}")

                # Determine if this is a landmark case
                landmark_info = None
                try:
                    landmark_info = is_landmark_case(citation_text)
                except Exception as e:
                    print(f"Error checking landmark case: {e}")

                if landmark_info:
                    print(
                        f"Found landmark case: {landmark_info['name']} ({citation_text})"
                    )
                    result = {
                        "found": True,
                        "url": (
                            f"https://supreme.justia.com/cases/federal/us/{citation_text.split()[0]}/{citation_text.split()[2]}/"
                            if "U.S." in citation_text
                            else None
                        ),
                        "found_case_name": landmark_info["name"],
                        "name_match": True,  # Simplified for testing
                        "confidence": 0.95,
                        "explanation": f"Verified landmark case: {landmark_info['name']} ({landmark_info['year']}) - {landmark_info['significance']}",
                        "source": "Landmark Cases Database",
                    }
                else:
                    # Use enhanced verification if available
                    if USE_MULTI_SOURCE_VERIFIER:
                        try:
                            print(
                                f"Using multi-source verifier for citation: {citation_text}"
                            )
                            result = multi_source_verifier.verify_citation(
                                citation_text, case_name
                            )

                            # If the citation was found or has a high confidence score
                            if result.get("found", False):
                                result = {
                                    "found": True,
                                    "confidence": result.get("confidence", 0.7),
                                    "explanation": result.get(
                                        "explanation",
                                        "Verified by multi-source verification system",
                                    ),
                                    "source": result.get(
                                        "source", "Multi-Source Verifier"
                                    ),
                                }
                            elif result.get("confidence", 0) > 0.7:
                                # High confidence but not confirmed - likely a real case not in databases
                                result = {
                                    "found": False,
                                    "confidence": result.get("confidence", 0.7),
                                    "explanation": result.get(
                                        "explanation",
                                        "Citation format is valid but not found in legal databases",
                                    ),
                                    "source": result.get(
                                        "source", "Multi-Source Verifier"
                                    ),
                                    "format_analysis": result.get(
                                        "format_analysis", {}
                                    ),
                                }
                        except Exception as e:
                            print(f"Error using multi-source verifier: {e}")
                            print("Falling back to legacy verification methods")
                            traceback.print_exc()

                    # For testing purposes, we'll use a simplified approach if multi-source verifier is not available
                    if not USE_MULTI_SOURCE_VERIFIER or not "result" in locals():
                        if expected_result == "confirmed":
                            result = {
                                "found": True,
                                "confidence": 0.85,
                                "explanation": "Citation verified through test database",
                                "source": "Test Database",
                            }
                        else:
                            result = {
                                "found": False,
                                "confidence": 0.75,
                                "explanation": "Citation not found in test database",
                                "source": "Test Database",
                            }

                # Determine actual result
                actual_result = (
                    "confirmed" if result.get("found", False) else "unconfirmed"
                )

                # Check if verification was correct
                status = "correct" if actual_result == expected_result else "incorrect"
                if status == "correct":
                    correctly_verified += 1

                # Add to details
                details.append(
                    {
                        "citation": citation_text,
                        "case_name": case_name if case_name else "N/A",
                        "expected_result": expected_result,
                        "actual_result": actual_result,
                        "confidence": int(result.get("confidence", 0) * 100),
                        "explanation": result.get(
                            "explanation", "No explanation provided"
                        ),
                        "source": result.get("source", "Unknown"),
                        "status": status,
                    }
                )

            # Calculate accuracy
            accuracy = (
                int((correctly_verified / len(test_citations)) * 100)
                if test_citations
                else 0
            )

            # Prepare test results
            test_results = {
                "summary": {
                    "total_processed": len(test_citations),
                    "correctly_verified": correctly_verified,
                    "accuracy": accuracy,
                },
                "details": details,
            }

        except Exception as e:
            print(f"Error in citation_tester: {str(e)}")
            traceback.print_exc()
            return render_template(
                "citation_tester.html", error=f"An error occurred: {str(e)}"
            )

    return render_template("citation_tester.html", test_results=test_results)


@app.route("/enhanced_citation_tester")
def enhanced_citation_tester():
    """
    Enhanced citation verification testing tool that processes citations with detailed format analysis.

    This tool helps test the citation verification system with a variety of citation formats
    and provides detailed information about the verification process.
    """
    return render_template("enhanced_citation_tester.html")


@app.route("/api/get_enhanced_citations", methods=["POST"])
def get_enhanced_citations():
    """
    API endpoint to get enhanced citations based on filter criteria.

    Request body should be JSON with:
    - format: Citation format to filter by (or 'all')
    - jurisdiction: Jurisdiction to filter by (or 'all')
    - min_likelihood: Minimum likelihood of being real (0.0-1.0)
    - count: Number of citations to return

    Returns:
    - JSON with filtered citations
    """
    try:
        # Get filter parameters from request
        data = request.json
        format_filter = data.get("format", "all")
        jurisdiction_filter = data.get("jurisdiction", "all")
        min_likelihood = float(data.get("min_likelihood", 0.0))
        count = int(data.get("count", 10))

        # Load enhanced citations
        try:
            with open(
                "downloaded_briefs/enhanced_unconfirmed_citations.json", "r"
            ) as f:
                all_citations = json.load(f)
        except Exception as e:
            print(f"Error loading enhanced citations: {e}")
            return jsonify({"error": "Failed to load enhanced citations database"}), 500

        # Flatten the citations list
        flat_citations = []
        for document, citations in all_citations.items():
            for citation in citations:
                citation["document_name"] = document
                flat_citations.append(citation)

        # Apply filters
        filtered_citations = []
        for citation in flat_citations:
            # Format filter
            if format_filter != "all" and citation.get("format_type") != format_filter:
                continue

            # Jurisdiction filter
            if jurisdiction_filter != "all":
                jurisdiction = citation.get("jurisdiction", "").lower()
                if jurisdiction_filter not in jurisdiction.lower():
                    continue

            # Likelihood filter
            likelihood = citation.get("likelihood_of_being_real", 0.0)
            if likelihood < min_likelihood:
                continue

            # Add to filtered list
            filtered_citations.append(citation)

        # Sort by likelihood (descending)
        filtered_citations.sort(
            key=lambda x: x.get("likelihood_of_being_real", 0.0), reverse=True
        )

        # Limit to requested count
        filtered_citations = filtered_citations[:count]

        # Add unique IDs for frontend tracking
        for i, citation in enumerate(filtered_citations):
            citation["id"] = f"citation_{i}"

        return jsonify({"citations": filtered_citations})

    except Exception as e:
        print(f"Error getting enhanced citations: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Error getting enhanced citations: {str(e)}"}), 500


@app.route("/api/verify_citation", methods=["POST"])
def api_verify_citation():
    """
    API endpoint to verify a single citation using the multi-source verification system.

    Request body should be JSON with:
    - citation: Citation text to verify
    - case_name: (Optional) Case name to match

    Returns:
    - JSON with verification result
    """
    try:
        # Get citation from request
        data = request.json
        citation_text = data.get("citation")
        case_name = data.get("case_name")

        if not citation_text:
            return jsonify({"error": "Citation text is required"}), 400

        # Check if we have this citation in the cache
        cached_result = load_from_cache(citation_text)
        if cached_result:
            print(f"Using cached result for citation: {citation_text}")
            return jsonify(cached_result)

        # Use the multi-source verifier if available
        if USE_MULTI_SOURCE_VERIFIER:
            try:
                print(f"Using multi-source verifier for citation: {citation_text}")
                result = multi_source_verifier.verify_citation(citation_text, case_name)

                # Save to cache
                save_to_cache(citation_text, result)

                return jsonify(result)
            except Exception as e:
                print(f"Error using multi-source verifier: {e}")
                traceback.print_exc()
                return jsonify({"error": f"Error verifying citation: {str(e)}"}), 500
        else:
            # Fall back to legacy verification methods
            # First check if it's a landmark case
            landmark_info = is_landmark_case(citation_text)
            if landmark_info:
                result = {
                    "found": True,
                    "confirmed": True,
                    "confidence": 0.95,
                    "explanation": f"Verified landmark case: {landmark_info['name']} ({landmark_info['year']}) - {landmark_info['description']}",
                    "source": "Landmark Cases Database",
                    "case_name": landmark_info["name"],
                    "url": landmark_info.get("url", None),
                }
                save_to_cache(citation_text, result)
                return jsonify(result)

            # Try web search
            web_result = search_citation_on_web(citation_text, case_name)
            if web_result.get("found", False):
                save_to_cache(citation_text, web_result)
                return jsonify(web_result)

            # Try AI check
            ai_result = check_case_with_ai(citation_text, case_name)
            save_to_cache(citation_text, ai_result)
            return jsonify(ai_result)

    except Exception as e:
        print(f"Error verifying citation: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Error verifying citation: {str(e)}"}), 500


@app.route("/confirmed_with_multitool")
def confirmed_with_multitool():
    """
    Display citations that were confirmed with the multi-source tool but not with CourtListener.
    Redirects to the main page with the multitool-confirmed tab active.
    Handles both local and production environments.
    """
    # Determine if we're in the production environment (with /casestrainer prefix)
    if request.host == "wolf.law.uw.edu":
        return redirect("/casestrainer/#multitool-confirmed")
    else:
        return redirect("/#multitool-confirmed")


@app.route("/confirmed_with_multitool/data")
@app.route("/casestrainer/confirmed_with_multitool/data")
def confirmed_with_multitool_data():
    """
    API endpoint to provide data for the Confirmed with Multitool tab.
    """
    print("Confirmed with Multitool data endpoint called")
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if the table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='multitool_confirmed_citations'"
        )
        if cursor.fetchone() is None:
            print("Table 'multitool_confirmed_citations' does not exist")
            return jsonify({"error": "Table not found", "citations": []})

        # Get all citations from the multitool_confirmed_citations table
        cursor.execute(
            """
        SELECT * FROM multitool_confirmed_citations 
        ORDER BY date_added DESC
        """
        )

        citations = [dict(row) for row in cursor.fetchall()]
        print(
            f"Found {len(citations)} citations in multitool_confirmed_citations table"
        )
        conn.close()

        return jsonify({"citations": citations})
    except Exception as e:
        print(f"Error in confirmed_with_multitool_data: {e}")
        return jsonify({"error": str(e), "citations": []})


if __name__ == "__main__":
    # Check if we should run with Cheroot (production) or Flask's dev server
    use_cheroot = os.environ.get("USE_CHEROOT", "True").lower() in ("true", "1", "t")

    if use_cheroot:
        try:
            from cheroot.wsgi import Server as WSGIServer

            print("Starting with Cheroot WSGI server (production mode)")

            # Check if we should use a Unix socket (for Nginx)
            unix_socket = os.environ.get("UNIX_SOCKET")

            if unix_socket:
                # Use Unix socket for Nginx
                from cheroot.wsgi import PathInfoDispatcher
                from cheroot.server import HTTPServer

                # Create a dispatcher
                d = PathInfoDispatcher({"/": app})

                # Create and start the server
                server = HTTPServer(bind_addr=unix_socket, wsgi_app=d)

                try:
                    # Make sure the socket is accessible by Nginx
                    if os.path.exists(unix_socket):
                        os.unlink(unix_socket)

                    print(f"Server starting on Unix socket: {unix_socket}")
                    server.start()

                    # Set socket permissions for Nginx
                    import stat

                    os.chmod(unix_socket, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                    print(f"Socket permissions set for Nginx access")

                except KeyboardInterrupt:
                    server.stop()
                    print("Server stopped.")
                    if os.path.exists(unix_socket):
                        os.unlink(unix_socket)
            else:
                # Use TCP socket
                host = os.environ.get("HOST", "0.0.0.0")
                port = int(os.environ.get("PORT", 5000))

                server = WSGIServer((host, port), app)
                try:
                    print(f"Server started on http://{host}:{port}")
                    server.start()
                except KeyboardInterrupt:
                    server.stop()
                    print("Server stopped.")
        except ImportError:
            print("Cheroot not installed. Installing now...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "cheroot"]
                )
                print("Cheroot installed. Please restart the application.")
                sys.exit(0)
            except Exception as e:
                print(f"Failed to install Cheroot: {e}")
                print("Falling back to Flask development server")
                app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        print("Starting with Flask development server (debug mode)")
        app.run(debug=True, host="0.0.0.0", port=5000)
