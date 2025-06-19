#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test multiple PDF extractors (PDFMiner, PyMuPDF, pdftotext) on a given PDF and print the context around occurrences of 'F.' and '3d'."""

import os
import re
import sys
import argparse
import logging
import subprocess
import tempfile
from io import StringIO

# PDFMiner (from pdfminer.high_level)
from pdfminer.high_level import extract_text as pdfminer_extract

# PyMuPDF (fitz) (if installed)
try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# pdftotext (Poppler) (if installed) – via subprocess
# (You can install Poppler on Windows via conda or a binary distribution, or on Linux via apt-get, etc.)

# OCR extraction (using pytesseract and pdf2image) – optional
try:
    import pytesseract
    from pdf2image import convert_from_path
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def pdfminer_extract_text(pdf_path):
    """Extract text using PDFMiner (pdfminer.high_level)."""
    try:
        text = pdfminer_extract(pdf_path)
        return text
    except Exception as e:
        logger.error(f"PDFMiner extraction error: {e}")
        return ""


def pymupdf_extract_text(pdf_path):
    """Extract text using PyMuPDF (fitz)."""
    if not HAS_PYMUPDF:
        logger.warning("PyMuPDF (fitz) not installed. Skipping extraction.")
        return ""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        logger.error(f"PyMuPDF extraction error: {e}")
        return ""


def pdftotext_extract_text(pdf_path):
    """Extract text using pdftotext (Poppler) via subprocess."""
    try:
        # pdftotext (Poppler) is assumed to be installed and available in PATH.
        # (On Windows, you may need to install Poppler and add its bin folder to PATH.)
        cmd = ["pdftotext", "-layout", pdf_path, "-"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            logger.error(f"pdftotext error: {stderr}")
            return ""
        return stdout
    except Exception as e:
        logger.error(f"pdftotext extraction error: {e}")
        return ""


def extract_text_ocr(pdf_path):
    """Extract text using OCR (pytesseract) via pdf2image (if installed)."""
    if not HAS_OCR:
        logger.warning("OCR (pytesseract/pdf2image) not installed. Skipping OCR extraction.")
        return ""
    try:
        # Convert PDF pages to images (using pdf2image)
        images = convert_from_path(pdf_path)
        text = ""
        for i, img in enumerate(images):
            # (Optional: log progress if PDF is large)
            logger.info(f"OCR processing page {i + 1} of {len(images)}")
            text += pytesseract.image_to_string(img) + "\n"
        return text
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
        return ""


def print_context(text, pattern, extractor_name):
    """Print the context (50 chars before and after) around occurrences of a regex pattern in the extracted text."""
    if not text:
        logger.warning(f"Extractor {extractor_name} produced empty text.")
        return
    for match in re.finditer(pattern, text):
        idx = match.start()
        context = text[max(0, idx - 50):idx + 50]
        logger.info(f"Extractor {extractor_name} – Context around '{match.group()}': ...{context}...")


def write_extracted_text(text, extractor_name, pdf_path):
    """Write the full extracted text (from a given extractor) to a file (e.g. 'extracted_pdfminer.txt')."""
    if not text:
        logger.warning(f"Extractor {extractor_name} produced empty text; skipping write.")
        return
    filename = f"extracted_{extractor_name.replace(' ', '_').lower()}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    logger.info(f"Full extracted text (from {extractor_name}) written to {filename}.")


def main(pdf_path):
    """Run extraction tests on the given PDF and print context around 'F.' and '3d'."""
    if not os.path.isfile(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        sys.exit(1)
    logger.info(f"Testing PDF extractors on: {pdf_path}")

    # PDFMiner extraction
    pdfminer_text = pdfminer_extract_text(pdf_path)
    print_context(pdfminer_text, r"F\.", "PDFMiner (pdfminer.high_level)")
    print_context(pdfminer_text, r"3d", "PDFMiner (pdfminer.high_level)")
    write_extracted_text(pdfminer_text, "PDFMiner (pdfminer.high_level)", pdf_path)

    # PyMuPDF extraction (if available)
    pymupdf_text = pymupdf_extract_text(pdf_path)
    print_context(pymupdf_text, r"F\.", "PyMuPDF (fitz)")
    print_context(pymupdf_text, r"3d", "PyMuPDF (fitz)")
    write_extracted_text(pymupdf_text, "PyMuPDF (fitz)", pdf_path)

    # pdftotext extraction (if Poppler is installed)
    pdftotext_text = pdftotext_extract_text(pdf_path)
    print_context(pdftotext_text, r"F\.", "pdftotext (Poppler)")
    print_context(pdftotext_text, r"3d", "pdftotext (Poppler)")
    write_extracted_text(pdftotext_text, "pdftotext (Poppler)", pdf_path)

    # OCR extraction (if available)
    ocr_text = extract_text_ocr(pdf_path)
    print_context(ocr_text, r"F\.", "OCR (pytesseract)")
    print_context(ocr_text, r"3d", "OCR (pytesseract)")
    write_extracted_text(ocr_text, "OCR (pytesseract)", pdf_path)

    logger.info("Extraction tests completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test PDF extractors (PDFMiner, PyMuPDF, pdftotext) on a given PDF and print context around 'F.' and '3d'.")
    parser.add_argument("--pdf", type=str, default="gov.uscourts.wyd.64014.141.0_1.pdf", help="Path to the PDF file (default: gov.uscourts.wyd.64014.141.0_1.pdf)")
    args = parser.parse_args()
    main(args.pdf) 