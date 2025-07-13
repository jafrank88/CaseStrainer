import os
import logging
import tempfile
import subprocess
import sys
import time
from pathlib import Path
import traceback
import warnings

logger = logging.getLogger(__name__)

# Try to import PDF processing libraries
try:
    from src.pdf_handler import extract_text_from_pdf, PDFHandler
except ImportError:
    extract_text_from_pdf = None

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
                        content_preview = content[:200].replace('\n', ' ')
                        logger.debug(f"[PDF2MD_DEBUG] First 200 characters of content: {content_preview}...")
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
                    text_preview = text[:200].replace('\n', ' ')
                    logger.debug(f"[PDF2MD_DEBUG] First 200 characters of extracted text: {text_preview}...")
                    # Convert to basic markdown by preserving paragraphs
                    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                    result = '\n\n'.join(paragraphs)
                    logger.debug(f"[PDF2MD_DEBUG] pdfminer formatted to Markdown: {len(result)} characters")
                    if result:
                        result_preview = result[:200].replace('\n', ' ')
                        logger.debug(f"[PDF2MD_DEBUG] First 200 characters of formatted Markdown: {result_preview}...")
                    return result
                else:
                    logger.warning("[PDF2MD_DEBUG] pdfminer extracted text is empty")
                    return None
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
    """
    DEPRECATED: Use src.document_processing_unified.extract_text_from_file instead.
    This function will be removed in a future version.
    """
    warnings.warn(
        "extract_text_from_file is deprecated. Use src.document_processing_unified.extract_text_from_file instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from src.document_processing_unified import extract_text_from_file as unified_extract_text_from_file
    return unified_extract_text_from_file(file_path, convert_pdf_to_md=convert_pdf_to_md)
