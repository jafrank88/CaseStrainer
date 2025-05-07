import os
import sys
import traceback
import PyPDF2

def extract_with_pypdf2(file_path):
    """Extract text from a PDF file using PyPDF2."""
    print("\n=== EXTRACTING WITH PYPDF2 ===")
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"PDF has {len(reader.pages)} pages")
            text = ''
            for i, page in enumerate(reader.pages):
                try:
                    print(f"Extracting text from page {i+1}...")
                    page_text = page.extract_text()
                    text += page_text + '\n'
                except Exception as e:
                    print(f"Error extracting text from page {i+1}: {e}")
            
            print(f"Successfully extracted {len(text)} characters with PyPDF2")
            return text
    except Exception as e:
        print(f"Error with PyPDF2: {e}")
        traceback.print_exc()
        return None

def extract_with_textract():
    """Try to install and use textract for PDF extraction."""
    print("\n=== TRYING TO INSTALL TEXTRACT ===")
    try:
        import pip
        pip.main(['install', 'textract'])
        import textract
        print("Textract installed successfully")
        return True
    except Exception as e:
        print(f"Error installing textract: {e}")
        traceback.print_exc()
        return False

def extract_with_pdfminer():
    """Try to install and use pdfminer.six for PDF extraction."""
    print("\n=== TRYING TO INSTALL PDFMINER.SIX ===")
    try:
        import pip
        pip.main(['install', 'pdfminer.six'])
        print("pdfminer.six installed successfully")
        return True
    except Exception as e:
        print(f"Error installing pdfminer.six: {e}")
        traceback.print_exc()
        return False

def extract_with_pdfminer_method(file_path):
    """Extract text from a PDF file using pdfminer.six."""
    print("\n=== EXTRACTING WITH PDFMINER.SIX ===")
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(file_path)
        print(f"Successfully extracted {len(text)} characters with pdfminer.six")
        return text
    except Exception as e:
        print(f"Error with pdfminer.six: {e}")
        traceback.print_exc()
        return None

def extract_with_textract_method(file_path):
    """Extract text from a PDF file using textract."""
    print("\n=== EXTRACTING WITH TEXTRACT ===")
    try:
        import textract
        text = textract.process(file_path, method='pdfminer').decode('utf-8')
        print(f"Successfully extracted {len(text)} characters with textract")
        return text
    except Exception as e:
        print(f"Error with textract: {e}")
        traceback.print_exc()
        return None

def save_text_to_file(text, filename):
    """Save extracted text to a file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Text saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving text to file: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python robust_pdf_test.py <path_to_pdf_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    print(f"Testing PDF extraction on file: {file_path}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        sys.exit(1)
    
    # Try PyPDF2 first
    pypdf2_text = extract_with_pypdf2(file_path)
    if pypdf2_text:
        save_text_to_file(pypdf2_text, "extracted_pypdf2.txt")
        print("\nFirst 500 characters extracted with PyPDF2:")
        print("-" * 80)
        print(pypdf2_text[:500])
        print("-" * 80)
    
    # Try pdfminer.six
    if extract_with_pdfminer():
        pdfminer_text = extract_with_pdfminer_method(file_path)
        if pdfminer_text:
            save_text_to_file(pdfminer_text, "extracted_pdfminer.txt")
            print("\nFirst 500 characters extracted with pdfminer.six:")
            print("-" * 80)
            print(pdfminer_text[:500])
            print("-" * 80)
    
    # Try textract as a last resort
    if extract_with_textract():
        textract_text = extract_with_textract_method(file_path)
        if textract_text:
            save_text_to_file(textract_text, "extracted_textract.txt")
            print("\nFirst 500 characters extracted with textract:")
            print("-" * 80)
            print(textract_text[:500])
            print("-" * 80)
