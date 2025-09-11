"""
Name and Year Extraction Module

This module handles the extraction of case names and years from text context
around citations, with confidence scoring and verification integration.
"""

import logging
from typing import List, Dict, Any, Optional
from .error_handler import handle_processor_errors, ProcessorErrorHandler

logger = logging.getLogger(__name__)

class NameYearExtractor:
    """Handles extraction of case names and years from citation context."""
    
    def __init__(self, enhanced_verifier=None, confidence_scorer=None, options=None):
        self.enhanced_verifier = enhanced_verifier
        self.confidence_scorer = confidence_scorer
        self.options = options or {}
        self.error_handler = ProcessorErrorHandler("NameYearExtractor")
    
    @handle_processor_errors("extract_names_years_local", default_return=[])
    def extract_names_years_local(self, citations: List, text: str) -> List[Dict]:
        """Enhanced local name/year extraction with verification and confidence scoring."""
        try:
            enhanced_citations = []
            
            for citation in citations:
                if isinstance(citation, dict) and 'citation' in citation:
                    citation_text = citation['citation']
                elif hasattr(citation, 'citation'):
                    citation_text = getattr(citation, 'citation', '')
                else:
                    citation_text = str(citation)
                
                if (not isinstance(citation, dict) and 
                    hasattr(citation, 'extracted_case_name') and 
                    getattr(citation, 'extracted_case_name', None)):
                    case_name = getattr(citation, 'extracted_case_name', None)
                    year = getattr(citation, 'extracted_date', None) or getattr(citation, 'extracted_year', None)
                    confidence_score = getattr(citation, 'confidence', 0.7)
                elif isinstance(citation, dict) and citation.get('extracted_case_name'):
                    case_name = citation.get('extracted_case_name')
                    year = citation.get('extracted_date') or citation.get('extracted_year')
                    confidence_score = citation.get('confidence_score', 0.7)
                else:
                    case_name = self._extract_case_name_local(text, citation_text)
                    year = self._extract_year_local(text, citation_text)
                    
                    confidence_score = 0.7  # Start with good confidence
                    if case_name:
                        confidence_score += 0.1  # Bonus for case name
                    if year:
                        confidence_score += 0.1  # Bonus for year
                
                verification_result = None
                
                if self.enhanced_verifier and self.options.get('enable_enhanced_verification', False):
                    try:
                        verification_result = self.enhanced_verifier.verify_citation_enhanced(
                            citation_text, case_name
                        )
                        
                        if verification_result.get('verified'):
                            confidence_score = verification_result.get('confidence', 0.7)
                            canonical_name = verification_result.get('canonical_name')
                            canonical_date = verification_result.get('canonical_date')
                            if canonical_date:
                                year = canonical_date
                        else:
                            confidence_score = 0.3
                            
                    except Exception as e:
                        logger.warning(f"Enhanced verification failed for {citation_text}: {e}")
                        verification_result = None
                
                if self.confidence_scorer and self.options.get('enable_confidence_scoring', False):
                    try:
                        citation_dict = {
                            'citation': citation_text,
                            'extracted_case_name': case_name,
                            'extracted_date': year,
                            'verified': verification_result.get('verified', False) if verification_result else False,
                            'method': 'enhanced_local_extraction'
                        }
                        
                        calculated_confidence = self.confidence_scorer.calculate_citation_confidence(
                            citation_dict, text
                        )
                        
                        if calculated_confidence < 0.3:
                            calculated_confidence = confidence_score
                        
                        if verification_result:
                            confidence_score = (confidence_score + calculated_confidence) / 2
                        else:
                            confidence_score = calculated_confidence
                            
                    except Exception as e:
                        logger.warning(f"Confidence scoring failed for {citation_text}: {e}")
                
                if self.options.get('enable_false_positive_prevention', False):
                    if not self._is_valid_citation(citation_text, case_name, year, confidence_score):
                        continue
                
                if (not isinstance(citation, dict) and 
                    hasattr(citation, 'extracted_case_name')):
                    enhanced_citation = citation
                    setattr(enhanced_citation, 'confidence_score', confidence_score)
                    setattr(enhanced_citation, 'verification_result', verification_result)
                    setattr(enhanced_citation, 'extraction_method', 'enhanced_local')
                    setattr(enhanced_citation, 'false_positive_filtered', False)
                    if case_name:
                        setattr(enhanced_citation, 'extracted_case_name', case_name)
                    if year:
                        setattr(enhanced_citation, 'extracted_date', year)
                    if 'canonical_name' in locals():
                        setattr(enhanced_citation, 'canonical_name', canonical_name)
                    if 'canonical_date' in locals():
                        setattr(enhanced_citation, 'canonical_date', canonical_date)
                else:
                    enhanced_citation = {
                        'citation': citation_text,
                        'extracted_case_name': case_name,
                        'extracted_date': year,
                        'confidence_score': confidence_score,
                        'verification_result': verification_result,
                        'extraction_method': 'enhanced_local',
                        'false_positive_filtered': False
                    }
                    if 'canonical_name' in locals():
                        enhanced_citation['canonical_name'] = canonical_name
                    if 'canonical_date' in locals():
                        enhanced_citation['canonical_date'] = canonical_date
                
                enhanced_citations.append(enhanced_citation)
            
            logger.info(f"Enhanced local extraction completed: {len(enhanced_citations)} citations")
            return enhanced_citations
            
        except Exception as e:
            logger.error(f"Enhanced local extraction failed: {e}")
            return self._extract_names_years_basic(citations, text)
    
    def _extract_case_name_local(self, text: str, citation: str) -> Optional[str]:
        """Extract case name from text context around citation using MASTER extraction function."""
        try:
            from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
            
            citation_start = text.find(citation)
            if citation_start == -1:
                citation_with_newline = citation.replace(' ', '\n', 1)
                citation_start = text.find(citation_with_newline)
                if citation_start != -1:
                    citation = citation_with_newline
            
            citation_end = citation_start + len(citation) if citation_start != -1 else None
            
            result = extract_case_name_and_date_master(
                text=text, 
                citation=citation, 
                citation_start=citation_start if citation_start != -1 else None,
                citation_end=citation_end,
                debug=False
            )
            case_name = result.get('case_name')
            return case_name
        except Exception as e:
            logger.warning(f"Case name extraction failed for {citation}: {e}")
            return None
    
    def _extract_year_local(self, text: str, citation: str) -> Optional[str]:
        """Extract year from text context around citation."""
        try:
            import re
            
            citation_start = text.find(citation)
            if citation_start == -1:
                return None
            
            # Look for year patterns around the citation
            context_start = max(0, citation_start - 200)
            context_end = min(len(text), citation_start + len(citation) + 200)
            context = text[context_start:context_end]
            
            # Look for 4-digit years
            year_pattern = r'\b(19|20)\d{2}\b'
            years = re.findall(year_pattern, context)
            
            if years:
                # Return the most recent year found
                return max(years)
            
            return None
            
        except Exception as e:
            logger.warning(f"Year extraction failed for {citation}: {e}")
            return None
    
    def _is_valid_citation(self, citation_text: str, case_name: Optional[str], year: Optional[str], confidence_score: float) -> bool:
        """Validate if citation meets quality thresholds."""
        if confidence_score < 0.3:
            return False
        
        if not case_name and not year:
            return False
        
        if len(citation_text.strip()) < 8:
            return False
        
        return True
    
    def _extract_names_years_basic(self, citations: List, text: str) -> List[Dict]:
        """Basic fallback extraction without advanced features."""
        enhanced_citations = []
        
        for citation in citations:
            if isinstance(citation, dict) and 'citation' in citation:
                citation_text = citation['citation']
            elif hasattr(citation, 'citation'):
                citation_text = getattr(citation, 'citation', '')
            else:
                citation_text = str(citation)
            
            enhanced_citation = {
                'citation': citation_text,
                'extracted_case_name': None,
                'extracted_date': None,
                'confidence_score': 0.5,
                'verification_result': None,
                'extraction_method': 'basic_fallback',
                'false_positive_filtered': False
            }
            
            enhanced_citations.append(enhanced_citation)
        
        return enhanced_citations
