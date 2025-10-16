#!/usr/bin/env python3
"""
Quick test of URL text extraction
"""

import requests
import tempfile
import os
from urllib.parse import urlparse

def quick_url_test(url: str):
    """Quick test to download and extract text from URL."""
    print(f"Testing URL: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Download PDF
        print("Downloading...")
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_path = temp_file.name

        print(f"Saved to: {temp_path}")
        print(f"File size: {os.path.getsize(temp_path)} bytes")

        # Extract text using PyMuPDF
        try:
            import fitz
            print("Extracting text with PyMuPDF...")

            doc = fitz.open(temp_path)
            text_parts = []
            for page_num in range(min(len(doc), 5)):  # First 5 pages only
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                text_parts.append(page_text)

            full_text = "\n".join(text_parts)
            print(f"Extracted {len(full_text)} characters")
            print(f"First 500 chars: {full_text[:500]}...")

        except ImportError:
            print("PyMuPDF not available")
        except Exception as e:
            print(f"Text extraction failed: {e}")

        # Clean up
        os.unlink(temp_path)
        print("Cleaned up temp file")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    url = "https://www.courthousenews.com/wp-content/uploads/2025/09/g-ross-intelligence-redacted-brief-thomson-reuters-interlocutory-appeal-third-circuit.pdf"
    quick_url_test(url)
