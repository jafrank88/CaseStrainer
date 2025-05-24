import tempfile
import os
import re
import requests
import PyPDF2
import json
from eyecite import get_citations
from eyecite.resolve import resolve_citations
from pdf_handler import extract_text_from_pdf  # Import at module level
import urllib.parse


def fetch_pdf_content(url_or_path):
    """Fetch content from a PDF URL or local file and extract text."""
    print(f"Fetching PDF from: {url_or_path}")

    # Check if it's a URL or a local file path
    if urllib.parse.urlparse(url_or_path).scheme in ("http", "https"):
        # Existing code for downloading from the web
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/pdf,*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            print("Sending GET request (extra logging)...")
            response = requests.get(
                url_or_path, headers=headers, timeout=60, stream=True
            )
            response.raise_for_status()
            print("GET request completed (extra logging).")
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                temp_file_path = temp_file.name
            print(f"PDF saved to temporary file (extra logging): {temp_file_path}")
            try:
                print("Calling extract_text_from_pdf (extra logging)...")
                text = extract_text_from_pdf(temp_file_path)
                print("extract_text_from_pdf returned (extra logging).")
                if isinstance(text, str) and text.startswith("Error:"):
                    print(f"Error extracting text (extra logging): {text}")
                    raise Exception(text)
                text = re.sub(r"\s+", " ", text).strip()
                print(f"Extracted {len(text)} characters from PDF (extra logging)")
                with open("pdf_extracted_text.txt", "w", encoding="utf-8") as f:
                    f.write(text)
                print("Saved extracted text to pdf_extracted_text.txt (extra logging)")
                os.unlink(temp_file_path)
                print("Temporary PDF file removed (extra logging).")
                return text
            except Exception as e:
                print(f"Error extracting text from PDF (extra logging): {e}")
                os.unlink(temp_file_path)
                raise
        except Exception as e:
            print(f"Error fetching PDF (extra logging): {e}")
            raise
    else:
        # Treat as local file path
        if not os.path.exists(url_or_path):
            raise FileNotFoundError(f"File not found: {url_or_path}")
        print(f"Opening local file: {url_or_path}")
        text = extract_text_from_pdf(url_or_path)
        print(f"Extracted {len(text)} characters from local PDF")
        return text


def extract_citations_with_eyecite(text):
    """Extract citations from text using eyecite and write to JSON."""
    print("Extracting citations using eyecite...")

    # Normalize whitespace so citations split by line breaks are found
    text = re.sub(r"\s+", " ", text).strip()

    # Get citations using eyecite
    citations = get_citations(text)
    print(f"Found {len(citations)} citations with eyecite")

    # Resolve citations
    resolved_citations = resolve_citations(citations)

    # Format citations for display
    formatted_citations = []
    for citation in citations:
        citation_info = {
            "citation_text": str(citation),
            "case_name": (
                getattr(citation, "plaintiff", "")
                + " v. "
                + getattr(citation, "defendant", "")
                if hasattr(citation, "plaintiff") and hasattr(citation, "defendant")
                else "Unknown"
            ),
            "reporter": getattr(citation, "reporter", ""),
            "volume": getattr(citation, "volume", ""),
            "page": getattr(citation, "page", ""),
            "year": getattr(citation, "year", ""),
            "court": getattr(citation, "court", ""),
        }
        formatted_citations.append(citation_info)

    # Print first 10 citations
    for i, citation in enumerate(formatted_citations[:10]):
        print(
            f"  {i+1}. {citation['citation_text']} - {citation['case_name']} ({citation['year']})"
        )

    if len(formatted_citations) > 10:
        print(f"  ... and {len(formatted_citations) - 10} more")

    # Save formatted citations to a JSON file
    with open("eyecite_citations.json", "w") as f:
        json.dump(formatted_citations, f, indent=2)
    print(
        "eyecite_citations.json written to:", os.path.abspath("eyecite_citations.json")
    )

    return formatted_citations


def process_text_in_chunks(text, chunk_size=1000000):
    """Process large text in chunks to avoid memory issues."""
    print(f"Processing text in chunks of {chunk_size} characters")
    all_citations = []

    # Split text into overlapping chunks to avoid missing citations at boundaries
    overlap = 1000  # Overlap size to ensure we don't miss citations at chunk boundaries
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i : i + chunk_size]
        chunks.append(chunk)

    print(f"Split text into {len(chunks)} chunks")

    # Process each chunk
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        try:
            # Extract citations from chunk
            citations = get_citations(chunk)  # Use standard tokenizer

            # Add unique citations to our list
            for citation in citations:
                citation_str = (
                    citation.corrected_citation()
                    if hasattr(citation, "corrected_citation")
                    else str(citation)
                )
                if citation_str not in all_citations:
                    all_citations.append(citation_str)

            print(f"Found {len(citations)} citations in chunk {i+1}")
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
            continue

    print(f"Total unique citations found: {len(all_citations)}")
    return all_citations


def process_pdf_url(url):
    """Process a PDF URL or local file to extract and analyze citations."""
    try:
        # Fetch PDF content
        text = fetch_pdf_content(url)
        print(f"Extracted text length: {len(text)}")
        print(f"Extracted text sample (first 500 chars): {text[:500]}")

        # Always extract citations and write JSON
        formatted_citations = extract_citations_with_eyecite(text)

        print(
            f"\nSuccessfully processed PDF and found {len(formatted_citations)} citations!"
        )
        print("Citations found:")
        for c in formatted_citations:
            print(f"  - {c['citation_text']}")
        return formatted_citations
    except Exception as e:
        print(f"Error processing PDF URL: {e}")
        return []


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Use the provided local PDF file path (e.g. C:/Users/jafrank/Downloads/22-451_7m58.pdf) if given.
        url = sys.argv[1]
    else:
        # Fallback to the hard-coded URL (e.g. the Avianca sanctions opinion PDF).
        url = "https://www.gibbonslawalert.com/wp-content/uploads/2023/07/Mata-v.-Avianca-Sanctions-opinion.pdf"
    process_pdf_url(url)
