#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for URL processing in CaseStrainer
This script tests the functionality of processing a PDF URL
"""

import os
import sys
import requests
import logging
from enhanced_validator_production import extract_text_from_file

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_url_processing")


def test_pdf_url(url):
    """Test processing a PDF URL"""
    logger.info(f"Testing URL: {url}")

    try:
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)

        # Fetch content from URL
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        logger.info("Sending request to URL...")
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        logger.info(f"URL content type: {content_type}")

        # Save PDF to temporary file
        pdf_path = os.path.join("uploads", "test_url.pdf")

        logger.info(f"Saving PDF to {pdf_path}...")
        with open(pdf_path, "wb") as f:
            f.write(response.content)

        # Extract text from PDF
        logger.info("Extracting text from PDF...")
        document_text = extract_text_from_file(pdf_path)
        logger.info(f"Extracted {len(document_text)} characters from PDF")

        # Save extracted text to file for inspection
        text_path = os.path.join("uploads", "test_url_content.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(document_text)

        logger.info(f"Saved extracted text to {text_path}")

        # Extract and print a sample of the text
        sample_text = (
            document_text[:500] + "..." if len(document_text) > 500 else document_text
        )
        logger.info(f"Sample text: {sample_text}")

        return True, document_text

    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        return False, str(e)


if __name__ == "__main__":
    # Test URL
    test_url = "https://www.gibbonslawalert.com/wp-content/uploads/2023/07/Mata-v.-Avianca-Sanctions-opinion.pdf"

    logger.info("Starting URL processing test...")
    success, result = test_pdf_url(test_url)

    if success:
        logger.info("URL processing test successful!")
    else:
        logger.error(f"URL processing test failed: {result}")
