import os
import logging
import tempfile
import subprocess
import sys
import time
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)

# Try to import PDF processing libraries
try:
    from src.document_processing_unified import extract_text_from_file
except ImportError:
    extract_text_from_file = None

# Check if pdf2md is available (commented out due to Pylance warning)
# try:
#     from pdf2md import extract_text as pdf2md_extract_text
#     PDF2MD_AVAILABLE = True
# except ImportError:
#     PDF2MD_AVAILABLE = False
PDF2MD_AVAILABLE = False

# Check if pdfminer is available
try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

# Check if pdf2md is installed as a command line tool
def is_pdf2md_installed():
    try:
        subprocess.run(['pdf2md', '--version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

PDF2MD_CMD_AVAILABLE = is_pdf2md_installed()

def convert_pdf_to_markdown(pdf_path):
    """
    Convert a PDF file to markdown format using available tools.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted markdown text or None if conversion fails
    """
    try:
        logger.debug(f"[PDF2MD_DEBUG] Starting PDF to Markdown conversion for file: {pdf_path}")
        logger.debug(f"[PDF2MD_DEBUG] File size: {os.path.getsize(pdf_path)} bytes")
        logger.debug(f"[PDF2MD_DEBUG] Checking availability of conversion tools")
        logger.debug(f"[PDF2MD_DEBUG] pdf2md Python library available: {PDF2MD_AVAILABLE}")
        logger.debug(f"[PDF2MD_DEBUG] pdf2md command-line tool available: {PDF2MD_CMD_AVAILABLE}")
        logger.debug(f"[PDF2MD_DEBUG] pdfminer library available: {PDFMINER_AVAILABLE}")

        # Try using pdf2md Python library (commented out due to Pylance warning - function not defined)
        # if PDF2MD_AVAILABLE:
        #     try:
        #         logger.debug("[PDF2MD_DEBUG] Attempting conversion with pdf2md Python library")
        #         start_time = time.time()
        #         result = pdf2md_extract_text(pdf_path)
        #         elapsed_time = time.time() - start_time
        #         logger.debug(f"[PDF2MD_DEBUG] pdf2md library conversion took {elapsed_time:.2f} seconds")
        #         logger.debug(f"[PDF2MD_DEBUG] pdf2md library result: {len(result) if result else 0} characters")
        #         if result:
        #             logger.debug(f"[PDF2MD_DEBUG] First 200 characters of result: {result[:200].replace('\n', ' ')}...")
        #         return result
        #     except Exception as e:
        #         logger.warning(f"[PDF2MD_DEBUG] pdf2md library failed: {str(e)}", exc_info=True)
        
        # Try using pdf2md command line tool
        if PDF2MD_CMD_AVAILABLE:
            try:
                logger.debug("[PDF2MD_DEBUG] Attempting conversion with pdf2md command-line tool")
                start_time = time.time()
                with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                logger.debug(f"[PDF2MD_DEBUG] Created temporary file for Markdown output: {temp_path}")
                result = subprocess.run(
                    ['pdf2md', '-o', temp_path, pdf_path],
                    capture_output=True,
                    text=True
                )
                elapsed_time = time.time() - start_time
                logger.debug(f"[PDF2MD_DEBUG] pdf2md command-line conversion took {elapsed_time:.2f} seconds")
                logger.debug(f"[PDF2MD_DEBUG] pdf2md command return code: {result.returncode}")
                logger.debug(f"[PDF2MD_DEBUG] pdf2md command stdout: {result.stdout}")
                if result.stderr:
                    logger.debug(f"[PDF2MD_DEBUG] pdf2md command stderr: {result.stderr}")
                
                if result.returncode == 0 and os.path.exists(temp_path):
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    logger.debug(f"[PDF2MD_DEBUG] Successfully read Markdown content from temp file: {len(content)} characters")
                    if content:
                        logger.debug(f"[PDF2MD_DEBUG] First 200 characters of content: {content[:200].replace('\n', ' ')}...")
                    return content
                else:
                    logger.warning(f"[PDF2MD_DEBUG] pdf2md command failed with return code {result.returncode}")
            except Exception as e:
                logger.warning(f"[PDF2MD_DEBUG] pdf2md command failed: {str(e)}", exc_info=True)
            finally:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                        logger.debug(f"[PDF2MD_DEBUG] Deleted temporary file: {temp_path}")
                    except Exception as e:
                        logger.warning(f"[PDF2MD_DEBUG] Failed to delete temporary file {temp_path}: {str(e)}")
        
        # Fall back to pdfminer with basic markdown formatting
        if PDFMINER_AVAILABLE:
            try:
                logger.debug("[PDF2MD_DEBUG] Attempting conversion with pdfminer as fallback")
                start_time = time.time()
                text = pdfminer_extract_text(pdf_path)
                elapsed_time = time.time() - start_time
                logger.debug(f"[PDF2MD_DEBUG] pdfminer extraction took {elapsed_time:.2f} seconds")
                logger.debug(f"[PDF2MD_DEBUG] pdfminer extracted text: {len(text) if text else 0} characters")
                if text:
                    logger.debug(f"[PDF2MD_DEBUG] First 200 characters of extracted text: {text[:200].replace('\n', ' ')}...")
                # Convert to basic markdown by preserving paragraphs
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                result = '\n\n'.join(paragraphs)
                logger.debug(f"[PDF2MD_DEBUG] pdfminer formatted to Markdown: {len(result)} characters")
                if result:
                    logger.debug(f"[PDF2MD_DEBUG] First 200 characters of formatted Markdown: {result[:200].replace('\n', ' ')}...")
                return result
            except Exception as e:
                logger.warning(f"[PDF2MD_DEBUG] pdfminer failed: {str(e)}", exc_info=True)
        
        logger.warning("[PDF2MD_DEBUG] No PDF to markdown conversion tools available")
        logger.debug("[PDF2MD_DEBUG] Ensure that at least one of pdf2md (library or command-line) or pdfminer is installed and accessible")
        return None
        
    except Exception as e:
        logger.error(f"[PDF2MD_DEBUG] Error converting PDF to markdown: {str(e)}", exc_info=True)
        logger.debug(f"[PDF2MD_DEBUG] Check if the file is a valid PDF and accessible at {pdf_path}")
        return None


def extract_text_from_file(file_path, convert_pdf_to_md=False, file_type=None, file_ext=None):
    """Extract text from a file based on its extension or MIME type."""
    print("\n=== FILE TEXT EXTRACTION DEBUG ===")
    print(f"Extracting text from file: {file_path}")
    print(f"File type: {file_type}, extension: {file_ext}")
    
    def sanitize_bytes_for_logging(bytes_data, max_length=200):
        """Sanitize bytes for logging by converting to hex representation."""
        if not bytes_data:
            return ""
        # Convert bytes to hex representation
        hex_str = bytes_data.hex()
        # Add spaces between bytes for readability
        hex_str = ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
        # Limit length and add ellipsis
        if len(hex_str) > max_length:
            hex_str = hex_str[:max_length] + "..."
        return hex_str
    
    try:
        # Determine file extension if not provided
        if not file_ext:
            file_ext = os.path.splitext(file_path)[1].lower()
            print(f"Detected file extension: {file_ext}")
        
        # Normalize file extension
        if file_ext and not file_ext.startswith('.'):
            file_ext = f".{file_ext}"
        
        # Binary file extensions that need special handling
        BINARY_EXTS = ['.pdf', '.doc', '.docx', '.rtf', '.odt', '.docm', '.dotx', '.dotm']
        
        # Check if file exists and is readable
        if not os.path.exists(file_path):
            error_msg = f"File does not exist: {file_path}"
            print(f"ERROR: {error_msg}")
            return f"Error: {error_msg}"
            
        # Get file size
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size/1024:.1f}KB")
        
        if file_size == 0:
            error_msg = f"File is empty: {file_path}"
            print(f"ERROR: {error_msg}")
            return f"Error: {error_msg}"
        
        # Handle PDF files
        if file_ext == '.pdf':
            print("\nProcessing PDF file...")
            try:
                extraction_start = time.time()
                print("Starting PDF extraction timing...")
                # Validate PDF header
                with open(file_path, 'rb') as f:
                    header = f.read(5)
                    # Log sanitized header bytes
                    print(f"PDF header (hex): {sanitize_bytes_for_logging(header)}")
                    if not header.startswith(b'%PDF-'):
                        error_msg = "Invalid PDF file: Missing PDF header"
                        print(f"ERROR: {error_msg}")
                        return f"Error: {error_msg}"
                    else:
                        # Try to decode version number if present
                        try:
                            version = header[5:].decode('ascii').strip()
                            print(f"PDF version: {version}")
                        except UnicodeDecodeError:
                            print("Could not decode PDF version number")
                # Extract text using PyPDF2 first
                print("Attempting extraction with PyPDF2...")
                text = extract_text_from_file(file_path)
                extraction_end = time.time()
                elapsed = extraction_end - extraction_start
                print(f"PDF extraction took {elapsed:.2f} seconds")
                if elapsed > 25:
                    print("WARNING: PDF extraction exceeded 25 seconds!")
                if text and isinstance(text, str):
                    if text.startswith("Error:"):
                        print(f"PDF extraction failed: {text}")
                        return text
                    else:
                        print(f"Successfully extracted {len(text)} characters from PDF")
                        return text
                else:
                    error_msg = f"PDF extraction returned invalid result: {type(text)}"
                    print(f"ERROR: {error_msg}")
                    return f"Error: {error_msg}"
            except Exception as e:
                error_msg = f"Error processing PDF file: {str(e)}"
                print(f"ERROR: {error_msg}")
                print("Stack trace:")
                traceback.print_exc()
                return f"Error: {error_msg}"
        # Handle DOCX files
        elif file_ext == '.docx':
            print("\nProcessing DOCX file...")
            try:
                from docx import Document
                doc = Document(file_path)
                text = '\n'.join([para.text for para in doc.paragraphs])
                print(f"Successfully extracted {len(text)} characters from DOCX")
                return text
            except ImportError:
                error_msg = "python-docx is not installed. Please install it to process DOCX files."
                print(f"ERROR: {error_msg}")
                return f"Error: {error_msg}"
            except Exception as e:
                error_msg = f"Error processing DOCX file: {str(e)}"
                print(f"ERROR: {error_msg}")
                return f"Error: {error_msg}"
        # Handle DOC files
        elif file_ext == '.doc':
            print("\nProcessing DOC file...")
            try:
                import textract
                text = textract.process(file_path).decode('utf-8')
                print(f"Successfully extracted {len(text)} characters from DOC")
                return text
            except ImportError:
                error_msg = "textract is not installed. Please install it to process DOC files."
                print(f"ERROR: {error_msg}")
                return f"Error: {error_msg}"
            except Exception as e:
                error_msg = f"Error processing DOC file: {str(e)}"
                print(f"ERROR: {error_msg}")
                return f"Error: {error_msg}"
        # Handle RTF files
        elif file_ext == '.rtf':
            print("\nProcessing RTF file...")
            try:
                from striprtf.striprtf import rtf_to_text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    rtf_content = f.read()
                text = rtf_to_text(rtf_content)
                print(f"Successfully extracted {len(text)} characters from RTF")
                return text
            except ImportError:
                error_msg = "striprtf is not installed. Please install it to process RTF files."
                print(f"ERROR: {error_msg}")
                return f"Error: {error_msg}"
            except Exception as e:
                error_msg = f"Error processing RTF file: {str(e)}"
                print(f"ERROR: {error_msg}")
                return f"Error: {error_msg}"
        # Handle HTML files
        elif file_ext in ['.html', '.htm']:
            print("\nProcessing HTML file...")
            try:
                from bs4 import BeautifulSoup
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text(separator='\n')
                print(f"Successfully extracted {len(text)} characters from HTML")
                return text
            except ImportError:
                error_msg = "BeautifulSoup4 is not installed. Please install it to process HTML files."
                print(f"ERROR: {error_msg}")
                return f"Error: {error_msg}"
            except Exception as e:
                error_msg = f"Error processing HTML file: {str(e)}"
                print(f"ERROR: {error_msg}")
                return f"Error: {error_msg}"
        # Handle other binary files
        elif file_ext in BINARY_EXTS:
            error_msg = f"Binary file type {file_ext} not supported for text extraction"
            print(f"ERROR: {error_msg}")
            return f"Error: {error_msg}"
        
        # Handle plain text files
        elif file_ext in ['.txt', '.md', '.markdown']:
            print("\nProcessing text or markdown file...")
            # Common text file encodings to try (in order of likelihood)
            ENCODINGS = ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'ascii']
            # Try different encodings
            for encoding in ENCODINGS:
                try:
                    print(f"Attempting to read with {encoding} encoding...")
                    with open(file_path, 'r', encoding=encoding) as file:
                        text = file.read()
                        # Sanitize text before logging
                        sanitized_text = ''.join(c for c in text[:100] if c.isprintable())
                        print(f"Successfully read file with {encoding} encoding: {len(text)} characters")
                        print(f"Sample text: {sanitized_text}...")
                        return text
                except UnicodeDecodeError:
                    print(f"Failed to decode with {encoding} encoding")
                    continue
            # If all else fails, try with errors='replace' to at least get some content
            try:
                print("Attempting to read with utf-8 encoding and replacement characters...")
                with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                    text = file.read()
                    # Sanitize text before logging
                    sanitized_text = ''.join(c for c in text[:100] if c.isprintable())
                    print(f"Read file with replacement characters: {len(text)} characters")
                    print(f"Sample text: {sanitized_text}...")
                    return text
            except Exception as e:
                error_msg = f"Failed to read file with any encoding: {str(e)}"
                print(f"ERROR: {error_msg}")
                return f"Error: {error_msg}"
                
    except Exception as e:
        error_msg = f"Unexpected error processing file: {str(e)}"
        print(f"ERROR: {error_msg}")
        print("Stack trace:")
        traceback.print_exc()
        return f"Error: {error_msg}"
