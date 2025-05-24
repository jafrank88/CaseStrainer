import os
import sys
import traceback


def install_pdfminer():
    """Install pdfminer.six package."""
    print("Installing pdfminer.six...")
    try:
        import pip

        pip.main(["install", "pdfminer.six"])
        print("pdfminer.six installed successfully")
        return True
    except Exception as e:
        print(f"Error installing pdfminer.six: {e}")
        traceback.print_exc()
        return False


def extract_text_with_pdfminer(file_path):
    """Extract text from a PDF file using pdfminer.six."""
    try:
        from pdfminer.high_level import extract_text

        print(f"Extracting text from {file_path}...")
        text = extract_text(file_path)
        print(f"Successfully extracted {len(text)} characters")
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        traceback.print_exc()
        return None


def save_text_to_file(text, filename):
    """Save extracted text to a file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Text saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving text to file: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdfminer_test.py <path_to_pdf_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"Testing PDF extraction on file: {file_path}")

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        sys.exit(1)

    # Install pdfminer.six if needed
    if install_pdfminer():
        # Extract text
        extracted_text = extract_text_with_pdfminer(file_path)
        if extracted_text:
            # Save to file
            save_text_to_file(extracted_text, "extracted_pdfminer.txt")

            # Display sample
            print("\nFirst 500 characters of extracted text:")
            print("-" * 80)
            print(extracted_text[:500])
            print("-" * 80)
        else:
            print("Failed to extract text from PDF")
    else:
        print("Failed to install pdfminer.six")
