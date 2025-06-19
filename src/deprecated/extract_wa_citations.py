#!/usr/bin/env python3
"""
Script to extract citations from Washington Appellate Court PDFs and prepare them for testing.
Uses eyecite for robust citation parsing with Hyperscan when available.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Set
import PyPDF2
from datetime import datetime
from eyecite import get_citations

# Try to import HyperscanTokenizer, fall back to default if not available
try:
    from eyecite.tokenizers import HyperscanTokenizer

    USE_HYPERSCAN = True
    logger = logging.getLogger(__name__)
    logger.info("Using HyperscanTokenizer for improved performance")
except ImportError:
    USE_HYPERSCAN = False
    logger = logging.getLogger(__name__)
    logger.warning("HyperscanTokenizer not available, using default tokenizer")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f'wa_citations_extraction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
        logging.StreamHandler(),
    ],
)

# Additional Washington-specific citation patterns
WA_CITATION_PATTERNS = [
    r"\b\d+\s+Wn\.2d\s+\d+\b",  # Washington Reports, Second Series
    r"\b\d+\s+Wn\.\s+\d+\b",  # Washington Reports
    r"\b\d+\s+Wn\.App\.\s+\d+\b",  # Washington Appellate Reports
    r"\b\d+\s+Wash\.2d\s+\d+\b",  # Alternative format
    r"\b\d+\s+Wash\.\s+\d+\b",  # Alternative format
    r"\b\d+\s+Wash\.App\.\s+\d+\b",  # Alternative format
]


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
        return ""


def find_citations(text: str) -> Set[str]:
    """
    DEPRECATED: Use extract_all_citations from citation_utils instead.
    """
    import warnings
    warnings.warn("find_citations is deprecated. Use extract_all_citations from citation_utils instead.", DeprecationWarning)
    citations = set()
    try:
        # Use HyperscanTokenizer if available, otherwise use default
        if USE_HYPERSCAN:
            tokenizer = HyperscanTokenizer()
            found_citations = get_citations(text, tokenizer=tokenizer)
        else:
            found_citations = get_citations(text)

        # Add citations found by eyecite
        for citation in found_citations:
            citation_text = citation.matched_text()
            start = max(0, citation.span()[0] - 50)
            end = min(len(text), citation.span()[1] + 50)
            context = text[start:end].strip()
            citations.add(f"{citation_text} (Context: {context})")

        # Add citations found by additional patterns
        for pattern in WA_CITATION_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                citation = match.group()
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                citations.add(f"{citation} (Context: {context})")

    except Exception as e:
        logger.error(f"Error finding citations: {str(e)}")

    return citations


def process_directory(directory_path: str, max_citations: int = 1000) -> List[str]:
    """Process all PDFs in the directory and extract citations."""
    all_citations = set()
    pdf_files = list(Path(directory_path).glob("**/*.pdf"))

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    for pdf_file in pdf_files:
        if len(all_citations) >= max_citations:
            break

        logger.info(f"Processing {pdf_file}")
        text = extract_text_from_pdf(str(pdf_file))
        citations = find_citations(text)

        # Add new citations up to the maximum
        remaining = max_citations - len(all_citations)
        new_citations = list(citations)[:remaining]
        all_citations.update(new_citations)

        logger.info(f"Found {len(citations)} citations in {pdf_file}")

    return list(all_citations)


def save_citations(citations: List[str], output_file: str = "wa_test_citations.txt"):
    """Save citations to a file."""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for citation in citations:
                f.write(f"{citation}\n\n")
        logger.info(f"Saved {len(citations)} citations to {output_file}")
    except Exception as e:
        logger.error(f"Error saving citations: {str(e)}")


def main():
    """Main function to process PDFs and extract citations."""
    directory_path = r"D:\WOLF Processing Folder\Wash App\wash-app full vol pdfs"

    if not os.path.exists(directory_path):
        logger.error(f"Directory not found: {directory_path}")
        return

    logger.info(f"Starting citation extraction from {directory_path}")
    citations = process_directory(directory_path)

    if citations:
        save_citations(citations)
        logger.info(f"Successfully extracted {len(citations)} citations")
    else:
        logger.warning("No citations found")


if __name__ == "__main__":
    main()
