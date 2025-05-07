import os
import sys
import PyPDF2
import traceback

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file with detailed logging."""
    print(f"Attempting to extract text from PDF: {file_path}")
    
    try:
        # Check if file exists and is readable
        if not os.path.exists(file_path):
            print(f"PDF file does not exist: {file_path}")
            return None
            
        file_size = os.path.getsize(file_path)
        print(f"PDF file size: {file_size} bytes")
        
        if file_size == 0:
            print(f"PDF file is empty: {file_path}")
            return None
            
        # Try to open and read the file
        with open(file_path, 'rb') as file:
            # Read first few bytes to check if it's a valid PDF
            header = file.read(5)
            print(f"PDF header bytes: {header}")
            
            if header != b'%PDF-':
                print(f"File does not appear to be a valid PDF (header: {header})")
                # Try to continue anyway
            
            # Reset file pointer to beginning
            file.seek(0)
            
            print("Creating PdfReader object...")
            reader = PyPDF2.PdfReader(file)
            
            print(f"PDF has {len(reader.pages)} pages")
            text = ''
            
            # Process each page with error handling
            for i, page in enumerate(reader.pages):
                try:
                    print(f"Extracting text from page {i+1}...")
                    page_text = page.extract_text()
                    print(f"Extracted {len(page_text)} characters from page {i+1}")
                    text += page_text + '\n'
                except Exception as page_error:
                    print(f"Error extracting text from page {i+1}: {page_error}")
                    traceback.print_exc()
            
            print(f"Successfully extracted {len(text)} characters from PDF")
            
            # Save the extracted text to a file for inspection
            try:
                output_file = 'extracted_pdf_text.txt'
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"Extracted PDF text saved to {output_file}")
            except Exception as e:
                print(f"Error saving extracted text to file: {e}")
                traceback.print_exc()
            
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_test.py <path_to_pdf_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    print(f"Testing PDF extraction on file: {file_path}")
    
    text = extract_text_from_pdf(file_path)
    
    if text:
        print(f"Successfully extracted {len(text)} characters of text")
        print("\nFirst 500 characters of extracted text:")
        print("-" * 80)
        print(text[:500])
        print("-" * 80)
    else:
        print("Failed to extract text from PDF")
