import requests
import tempfile
import os
import re
import PyPDF2
from bs4 import BeautifulSoup
import json


def fetch_url_content(url):
    """Fetch content from a URL and extract text."""
    print(f"Fetching content from URL: {url}")

    # Validate URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Set headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        # Fetch the URL content
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses

        # Check content type to handle different file types
        content_type = response.headers.get("Content-Type", "").lower()
        print(f"Content type: {content_type}")

        # Handle PDF files directly
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            print("Detected PDF file, using direct PDF extraction")

            # Create a temporary file to store the PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                # Download the PDF in chunks to avoid memory issues
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)

                temp_file_path = temp_file.name

            print(f"PDF saved to temporary file: {temp_file_path}")

            try:
                # Extract text from PDF
                text = ""
                with open(temp_file_path, "rb") as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    num_pages = len(pdf_reader.pages)
                    print(f"PDF has {num_pages} pages")

                    # Limit to first 20 pages for large PDFs
                    max_pages = min(num_pages, 20)
                    print(f"Processing first {max_pages} pages")

                    for page_num in range(max_pages):
                        print(
                            f"Extracting text from page {page_num + 1}/{max_pages}..."
                        )
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"

                # Clean up the text (remove excessive whitespace)
                text = re.sub(r"\s+", " ", text).strip()
                print(f"Extracted {len(text)} characters from PDF")

                # Save the extracted text to a file for inspection
                with open("extracted_text.txt", "w", encoding="utf-8") as f:
                    f.write(text)
                print("Saved extracted text to extracted_text.txt")

                # Clean up the temporary file
                os.unlink(temp_file_path)

                return text
            except Exception as e:
                print(f"Error extracting text from PDF: {e}")
                # Clean up the temporary file
                os.unlink(temp_file_path)
                raise
        else:
            # Handle HTML and other text-based content
            print("Processing as HTML/text content")

            # Parse the HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text content
            text = soup.get_text(separator=" ", strip=True)

            # Clean up the text (remove excessive whitespace)
            text = re.sub(r"\s+", " ", text).strip()

            print(f"Extracted {len(text)} characters from HTML")

            # Save the extracted text to a file for inspection
            with open("extracted_text.txt", "w", encoding="utf-8") as f:
                f.write(text)
            print("Saved extracted text to extracted_text.txt")

            return text
    except Exception as e:
        print(f"Error fetching URL: {e}")
        raise


def extract_citations(text):
    """Extract citations from text using regex patterns."""
    print("Extracting citations from text...")

    # Define regex patterns for common citation formats
    patterns = [
        r"\d+ U\.S\. \d+",  # US Reports
        r"\d+ S\. ?Ct\. \d+",  # Supreme Court Reporter
        r"\d+ L\. ?Ed\. ?\d+",  # Lawyers' Edition
        r"\d+ F\.\d+d \d+",  # Federal Reporter
        r"\d+ F\. ?Supp\. ?\d+d? \d+",  # Federal Supplement
    ]

    # Combine patterns
    combined_pattern = "|".join(f"({pattern})" for pattern in patterns)

    # Find all citations
    import re

    citations = re.findall(combined_pattern, text)

    # Flatten the list of tuples
    citations = [c for group in citations for c in group if c]

    print(f"Found {len(citations)} citations")

    # Print first 10 citations
    for i, citation in enumerate(citations[:10]):
        print(f"  {i+1}. {citation}")

    if len(citations) > 10:
        print(f"  ... and {len(citations) - 10} more")

    return citations


def main():
    """Main function to test URL handling."""
    # URL to test
    url = "https://www.gibbonslawalert.com/wp-content/uploads/2023/07/Mata-v.-Avianca-Sanctions-opinion.pdf"

    try:
        # Fetch content from URL
        text = fetch_url_content(url)

        # Extract citations
        citations = extract_citations(text)

        # Save citations to a JSON file
        with open("citations.json", "w") as f:
            json.dump(citations, f, indent=2)
        print("Saved citations to citations.json")

        print("\nURL handling test completed successfully!")
    except Exception as e:
        print(f"Error in main function: {e}")


if __name__ == "__main__":
    main()
