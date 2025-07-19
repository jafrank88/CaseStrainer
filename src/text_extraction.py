import os
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(file_path: str) -> Dict[str, Any]:
    """
    Extract text from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'File not found: {file_path}',
                'text': None
            }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return {
            'success': True,
            'text': text,
            'metadata': {
                'filename': os.path.basename(file_path),
                'size': os.path.getsize(file_path)
            }
        }
    except Exception as e:
        logger.error(f"Error extracting text from file {file_path}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'text': None
        }

def extract_text_from_url(url: str) -> Dict[str, Any]:
    """
    Extract text from a URL.
    
    Args:
        url: URL to extract text from
        
    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        response = requests.get(url, timeout=30, timeout=30)
        response.raise_for_status()
        
        return {
            'success': True,
            'text': response.text,
            'metadata': {
                'url': url,
                'content_type': response.headers.get('content-type'),
                'status_code': response.status_code
            }
        }
    except Exception as e:
        logger.error(f"Error extracting text from URL {url}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'text': None
        } 