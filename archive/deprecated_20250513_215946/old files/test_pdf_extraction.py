import sys
import os
import PyPDF2


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file and save it to a text file."""
    print(f"Extracting text from PDF: {file_path}")

    if not os.path.exists(file_path):
        print(f"Error: File does not exist: {file_path}")
        return

    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            print(f"PDF has {len(reader.pages)} pages")

            text = ""
            for i, page in enumerate(reader.pages):
                print(f"Extracting text from page {i+1}/{len(reader.pages)}")
                page_text = page.extract_text()
                text += page_text + "\n"

            print(f"Successfully extracted {len(text)} characters")

            # Save the extracted text to a file
            output_file = "extracted_pdf_text_direct.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"Extracted text saved to {output_file}")

            # Print a sample of the extracted text
            print("\nSample of extracted text (first 500 characters):")
            print(text[:500])
            print("...")

            # Print a sample from the middle of the document
            middle = len(text) // 2
            print(
                f"\nSample from middle of document (characters {middle} to {middle+500}):"
            )
            print(text[middle : middle + 500])
            print("...")

            # Print the last 500 characters
            print("\nSample from end of document (last 500 characters):")
            print(text[-500:])

            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pdf_extraction.py <path_to_pdf_file>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    extract_text_from_pdf(pdf_path)
