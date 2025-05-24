import requests
import PyPDF2
import io
import re


def download_and_analyze_pdf():
    # Download the PDF
    url = "https://www.supremecourt.gov/opinions/24pdf/23-715_5426.pdf"
    print(f"Downloading PDF from {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Save the PDF
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
        print("PDF downloaded successfully")

        # Read the PDF
        with open("temp.pdf", "rb") as f:
            reader = PyPDF2.PdfReader(f)
            print(f"PDF has {len(reader.pages)} pages")

            # Extract text from all pages
            all_text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n"

            # --- Text Normalization and PDF Fixes ---
            # 1. Remove hyphenation at line breaks (e.g., 'exam-\nple' -> 'example')
            all_text = re.sub(r"-\n(\w+)", r"\1", all_text)
            # 2. Replace line breaks in the middle of sentences with a space
            all_text = re.sub(r"(?<!\n)\n(?!\n)", " ", all_text)
            # 3. Collapse multiple spaces
            all_text = re.sub(r"\s+", " ", all_text)
            # 4. Strip leading/trailing whitespace
            all_text = all_text.strip()

            print("\nFirst 1000 characters of normalized text:")
            print(all_text[:1000])

            # Look for citations with more flexible patterns
            citation_patterns = [
                r"\b\d+\s+U\.?\s*S\.?\s+\d+\b",  # U.S. Reports (more flexible)
                r"\b\d+\s+S\.?\s*Ct\.?\s+\d+\b",  # Supreme Court Reporter (more flexible)
                r"\b\d+\s+L\.?\s*Ed\.?\s+\d+\b",  # Lawyers Edition (more flexible)
                r"\b\d+\s+U\.?\s*S\.?\s+C\.?\s+\d+\b",  # U.S. Court of Appeals
                r"\b\d+\s+F\.?\s*(?:2d|3d|4th)?\s+\d+\b",  # Federal Reporter
                r"\b\d+\s+F\.?\s*Supp\.?\s*(?:2d|3d)?\s+\d+\b",  # Federal Supplement
            ]

            print("\nSearching for citations...")
            found_citations = set()
            for pattern in citation_patterns:
                matches = re.finditer(pattern, all_text)
                for match in matches:
                    citation = match.group()
                    # Clean up the citation
                    citation = re.sub(r"\s+", " ", citation)  # Normalize spaces
                    citation = re.sub(
                        r"\.\s+", ".", citation
                    )  # Remove spaces after periods
                    found_citations.add(citation)

            print("\nFound citations:")
            for citation in sorted(found_citations):
                print(f"- {citation}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    download_and_analyze_pdf()
