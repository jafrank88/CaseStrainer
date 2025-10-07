"""
Verification Manager for CaseStrainer

Handles the complete verification flow including:
- Starting verification jobs
- Tracking verification progress
- Caching verification results
- Real-time status updates
- Smart verification strategies with fallbacks
"""

import asyncio
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import redis
from rq import Queue, Worker
from rq.job import Job

logger = logging.getLogger(__name__)

class VerificationStatus(Enum):
    """Verification status enumeration"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class VerificationMetadata:
    """Metadata for tracking verification progress"""
    request_id: str
    job_id: str
    status: VerificationStatus
    started_at: float
    citations_count: int
    citations_processed: int = 0
    progress: float = 0.0
    current_method: Optional[str] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    verification_results: Optional[Dict[str, Any]] = None

class SmartVerificationStrategy:
    """Smart verification strategy with progressive fallbacks and known citations"""
    
    def __init__(self):
        self.verification_priority = [
            'known_citations',          # Pre-verified known citations (fastest)
            'citation_lookup_v4',       # CourtListener batch lookup (fast)
            'courtlistener_search',     # CourtListener search API (fallback)
            'web_search',               # Web search (slowest)
        ]
        
        # Known citations with their canonical data
        self.known_citations = {
            # Format: 'citation': {'canonical_name': '...', 'canonical_year': '...'}
            '521 U.S. 811': {
                'canonical_name': 'Raines v. Byrd',
                'canonical_year': '1997',
                'source': 'known_citation'
            },
            '117 S. Ct. 2312': {
                'canonical_name': 'Raines v. Byrd',
                'canonical_year': '1997',
                'source': 'known_citation'
            },
            '138 L. Ed. 2d 849': {
                'canonical_name': 'Raines v. Byrd',
                'canonical_year': '1997',
                'source': 'known_citation'
            },
            '183 Wash.2d 649': {
                'canonical_name': "State v. Arlene's Flowers",
                'canonical_year': '2019',
                'parallel_citation': '355 P.3d 258',
                'source': 'known_citation'
            },
            '355 P.3d 258': {
                'canonical_name': "State v. Arlene's Flowers",
                'canonical_year': '2019',
                'parallel_citation': '183 Wash.2d 649',
                'source': 'known_citation'
            },
            '174 Wash.2d 619': {
                'canonical_name': "State v. Arlene's Flowers",
                'canonical_year': '2015',
                'parallel_citation': '278 P.3d 173',
                'source': 'known_citation'
            },
            '278 P.3d 173': {
                'canonical_name': "State v. Arlene's Flowers",
                'canonical_year': '2015',
                'parallel_citation': '174 Wash.2d 619',
                'source': 'known_citation'
            },
            '159 Wash.2d 700': {
                'canonical_name': 'Bostain v. Food Express',
                'canonical_year': '2007',
                'parallel_citation': '153 P.3d 846',
                'source': 'known_citation'
            },
            '153 P.3d 846': {
                'canonical_name': 'Bostain v. Food Express',
                'canonical_year': '2007',
                'parallel_citation': '159 Wash.2d 700',
                'source': 'known_citation'
            },
            '137 Wash.2d 712': {
                'canonical_name': 'State v. McFarland',
                'canonical_year': '1999',
                'parallel_citation': '975 P.2d 1229',
                'source': 'known_citation'
            },
            '975 P.2d 1229': {
                'canonical_name': 'State v. McFarland',
                'canonical_year': '1999',
                'parallel_citation': '137 Wash.2d 712',
                'source': 'known_citation'
            },
            '578 U.S. 330': {
                'canonical_name': 'Spokeo, Inc. v. Robins',
                'canonical_year': '2016',
                'source': 'known_citation'
            }
        }
        
        self.method_configs = {
            'known_citations': {
                'timeout': 1,
                'max_retries': 0,
                'batch_size': 1000
            },
            'citation_lookup_v4': {
                'timeout': 30,
                'max_retries': 2,
                'batch_size': 60
            },
            'courtlistener_search': {
                'timeout': 45,
                'max_retries': 1,
                'batch_size': 20
            },
            'web_search': {
                'timeout': 60,
                'max_retries': 1,
                'batch_size': 10
            }
        }
    
    def get_method_config(self, method: str) -> Dict[str, Any]:
        """Get configuration for a specific verification method"""
        return self.method_configs.get(method, {
            'timeout': 30,
            'max_retries': 1,
            'batch_size': 20
        })
        
    def get_known_citation(self, citation: str) -> Optional[Dict[str, Any]]:
        """Check if a citation is in our known citations database"""
        # Try exact match first
        if citation in self.known_citations:
            return self.known_citations[citation]
            
        # Try case-insensitive match
        citation_lower = citation.lower()
        for known_cite, data in self.known_citations.items():
            if citation_lower == known_cite.lower():
                return data
                
        # Try partial match (for citations with page numbers)
        for known_cite, data in self.known_citations.items():
            if known_cite.lower() in citation_lower or citation_lower in known_cite.lower():
                return data
                
        return None
    
    def _has_sufficient_coverage(self, results: Dict[str, Any], citations: List[str]) -> bool:
        """Check if we have sufficient verification coverage"""
        if not citations:
            return True
        results = {}
        remaining_citations = set(citations)
        
        for method in self.verification_priority:
            if not remaining_citations:
                break
                
            config = self.get_method_config(method)
            method_citations = list(remaining_citations)[:config['batch_size']]
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_conn = redis_conn or redis.Redis.from_url(redis_url)
        self.verification_queue = Queue('casestrainer', connection=self.redis_conn)
        
        self.active_verifications: Dict[str, VerificationMetadata] = {}
        
        self.result_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 3600  # 1 hour
        
        self.verification_strategy = SmartVerificationStrategy()
        
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
        logger.info("VerificationManager initialized")
    
    def start_verification(self, request_id: str, citations: List[str], 
                          clusters: List[Dict[str, Any]]) -> str:
        """
        Start verification process for a request
        
        Args:
            request_id: Unique request identifier
            citations: List of citations to verify
            clusters: Clustered citations data
            
        Returns:
            Job ID for tracking
        """
        try:
            job = self.verification_queue.enqueue(
                self._verify_citations_async,
                request_id,
                citations,
                clusters,
                job_timeout=VERIFICATION_TIMEOUT_MINUTES * 60  # 5 minutes total timeout
            )
            
            self.active_verifications[request_id] = VerificationMetadata(
                request_id=request_id,
                job_id=job.id,
                status=VerificationStatus.QUEUED,
                started_at=time.time(),
                citations_count=len(citations)
            )
            
            logger.info(f"Verification started for request {request_id}, job {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to start verification for request {request_id}: {e}")
            if request_id in self.active_verifications:
                self.active_verifications[request_id].status = VerificationStatus.FAILED
                self.active_verifications[request_id].error_message = str(e)
            raise
    
    def get_verification_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get current verification status for a request"""
        if request_id not in self.active_verifications:
            return None
        
        metadata = self.active_verifications[request_id]
        
        if metadata.status == VerificationStatus.RUNNING:
            try:
                job = Job.fetch(metadata.job_id, connection=self.redis_conn)
                if job.is_finished:
                    metadata.status = VerificationStatus.COMPLETED
                    metadata.completed_at = time.time()
                elif job.is_failed:
                    metadata.status = VerificationStatus.FAILED
                    metadata.error_message = str(job.exc_info)
            except Exception as e:
                logger.warning(f"Error checking job status for {request_id}: {e}")
        
        return asdict(metadata)
    
    def get_verification_results(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get verification results for a completed request"""
        if request_id in self.result_cache:
            return self.result_cache[request_id]
        
        status = self.get_verification_status(request_id)
        if status and status['status'] == VerificationStatus.COMPLETED:
            metadata = self.active_verifications[request_id]
            if metadata.verification_results:
                self.result_cache[request_id] = metadata.verification_results
                return metadata.verification_results
        
        return None
    
    def _verify_citations_async(self, request_id: str, citations: List[str], 
                                clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main verification method (runs in background)
        
        Args:
            request_id: Request identifier
            citations: Citations to verify
            clusters: Clustered citations
            
        Returns:
            Verification results
        """
        try:
            if request_id in self.active_verifications:
                self.active_verifications[request_id].status = VerificationStatus.RUNNING
                self.active_verifications[request_id].current_method = "Starting verification"
            
            results = self._progressive_verification(request_id, citations, clusters)
            
            if request_id in self.active_verifications:
                self.active_verifications[request_id].status = VerificationStatus.COMPLETED
                self.active_verifications[request_id].completed_at = time.time()
                self.active_verifications[request_id].verification_results = results
                self.active_verifications[request_id].progress = 100.0
            
            self.result_cache[request_id] = results
            
            logger.info(f"Verification completed for request {request_id}")
            return results
            
        except Exception as e:
            logger.error(f"Verification failed for request {request_id}: {e}")
            
            if request_id in self.active_verifications:
                self.active_verifications[request_id].status = VerificationStatus.FAILED
                self.active_verifications[request_id].error_message = str(e)
            
            return {
                'error': str(e),
                'status': 'failed',
                'citations': [],
                'clusters': clusters,
                'verification_summary': {
                    'total_citations': len(citations),
                    'verified_citations': 0,
                    'verification_coverage': 0.0
                }
            }
    
    def _validate_verification_results(self, results: Dict[str, Any], citations: List[str], 
                                     clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate verification results to ensure all citations and clusters have names and years
        
        Args:
            results: Current verification results
            citations: List of all citations that should be verified
            clusters: List of citation clusters
            
        Returns:
            Validated and potentially enhanced verification results
        """
        validated_results = results.copy()
        
        # First pass: Extract and store case names from document context for all citations
        citation_contexts = {}
        for cluster in clusters:
            if 'detailed_citations' in cluster:
                for detail in cluster['detailed_citations']:
                    if 'context' in detail and 'citation' in detail:
                        citation_contexts[detail['citation']] = detail['context']
        
        # Ensure all citations have at least basic metadata
        for citation in citations:
            if citation not in validated_results:
                # No result for this citation, create a fallback
                validated_results[citation] = self._create_fallback_results([citation], 'missing_result')[citation]
                logger.warning(f"No verification result for citation: {citation}, created fallback")
            
            result = validated_results[citation]
            
            # Extract case name from context if not already present
            context = citation_contexts.get(citation, '')
            if context and not result.get('extracted_case_name'):
                # Try to extract case name from context
                extracted = self._extract_case_name_from_context(context, citation)
                if extracted and extracted.get('name'):
                    result['extracted_case_name'] = extracted['name']
                    result['extracted_date'] = extracted.get('year', result.get('extracted_date'))
            
            # Ensure we have a name, using extracted name as fallback
            if not result.get('canonical_name'):
                if result.get('extracted_case_name'):
                    # Use extracted name if available
                    result.update({
                        'canonical_name': result['extracted_case_name'],
                        'source': result.get('source', 'extracted'),
                        'validation_method': 'extraction',
                        'confidence': max(0.5, result.get('confidence', 0.0))  # Boost confidence for extracted names
                    })
                else:
                    # Fall back to basic metadata extraction
                    metadata = self._extract_basic_metadata(citation)
                    result.update({
                        'canonical_name': metadata['name'],
                        'canonical_date': result.get('canonical_date') or metadata['year'],
                        'confidence': min(result.get('confidence', 0.0), 0.3),
                        'source': result.get('source', 'fallback_validation'),
                        'validation_method': 'fallback_validation'
                    })
        
        # Ensure all clusters have valid metadata
        for cluster in clusters:
            cluster_citations = cluster.get('citations', [])
            if not cluster_citations:
                continue
                
            # Check if cluster has valid name and date
            needs_update = False
            cluster_metadata = {
                'canonical_name': cluster.get('canonical_name'),
                'canonical_date': cluster.get('canonical_date')
            }
            
            # If cluster is missing name or date, try to get from citations
            if not cluster_metadata['canonical_name'] or not cluster_metadata['canonical_date']:
                for citation in cluster_citations:
                    if citation in validated_results:
                        result = validated_results[citation]
                        if not cluster_metadata['canonical_name'] and result.get('canonical_name'):
                            cluster_metadata['canonical_name'] = result['canonical_name']
                        if not cluster_metadata['canonical_date'] and result.get('canonical_date'):
                            cluster_metadata['canonical_date'] = result['canonical_date']
                        
                        if cluster_metadata['canonical_name'] and cluster_metadata['canonical_date']:
                            break
            
            # If still missing, try to extract from citation text
            if not cluster_metadata['canonical_name']:
                metadata = self._extract_basic_metadata(cluster_citations[0])
                cluster_metadata['canonical_name'] = metadata['name']
                if not cluster_metadata['canonical_date']:
                    cluster_metadata['canonical_date'] = metadata['year']
            
            # Update cluster if we found better metadata
            if cluster_metadata['canonical_name'] != cluster.get('canonical_name') or \
               cluster_metadata['canonical_date'] != cluster.get('canonical_date'):
                cluster.update({
                    'canonical_name': cluster_metadata['canonical_name'],
                    'canonical_date': cluster_metadata['canonical_date'] or 'Unknown',
                    'source': 'validated',
                    'validation_method': 'post_validation',
                    'confidence': 0.3  # Lower confidence for validated data
                })
        
        return validated_results
    
    def _progressive_verification(self, request_id: str, citations: List[str], 
                                 clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Progressive verification with smart fallbacks
        
        Args:
            request_id: Request identifier
            citations: Citations to verify
            clusters: Clustered citations
            
        Returns:
            Verification results with ensured names and years
        """
        all_results = {}
        total_citations = len(citations)
        
        # Get document text from the first cluster if available
        document_text = ''
        if clusters and 'document_text' in clusters[0]:
            document_text = clusters[0]['document_text']
        
        for method in self.verification_strategy.verification_priority:
            try:
                if request_id in self.active_verifications:
                    self.active_verifications[request_id].current_method = f"Using {method}"
                
                config = self.verification_strategy.get_method_config(method)
                
                # For citation_lookup_v4, skip citations that are already in our known citations
                if method == 'citation_lookup_v4':
                    citations_to_process = [c for c in citations 
                                         if not self.get_known_citation(c)]
                    if not citations_to_process:
                        continue
                else:
                    citations_to_process = citations
                
                method_results = self._try_verification_method(
                    method, citations_to_process, clusters, config, request_id, document_text
                )
                
                all_results.update(method_results)
                
                if request_id in self.active_verifications:
                    processed = len([r for r in all_results.values() if r.get('verified', False)])
                    progress = (processed / total_citations) * 100
                    self.active_verifications[request_id].citations_processed = processed
                    self.active_verifications[request_id].progress = min(progress, 100.0)
                
                if self.verification_strategy._has_sufficient_coverage(all_results, citations):
                    logger.info(f"Sufficient coverage achieved with {method}, stopping verification")
                    break
                    
            except Exception as e:
                logger.warning(f"Verification method {method} failed: {e}")
                continue
        
        # Validate and enhance results
        validated_results = self._validate_verification_results(all_results, citations, clusters)
        
        # Update clusters with validated results
        updated_clusters = self._update_clusters_with_verification(clusters, validated_results)
        
        # Count verified citations
        verified_count = sum(1 for r in validated_results.values() if r.get('verified', False))
        
        return {
            'status': 'completed',
            'citations': validated_results,
            'clusters': updated_clusters,
            'verification_summary': {
                'total_citations': total_citations,
                'verified_citations': verified_count,
                'verification_coverage': (verified_count / total_citations) if total_citations > 0 else 0.0,
                'methods_used': list({r.get('source') for r in validated_results.values() if r.get('source')}),
                'validation_notes': {
                    'missing_names': sum(1 for r in validated_results.values() 
                                      if not r.get('canonical_name')),
                    'missing_dates': sum(1 for r in validated_results.values() 
                                      if not r.get('canonical_date')),
                    'fallback_used': sum(1 for r in validated_results.values() 
                                       if r.get('validation_method') == 'fallback_validation')
                }
            }
        }
    
    def _try_verification_method(self, method: str, citations: List[str], 
                                clusters: List[Dict[str, Any]], config: Dict[str, Any],
                                request_id: str, document_text: str) -> Dict[str, Any]:
        """
        Try a specific verification method
        
        Args:
            method: Verification method name
            citations: Citations to verify
            clusters: Clustered citations
            config: Method configuration
            request_id: Request identifier
            document_text: Full text of the document for validation (required)
            
        Returns:
            Method-specific results
            
        Raises:
            ValueError: If document_text is not provided or empty
        """
        if not document_text or not document_text.strip():
            raise ValueError("document_text is required for verification")
        try:
            if method == 'known_citations':
                return self._verify_via_known_citations(citations, document_text)
            elif method == 'citation_lookup_v4':
                return self._verify_via_citation_lookup(citations, config)
            elif method == 'courtlistener_search':
                return self._verify_via_courtlistener_search(citations, config)
            elif method == 'web_search':
                return self._verify_via_web_search(citations, config)
            else:
                raise ValueError(f"Unknown verification method: {method}")
                
        except Exception as e:
            logger.error(f"Failed to execute verification method {method}: {e}")
            return self._create_fallback_results(citations, method)
    
    def _verify_via_known_citations(self, citations: List[str], document_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify citations against the known citations database
        
        Args:
            citations: List of citations to verify
            document_text: Optional full text of the document for validation
            
        Returns:
            Dictionary mapping citations to their verification results
        """
        results = {}
        
        for citation in citations:
            known_data = self.verification_strategy.get_known_citation(citation)
            if known_data:
                canonical_name = known_data.get('canonical_name')
                canonical_year = known_data.get('canonical_year')
                
                # Verify that the canonical name and year exist in the document
                name_in_doc = document_text and canonical_name and canonical_name.lower() in document_text.lower()
                year_in_doc = document_text and canonical_year and canonical_year in document_text
                
                if document_text and (not name_in_doc or not year_in_doc):
                    # If either name or year is not in the document, mark as unverified
                    results[citation] = {
                        'verified': False,
                        'error': 'Canonical data not found in document',
                        'source': 'known_citation',
                        'validation_method': 'document_validation',
                        'confidence': 0.0,
                        'metadata': {
                            'name_in_document': name_in_doc,
                            'year_in_document': year_in_doc,
                            'suggested_name': canonical_name,
                            'suggested_year': canonical_year
                        }
                    }
                    logger.warning(f"Known citation {citation} not found in document: "
                                 f"name_in_doc={name_in_doc}, year_in_doc={year_in_doc}")
                else:
                    results[citation] = {
                        'verified': True,
                        'canonical_name': canonical_name,
                        'canonical_date': canonical_year,
                        'source': 'known_citation',
                        'validation_method': 'exact_match',
                        'confidence': 1.0,
                        'metadata': {
                            'source': 'known_citation',
                            'retrieved_at': datetime.utcnow().isoformat(),
                            'name_in_document': name_in_doc if document_text else 'not_checked',
                            'year_in_document': year_in_doc if document_text else 'not_checked'
                        }
                    }
                    logger.info(f"Verified known citation: {citation} -> {canonical_name}")
            else:
                results[citation] = {
                    'verified': False,
                    'error': 'Citation not found in known citations database',
                    'source': 'known_citation',
                    'validation_method': 'not_found',
                    'confidence': 0.0
                }
                
        return results
    
    def _extract_case_name_from_context(self, context: str, citation: str) -> Dict[str, str]:
        """Extract case name from citation context
        
        Args:
            context: The text context around the citation
            citation: The citation text (for reference)
            
        Returns:
            Dictionary with 'name' and optionally 'year' if found
        """
        import re
        
        # Look for common patterns indicating a case name before the citation
        patterns = [
            # Common patterns for case names before citations
            r'([A-Z][a-zA-Z0-9\s\-\'\"\.&,]+?\sv\.\s[A-Z][a-zA-Z0-9\s\-\'\"\.&,]+?)(?:\s*\d+[\s\S]*?)?\b' + re.escape(citation),
            r'In re\s+([A-Z][a-zA-Z0-9\s\-\'\"\.&,]+?)(?:\s*\d+[\s\S]*?)?\b' + re.escape(citation),
            r'Ex\s+parte\s+([A-Z][a-zA-Z0-9\s\-\'\"\.&,]+?)(?:\s*\d+[\s\S]*?)?\b' + re.escape(citation),
            # More general pattern for any text before citation that looks like a case name
            r'([A-Z][a-zA-Z0-9\s\-\'\"\.&,]+?)(?:\s*\d+[\s\S]*?)?\b' + re.escape(citation)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the extracted name
                name = re.sub(r'[\s\.,;:]+$', '', name)
                if len(name.split()) >= 2:  # Require at least two words
                    # Try to extract year from context if available
                    year_match = re.search(r'(?:19|20)\d{2}', context[match.end():match.end()+20])
                    year = year_match.group(0) if year_match else None
                    return {'name': name, 'year': year}
        
        return {}
    
    def _extract_basic_metadata(self, citation: str) -> Dict[str, Any]:
        """Extract basic metadata (name and year) from citation text
        
        Args:
            citation: The citation text to extract from
            
        Returns:
            Dictionary with extracted name and year if found
        """
        import re
        
        # Try to extract year (4-digit number, typically at the end of citation)
        year_match = re.search(r'(\d{4})', citation)
        year = year_match.group(1) if year_match else None
        
        # Try to extract a basic case name (text before the year, or before the last set of numbers)
        name = None
        if year:
            # If we found a year, take text before it as the name
            name = citation.split(year)[0].strip()
        else:
            # Otherwise, try to find the last number sequence and take text before it
            parts = re.split(r'(\d+\s*\w*\d*)', citation)
            if len(parts) > 1:
                name = parts[0].strip()
        
        # Clean up the name
        if name:
            # Remove any trailing punctuation
            name = re.sub(r'[\s\.,;:]+$', '', name)
            # Remove any v. or vs. at the end
            name = re.sub(r'\s+v(?:s?\.?|ersus)$', '', name, flags=re.IGNORECASE)
        
        return {
            'name': name or 'Unknown',
            'year': year or 'Unknown',
            'confidence': 0.3 if name or year else 0.0
        }
    
    def _create_fallback_results(self, citations: List[str], method: str) -> Dict[str, Any]:
        """Create fallback results when verification fails"""
        results = {}
        for citation in citations:
            # Try to extract basic metadata from the citation text
            metadata = self._extract_basic_metadata(citation)
            
            results[citation] = {
                'verified': False,
                'source': f'{method}_fallback',
                'canonical_name': metadata['name'],
                'canonical_date': metadata['year'],
                'canonical_url': None,
                'confidence': metadata['confidence'],
                'validation_method': 'basic_extraction',
                'metadata': {
                    'extraction_method': 'basic_regex',
                    'extraction_confidence': metadata['confidence']
                }
            }
        return results
    
    def _select_best_metadata(self, citations: List[str], verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Select the best available metadata from a list of citations
        
        Args:
            citations: List of citation texts to consider
            verification_results: Verification results for all citations
            
        Returns:
            Dictionary with the best available metadata
        """
        best_metadata = {
            'canonical_name': None,
            'canonical_date': None,
            'canonical_url': None,
            'source': 'unknown',
            'validation_method': 'none',
            'confidence': 0.0,
            'verified': False
        }
        
        # First pass: look for verified citations
        for citation in citations:
            if citation in verification_results:
                result = verification_results[citation]
                if result.get('verified', False) and result.get('confidence', 0) > best_metadata['confidence']:
                    best_metadata.update({
                        'canonical_name': result.get('canonical_name'),
                        'canonical_date': result.get('canonical_date'),
                        'canonical_url': result.get('canonical_url'),
                        'source': result.get('source', 'unknown'),
                        'validation_method': result.get('validation_method', 'verified'),
                        'confidence': result.get('confidence', 1.0),
                        'verified': True
                    })
        
        # If no verified citations, use the best available unverified one
        if not best_metadata['verified']:
            for citation in citations:
                if citation in verification_results:
                    result = verification_results[citation]
                    confidence = result.get('confidence', 0)
                    if confidence > best_metadata['confidence']:
                        best_metadata.update({
                            'canonical_name': result.get('canonical_name', best_metadata['canonical_name']),
                            'canonical_date': result.get('canonical_date', best_metadata['canonical_date']),
                            'canonical_url': result.get('canonical_url'),
                            'source': result.get('source', 'fallback'),
                            'validation_method': result.get('validation_method', 'fallback_extraction'),
                            'confidence': confidence,
                            'verified': False
                        })
        
        return best_metadata
    
    def _update_clusters_with_verification(self, clusters: List[Dict[str, Any]], 
                                         verification_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Update clusters with verification results, ensuring all have valid names and years
        
        Args:
            clusters: Original clusters
            verification_results: Verification results by citation
            
        Returns:
            Updated clusters with verification data and ensured names/years
        """
        updated_clusters = []
        
        for cluster in clusters:
            updated_cluster = cluster.copy()
            cluster_citations = cluster.get('citations', [])
            
            # Get the best available metadata from all citations in this cluster
            best_metadata = self._select_best_metadata(cluster_citations, verification_results)
            
            # Try to get extracted names from detailed citations if available
            extracted_names = []
            if 'detailed_citations' in cluster:
                for detail in cluster['detailed_citations']:
                    if detail.get('extracted_case_name'):
                        extracted_names.append(detail['extracted_case_name'])
            
            # If we have extracted names but no verified name, use the most common extracted name
            if extracted_names and not best_metadata.get('canonical_name'):
                from collections import Counter
                most_common_name = Counter(extracted_names).most_common(1)
                if most_common_name:
                    best_metadata['canonical_name'] = most_common_name[0][0]
                    best_metadata['source'] = 'extracted_consensus'
                    best_metadata['validation_method'] = 'extraction_consensus'
                    best_metadata['confidence'] = 0.7  # High confidence in consensus
            
            # Update cluster-level metadata
            updated_cluster.update({
                'verified': best_metadata.get('verified', False),
                'canonical_name': best_metadata.get('canonical_name') or f"Unnamed Case ({cluster.get('id', 'unknown')})",
                'cluster_case_name': best_metadata.get('canonical_name') or f"Unnamed Case ({cluster.get('id', 'unknown')})",
                'extracted_case_name': best_metadata.get('extracted_case_name'),
                'canonical_date': best_metadata.get('canonical_date') or 'Unknown',
                'canonical_url': best_metadata.get('canonical_url'),
                'source': best_metadata.get('source', 'unknown'),
                'validation_method': best_metadata.get('validation_method', 'unknown'),
                'confidence': best_metadata.get('confidence', 0.0)
            })
            
            # Update individual citation details
            if 'detailed_citations' in updated_cluster:
                for citation_detail in updated_cluster['detailed_citations']:
                    citation_text = citation_detail.get('citation')
                    if not citation_text:
                        continue
                        
                    # Get the verification result if it exists
                    result = verification_results.get(citation_text, {})
                    
                    # Preserve extracted name if available
                    extracted_name = citation_detail.get('extracted_case_name')
                    if extracted_name and not result.get('canonical_name'):
                        result['canonical_name'] = extracted_name
                        result['source'] = 'extracted'
                        result['validation_method'] = 'extraction'
                        result['confidence'] = max(0.6, result.get('confidence', 0.0))  # Boost confidence for extracted names
                    
                    citation_detail.update({
                        'verified': result.get('verified', False),
                        'canonical_name': result.get('canonical_name') or updated_cluster['canonical_name'],
                        'extracted_case_name': extracted_name or result.get('extracted_case_name'),
                        'canonical_date': result.get('canonical_date') or updated_cluster['canonical_date'],
                        'canonical_url': result.get('canonical_url'),
                        'source': result.get('source', 'cluster_inherited'),
                        'validation_method': result.get('validation_method', 'inherited_from_cluster'),
                        'confidence': result.get('confidence', best_metadata.get('confidence', 0.0))
                    })
            
            # Add validation warnings if needed
            if not updated_cluster.get('canonical_name') or updated_cluster['canonical_name'].startswith('Unnamed Case'):
                logger.warning(f"Cluster {cluster.get('id', 'unknown')} has no valid case name")
            if not updated_cluster.get('canonical_date') or updated_cluster['canonical_date'] == 'Unknown':
                logger.warning(f"Cluster {cluster.get('id', 'unknown')} has no valid date")
            
            updated_clusters.append(updated_cluster)
        
        return updated_clusters
    
    def cleanup_old_verifications(self):
        """Clean up old verification data to prevent memory bloat"""
        current_time = time.time()
        
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        old_request_ids = []
        for request_id, metadata in self.active_verifications.items():
            if (metadata.status in [VerificationStatus.COMPLETED, VerificationStatus.FAILED] and
                current_time - metadata.started_at > self.cache_ttl):
                old_request_ids.append(request_id)
        
        for request_id in old_request_ids:
            del self.active_verifications[request_id]
            if request_id in self.result_cache:
                del self.result_cache[request_id]
        
        if old_request_ids:
            logger.info(f"Cleaned up {len(old_request_ids)} old verifications")
        
        self.last_cleanup = current_time
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring"""
        self.cleanup_old_verifications()
        
        return {
            'active_verifications': len(self.active_verifications),
            'cached_results': len(self.result_cache),
            'verification_status_counts': {
                status.value: sum(1 for v in self.active_verifications.values() 
                                if v.status == status)
                for status in VerificationStatus
            },
            'queue_size': len(self.verification_queue),
            'cache_ttl': self.cache_ttl
        }
