import sys
import os
import traceback
import time
from pdf_handler import extract_text_from_pdf


def main():
    """Test the PDF extraction on a specific file."""
    # Check if a file path was provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default to the problematic file in Downloads folder
        pdf_path = os.path.expanduser("~/Downloads/999562 Plaintiff Opening Brief.pdf")

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        print("Checking if file exists at absolute path...")
        absolute_path = os.path.abspath(pdf_path)
        print(f"Absolute path: {absolute_path}")
        if os.path.exists(absolute_path):
            print(f"File exists at absolute path: {absolute_path}")
            pdf_path = absolute_path
        else:
            print("File does not exist at absolute path either.")
            print("Checking Downloads folder...")
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            print(f"Downloads path: {downloads_path}")
            if os.path.exists(downloads_path):
                print("Downloads folder exists, checking contents:")
                files = os.listdir(downloads_path)
                pdf_files = [f for f in files if f.lower().endswith(".pdf")]
                print(f"Found {len(pdf_files)} PDF files in Downloads folder:")
                for i, file in enumerate(pdf_files):
                    print(f"  {i+1}. {file}")
                if pdf_files:
                    print(
                        "\nPlease specify the full path to the PDF file you want to process."
                    )
                    print("Usage: python test_pdf.py [path_to_pdf]")
                    return
            print("\nNo PDF files found in Downloads folder.")
            print("Usage: python test_pdf.py [path_to_pdf]")
            return

    print(f"\nTesting PDF extraction on: {pdf_path}")
    print(f"File exists: {os.path.exists(pdf_path)}")
    print(f"File size: {os.path.getsize(pdf_path)} bytes")
    print("Using robust extraction methods...")

    try:
        # Start timer
        start_time = time.time()

        # Extract text from the PDF
        text = extract_text_from_pdf(pdf_path)

        # End timer
        end_time = time.time()
        elapsed_time = end_time - start_time

        # Check if extraction was successful
        if text and isinstance(text, str):
            if text.startswith("Error:"):
                print(f"\nExtraction failed: {text}")
                print(f"Elapsed time: {elapsed_time:.2f} seconds")
                return
        else:
            print(f"\nExtraction returned invalid result: {type(text)}")
            print(f"Elapsed time: {elapsed_time:.2f} seconds")
            return
    except Exception as e:
        print(f"\nException during extraction: {e}")
        traceback.print_exc()
        return

    # Print statistics and sample of extracted text
    print(f"Successfully extracted {len(text)} characters")
    print("\nFirst 300 characters:")
    print("-" * 50)
    print(text[:300])
    print("-" * 50)

    # Save the extracted text to a file
    output_file = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_extracted.txt"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\nExtracted text saved to: {output_file}")
    except Exception as e:
        print(f"Error saving extracted text: {e}")


if __name__ == "__main__":
    main()
