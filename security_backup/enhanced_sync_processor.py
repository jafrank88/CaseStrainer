"""
Enhanced Sync Processor with Async Verification
Implements Option 1: Enhanced Sync + Async Verification for all input types.

This processor provides:
1. Immediate results with local citation extraction, normalization, and clustering
2. Background async verification using fallback verifier
3. Support for text, files, and URLs
4. No timeouts or blocking operations
"""

import os
import sys
import time
import logging
import hashlib
import tempfile
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from pathlib import Path

# Enhanced verification imports
try:
    from src.enhanced_courtlistener_verification import EnhancedCourtListenerVerifier
    enhanced_verification_available = True
except ImportError:
    enhanced_verification_available = False
    logger = logging.getLogger(__name__)
    logger.warning("Enhanced verification not available, using fallback verifier")

# Confidence scoring imports
try:
    from src.citation_utils_consolidated import ConfidenceScorer
    confidence_scoring_available = True
except ImportError:
    confidence_scoring_available = False
    logger = logging.getLogger(__name__)
    logger.warning("Confidence scoring not available")

logger = logging.getLogger(__name__)

@dataclass
class ProcessingOptions:
    """Configuration options for enhanced processing."""
    
    # Basic processing options
    enable_local_processing: bool = True
    enable_async_verification: bool = True
    
    # Thresholds for different processing modes
    enhanced_sync_threshold: int = 15 * 1024  # 15KB for enhanced sync
    ultra_fast_threshold: int = 500  # 500 chars for ultra-fast
    clustering_threshold: int = 300  # 300 chars for clustering
    max_citations_for_local_clustering: int = 10
    
    # Enhanced verification options
    enable_enhanced_verification: bool = True
    enable_cross_validation: bool = True
    enable_false_positive_prevention: bool = True
    enable_confidence_scoring: bool = True
    
    # Verification quality thresholds
    min_confidence_threshold: float = 0.7
    cross_validation_confidence_boost: float = 0.15
    false_positive_filter_strictness: str = "medium"  # low, medium, high
    
    # API configuration
    courtlistener_api_key: Optional[str] = None
    enable_search_api_primary: bool = True
    enable_citation_lookup_fallback: bool = True

class EnhancedSyncProcessor:
    """
    Enhanced processor that provides immediate results with local processing
    and queues verification for background async processing.
    """
    
    def __init__(self, options: Optional[ProcessingOptions] = None):
        """Initialize the enhanced sync processor with configuration options."""
        self.options = options or ProcessingOptions()
        
        # Initialize enhanced verification if available
        self.enhanced_verifier = None
        if (self.options.enable_enhanced_verification and 
            enhanced_verification_available and 
            self.options.courtlistener_api_key):
            try:
                self.enhanced_verifier = EnhancedCourtListenerVerifier(self.options.courtlistener_api_key)
                logger.info("Enhanced verification initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced verification: {e}")
                self.enhanced_verifier = None
        
        # Initialize confidence scorer if available
        self.confidence_scorer = None
        if self.options.enable_confidence_scoring and confidence_scoring_available:
            try:
                self.confidence_scorer = ConfidenceScorer()
                logger.info("Confidence scoring initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize confidence scoring: {e}")
                self.confidence_scorer = None
        
        # Log configuration
        logger.info(f"EnhancedSyncProcessor initialized with options: {self.options}")
        logger.info(f"Enhanced verification: {'Available' if self.enhanced_verifier else 'Not available'}")
        logger.info(f"Confidence scoring: {'Available' if self.confidence_scorer else 'Not available'}")
        
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        self._cache_cleanup_interval = 300  # Clean cache every 5 minutes
        self._last_cache_cleanup = time.time()
        
        # Performance thresholds
        self.enhanced_sync_threshold = self.options.enhanced_sync_threshold
        self.ultra_fast_threshold = self.options.ultra_fast_threshold
        self.clustering_threshold = self.options.clustering_threshold
        self.max_citations_for_local_clustering = self.options.max_citations_for_local_clustering
        
        logger.info(f"[EnhancedSyncProcessor] Initialized with thresholds: "
                   f"enhanced_sync={self.enhanced_sync_threshold}, "
                   f"ultra_fast={self.ultra_fast_threshold}, "
                   f"clustering={self.clustering_threshold}")
    
    def process_any_input_enhanced(self, input_data: Any, input_type: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process any input type (text, file, URL) with enhanced sync processing.
        
        Args:
            input_data: The input data (text string, file path, or URL string)
            input_type: Type of input ('text', 'file', 'url')
            options: Optional processing options
            
        Returns:
            Dictionary with immediate processing results and async verification status
        """
        start_time = time.time()
        request_id = f"enhanced_{int(start_time * 1000)}"
        
        try:
            logger.info(f"[EnhancedSyncProcessor {request_id}] Processing {input_type} input")
            
            # 1. Extract text from input (regardless of type)
            text_result = self._extract_text_from_input(input_data, input_type, request_id)
            
            if not text_result['success']:
                return text_result
            
            text = text_result['text']
            metadata = text_result.get('metadata', {})
            
            # 2. Check if this should use enhanced sync processing
            if self._should_use_enhanced_sync(text):
                logger.info(f"[EnhancedSyncProcessor {request_id}] Using enhanced sync processing")
                result = self._process_enhanced_sync(text, request_id, options)
            else:
                logger.info(f"[EnhancedSyncProcessor {request_id}] Text too long, redirecting to async")
                return self._redirect_to_full_async(text, request_id, input_type, metadata)
            
            # 3. Queue async verification if enabled and citations found
            if (self.options.enable_async_verification and 
                result.get('success') and 
                result.get('citations')):
                
                verification_status = self._queue_async_verification(
                    result['citations'], text, request_id, input_type, metadata
                )
                result['verification_status'] = verification_status
                result['async_verification_queued'] = True
            
            # 4. Add metadata and return
            result.update({
                'processing_mode': 'enhanced_sync',
                'processing_time': time.time() - start_time,
                'request_id': request_id,
                'text_length': len(text),
                'input_type': input_type,
                'metadata': metadata
            })
            
            logger.info(f"[EnhancedSyncProcessor {request_id}] Enhanced processing completed in {result['processing_time']:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] Error in enhanced processing: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Enhanced processing failed: {str(e)}',
                'citations': [],
                'clusters': [],
                'processing_mode': 'enhanced_sync_error',
                'processing_time': time.time() - start_time,
                'request_id': request_id,
                'input_type': input_type
            }
        finally:
            # Clean up old cache entries periodically
            self._cleanup_cache()
    
    def _should_use_enhanced_sync(self, text: str) -> bool:
        """Determine if text should use enhanced sync processing."""
        return len(text) < self.enhanced_sync_threshold
    
    def _extract_text_from_input(self, input_data: Any, input_type: str, request_id: str) -> Dict[str, Any]:
        """Extract text from any input type."""
        try:
            if input_type == 'text':
                return self._extract_from_text(input_data, request_id)
            elif input_type == 'file':
                return self._extract_from_file(input_data, request_id)
            elif input_type == 'url':
                return self._extract_from_url(input_data, request_id)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported input type: {input_type}',
                    'text': '',
                    'metadata': {'input_type': input_type}
                }
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] Text extraction failed: {e}")
            return {
                'success': False,
                'error': f'Text extraction failed: {str(e)}',
                'text': '',
                'metadata': {'input_type': input_type}
            }
    
    def _extract_from_text(self, text: str, request_id: str) -> Dict[str, Any]:
        """Extract text from text input."""
        return {
            'success': True,
            'text': text,
            'metadata': {'input_type': 'text', 'extraction_method': 'direct'}
        }
    
    def _extract_from_file(self, file_path: str, request_id: str) -> Dict[str, Any]:
        """Extract text from file input."""
        try:
            from src.pdf_extraction_optimized import extract_text_from_pdf_smart
            
            path_obj = Path(file_path)
            if not path_obj.exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}',
                    'text': '',
                    'metadata': {'input_type': 'file', 'file_path': file_path}
                }
            
            # Extract text based on file type
            if path_obj.suffix.lower() == '.pdf':
                text = extract_text_from_pdf_smart(file_path)
            else:
                # Handle other file types
                with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            
            return {
                'success': True,
                'text': text,
                'metadata': {
                    'input_type': 'file',
                    'file_path': file_path,
                    'file_size': path_obj.stat().st_size,
                    'extraction_method': 'file_reader'
                }
            }
            
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] File extraction failed: {e}")
            return {
                'success': False,
                'error': f'File extraction failed: {str(e)}',
                'text': '',
                'metadata': {'input_type': 'file', 'file_path': file_path}
            }
    
    def _extract_from_url(self, url: str, request_id: str) -> Dict[str, Any]:
        """Extract text from URL input."""
        try:
            from src.progress_manager import fetch_url_content
            
            # Fetch URL content - returns string directly
            text = fetch_url_content(url)
            
            if not text:
                return {
                    'success': False,
                    'error': 'URL fetch returned empty content',
                    'text': '',
                    'metadata': {'input_type': 'url', 'url': url}
                }
            
            return {
                'success': True,
                'text': text,
                'metadata': {
                    'input_type': 'url',
                    'url': url,
                    'content_length': len(text),
                    'extraction_method': 'url_fetch'
                }
            }
            
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] URL extraction failed: {e}")
            return {
                'success': False,
                'error': f'URL extraction failed: {str(e)}',
                'text': '',
                'metadata': {'input_type': 'url', 'url': url}
            }
    
    def _process_enhanced_sync(self, text: str, request_id: str, options: Optional[Dict]) -> Dict[str, Any]:
        """Enhanced sync processing with local normalization and clustering."""
        try:
            logger.info(f"[EnhancedSyncProcessor {request_id}] Enhanced sync processing for {len(text)} characters")
            
            # 1. Fast citation extraction
            citations = self._extract_citations_fast(text)
            
            # 2. Local citation normalization (no API calls)
            normalized_citations = self._normalize_citations_local(citations, text)
            
            # 3. Local name/year extraction (no API calls)
            enhanced_citations = self._extract_names_years_local(normalized_citations, text)
            
            # 4. Local clustering (no verification)
            clusters = self._cluster_citations_local(enhanced_citations, text, request_id)
            
            # 5. Convert to standard format
            citations_list = self._convert_citations_to_dicts(enhanced_citations)
            clusters_list = self._convert_clusters_to_dicts(clusters)
            
            return {
                'success': True,
                'citations': citations_list,
                'clusters': clusters_list,
                'processing_strategy': 'enhanced_sync',
                'extraction_method': 'enhanced_local',
                'verification_status': 'pending_async',
                'local_processing_complete': True,
                'citations_found': len(citations_list),
                'clusters_created': len(clusters_list)
            }
            
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] Enhanced sync failed: {e}")
            # Fall back to basic processing
            return self._process_basic_sync(text, request_id)
    
    def _extract_citations_fast(self, text: str) -> List:
        """Fast citation extraction using optimized methods."""
        try:
            from src.citation_extractor import CitationExtractor
            
            extractor = CitationExtractor()
            citations = extractor.extract_citations(text)
            
            logger.info(f"[EnhancedSyncProcessor] Fast extraction found {len(citations)} citations")
            return citations
            
        except Exception as e:
            logger.warning(f"[EnhancedSyncProcessor] Fast extraction failed: {e}")
            # Fall back to basic regex
            return self._extract_citations_basic_regex(text)
    
    def _extract_citations_basic_regex(self, text: str) -> List:
        """Basic regex extraction as fallback."""
        import re
        
        # Basic Washington citation patterns
        patterns = [
            r'\b\d+\s+Wn\.\d+\s+\d+',  # 200 Wn.2d 72
            r'\b\d+\s+P\.\d+\s+\d+',   # 514 P.3d 643
            r'\b\d+\s+Wn\.\s*App\.\s*\d+',  # 136 Wn. App. 104
        ]
        
        citations = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        
        logger.info(f"[EnhancedSyncProcessor] Basic regex found {len(citations)} citations")
        return citations
    
    def _normalize_citations_local(self, citations: List, text: str) -> List:
        """Local citation normalization without API calls."""
        try:
            normalized = []
            for citation in citations:
                # Check if this is a CitationResult object - preserve it
                if (not isinstance(citation, dict) and 
                    hasattr(citation, 'citation')):
                    # This is a CitationResult object, preserve it
                    normalized.append(citation)
                    continue
                
                # For dict citations, do basic normalization
                if isinstance(citation, dict) and 'citation' in citation:
                    citation_text = citation['citation']
                else:
                    citation_text = str(citation).strip()
                
                # Extract basic components
                parts = citation_text.split()
                if len(parts) >= 3:
                    volume = parts[0]
                    reporter = parts[1]
                    page = parts[2]
                    
                    # Create normalized structure
                    normalized.append({
                        'citation': citation_text,
                        'volume': volume,
                        'reporter': reporter,
                        'page': page,
                        'normalized': True
                    })
                else:
                    normalized.append({
                        'citation': citation_text,
                        'normalized': False
                    })
            
            logger.info(f"[EnhancedSyncProcessor] Local normalization completed for {len(normalized)} citations")
            return normalized
            
        except Exception as e:
            logger.warning(f"[EnhancedSyncProcessor] Local normalization failed: {e}")
            return citations
    
    def _extract_names_years_local(self, citations: List, text: str) -> List[Dict]:
        """Enhanced local name/year extraction with verification and confidence scoring."""
        try:
            enhanced_citations = []
            
            for citation in citations:
                citation_text = citation['citation'] if isinstance(citation, dict) and 'citation' in citation else str(citation)
                
                # Check if this is a CitationResult object with existing data
                if (not isinstance(citation, dict) and 
                    hasattr(citation, 'extracted_case_name') and 
                    getattr(citation, 'extracted_case_name', None)):
                    # Use existing data from CitationResult
                    case_name = getattr(citation, 'extracted_case_name', None)
                    year = getattr(citation, 'extracted_date', None) or getattr(citation, 'extracted_year', None)
                    confidence_score = getattr(citation, 'confidence', 0.7)
                    logger.debug(f"Using existing data from CitationResult: {case_name}, {year}")
                elif isinstance(citation, dict) and citation.get('extracted_case_name'):
                    # Use existing data from dict
                    case_name = citation.get('extracted_case_name')
                    year = citation.get('extracted_date') or citation.get('extracted_year')
                    confidence_score = citation.get('confidence_score', 0.7)
                    logger.debug(f"Using existing data from dict: {case_name}, {year}")
                else:
                    # Extract case name and year locally
                    case_name = self._extract_case_name_local(text, citation_text)
                    year = self._extract_year_local(text, citation_text)
                    
                    # Set initial confidence based on extraction success
                    confidence_score = 0.7  # Start with good confidence
                    if case_name:
                        confidence_score += 0.1  # Bonus for case name
                    if year:
                        confidence_score += 0.1  # Bonus for year
                
                # Enhanced verification if available
                verification_result = None
                
                if self.enhanced_verifier and self.options.enable_enhanced_verification:
                    try:
                        # Enhanced verification with cross-validation
                        verification_result = self.enhanced_verifier.verify_citation_enhanced(
                            citation_text, case_name
                        )
                        
                        # Extract verification data
                        if verification_result.get('verified'):
                            confidence_score = verification_result.get('confidence', 0.7)
                            # Use canonical data if available
                            if verification_result.get('canonical_name'):
                                case_name = verification_result.get('canonical_name')
                            if verification_result.get('canonical_date'):
                                year = verification_result.get('canonical_date')
                        else:
                            # Lower confidence for unverified citations
                            confidence_score = 0.3
                            
                    except Exception as e:
                        logger.warning(f"Enhanced verification failed for {citation_text}: {e}")
                        verification_result = None
                
                # Confidence scoring if available
                if self.confidence_scorer and self.options.enable_confidence_scoring:
                    try:
                        # Create citation dict for confidence calculation
                        citation_dict = {
                            'citation': citation_text,
                            'extracted_case_name': case_name,
                            'extracted_date': year,
                            'verified': verification_result.get('verified', False) if verification_result else False,
                            'method': 'enhanced_local_extraction'
                        }
                        
                        # Calculate confidence score
                        calculated_confidence = self.confidence_scorer.calculate_citation_confidence(
                            citation_dict, text
                        )
                        
                        # If confidence scorer returns very low score, use our calculated score
                        if calculated_confidence < 0.3:
                            # Use our extraction-based confidence instead
                            calculated_confidence = confidence_score
                        
                        # Combine with verification confidence if available
                        if verification_result:
                            confidence_score = (confidence_score + calculated_confidence) / 2
                        else:
                            confidence_score = calculated_confidence
                            
                    except Exception as e:
                        logger.warning(f"Confidence scoring failed for {citation_text}: {e}")
                        # Keep our extraction-based confidence if scoring fails
                
                # False positive prevention
                if self.options.enable_false_positive_prevention:
                    if not self._is_valid_citation(citation_text, case_name, year, confidence_score):
                        logger.debug(f"Filtered out potential false positive: {citation_text}")
                        continue
                
                # Create enhanced citation result
                if (not isinstance(citation, dict) and 
                    hasattr(citation, 'extracted_case_name')):
                    # This is a CitationResult object, preserve it and add enhanced data
                    enhanced_citation = citation
                    # Update the existing object with enhanced data
                    setattr(enhanced_citation, 'confidence_score', confidence_score)
                    setattr(enhanced_citation, 'verification_result', verification_result)
                    setattr(enhanced_citation, 'extraction_method', 'enhanced_local')
                    setattr(enhanced_citation, 'false_positive_filtered', False)
                    # Ensure the extracted case name is preserved
                    if case_name:
                        setattr(enhanced_citation, 'extracted_case_name', case_name)
                    if year:
                        setattr(enhanced_citation, 'extracted_date', year)
                else:
                    # Create new enhanced citation result
                    enhanced_citation = {
                        'citation': citation_text,
                        'extracted_case_name': case_name,
                        'extracted_date': year,
                        'confidence_score': confidence_score,
                        'verification_result': verification_result,
                        'extraction_method': 'enhanced_local',
                        'false_positive_filtered': False
                    }
                
                enhanced_citations.append(enhanced_citation)
            
            logger.info(f"Enhanced local extraction completed: {len(enhanced_citations)} citations")
            return enhanced_citations
            
        except Exception as e:
            logger.error(f"Enhanced local extraction failed: {e}")
            # Fall back to basic extraction
            return self._extract_names_years_basic(citations, text)
    
    def _extract_case_name_local(self, text: str, citation: str) -> Optional[str]:
        """Extract case name from text context around citation."""
        try:
            # Find citation position in text
            pos = text.find(citation)
            if pos == -1:
                return None
            
            # Look for case name patterns before citation
            before_text = text[max(0, pos-300):pos]  # Increased context window
            
            # More flexible case name patterns
            patterns = [
                # Standard v. pattern
                r'([A-Z][a-zA-Z\s&.,]+)\s+v\.\s+([A-Z][a-zA-Z\s&.,]+)',
                # In re pattern
                r'In\s+re\s+([A-Z][a-zA-Z\s&.,]+)',
                # State v. pattern
                r'State\s+v\.\s+([A-Z][a-zA-Z\s&.,]+)',
                # LLC pattern (common in business cases)
                r'([A-Z][a-zA-Z\s&.,]+LLC)\s+v\.\s+([A-Z][a-zA-Z\s&.,]+LLC)',
                # Department pattern
                r'([A-Z][a-zA-Z\s&.,]+)\s+v\.\s+([A-Z][a-zA-Z\s&.,]+)',
            ]
            
            import re
            for pattern in patterns:
                match = re.search(pattern, before_text)
                if match:
                    case_name = match.group(0).strip()
                    # Clean up the case name
                    case_name = re.sub(r'\s+', ' ', case_name)  # Normalize whitespace
                    if len(case_name) > 5:  # Ensure it's a reasonable length
                        return case_name
            
            # If no pattern match, try to extract the most recent capitalized phrase
            # Look for phrases that end with a period or comma before the citation
            words = before_text.split()
            potential_names = []
            
            for i in range(len(words) - 1, -1, -1):  # Go backwards
                word = words[i]
                if word.endswith('.') or word.endswith(','):
                    # Found a potential end of case name
                    name_parts = words[max(0, i-3):i+1]  # Take up to 4 words
                    potential_name = ' '.join(name_parts).strip('., ')
                    if potential_name and len(potential_name) > 5:
                        potential_names.append(potential_name)
                        if len(potential_names) >= 2:  # Take the second most recent
                            return potential_names[1]
            
            return None
            
        except Exception as e:
            logger.debug(f"Case name extraction failed: {e}")
            return None
    
    def _extract_year_local(self, text: str, citation: str) -> Optional[str]:
        """Extract year from citation text or surrounding context."""
        import re
        
        # First try to find year in the citation itself
        year_match = re.search(r'\((\d{4})\)', citation)
        if year_match:
            return year_match.group(1)
        
        # If no year in citation, look in surrounding context
        pos = text.find(citation)
        if pos != -1:
            # Look in a window around the citation
            context_start = max(0, pos - 50)
            context_end = min(len(text), pos + len(citation) + 50)
            context = text[context_start:context_end]
            
            # Look for year patterns
            year_patterns = [
                r'\((\d{4})\)',  # (2022)
                r'(\d{4})',      # 2022
                r'(\d{2})',      # 22 (for recent years)
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, context)
                for match in matches:
                    year = match
                    # Validate year
                    if len(year) == 4 and 1900 <= int(year) <= 2030:
                        return year
                    elif len(year) == 2 and 20 <= int(year) <= 30:
                        return f"20{year}"
        
        return None
    
    def _extract_names_years_basic(self, citations: List, text: str) -> List[Dict]:
        """Basic name and year extraction as fallback."""
        try:
            basic_citations = []
            
            for citation in citations:
                citation_text = citation['citation'] if isinstance(citation, dict) and 'citation' in citation else str(citation)
                
                # Basic extraction
                case_name = self._extract_case_name_local(text, citation_text)
                year = self._extract_year_local(text, citation_text)
                
                basic_citation = {
                    'citation': citation_text,
                    'extracted_case_name': case_name,
                    'extracted_date': year,
                    'confidence_score': 0.5,  # Default confidence
                    'verification_result': None,
                    'extraction_method': 'basic_fallback',
                    'false_positive_filtered': False
                }
                
                basic_citations.append(basic_citation)
            
            logger.info(f"Basic extraction completed: {len(basic_citations)} citations")
            return basic_citations
            
        except Exception as e:
            logger.error(f"Basic extraction failed: {e}")
            # Return original citations as last resort
            return [{'citation': str(c), 'extracted_case_name': None, 'extracted_date': None, 
                    'confidence_score': 0.0, 'verification_result': None, 
                    'extraction_method': 'error_fallback', 'false_positive_filtered': False} 
                   for c in citations]

    def _is_valid_citation(self, citation: str, case_name: Optional[str], year: Optional[str], confidence: float) -> bool:
        """
        Apply false positive prevention logic.
        This is a placeholder and can be enhanced with more sophisticated rules.
        """
        if not self.options.enable_false_positive_prevention:
            return True

        # During initial extraction, be more lenient - allow citations through
        # even if case names or years aren't extracted yet
        if confidence >= 0.5:  # Lower threshold for initial extraction
            return True

        # Only apply strict filtering for very low confidence citations
        if confidence < 0.3:
            # Very strict filtering for extremely low confidence
            if not case_name and not year:
                logger.debug(f"Filtered out very low confidence citation: {citation} (Confidence: {confidence:.2f})")
                return False
            
            # Filter out citations with very short case names during strict filtering
            if case_name and len(case_name.split()) < 2:
                logger.debug(f"Filtered out citation with very short case name: {citation} (Case: '{case_name}')")
                return False

        return True
    
    def _cluster_citations_local(self, citations: List, text: str, request_id: str) -> List:
        """Local citation clustering without verification."""
        try:
            if len(text) < self.clustering_threshold or len(citations) <= self.max_citations_for_local_clustering:
                logger.info(f"[EnhancedSyncProcessor {request_id}] Skipping local clustering for short text/few citations")
                return []
            
            # Simple clustering based on reporter and proximity
            clusters = []
            processed = set()
            
            for i, citation in enumerate(citations):
                if i in processed:
                    continue
                
                citation_text = citation.get('citation', str(citation))
                cluster = [citation]
                processed.add(i)
                
                # Find similar citations
                for j, other_citation in enumerate(citations[i+1:], i+1):
                    if j in processed:
                        continue
                    
                    other_text = other_citation.get('citation', str(other_citation))
                    
                    # Check if citations are from same reporter
                    if self._same_reporter(citation_text, other_text):
                        cluster.append(other_citation)
                        processed.add(j)
                
                if len(cluster) > 1:
                    clusters.append({
                        'cluster_id': f"local_cluster_{len(clusters)}",
                        'citations': cluster,
                        'reporter': self._extract_reporter(citation_text),
                        'cluster_type': 'local_proximity'
                    })
            
            logger.info(f"[EnhancedSyncProcessor {request_id}] Local clustering created {len(clusters)} clusters")
            return clusters
            
        except Exception as e:
            logger.warning(f"[EnhancedSyncProcessor {request_id}] Local clustering failed: {e}")
            return []
    
    def _same_reporter(self, citation1: str, citation2: str) -> bool:
        """Check if two citations are from the same reporter."""
        try:
            reporter1 = self._extract_reporter(citation1)
            reporter2 = self._extract_reporter(citation2)
            return reporter1 == reporter2
        except:
            return False
    
    def _extract_reporter(self, citation: str) -> str:
        """Extract reporter from citation."""
        import re
        match = re.search(r'\b(Wn\.|P\.|U\.S\.|S\.Ct\.)', citation)
        return match.group(1) if match else "Unknown"
    
    def _process_basic_sync(self, text: str, request_id: str) -> Dict[str, Any]:
        """Basic sync processing as fallback."""
        try:
            citations = self._extract_citations_basic_regex(text)
            citations_list = [{'citation': c, 'extracted_case_name': None, 'extracted_date': None} for c in citations]
            
            return {
                'success': True,
                'citations': citations_list,
                'clusters': [],
                'processing_strategy': 'basic_sync',
                'extraction_method': 'basic_regex',
                'verification_status': 'pending_async',
                'local_processing_complete': True
            }
            
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] Basic sync failed: {e}")
            return {
                'success': False,
                'error': f'Basic sync failed: {str(e)}',
                'citations': [],
                'clusters': []
            }
    
    def _queue_async_verification(self, citations: List, text: str, request_id: str, input_type: str, metadata: Dict) -> Dict[str, Any]:
        """Queue citations for async verification using fallback verifier."""
        try:
            from rq import Queue
            from redis import Redis
            
            # Connect to Redis
            redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
            redis_conn = Redis.from_url(redis_url)
            queue = Queue('casestrainer', connection=redis_conn)
            
            # Queue async verification job
            job = queue.enqueue(
                'src.async_verification_worker.verify_citations_enhanced',
                args=(citations, text, request_id, input_type, metadata),
                job_id=f"verify_enhanced_{request_id}",
                job_timeout='10m',
                result_ttl=86400,
                failure_ttl=86400
            )
            
            logger.info(f"[EnhancedSyncProcessor {request_id}] Async verification queued with job_id: {job.id}")
            
            return {
                'verification_queued': True,
                'verification_job_id': job.id,
                'verification_queue': 'casestrainer',
                'message': 'Citations queued for async verification with fallback verifier'
            }
            
        except Exception as e:
            logger.error(f"[EnhancedSyncProcessor {request_id}] Failed to queue verification: {e}")
            return {
                'verification_queued': False,
                'error': str(e),
                'message': 'Failed to queue async verification'
            }
    
    def _redirect_to_full_async(self, text: str, request_id: str, input_type: str, metadata: Dict) -> Dict[str, Any]:
        """Redirect to full async processing when text is too long."""
        return {
            'success': True,
            'status': 'redirected_to_full_async',
            'message': f'Text too long ({len(text)} chars) for enhanced sync processing. Redirecting to full async.',
            'task_id': request_id,
            'processing_mode': 'full_async_redirect',
            'text_length': len(text),
            'request_id': request_id,
            'input_type': input_type,
            'metadata': metadata
        }
    
    def _debug_citation_object(self, citation, prefix="DEBUG"):
        """Debug method to inspect citation objects thoroughly."""
        try:
            logger.info(f"[{prefix}] Citation object type: {type(citation)}")
            logger.info(f"[{prefix}] Citation object: {citation}")
            
            if hasattr(citation, '__dict__'):
                logger.info(f"[{prefix}] Citation object attributes: {citation.__dict__}")
                for attr, value in citation.__dict__.items():
                    logger.info(f"[{prefix}]   {attr}: {value} (type: {type(value)})")
            
            # Check specific attributes
            for attr in ['citation', 'extracted_case_name', 'extracted_date', 'extracted_year', 'canonical_name', 'canonical_date']:
                if hasattr(citation, attr):
                    value = getattr(citation, attr)
                    logger.info(f"[{prefix}]   {attr}: {value} (type: {type(value)})")
                else:
                    logger.info(f"[{prefix}]   {attr}: NOT FOUND")
                    
        except Exception as e:
            logger.error(f"[{prefix}] Debug failed: {e}")

    def _convert_citations_to_dicts(self, citations: List) -> List[Dict[str, Any]]:
        """Convert enhanced citations to standard format."""
        print(f"DEBUG: _convert_citations_to_dicts called with {len(citations)} citations")
        try:
            converted = []
            
            for i, citation in enumerate(citations):
                print(f"DEBUG: Processing citation {i+1}: {type(citation)} - {citation}")
                
                if isinstance(citation, dict):
                    print(f"DEBUG: Citation {i+1} is a dict")
                    # Enhanced citation format
                    converted_citation = {
                        'citation': citation.get('citation', ''),
                        'extracted_case_name': citation.get('extracted_case_name'),
                        'extracted_date': citation.get('extracted_date'),
                        'confidence_score': citation.get('confidence_score', 0.5),
                        'extraction_method': citation.get('extraction_method', 'unknown'),
                        'false_positive_filtered': citation.get('false_positive_filtered', False)
                    }
                    
                    # Add verification metadata if available
                    verification_result = citation.get('verification_result')
                    if verification_result:
                        converted_citation.update({
                            'verified': verification_result.get('verified', False),
                            'canonical_name': verification_result.get('canonical_name'),
                            'canonical_date': verification_result.get('canonical_date'),
                            'url': verification_result.get('url'),
                            'source': verification_result.get('source'),
                            'validation_method': verification_result.get('validation_method'),
                            'verification_confidence': verification_result.get('confidence', 0.0)
                        })
                    else:
                        converted_citation.update({
                            'verified': False,
                            'canonical_name': None,
                            'canonical_date': None,
                            'url': None,
                            'source': 'local_extraction',
                            'validation_method': 'none',
                            'verification_confidence': 0.0
                        })
                    
                    converted.append(converted_citation)
                    print(f"DEBUG: Converted dict citation {i+1}: {converted_citation}")
                    
                elif hasattr(citation, 'citation'):
                    print(f"DEBUG: Citation {i+1} has citation attribute")
                    # Handle CitationResult objects or similar citation objects
                    try:
                        # Debug the citation object
                        self._debug_citation_object(citation, "CONVERSION")
                        
                        # Extract citation text
                        citation_text = getattr(citation, 'citation', str(citation))
                        
                        # Extract case name from various possible attributes
                        case_name = None
                        if hasattr(citation, 'extracted_case_name') and getattr(citation, 'extracted_case_name'):
                            case_name = getattr(citation, 'extracted_case_name')
                            print(f"DEBUG: Found extracted_case_name: {case_name}")
                        elif hasattr(citation, 'canonical_name') and getattr(citation, 'canonical_name'):
                            case_name = getattr(citation, 'canonical_name')
                            print(f"DEBUG: Found canonical_name: {case_name}")
                        
                        # Extract date from various possible attributes
                        extracted_date = None
                        if hasattr(citation, 'extracted_date') and getattr(citation, 'extracted_date'):
                            extracted_date = getattr(citation, 'extracted_date')
                            print(f"DEBUG: Found extracted_date: {extracted_date}")
                        elif hasattr(citation, 'extracted_year') and getattr(citation, 'extracted_year'):
                            extracted_date = getattr(citation, 'extracted_year')
                            print(f"DEBUG: Found extracted_year: {extracted_date}")
                        elif hasattr(citation, 'canonical_date') and getattr(citation, 'canonical_date'):
                            extracted_date = getattr(citation, 'canonical_date')
                            print(f"DEBUG: Found canonical_date: {extracted_date}")
                        
                        # Extract confidence
                        confidence = 0.7  # Default confidence
                        if hasattr(citation, 'confidence') and getattr(citation, 'confidence'):
                            confidence = getattr(citation, 'confidence', 0.7)
                        elif hasattr(citation, 'confidence_score') and getattr(citation, 'confidence_score'):
                            confidence = getattr(citation, 'confidence_score', 0.7)
                        
                        # Extract method
                        method = 'citation_object'
                        if hasattr(citation, 'method') and getattr(citation, 'method'):
                            method = getattr(citation, 'method', 'citation_object')
                        elif hasattr(citation, 'extraction_method') and getattr(citation, 'extraction_method'):
                            method = getattr(citation, 'extraction_method', 'citation_object')
                        
                        # Extract verification status
                        verified = False
                        if hasattr(citation, 'verified') and getattr(citation, 'verified'):
                            verified = getattr(citation, 'verified', False)
                        
                        # Extract URL
                        url = None
                        if hasattr(citation, 'url') and getattr(citation, 'url'):
                            url = getattr(citation, 'url')
                        elif hasattr(citation, 'canonical_url') and getattr(citation, 'canonical_url'):
                            url = getattr(citation, 'canonical_url')
                        
                        # Log what we found for debugging
                        print(f"DEBUG: Converting CitationResult: citation='{citation_text}', case_name='{case_name}', date='{extracted_date}', confidence={confidence}")
                        
                        converted_citation = {
                            'citation': citation_text,
                            'extracted_case_name': case_name,
                            'extracted_date': extracted_date,
                            'confidence_score': confidence,
                            'extraction_method': method,
                            'false_positive_filtered': False,
                            'verified': verified,
                            'canonical_name': case_name,  # Use extracted case name as canonical for now
                            'canonical_date': extracted_date,  # Use extracted date as canonical for now
                            'url': url,
                            'source': 'citation_object',
                            'validation_method': 'object_extraction',
                            'verification_confidence': confidence
                        }
                        
                        converted.append(converted_citation)
                        print(f"DEBUG: Converted object citation {i+1}: {converted_citation}")
                        
                    except Exception as e:
                        print(f"DEBUG: Failed to convert citation object: {e}")
                        logger.warning(f"Failed to convert citation object: {e}")
                        # Fall back to basic conversion
                        converted.append({
                            'citation': str(citation),
                            'extracted_case_name': None,
                            'extracted_date': None,
                            'confidence_score': 0.5,
                            'extraction_method': 'object_fallback',
                            'false_positive_filtered': False,
                            'verified': False,
                            'canonical_name': None,
                            'canonical_date': None,
                            'url': None,
                            'source': 'object_fallback',
                            'validation_method': 'none',
                            'verification_confidence': 0.0
                        })
                else:
                    print(f"DEBUG: Citation {i+1} is neither dict nor has citation attribute")
                    # Fallback for non-dict citations
                    converted.append({
                        'citation': str(citation),
                        'extracted_case_name': None,
                        'extracted_date': None,
                        'confidence_score': 0.5,
                        'extraction_method': 'fallback',
                        'false_positive_filtered': False,
                        'verified': False,
                        'canonical_name': None,
                        'canonical_date': None,
                        'url': None,
                        'source': 'fallback',
                        'validation_method': 'none',
                        'verification_confidence': 0.0
                    })
            
            print(f"DEBUG: Conversion completed. Converted {len(converted)} citations")
            logger.info(f"Converted {len(converted)} citations to standard format")
            return converted
            
        except Exception as e:
            print(f"DEBUG: Citation conversion failed: {e}")
            logger.error(f"Citation conversion failed: {e}")
            # Return basic format as fallback
            return [{'citation': str(c), 'extracted_case_name': None, 'extracted_date': None, 
                    'confidence_score': 0.0, 'extraction_method': 'error_fallback', 
                    'false_positive_filtered': False, 'verified': False, 'canonical_name': None, 
                    'canonical_date': None, 'url': None, 'source': 'error', 'validation_method': 'none', 
                    'verification_confidence': 0.0} for c in citations]
    
    def _convert_clusters_to_dicts(self, clusters: List) -> List[Dict[str, Any]]:
        """Convert cluster objects to dictionaries for API response."""
        clusters_list = []
        if clusters:
            for cluster in clusters:
                if isinstance(cluster, dict):
                    cluster_dict = cluster.copy()
                else:
                    cluster_dict = {
                        'cluster_id': getattr(cluster, 'cluster_id', None),
                        'citations': [str(c) for c in getattr(cluster, 'citations', [])],
                        'reporter': getattr(cluster, 'reporter', None),
                        'cluster_type': getattr(cluster, 'cluster_type', 'local')
                    }
                clusters_list.append(cluster_dict)
        
        return clusters_list
    
    def _cleanup_cache(self):
        """Clean up old cache entries to prevent memory bloat."""
        current_time = time.time()
        if current_time - self._last_cache_cleanup > self._cache_cleanup_interval:
            old_keys = [
                key for key, value in self.cache.items()
                if current_time - value.get('cache_time', 0) > self.cache_ttl
            ]
            for key in old_keys:
                del self.cache[key]
            
            if old_keys:
                logger.info(f"[EnhancedSyncProcessor] Cleared {len(old_keys)} old cache entries")
            
            self._last_cache_cleanup = current_time
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        return {
            'cache': {
                'cache_size': len(self.cache),
                'cache_ttl': self.cache_ttl
            },
            'thresholds': {
                'enhanced_sync_threshold': self.enhanced_sync_threshold,
                'ultra_fast_threshold': self.ultra_fast_threshold,
                'clustering_threshold': self.clustering_threshold,
                'max_citations_for_local_clustering': self.max_citations_for_local_clustering
            },
            'processing_modes': ['enhanced_sync', 'basic_sync', 'full_async_redirect'],
            'features': ['local_extraction', 'local_normalization', 'local_clustering', 'async_verification']
        }
