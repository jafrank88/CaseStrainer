import os
import logging
import sys
import json
from src.file_utils import extract_text_from_file
from enhanced_validator_production import enhanced_analyze

# Configure logging to output to console with DEBUG level for all modules
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

# Ensure that the src.file_utils logger is set to DEBUG level and has a console handler
file_utils_logger = logging.getLogger('src.file_utils')
file_utils_logger.setLevel(logging.DEBUG)

# Remove any existing handlers to avoid duplication or conflicts
file_utils_logger.handlers = []

# Add a new console handler to ensure output to stdout
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
console_handler.setFormatter(formatter)
file_utils_logger.addHandler(console_handler)

# Path to the PDF file provided by the user
PDF_FILE_PATH = r"C:\Users\jafrank\Downloads\gov.uscourts.wyd.64014.141.0_1.pdf"

def main():
    if not os.path.exists(PDF_FILE_PATH):
        print(f"Error: PDF file not found at {PDF_FILE_PATH}")
        sys.exit(1)
    
    print(f"Processing PDF file: {PDF_FILE_PATH}")
    try:
        # Extract text with PDF to Markdown conversion enabled
        print("Starting text extraction with Markdown conversion...")
        text = extract_text_from_file(PDF_FILE_PATH, convert_pdf_to_md=True)
        if text and text.strip():
            print(f"Successfully extracted text: {len(text)} characters")
            # Optionally, save the output to a file for review
            output_path = "extracted_text.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Extracted text saved to {output_path}")
            
            # Now analyze the text for citations
            print("Analyzing extracted text for citations...")
            request_data = {
                'text': text,
                'options': {
                    'convert_pdf_to_md': True
                }
            }
            analysis_result = enhanced_analyze(request_data)
            
            # Check if analysis_result contains citations
            if isinstance(analysis_result, dict) and 'validation_results' in analysis_result:
                print("\nCitations found in the document:")
                citations = analysis_result.get('validation_results', [])
                if citations:
                    for idx, citation in enumerate(citations, 1):
                        citation_text = citation.get('citation', '')
                        verified = citation.get('verified', False)
                        status = "Verified" if verified else "Not Verified"
                        print(f"{idx}. {citation_text} - {status}")
                else:
                    print("No citations found in the document.")
            else:
                print("Analysis did not return citation data. Result format unexpected.")
                print(f"Analysis result: {json.dumps(analysis_result, indent=2)[:1000]}... (truncated)")
        else:
            print("Failed to extract text or extracted content is empty")
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        logging.error(f"Error during processing: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
