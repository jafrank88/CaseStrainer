"""
Worker tasks module for RQ worker.
"""
import os
import sys
import re
import logging
import importlib
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path if not already there
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
    logger.info(f"Added {src_dir} to Python path")

def simple_task():
    """A simple task that returns a success message."""
    return {
        "status": "success",
        "message": "Hello from worker! This is a test task.",
        "python_path": __file__
    }

def test_imports() -> Dict[str, Dict[str, Any]]:
    """
    Test if required modules can be imported in the worker environment.
    
    Returns:
        Dict with import test results for each module
    """
    modules = [
        'unified_extraction_architecture',
        'models',
        'src.unified_extraction_architecture',
        'src.models',
        'src.worker_tasks',
        'rq',
        'redis',
        'flask'
    ]
    
    results = {}
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            results[module_name] = {
                'status': 'success',
                'path': getattr(module, '__file__', 'unknown')
            }
        except Exception as e:
            results[module_name] = {
                'status': 'error',
                'error': str(e)
            }
    
    # Also include sys.path for debugging
    results['_sys_path'] = {
        'status': 'info',
        'path': sys.path
    }
    
    # And environment variables
    results['_env'] = {
        'status': 'info',
        'python_path': os.environ.get('PYTHONPATH', 'not set'),
        'cwd': os.getcwd(),
        'user': os.environ.get('USER', 'unknown')
    }
    
    return results

def verify_citations_enhanced(citations, text, doc_id, doc_type, metadata):
    """Enhanced citation verification task.
    
    Args:
        citations: List of citations to verify (can be empty, will be extracted from text if so)
        text: Full document text
        doc_id: Document ID
        doc_type: Type of document
        metadata: Additional metadata
        
    Returns:
        dict: Verification results with citations and metadata
    """
    import logging
    from datetime import datetime
    from typing import List, Dict, Any, Optional
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Import necessary components
        from unified_extraction_architecture import get_unified_extractor
        from models import CitationResult
        
        start_time = datetime.utcnow()
        logger.info(f"Starting citation verification for doc_id: {doc_id}")
        
        # Initialize result structure
        result = {
            "status": "success",
            "doc_id": doc_id,
            "doc_type": doc_type,
            "start_time": start_time.isoformat(),
            "end_time": None,
            "citation_count": 0,
            "verified_citations": [],
            "error": None,
            "warnings": []
        }
        
        # If no citations provided, extract them from the text
        if not citations and text:
            logger.info("No citations provided, extracting from text...")
            try:
                from unified_extraction_architecture import extract_case_name_and_year_unified
                
                # First, try to find case citations using the unified extractor
                # This is a simplified approach - you might need to adjust based on your needs
                
                # Look for common citation patterns in the text
                citation_patterns = [
                    # Case citations like: 123 Wn.2d 456, 789 P.2d 123 (1990)
                    r'\b\d+\s+[A-Za-z]+\.?\s*\d+[a-z]?\s*,\s*\d+\s+[A-Za-z]+\s*\d+\s*\(\d{4}\)',
                    # Simple case names like: Smith v. Jones, 123 Wn.2d 456 (1990)
                    r'[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+',
                    # Case citations with volume and reporter: 123 Wn.2d 456
                    r'\b\d+\s+[A-Za-z]+\s*\d+\b',
                ]
                
                citations = []
                for pattern in citation_patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        citation = match.group(0).strip()
                        if citation not in citations:  # Avoid duplicates
                            citations.append(citation)
                
                logger.info(f"Found {len(citations)} potential citations in text")
                
                # Process each citation to extract case names and years
                verified_citations = []
                for i, citation in enumerate(citations):
                    try:
                        # Use the unified extractor to get case name and year
                        result = extract_case_name_and_year_unified(
                            text=text,
                            citation=citation,
                            start_index=text.find(citation),
                            end_index=text.find(citation) + len(citation),
                            debug=False
                        )
                        
                        if result and isinstance(result, dict) and result.get('case_name'):
                            verified_citations.append({
                                'id': i + 1,
                                'original_citation': citation,
                                'case_name': result.get('case_name', ''),
                                'year': result.get('year', ''),
                                'confidence': result.get('confidence', 0.0),
                                'method': result.get('method', 'unknown'),
                                'status': 'verified'
                            })
                        else:
                            verified_citations.append({
                                'id': i + 1,
                                'original_citation': citation,
                                'status': 'unverified',
                                'reason': 'Could not extract case name and year'
                            })
                            
                    except Exception as e:
                        logger.error(f"Error processing citation {citation}: {str(e)}", exc_info=True)
                        verified_citations.append({
                            'id': i + 1,
                            'original_citation': citation,
                            'status': 'error',
                            'error': str(e)
                        })
                
                # Update the result with verified citations
                result['verified_citations'] = verified_citations
                result['citation_count'] = len(verified_citations)
                
                # If we found any citations, update the status
                if verified_citations:
                    result['status'] = 'partial' if any(c['status'] != 'verified' for c in verified_citations) else 'success'
                
                logger.info(f"Processed {len(verified_citations)} citations")
                return result
                
            except Exception as e:
                error_msg = f"Error extracting citations: {str(e)}"
                logger.error(error_msg, exc_info=True)
                result['status'] = 'error'
                result['error'] = error_msg
                return result
            
            if not citations:
                result["warnings"].append("No citations found in the provided text")
        
        # Process each citation
        verified_citations = []
        for i, citation in enumerate(citations):
            try:
                # Here you would add the actual citation verification logic
                # This is a simplified example
                verified_citation = {
                    "id": i + 1,
                    "original_citation": citation,
                    "status": "verified",  # or "not_found", "ambiguous", etc.
                    "verification_source": "CaseStrainer",
                    "confidence": 0.95,  # Example confidence score
                    "metadata": {
                        "position_in_doc": text.find(citation) if text and citation else -1,
                        "verification_timestamp": datetime.utcnow().isoformat()
                    }
                }
                verified_citations.append(verified_citation)
                
            except Exception as e:
                logger.error(f"Error processing citation {citation}: {str(e)}", exc_info=True)
                verified_citations.append({
                    "id": i + 1,
                    "original_citation": citation,
                    "status": "error",
                    "error": str(e)
                })
        
        # Update result with verified citations
        result["verified_citations"] = verified_citations
        result["citation_count"] = len(verified_citations)
        
        # Add timing information
        end_time = datetime.utcnow()
        result["end_time"] = end_time.isoformat()
        result["processing_time_seconds"] = (end_time - start_time).total_seconds()
        
        logger.info(f"Completed verification of {len(verified_citations)} citations for doc_id: {doc_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in verify_citations_enhanced: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "doc_id": doc_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
