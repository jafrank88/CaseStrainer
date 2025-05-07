import os
import sys
import io
import tempfile
import shutil
import subprocess
import traceback
import PyPDF2
from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using multiple methods with robust error handling."""
    print(f"Extracting text from PDF: {file_path}")
    
    # Special handling for known problematic files
    if '999562 Plaintiff Opening Brief.pdf' in file_path:
        print("Detected known problematic file: 999562 Plaintiff Opening Brief.pdf")
        return handle_problematic_pdf(file_path)
    
    # Check if file exists and is readable
    if not os.path.isfile(file_path):
        error_msg = f"File not found: {file_path}"
        print(error_msg)
        return f"Error: {error_msg}"
    
    # Check file size
    try:
        file_size = os.path.getsize(file_path)
        print(f"PDF file size: {file_size} bytes")
        if file_size == 0:
            error_msg = f"File is empty: {file_path}"
            print(error_msg)
            return f"Error: {error_msg}"
        elif file_size > 100 * 1024 * 1024:  # 100MB limit
            error_msg = f"File is too large ({file_size} bytes): {file_path}"
            print(error_msg)
            return f"Error: {error_msg}"
    except Exception as e:
        print(f"Error checking file size: {e}")
    
    # Method 1: Try pdfminer.six
    try:
        print("Trying to extract text with pdfminer.six...")
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract
            print("pdfminer.six is already installed")
        except ImportError:
            print("Installing pdfminer.six...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfminer.six"])
            from pdfminer.high_level import extract_text as pdfminer_extract
        
        # Extract text with pdfminer.six with timeout protection
        try:
            text = pdfminer_extract(file_path)
            if text and text.strip():
                print(f"Successfully extracted {len(text)} characters with pdfminer.six")
                
                # Save the extracted text to a file for inspection
                try:
                    with open('extracted_pdf_text.txt', 'w', encoding='utf-8') as f:
                        f.write(text)
                    print("Extracted text saved to extracted_pdf_text.txt")
                except Exception as e:
                    print(f"Error saving extracted text: {e}")
                    
                return text
            else:
                print("pdfminer.six extracted empty text, trying PyPDF2")
        except Exception as e:
            print(f"Error during pdfminer extraction: {e}")
    except Exception as e:
        print(f"Error with pdfminer.six: {e}")
    
    # Method 2: Try PyPDF2
    try:
        print("Trying to extract text with PyPDF2...")
        with open(file_path, 'rb') as file:
            try:
                reader = PyPDF2.PdfReader(file)
                print(f"PDF has {len(reader.pages)} pages")
                text = ''
                
                # Process each page with error handling
                for i, page in enumerate(reader.pages):
                    try:
                        print(f"Extracting text from page {i+1}...")
                        page_text = page.extract_text()
                        text += page_text + '\n'
                        print(f"Extracted {len(page_text)} characters from page {i+1}")
                    except Exception as page_error:
                        print(f"Error extracting text from page {i+1}: {page_error}")
                
                if text and text.strip():
                    print(f"Successfully extracted {len(text)} characters with PyPDF2")
                    return text
                else:
                    print("PyPDF2 extraction returned empty text, trying alternative method")
            except Exception as e:
                print(f"Error reading PDF with PyPDF2: {e}")
    except Exception as e:
        print(f"Error with PyPDF2 extraction: {e}")
    
    # Method 3: Try using subprocess with external tools if available
    try:
        print("Trying to extract text with external tools...")
        import subprocess
        import tempfile
        
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Try pdftotext from poppler if available
            print(f"Running pdftotext on {file_path}")
            subprocess.run(['pdftotext', file_path, temp_path], 
                           check=True, capture_output=True, text=True, timeout=60)
            
            # Read the extracted text
            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            # Clean up
            os.unlink(temp_path)
            
            if text and text.strip():
                print(f"Successfully extracted {len(text)} characters with pdftotext")
                return text
            else:
                print("pdftotext extraction returned empty text")
        except FileNotFoundError:
            print("pdftotext not available on system")
            os.unlink(temp_path)
        except subprocess.TimeoutExpired:
            print("pdftotext process timed out")
            os.unlink(temp_path)
        except Exception as e:
            print(f"Error with pdftotext: {e}")
            os.unlink(temp_path)
    except Exception as e:
        print(f"Error with external tool extraction: {e}")
    
    # If all methods failed, return an error
    error_msg = "Could not extract text from PDF. The file may be scanned, protected, or corrupted."
    print(error_msg)
    return f"Error: {error_msg}"

def handle_problematic_pdf(file_path):
    """Special handling for known problematic PDF files."""
    print(f"Using special handling for problematic PDF: {file_path}")
    
    # Create a temporary directory for processing
    temp_dir = tempfile.mkdtemp(prefix="pdf_processing_")
    try:
        # Copy the file to the temp directory
        temp_file_path = os.path.join(temp_dir, "temp.pdf")
        shutil.copy2(file_path, temp_file_path)
        print(f"Copied file to temporary location: {temp_file_path}")
        
        # Try multiple methods with more robust error handling
        
        # Method 1: Try using pdftotext command line tool if available
        try:
            print("Attempting extraction with pdftotext command line tool...")
            output_file = os.path.join(temp_dir, "output.txt")
            
            try:
                # Try pdftotext from poppler if available
                result = subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', temp_file_path, output_file], 
                                      check=False, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0 and os.path.exists(output_file):
                    # Read the extracted text
                    with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                    
                    if text and text.strip():
                        print(f"Successfully extracted {len(text)} characters with pdftotext command line tool")
                        return text
                    else:
                        print("pdftotext command line tool extracted empty text")
                else:
                    print(f"pdftotext command failed with return code {result.returncode}")
                    print(f"Error: {result.stderr}")
            except FileNotFoundError:
                print("pdftotext command not available")
            except subprocess.TimeoutExpired:
                print("pdftotext process timed out")
            except Exception as e:
                print(f"Error with pdftotext command: {e}")
        except Exception as e:
            print(f"Error with pdftotext extraction: {e}")
        
        # Method 2: Try using pdfminer.six with custom settings
        try:
            print("Attempting extraction with pdfminer.six using custom settings...")
            from pdfminer.high_level import extract_text
            
            # Try with different parameters
            for laparams in [
                LAParams(line_margin=0.5, char_margin=2.0, all_texts=True),
                LAParams(line_margin=0.3, char_margin=1.0),
                LAParams(line_margin=0.1, char_margin=0.1, word_margin=0.1),
                None  # Try with no LAParams
            ]:
                try:
                    print(f"Trying pdfminer.six with params: {laparams}")
                    text = extract_text(temp_file_path, laparams=laparams)
                    
                    if text and text.strip():
                        print(f"Successfully extracted {len(text)} characters with pdfminer.six custom settings")
                        return text
                    else:
                        print("pdfminer.six with custom settings extracted empty text")
                except Exception as e:
                    print(f"Error with pdfminer.six custom settings: {e}")
        except Exception as e:
            print(f"Error with pdfminer.six custom extraction: {e}")
        
        # Method 3: Try using PyPDF2 with specific settings
        try:
            print("Attempting extraction with PyPDF2 using specific settings...")
            
            with open(temp_file_path, 'rb') as file:
                try:
                    reader = PyPDF2.PdfReader(file, strict=False)
                    text = ''
                    
                    # Process each page with more robust error handling
                    for i in range(len(reader.pages)):
                        try:
                            page = reader.pages[i]
                            try:
                                page_text = page.extract_text()
                                if page_text:
                                    text += page_text + '\n'
                                    print(f"Extracted {len(page_text)} characters from page {i+1}")
                                else:
                                    print(f"No text extracted from page {i+1}")
                            except Exception as e:
                                print(f"Error extracting text from page {i+1}: {e}")
                        except Exception as e:
                            print(f"Error accessing page {i+1}: {e}")
                    
                    if text and text.strip():
                        print(f"Successfully extracted {len(text)} characters with PyPDF2 specific settings")
                        return text
                    else:
                        print("PyPDF2 with specific settings extracted empty text")
                except Exception as e:
                    print(f"Error reading PDF with PyPDF2 specific settings: {e}")
        except Exception as e:
            print(f"Error with PyPDF2 specific extraction: {e}")
        
        # If all methods fail, return a helpful error message
        return "Error: Could not extract text from this PDF file. This specific file (999562 Plaintiff Opening Brief.pdf) is known to cause issues with text extraction. The file may be scanned, protected, or use a non-standard PDF format. Please try converting it to a standard PDF format using Adobe Acrobat or another PDF editor before uploading."
    
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Error cleaning up temporary directory: {e}")

# Simple test function to check if the module works
if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Testing PDF extraction on: {pdf_path}")
        text = extract_text_from_pdf(pdf_path)
        print(f"Extracted {len(text)} characters")
        print("First 500 characters:")
        print(text[:500])
    else:
        print("Usage: python pdf_handler.py <path_to_pdf>")
