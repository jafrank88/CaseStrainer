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
from src.complex_citation_integration import ComplexCitationIntegrator, format_complex_citation_for_frontend

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
            # Use extract_and_verify_citations to properly verify the extracted citations
            verified_citations, verification_metadata = extract_and_verify_citations(text, options={'extract_case_names': extract_case_names})
            
            if verified_citations:
                result['citations'] = verified_citations
                result['verification_metadata'] = verification_metadata
                logger.info(f"Successfully verified {len(verified_citations)} citations using extract_and_verify_citations")
                logger.info(f"[DEBUG] Successfully verified {len(verified_citations)} citations using extract_and_verify_citations")
                for i, citation in enumerate(verified_citations, 1):
                    logger.info(f"[DEBUG] Verified citation {i}: {citation.get('citation', 'N/A')} (verified={citation.get('verified', 'false')})")
            else:
                logger.info("No citations were verified, keeping original unverified citations")
                logger.info(f"[DEBUG] No citations were verified, keeping original unverified citations")
        except Exception as e:
            logger.error(f"Error during citation verification: {str(e)}")
            logger.info("Continuing with unverified citations due to verification error")
            logger.info(f"[DEBUG] Error during citation verification: {str(e)}")
            verified_citations = []  # Ensure it's always defined
        
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
            "summary": result.get("summary", {}),
            "verification_metadata": result.get("verification_metadata", {})
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
    import re
    from citation_processor import CitationProcessor
    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
    from src.complex_citation_integration import ComplexCitationIntegrator, format_complex_citation_for_frontend
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
            # Handle eyecite object representations
            if isinstance(citation_text, str):
                # Check for eyecite object representations that should be filtered out
                if any(pattern in citation_text for pattern in [
                    "IdCitation('Id.", 
                    "IdCitation('id.", 
                    "IdCitation('Ibid.", 
                    "IdCitation('ibid.",
                    "ShortCaseCitation(",
                    "UnknownCitation(",
                    "SupraCitation(",
                    "InfraCitation("
                ]):
                    return False  # These are short form citations, exclude them
                
                # Check for short citations with "at" before page numbers (e.g., "97 Wash. 2d at 30")
                # These are references to previously cited cases and should be excluded
                at_pattern = re.search(r"\bat\s+\d+", citation_text, re.IGNORECASE)
                if at_pattern:
                    return False  # This is a short citation, exclude it
                
                # Check for citations that are too short to be meaningful
                # Remove common punctuation and normalize spaces
                cleaned_text = re.sub(r'[.,;]', ' ', citation_text)
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                
                # Split into words
                words = cleaned_text.split()
                
                # Must have at least 3 parts (e.g., "123 F 456")
                if len(words) < 3:
                    return False  # Too few components
                
                # Check for basic citation pattern: number + reporter + number
                basic_pattern = bool(re.search(r"\b\d+\s+[A-Za-z\. ]+\s+\d+([,\s\d\(\)\.]*)\b", citation_text))
                
                return basic_pattern
            else:
                # For non-string objects, check their string representation
                return is_probable_legal_citation(str(citation_text))
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

        # Normalize all citation fields to strings for matching
        def normalize_citation(citation):
            """Normalize citation text, handling eyecite objects and other formats."""
            if not citation:
                return ""
            
            # If it's already a string, return as is
            if isinstance(citation, str):
                return citation
            
            # If it's a list, join with commas
            if isinstance(citation, list):
                return ', '.join(str(item) for item in citation if item)
            
            # Handle eyecite objects and other citation objects
            citation_str = str(citation)
            
            # Extract citation from eyecite object representations
            import re
            
            # Handle FullCaseCitation format
            full_case_match = re.search(r"FullCaseCitation\('([^']+)'", citation_str)
            if full_case_match:
                return full_case_match.group(1)
            
            # Handle ShortCaseCitation format
            short_case_match = re.search(r"ShortCaseCitation\('([^']+)'", citation_str)
            if short_case_match:
                return short_case_match.group(1)
            
            # Handle FullLawCitation format
            law_match = re.search(r"FullLawCitation\('([^']+)'", citation_str)
            if law_match:
                return law_match.group(1)
            
            # If it's an object with a 'cite' attribute (eyecite objects)
            if hasattr(citation, 'cite') and citation.cite:
                return citation.cite
            
            # If it's an object with a 'citation' attribute
            if hasattr(citation, 'citation') and citation.citation:
                return citation.citation
            
            # If it's an object with 'groups' attribute (eyecite objects)
            if hasattr(citation, 'groups') and citation.groups:
                groups = citation.groups
                volume = groups.get('volume', '')
                reporter = groups.get('reporter', '')
                page = groups.get('page', '')
                if volume and reporter and page:
                    return f"{volume} {reporter} {page}"
            
            # Fallback to string representation
            return citation_str

        # Store original citations for external web searches
        original_citations = [normalize_citation(c['citation']) for c in citations]
        
        # Initialize verifier for complex citation processing
        verifier = EnhancedMultiSourceVerifier()
        logger.info("[extract_and_verify_citations] Initialized EnhancedMultiSourceVerifier for citation verification")
        
        # Use complex citation processing on the entire text
        integrator = ComplexCitationIntegrator()
        results = integrator.process_text_with_complex_citations_original(text)
        logger.info(f"[extract_and_verify_citations] Complex processing returned {len(results)} results")
        
        # DEBUG: Log complex results before processing
        for i, cr in enumerate(results):
            logger.info(f"[extract_and_verify_citations] Complex result {i+1}: citation={cr.get('citation')}, verified={cr.get('verified')}")
        
        # Process each result from complex citation processing
        processed_results = []
        for complex_result in results:
            # Format for frontend
            formatted_result = format_complex_citation_for_frontend(complex_result)
            enriched = complex_result.copy()
            enriched.update(formatted_result)
            
            # DEBUG: Log after format_complex_citation_for_frontend
            logger.info(f"[extract_and_verify_citations] After format_complex_citation_for_frontend: citation={enriched.get('citation')}, verified={enriched.get('verified')}")
            
            # Normalize citation field for matching
            enriched['citation'] = normalize_citation(enriched.get('citation'))
            
            # DEBUG: Log after normalization
            logger.info(f"[extract_and_verify_citations] After normalization: citation={enriched.get('citation')}, verified={enriched.get('verified')}")
            
            # Handle parallel citations if present
            if enriched.get('parallel_citations') and enriched.get('verified') == 'true':
                # Create separate entries for each parallel citation
                primary_verified = enriched.get('verified') == 'true'
                
                # Add the primary citation
                enriched = enrich_citation_with_database_fields(enriched)
                
                # DEBUG: Log after enrich_citation_with_database_fields for primary
                logger.info(f"[extract_and_verify_citations] After enrich_citation_with_database_fields (primary): citation={enriched.get('citation')}, verified={enriched.get('verified')}")
                
                processed_results.append(enriched)
                
                # Add parallel citations with 'true_by_parallel' status
                for parallel_citation in enriched.get('parallel_citations', []):
                    parallel_enriched = enriched.copy()
                    parallel_enriched['citation'] = normalize_citation(parallel_citation)
                    parallel_enriched['verified'] = 'true_by_parallel' if primary_verified else 'false'
                    parallel_enriched['is_parallel_citation'] = True
                    parallel_enriched['primary_citation'] = enriched.get('citation')
                    
                    # DEBUG: Log before enrich_citation_with_database_fields for parallel
                    logger.info(f"[extract_and_verify_citations] Before enrich_citation_with_database_fields (parallel): citation={parallel_enriched.get('citation')}, verified={parallel_enriched.get('verified')}")
                    
                    # Enrich with database fields
                    parallel_enriched = enrich_citation_with_database_fields(parallel_enriched)
                    
                    # DEBUG: Log after enrich_citation_with_database_fields for parallel
                    logger.info(f"[extract_and_verify_citations] After enrich_citation_with_database_fields (parallel): citation={parallel_enriched.get('citation')}, verified={parallel_enriched.get('verified')}")
                    
                    processed_results.append(parallel_enriched)
            else:
                # No parallel citations, just add the single result
                enriched = enrich_citation_with_database_fields(enriched)
                
                # DEBUG: Log after enrich_citation_with_database_fields for single
                logger.info(f"[extract_and_verify_citations] After enrich_citation_with_database_fields (single): citation={enriched.get('citation')}, verified={enriched.get('verified')}")
                
                processed_results.append(enriched)
                
        # Use the processed results for merging
        results = processed_results
        
        # DEBUG: Print original and result citations before merging
        logger.info(f"[extract_and_verify_citations] Original citations for merge:")
        for i, oc in enumerate(original_citations, 1):
            logger.info(f"  {i}. {oc} (type={type(oc)})")
        logger.info(f"[extract_and_verify_citations] Result citations for merge:")
        for i, rc in enumerate(results, 1):
            logger.info(f"  {i}. {rc.get('citation')} (type={type(rc.get('citation'))}) -> verified: {rc.get('verified')}")

        # Helper to stringify any citation (including FullCaseCitation)
        def stringify_citation(cit):
            if hasattr(cit, '__str__'):
                return str(cit)
            if isinstance(cit, list):
                return ', '.join([stringify_citation(x) for x in cit])
            return str(cit)

        # Helper to extract the actual citation text from various formats
        def extract_citation_text(citation_obj):
            """Extract the actual citation text from various citation formats."""
            if isinstance(citation_obj, str):
                return citation_obj
            elif isinstance(citation_obj, list):
                return citation_obj[0] if citation_obj else ""
            elif hasattr(citation_obj, '__str__'):
                # Handle FullCaseCitation objects
                citation_str = str(citation_obj)
                # Try to extract just the citation part (before the metadata)
                if '(' in citation_str:
                    citation_part = citation_str.split('(')[0].strip()
                    if citation_part:
                        return citation_part
                return citation_str
            return str(citation_obj)

        # Helper to normalize citation for matching
        def normalize_for_matching(citation_text):
            """Normalize citation text for matching purposes."""
            if not citation_text:
                return ""
            # Remove common prefixes and normalize whitespace
            normalized = str(citation_text).strip()
            # Remove any metadata or extra information
            if '(' in normalized:
                normalized = normalized.split('(')[0].strip()
            # Remove common prefixes like "See", "See also", etc.
            normalized = re.sub(r'^(See|See also|Cf\.|But see|But cf\.)\s+', '', normalized, flags=re.IGNORECASE)
            # Normalize whitespace and remove extra spaces
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            return normalized

        # Create a mapping of normalized citations to their verification results
        verification_map = {}
        for result in results:
            citation_text = extract_citation_text(result.get('citation'))
            normalized = normalize_for_matching(citation_text)
            if normalized:
                verification_map[normalized] = result
                logger.info(f"[extract_and_verify_citations] Added to verification map: {normalized} -> verified: {result.get('verified')}")

        # Maintain original order and ensure all citations are included
        merged_citations = []
        verified_primary_citations = {}  # Track verified primary citations for inheritance
        
        for orig_citation in original_citations:
            orig_str = stringify_citation(orig_citation)
            orig_normalized = normalize_for_matching(orig_str)
            
            logger.info(f"[extract_and_verify_citations] Processing original citation: {orig_str} (normalized: {orig_normalized})")
            
            # Try to find a match in the verification results
            matched_result = None
            
            # First, try exact normalized match
            if orig_normalized in verification_map:
                matched_result = verification_map[orig_normalized]
                logger.info(f"[extract_and_verify_citations] Found exact match for {orig_str}: verified={matched_result.get('verified')}")
            else:
                # Try partial matching for complex citations
                for normalized_key, result in verification_map.items():
                    if orig_normalized in normalized_key or normalized_key in orig_normalized:
                        matched_result = result
                        logger.info(f"[extract_and_verify_citations] Found partial match for {orig_str}: {normalized_key} -> verified={result.get('verified')}")
                        break
                
                # If still no match, try more flexible matching
                if not matched_result:
                    # Try matching by extracting just the volume and reporter parts
                    import re
                    volume_reporter_match = re.search(r'(\d+)\s+([A-Za-z\.\s]+)\s+(\d+)', orig_normalized)
                    if volume_reporter_match:
                        volume = volume_reporter_match.group(1)
                        reporter = volume_reporter_match.group(2).strip()
                        page = volume_reporter_match.group(3)
                        search_pattern = f"{volume} {reporter} {page}"
                        
                        for normalized_key, result in verification_map.items():
                            if search_pattern in normalized_key:
                                matched_result = result
                                logger.info(f"[extract_and_verify_citations] Found flexible match for {orig_str}: {search_pattern} -> verified={result.get('verified')}")
                                break
            
            if matched_result:
                # Use the matched result, but preserve the original citation text
                final_result = matched_result.copy()
                final_result['citation'] = orig_str  # Keep the original citation format
                
                # If this is a verified primary citation, track it for inheritance
                if final_result.get('verified') == 'true':
                    verified_primary_citations[orig_normalized] = final_result
                
                merged_citations.append(final_result)
                logger.info(f"[extract_and_verify_citations] Added matched result: {orig_str} -> verified: {final_result.get('verified')}")
            else:
                # If no match found, add a default unverified entry
                default_entry = {
                    "citation": orig_str, 
                    "verified": "false",
                    "canonical_name": "",
                    "canonical_date": "",
                    "url": "",
                    "court": "",
                    "docket_number": "",
                    "source": "",
                    "parallel_citations": []
                }
                logger.info(f"[extract_and_verify_citations] No match found for {orig_str}, adding default: verified={default_entry.get('verified')}")
                merged_citations.append(default_entry)
        
        # Also add any verification results that weren't matched to original citations
        # (this handles cases where complex citation processing found additional citations)
        for result in results:
            citation_text = extract_citation_text(result.get('citation'))
            normalized = normalize_for_matching(citation_text)
            
            # Check if this result is already in merged_citations
            already_included = any(
                normalize_for_matching(merged.get('citation')) == normalized 
                for merged in merged_citations
            )
            
            if not already_included:
                logger.info(f"[extract_and_verify_citations] Adding unmatched result: {citation_text} -> verified: {result.get('verified')}")
                merged_citations.append(result)
        
        # Now handle parallel citation inheritance for citations from the same case
        # Group citations by case name to identify parallels
        case_groups = {}
        for citation in merged_citations:
            case_name = citation.get('canonical_name') or citation.get('case_name')
            if case_name and case_name != 'N/A':
                if case_name not in case_groups:
                    case_groups[case_name] = []
                case_groups[case_name].append(citation)
        
        # For each case group, ensure parallels inherit from verified primary
        for case_name, citations in case_groups.items():
            if len(citations) > 1:  # Multiple citations for the same case
                # Find the verified primary citation
                verified_primary = None
                for citation in citations:
                    if citation.get('verified') == 'true':
                        verified_primary = citation
                        break
                
                if verified_primary:
                    # Copy canonical metadata to all other citations in the group
                    canonical_fields = [
                        'canonical_name', 'canonical_date', 'case_name', 'url', 
                        'court', 'docket_number', 'source', 'confidence'
                    ]
                    
                    for citation in citations:
                        if citation.get('verified') != 'true':  # Not the primary
                            # Mark as parallel citation
                            citation['verified'] = 'true_by_parallel'
                            citation['is_parallel_citation'] = True
                            citation['primary_citation'] = verified_primary.get('citation')
                            
                            # Copy canonical metadata from primary
                            for field in canonical_fields:
                                if field in verified_primary and verified_primary[field]:
                                    citation[field] = verified_primary[field]
                            
                            logger.info(f"[extract_and_verify_citations] Updated parallel citation {citation.get('citation')} with inherited metadata from {verified_primary.get('citation')}")
        
        results = merged_citations
        
        # DEBUG: Log final results after merging
        logger.info(f"[extract_and_verify_citations] Final results after merging:")
        for i, result in enumerate(results, 1):
            logger.info(f"  {i}. {result.get('citation')} -> verified: {result.get('verified')}")
        
        final_count = len(results)
        logger.info(f"[extract_and_verify_citations] Final number of processed citations: {final_count}")
        if final_count > 0:
            logger.info(f"[extract_and_verify_citations] Sample of final citations: {[r.get('citation', '') for r in results[:5]]}")
        else:
            logger.warning("[extract_and_verify_citations] No citations remaining after processing and verification")
        # DEBUG: Log all results before returning
        logger.info(f"[extract_and_verify_citations] Final results: {[{'citation': r.get('citation'), 'verified': r.get('verified')} for r in results]}")

        verification_metadata['status'] = 'success'
        verification_metadata['verified_count'] = sum(1 for r in results if r.get('verified') in ['true', 'true_by_parallel'])
        verification_metadata['total'] = len(results)
        verification_metadata['complex_citations_processed'] = sum(1 for r in results if r.get('is_complex_citation', False))
        logger.info(f"[extract_and_verify_citations] Verification metadata: {verification_metadata}")
        
        # DEBUG: Print final results
        logger.info(f"[extract_and_verify_citations] Final results:")
        for i, rc in enumerate(results, 1):
            logger.info(f"  {i}. {rc.get('citation')} (type={type(rc.get('citation'))}) -> verified: {rc.get('verified')}")

        # After extracting citations and before verification, propagate extracted case name and year to parallels in the same block/line
        # Group citations by their position in the text (e.g., same line or block)
        import re
        
        # Build a mapping from citation text to citation object
        citation_map = {c['citation']: c for c in citations if 'citation' in c}
        
        # Find all lines containing citations
        lines = text.split('\n')
        for line in lines:
            # Find all citations in this line
            found = [c for c in citations if c['citation'] in line]
            if len(found) > 1:
                # If any citation in this line has an extracted_case_name or extracted_date/year, propagate to all
                case_name = next((c.get('extracted_case_name') for c in found if c.get('extracted_case_name') and c.get('extracted_case_name') != 'N/A'), None)
                year = next((c.get('extracted_date') for c in found if c.get('extracted_date')), None)
                # Fallback: try to extract year from the line if not present
                if not year:
                    year_match = re.search(r'\((\d{4})\)', line)
                    if year_match:
                        year = year_match.group(1)
                for c in found:
                    if case_name:
                        c['extracted_case_name'] = case_name
                    if year:
                        c['extracted_date'] = year

        # Return the results directly since we processed everything as complex citations
        return results, verification_metadata

    except Exception as e:
        logger.error(f"[extract_and_verify_citations] Error: {e}")
        verification_metadata['status'] = 'error'
        verification_metadata['error'] = str(e)
    return results, verification_metadata
