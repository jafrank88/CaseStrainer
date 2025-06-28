"""
Unified document processing module for CaseStrainer.
Handles text extraction from various file formats and input types.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests
from urllib.parse import urlparse
import re

# Import text extraction libraries
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    logging.warning("BeautifulSoup not available - HTML/HTM processing will be limited")

try:
    from striprtf.striprtf import rtf_to_text
    STRIPRTF_AVAILABLE = True
except ImportError:
    STRIPRTF_AVAILABLE = False
    logging.warning("striprtf not available - RTF processing will not work")

# Import existing processing modules
from src.pdf_handler import PDFHandler, PDFExtractionConfig, PDFExtractionMethod
from src.citation_extractor import CitationExtractor

logger = logging.getLogger(__name__)


def extract_text_from_html_file(file_path: str) -> str:
    """
    Extract text from HTML/HTM files using BeautifulSoup.
    
    Args:
        file_path: Path to the HTML/HTM file
        
    Returns:
        Extracted text content
    """
    if not BEAUTIFULSOUP_AVAILABLE:
        raise ImportError("BeautifulSoup is required for HTML/HTM processing")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract text with proper spacing
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up extra whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        logger.info(f"Successfully extracted {len(text)} characters from HTML file")
        return text
        
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        logger.info(f"Successfully extracted {len(text)} characters from HTML file using latin-1 encoding")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from HTML file: {str(e)}")
        raise


def extract_text_from_rtf_file(file_path: str) -> str:
    """
    Extract text from RTF files using striprtf.
    
    Args:
        file_path: Path to the RTF file
        
    Returns:
        Extracted text content
    """
    if not STRIPRTF_AVAILABLE:
        raise ImportError("striprtf is required for RTF processing")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            rtf_content = f.read()
        
        # Convert RTF to plain text
        text = rtf_to_text(rtf_content)
        
        # Clean up the text
        text = text.strip()
        
        logger.info(f"Successfully extracted {len(text)} characters from RTF file")
        return text
        
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            rtf_content = f.read()
        
        text = rtf_to_text(rtf_content)
        text = text.strip()
        
        logger.info(f"Successfully extracted {len(text)} characters from RTF file using latin-1 encoding")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from RTF file: {str(e)}")
        raise


def extract_text_from_odt_file(file_path: str) -> str:
    """
    Extract text from ODT files using python-docx or alternative method.
    
    Args:
        file_path: Path to the ODT file
        
    Returns:
        Extracted text content
    """
    try:
        # Try using python-docx first (works for some ODT files)
        import docx
        doc = docx.Document(file_path)
        paragraphs = [paragraph.text for paragraph in doc.paragraphs]
        text = "\n".join(paragraphs)
        
        logger.info(f"Successfully extracted {len(text)} characters from ODT file using python-docx")
        return text
        
    except Exception as e:
        logger.warning(f"python-docx failed for ODT file: {str(e)}")
        
        # Fallback: try to read as text file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            logger.info(f"Successfully extracted {len(text)} characters from ODT file as text")
            return text
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
            logger.info(f"Successfully extracted {len(text)} characters from ODT file as text using latin-1")
            return text
        except Exception as e2:
            logger.error(f"Error extracting text from ODT file: {str(e2)}")
            raise


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text content
    """
    file_extension = Path(file_path).suffix.lower()
    
    try:
        if file_extension == '.pdf':
            logger.info("Processing PDF file")
            handler = PDFHandler(PDFExtractionConfig(
                preferred_method=PDFExtractionMethod.PDFMINER,
                use_fallback=False,
                timeout=30,
                clean_text=True
            ))
            text = handler.extract_text(file_path)
            if text.startswith("Error:"):
                raise Exception(text)
            return text
            
        elif file_extension in ['.doc', '.docx']:
            logger.info("Processing Word document")
            import docx
            doc = docx.Document(file_path)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs]
            text = "\n".join(paragraphs)
            return text
            
        elif file_extension in ['.html', '.htm']:
            logger.info("Processing HTML/HTM file")
            return extract_text_from_html_file(file_path)
            
        elif file_extension == '.rtf':
            logger.info("Processing RTF file")
            return extract_text_from_rtf_file(file_path)
            
        elif file_extension == '.odt':
            logger.info("Processing ODT file")
            return extract_text_from_odt_file(file_path)
            
        elif file_extension == '.txt':
            logger.info("Processing text file")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
                    
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
            
    except Exception as e:
        logger.error(f"Error extracting text from file {file_path}: {str(e)}")
        raise


def extract_text_from_url(url: str) -> str:
    """
    Extract text from a URL, handling different content types including PDFs and other document formats.
    
    Args:
        url: URL to extract text from
        
    Returns:
        Extracted text content
    """
    try:
        logger.info(f"Fetching content from URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '').lower()
        logger.info(f"Content type of URL {url}: {content_type}")
        
        # Mapping of content types to file extensions for temporary files
        content_type_to_extension = {
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/rtf': '.rtf',
            'application/vnd.oasis.opendocument.text': '.odt'
        }
        
        # Check if the content type corresponds to a supported document format
        for ct, ext in content_type_to_extension.items():
            if ct in content_type:
                # Handle document content by downloading to a temporary file and processing as a file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                logger.info(f"Downloaded content to temporary file: {temp_file_path}")
                
                try:
                    text = extract_text_from_file(temp_file_path)
                    logger.info(f"Successfully extracted {len(text)} characters from {ct} URL")
                    logger.info(f"Sample of extracted text (first 500 characters): {text[:500]}...")
                    return text
                finally:
                    os.unlink(temp_file_path)  # Clean up temporary file
                    logger.info(f"Deleted temporary file: {temp_file_path}")
        
        if 'text/html' in content_type:
            # Parse HTML content
            if BEAUTIFULSOUP_AVAILABLE:
                soup = BeautifulSoup(response.text, 'html.parser')
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text(separator='\n', strip=True)
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
            else:
                # Fallback to raw text
                text = response.text
        else:
            # Treat as plain text
            text = response.text
        
        logger.info(f"Successfully extracted {len(text)} characters from URL")
        logger.info(f"Sample of extracted text (first 500 characters): {text[:500]}...")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from URL {url}: {str(e)}")
        raise


def process_document(
    content: str = None,
    file_path: str = None,
    url: str = None,
    extract_case_names: bool = True
) -> Dict[str, Any]:
    """
    Process a document and extract citations and case names.
    
    Args:
        content: Direct text content
        file_path: Path to a file
        url: URL to fetch content from
        extract_case_names: Whether to extract case names
        
    Returns:
        Dictionary containing processing results
    """
    try:
        # Determine input type and extract text
        if content:
            logger.info("Processing direct text content")
            text = content
            source_type = "text"
            source_name = "pasted_text"
        elif file_path:
            logger.info(f"Processing file: {file_path}")
            text = extract_text_from_file(file_path)
            source_type = "file"
            source_name = Path(file_path).name
        elif url:
            logger.info(f"Processing URL: {url}")
            text = extract_text_from_url(url)
            source_type = "url"
            source_name = urlparse(url).netloc
        else:
            raise ValueError("Must provide content, file_path, or url")
        
        if not text.strip():
            logger.error("No text content extracted from input")
            return {
                "success": False,
                "error": "No text content extracted",
                "citations": [],
                "case_names": []
            }
        
        logger.info(f"Extracted text length: {len(text)} characters")
        logger.info(f"Sample of extracted text (first 500 characters): {text[:500]}...")
        
        # Extract citations and case names
        extractor = CitationExtractor()
        result = extractor.extract_citations_with_case_names(text) if extract_case_names else extractor.extract_citations(text)
        initial_citation_count = len(result.get('citations', []))
        logger.info(f"Initially extracted {initial_citation_count} citations before verification")
        if initial_citation_count > 0:
            logger.info(f"All initial citations extracted before verification:")
            for i, citation in enumerate(result.get('citations', []), 1):
                logger.info(f"Citation {i}: {citation.get('citation', 'N/A')}")
        # DEBUG: Log all extracted citations before verification
        logger.info(f"[DEBUG] Extracted {initial_citation_count} citations before verification")
        for i, citation in enumerate(result.get('citations', []), 1):
            logger.info(f"[DEBUG] Citation {i}: {citation.get('citation', 'N/A')}")
        
        # VERIFICATION STEP: Verify extracted citations using EnhancedMultiSourceVerifier
        logger.info(f"Extracted {initial_citation_count} citations, now verifying them...")
        logger.info(f"[DEBUG] Verifying {initial_citation_count} citations...")
        
        try:
            from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            from src.complex_citation_integration import process_text_with_complex_citations, format_complex_citation_for_frontend
            verifier = EnhancedMultiSourceVerifier()
            complex_results_data = process_text_with_complex_citations(text, verifier)
            complex_results = complex_results_data.get('results', [])
            statistics = complex_results_data.get('statistics', {})
            summary = complex_results_data.get('summary', {})
            if complex_results:
                verified_citations = []
                for complex_result in complex_results:
                    formatted_result = format_complex_citation_for_frontend(complex_result)
                    complex_result.update(formatted_result)
                    verified_citations.append(complex_result)
                result['citations'] = verified_citations
                result['statistics'] = statistics
                result['summary'] = summary
                logger.info(f"Successfully processed {len(verified_citations)} citations with complex citation support")
                logger.info(f"Statistics: {statistics}")
                logger.info(f"[DEBUG] Successfully processed {len(verified_citations)} citations with complex citation support")
                for i, citation in enumerate(verified_citations, 1):
                    logger.info(f"[DEBUG] Verified citation {i}: {citation.get('citation', 'N/A')} (verified={citation.get('verified', False)})")
            else:
                logger.info("Complex citation processing found no results, falling back to individual processing")
                verified_citations = []
                for citation in result.get('citations', []):
                    citation_text = citation.get('citation', '')
                    if citation_text:
                        try:
                            complex_results_data = process_text_with_complex_citations(citation_text, verifier)
                            complex_results = complex_results_data.get('results', [])
                            for complex_result in complex_results:
                                enriched = citation.copy()
                                enriched.update(complex_result)
                                formatted_result = format_complex_citation_for_frontend(enriched)
                                enriched.update(formatted_result)
                                verified_citations.append(enriched)
                        except Exception as e:
                            logger.warning(f"Error verifying citation '{citation_text}': {str(e)}")
                            verified_citations.append(citation)
                    else:
                        verified_citations.append(citation)
                result['citations'] = verified_citations
                logger.info(f"Successfully verified {len(verified_citations)} citations with individual processing")
                logger.info(f"[DEBUG] Successfully verified {len(verified_citations)} citations with individual processing")
                for i, citation in enumerate(verified_citations, 1):
                    logger.info(f"[DEBUG] Verified citation {i}: {citation.get('citation', 'N/A')} (verified={citation.get('verified', False)})")
        except Exception as e:
            logger.error(f"Error during citation verification: {str(e)}")
            logger.info("Continuing with unverified citations due to verification error")
            logger.info(f"[DEBUG] Error during citation verification: {str(e)}")
        final_citation_count = len(result.get('citations', []))
        logger.info(f"Final number of citations after verification: {final_citation_count}")
        if final_citation_count > 0:
            logger.info(f"Sample of final citations: {[c.get('citation', '') for c in result.get('citations', [])[:5]]}")
        else:
            logger.warning("No citations remaining after verification and processing")
        logger.info(f"[DEBUG] Final number of citations after verification: {final_citation_count}")
        for i, citation in enumerate(result.get('citations', []), 1):
            logger.info(f"[DEBUG] Final citation {i}: {citation.get('citation', 'N/A')} (verified={citation.get('verified', False)})")
        # Extract case names from citations if they have case_name fields
        case_names = []
        if extract_case_names and result.get("citations"):
            for citation in result.get("citations", []):
                case_name = citation.get("case_name", "")
                if case_name and case_name != "N/A" and case_name not in case_names:
                    case_names.append(case_name)
            logger.info(f"Extracted {len(case_names)} unique case names from citations")
        if extract_case_names and not case_names:
            case_names = extractor._extract_case_names_from_text(text)
            logger.info(f"Extracted {len(case_names)} unique case names directly from text")
        # DEBUG: Log the full result returned
        logger.info(f"[DEBUG] Returning from process_document: success={True}, citations={len(result.get('citations', []))}, case_names={len(case_names)}")
        return {
            "success": True,
            "text_length": len(text),
            "source_type": source_type,
            "source_name": source_name,
            "citations": result.get("citations", []),
            "case_names": case_names,
            "extraction_metadata": result.get("metadata", {}),
            "statistics": result.get("statistics", {}),
            "summary": result.get("summary", {})
        }
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "citations": [],
            "case_names": []
        }


def process_document_input(input_type, input_value, file_ext=None):
    """
    Unified document input handler for file, url, or text.
    Returns: (text, metadata)
    """
    logger = logging.getLogger(__name__)
    meta = {}
    text = None
    try:
        if input_type == 'file':
            from src.file_utils import extract_text_from_file
            text_result = extract_text_from_file(input_value, file_ext=file_ext)
            if isinstance(text_result, tuple):
                text, extracted_case_name = text_result
                meta['extracted_case_name'] = extracted_case_name
            else:
                text = text_result
            meta['source_type'] = 'file'
            meta['source_name'] = input_value
        elif input_type == 'url':
            from src.enhanced_validator_production import extract_text_from_url
            text_result = extract_text_from_url(input_value)
            text = text_result.get('text', '')
            meta['content_type'] = text_result.get('content_type')
            meta['source_type'] = 'url'
            meta['source_name'] = input_value
            meta['status'] = text_result.get('status')
            meta['error'] = text_result.get('error')
        elif input_type == 'text':
            text = input_value
            meta['source_type'] = 'text'
            meta['source_name'] = 'pasted_text'
        else:
            raise ValueError("Unknown input type")
        meta['text_length'] = len(text) if text else 0
    except Exception as e:
        logger.error(f"[process_document_input] Error processing {input_type}: {e}")
        meta['error'] = str(e)
        text = ''
    return text, meta


def extract_and_verify_citations(text, options=None):
    """
    Extract and verify citations from text using the best practices from all input types.
    Now includes enhanced complex citation processing.
    Returns: (citations, verification_metadata)
    """
    from citation_processor import CitationProcessor
    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
    from src.complex_citation_integration import process_text_with_complex_citations, format_complex_citation_for_frontend
    from src.vue_api_endpoints import enrich_citation_with_database_fields
    from src.extract_case_name import extract_case_name_from_context_unified
    import logging
    logger = logging.getLogger(__name__)
    verification_metadata = {}
    citations = []
    try:
        # Use options if provided, else defaults
        processor = CitationProcessor()
        citations = processor.extract_citations(text)
        initial_count = len(citations)
        logger.info(f"[extract_and_verify_citations] Extracted {initial_count} citations from text.")
        if not citations:
            verification_metadata['status'] = 'no_citations'
            logger.warning("[extract_and_verify_citations] No citations extracted from text")
            return [], verification_metadata
        else:
            logger.info(f"[extract_and_verify_citations] Sample of extracted citations: {[c.get('citation', '') for c in citations[:5]]}")

        # --- FILTER: Only keep valid legal citations (not case names) ---
        def is_probable_legal_citation(citation_text):
            # Loosened pattern: number + reporter + number, allow extra numbers, commas, parentheses
            return bool(re.search(r"\b\d+\s+[A-Za-z\. ]+\s+\d+([,\s\d\(\)\.]*)\b", citation_text))
        filtered_citations = [c for c in citations if is_probable_legal_citation(c.get('citation', ''))]
        if len(filtered_citations) < len(citations):
            filtered_out = len(citations) - len(filtered_citations)
            logger.info(f"[extract_and_verify_citations] Filtered out {filtered_out} non-citation items (likely case names).")
            logger.info(f"[extract_and_verify_citations] Filtered citations: {[c.get('citation', '') for c in citations if c not in filtered_citations][:5]}")
        else:
            logger.info("[extract_and_verify_citations] No citations filtered out based on legal citation pattern")
        citations = filtered_citations

        # Extract case names from context for each citation
        for citation in citations:
            citation_text = citation.get('citation', '')
            if citation_text:
                # Find the citation in the text and get context before it
                citation_index = text.find(citation_text)
                if citation_index != -1:
                    # Get context before the citation (500 characters)
                    context_before = text[max(0, citation_index - 500):citation_index]
                    # Extract case name from context around the citation
                    extracted_case_name = extract_case_name_from_context_unified(context_before, citation_text)
                    if extracted_case_name:
                        citation['extracted_case_name'] = extracted_case_name
                    else:
                        citation['extracted_case_name'] = 'N/A'
                else:
                    citation['extracted_case_name'] = 'N/A'
            else:
                citation['extracted_case_name'] = 'N/A'
        logger.info(f"[extract_and_verify_citations] Completed case name extraction for {len(citations)} citations")

        # Store original citations for external web searches
        original_citations = [c['citation'] for c in citations]
        
        # Initialize verifier for complex citation processing
        verifier = EnhancedMultiSourceVerifier()
        logger.info("[extract_and_verify_citations] Initialized EnhancedMultiSourceVerifier for citation verification")
        
        # Process each citation with complex citation support
        results = []
        for citation in citations:
            citation_text = citation['citation']
            try:
                # Use complex citation processing for better handling of complex citations
                complex_results_data = process_text_with_complex_citations(citation_text, verifier)
                complex_results = complex_results_data.get('results', [])
                logger.info(f"[extract_and_verify_citations] Complex processing for '{citation_text}' returned {len(complex_results)} results")
                
                # Process each result from complex citation processing
                for complex_result in complex_results:
                    # Merge with original citation data
                    enriched = citation.copy()
                    enriched.update(complex_result)
                    
                    # Format for frontend
                    formatted_result = format_complex_citation_for_frontend(enriched)
                    enriched.update(formatted_result)
                    
                    # Enrich with database fields
                    enriched = enrich_citation_with_database_fields(enriched)
                    
                    results.append(enriched)
                    
            except Exception as e:
                logger.error(f"[extract_and_verify_citations] Complex citation processing failed for {citation_text}: {e}")
                # Fallback to basic processing
                try:
                    fallback_result = verifier.verify_citation_unified_workflow(
                        citation_text,
                        extracted_case_name=citation.get('extracted_case_name')
                    )
                    enriched = citation.copy()
                    enriched.update(fallback_result)
                    enriched = enrich_citation_with_database_fields(enriched)
                    results.append(enriched)
                    logger.info(f"[extract_and_verify_citations] Fallback verification successful for {citation_text}")
                except Exception as fallback_e:
                    logger.error(f"[extract_and_verify_citations] Fallback verification also failed for {citation_text}: {fallback_e}")
                    enriched = citation.copy()
                    enriched['verified'] = 'false'
                    enriched['error'] = str(fallback_e)
                    results.append(enriched)
        
        # Maintain original order
        results.sort(key=lambda x: original_citations.index(x['citation']) if x['citation'] in original_citations else 9999)
        final_count = len(results)
        logger.info(f"[extract_and_verify_citations] Final number of processed citations: {final_count}")
        if final_count > 0:
            logger.info(f"[extract_and_verify_citations] Sample of final citations: {[r.get('citation', '') for r in results[:5]]}")
        else:
            logger.warning("[extract_and_verify_citations] No citations remaining after processing and verification")

        verification_metadata['status'] = 'success'
        verification_metadata['verified_count'] = sum(1 for r in results if r.get('verified') in ['true', 'true_by_parallel'])
        verification_metadata['total'] = len(results)
        verification_metadata['complex_citations_processed'] = sum(1 for r in results if r.get('is_complex_citation', False))
        logger.info(f"[extract_and_verify_citations] Verification metadata: {verification_metadata}")
        
    except Exception as e:
        logger.error(f"[extract_and_verify_citations] Error: {e}")
        verification_metadata['status'] = 'error'
        verification_metadata['error'] = str(e)
    return results, verification_metadata
