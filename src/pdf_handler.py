import os
import sys
import io
import tempfile
import shutil
import subprocess
import traceback
import PyPDF2
from io import StringIO
from datetime import datetime
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.high_level import extract_text as pdfminer_extract_text
from PIL import ImageEnhance
import re

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using multiple methods with robust error handling."""
    try:
        # Try PyPDF2 first with enhanced settings
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                all_text = ""
                for page in reader.pages:
                    # Extract text with enhanced settings
                    page_text = page.extract_text()
                    if page_text:
                        # Clean up the text
                        page_text = re.sub(r'\s+', ' ', page_text)  # Normalize whitespace
                        page_text = re.sub(r'([A-Z])\.\s+([A-Z])', r'\1.\2', page_text)  # Fix spacing in abbreviations
                        all_text += page_text + "\n"
                
                if all_text.strip():
                    print("Successfully extracted text using PyPDF2")
                    return clean_extracted_text(all_text)
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
        
        # Try with enhanced pdfminer settings
        try:
            # Configure pdfminer for better text extraction
            laparams = LAParams(
                line_margin=0.3,  # Reduced line margin for better line break handling
                word_margin=0.1,  # Reduced word margin for better word spacing
                char_margin=1.5,  # Adjusted char margin for better character spacing
                boxes_flow=0.5,   # Adjusted flow of text boxes
                detect_vertical=True,  # Enable vertical text detection
                all_texts=True   # Extract all text elements
            )
            
            resource_manager = PDFResourceManager()
            text_output = io.StringIO()
            converter = TextConverter(resource_manager, text_output, laparams=laparams)
            interpreter = PDFPageInterpreter(resource_manager, converter)
            
            with open(file_path, 'rb') as file:
                for page in PDFPage.get_pages(file):
                    interpreter.process_page(page)
            
            text = text_output.getvalue()
            converter.close()
            text_output.close()
            
            if text and len(text.strip()) > 0:
                print("Successfully extracted text using enhanced pdfminer settings")
                return clean_extracted_text(text)
        except Exception as e:
            print(f"Enhanced pdfminer extraction failed: {e}")
        
        # If both methods fail, try using pdfminer's high-level extract_text function
        try:
            text = pdfminer_extract_text(file_path)
            if text and len(text.strip()) > 0:
                print("Successfully extracted text using pdfminer's high-level function")
                return clean_extracted_text(text)
        except Exception as e:
            print(f"pdfminer high-level extraction failed: {e}")
        
        return "Could not extract text from PDF. The file may be scanned, protected, or corrupted."
    except Exception as e:
        print(f"Error in extract_text_from_pdf: {e}")
        return None

def clean_extracted_text(text):
    """Clean and normalize extracted text to improve citation detection."""
    if not text:
        return ""
    
    try:
        # Remove non-printable characters but preserve citation patterns
        text = ''.join(char for char in text if char.isprintable() or char in '.,;:()[]{}')
        
        # Fix common OCR errors in citations - using raw strings and simpler patterns
        text = re.sub(r'(\d+)\s*[Uu]\.?\s*[Ss]\.?\s*(\d+)', r'\1 U.S. \2', text)  # Fix U.S. spacing
        text = re.sub(r'(\d+)\s*[Ss]\.?\s*[Cc][Tt]\.?\s*(\d+)', r'\1 S.Ct. \2', text)  # Fix S.Ct. spacing
        text = re.sub(r'(\d+)\s*[Ll]\.?\s*[Ee][Dd]\.?\s*(\d+)', r'\1 L.Ed. \2', text)  # Fix L.Ed. spacing
        text = re.sub(r'(\d+)\s*[Ff]\.?\s*(?:2[Dd]|3[Dd]|4[Tt][Hh])?\s*(\d+)', r'\1 F. \2', text)  # Fix F. spacing
        
        # Fix line breaks within citations
        text = re.sub(r'(\d+)\s*U\.?\s*S\.?\s*\n\s*(\d+)', r'\1 U.S. \2', text)
        text = re.sub(r'(\d+)\s*S\.?\s*Ct\.?\s*\n\s*(\d+)', r'\1 S.Ct. \2', text)
        text = re.sub(r'(\d+)\s*L\.?\s*Ed\.?\s*\n\s*(\d+)', r'\1 L.Ed. \2', text)
        text = re.sub(r'(\d+)\s*F\.?\s*(?:2d|3d|4th)?\s*\n\s*(\d+)', r'\1 F. \2', text)
        
        # Fix page breaks within citations
        text = re.sub(r'(\d+)\s*U\.?\s*S\.?\s*-\s*(\d+)', r'\1 U.S. \2', text)  # Fix page break markers
        text = re.sub(r'(\d+)\s*S\.?\s*Ct\.?\s*-\s*(\d+)', r'\1 S.Ct. \2', text)
        text = re.sub(r'(\d+)\s*L\.?\s*Ed\.?\s*-\s*(\d+)', r'\1 L.Ed. \2', text)
        text = re.sub(r'(\d+)\s*F\.?\s*(?:2d|3d|4th)?\s*-\s*(\d+)', r'\1 F. \2', text)
        
        # Fix common OCR errors in numbers - using simpler patterns
        text = re.sub(r'[Oo](\d)', r'0\1', text)  # Fix O/0 confusion
        text = re.sub(r'(\d)[Oo]', r'\10', text)  # Fix O/0 confusion at end of numbers
        text = re.sub(r'[lI](\d)', r'1\1', text)  # Fix l/I/1 confusion
        text = re.sub(r'(\d)[lI]', r'\11', text)  # Fix l/I/1 confusion at end of numbers
        
        # Fix spacing in abbreviations
        text = re.sub(r'([A-Z])\.\s+([A-Z])', r'\1.\2', text)
        
        # Normalize whitespace while preserving citation patterns
        text = re.sub(r'\s+', ' ', text)
        
        # Remove any remaining page numbers or headers/footers
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    except Exception as e:
        print(f"Error in clean_extracted_text: {e}")
        # Return the original text if cleaning fails
        return text.strip()

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
