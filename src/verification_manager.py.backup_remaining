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
    """Smart verification strategy with progressive fallbacks"""
    
    def __init__(self):
        self.verification_priority = [
            'citation_lookup_v4',      # CourtListener batch lookup (fastest)
            'courtlistener_search',     # CourtListener search API (fallback)
            'web_search',              # Web search (slowest)
        ]
        
        self.method_configs = {
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
    
    def _has_sufficient_coverage(self, results: Dict[str, Any], citations: List[str]) -> bool:
        """Check if we have sufficient verification coverage"""
        verified_count = sum(1 for r in results.values() if r.get('verified', False))
        coverage_threshold = 0.7  # 70% coverage is sufficient
        
        return (verified_count / len(citations)) >= coverage_threshold

class VerificationManager:
    """Manages the complete verification flow with real-time updates"""
    
    def __init__(self, redis_conn: Optional[redis.Redis] = None):
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
    
    def _progressive_verification(self, request_id: str, citations: List[str], 
                                 clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Progressive verification with smart fallbacks
        
        Args:
            request_id: Request identifier
            citations: Citations to verify
            clusters: Clustered citations
            
        Returns:
            Verification results
        """
        all_results = {}
        total_citations = len(citations)
        
        for method in self.verification_strategy.verification_priority:
            try:
                if request_id in self.active_verifications:
                    self.active_verifications[request_id].current_method = f"Using {method}"
                
                config = self.verification_strategy.get_method_config(method)
                
                method_results = self._try_verification_method(
                    method, citations, clusters, config, request_id
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
        
        verified_count = sum(1 for r in all_results.values() if r.get('verified', False))
        
        return {
            'status': 'completed',
            'citations': all_results,
            'clusters': self._update_clusters_with_verification(clusters, all_results),
            'verification_summary': {
                'total_citations': total_citations,
                'verified_citations': verified_count,
                'verification_coverage': (verified_count / total_citations) if total_citations > 0 else 0.0,
                'methods_used': [m for m in self.verification_strategy.verification_priority 
                                if any(r.get('source') == m for r in all_results.values())]
            }
        }
    
    def _try_verification_method(self, method: str, citations: List[str], 
                                clusters: List[Dict[str, Any]], config: Dict[str, Any],
                                request_id: str) -> Dict[str, Any]:
        """
        Try a specific verification method
        
        Args:
            method: Verification method name
            citations: Citations to verify
            clusters: Clustered citations
            config: Method configuration
            request_id: Request identifier
            
        Returns:
            Method-specific results
        """
        try:
            from verification_services import VerificationServiceFactory
            
            if method == 'citation_lookup_v4':
                from verification_services import CourtListenerService
                service = CourtListenerService()
                return service.verify_citations_batch(citations)
            elif method == 'courtlistener_search':
                from verification_services import CourtListenerService
                service = CourtListenerService()
                return service.verify_citations_search(citations)
            elif method == 'web_search':
                from verification_services import WebSearchService
                service = WebSearchService()
                return service.verify_citations(citations)
            else:
                raise ValueError(f"Unknown verification method: {method}")
                
        except Exception as e:
            logger.error(f"Failed to create verification service for {method}: {e}")
            return self._create_fallback_results(citations, method)
    
    def _create_fallback_results(self, citations: List[str], method: str) -> Dict[str, Any]:
        """Create fallback results when verification fails"""
        results = {}
        for citation in citations:
            results[citation] = {
                'verified': False,
                'source': method,
                'canonical_name': None,
                'canonical_date': None,
                'canonical_url': None,
                'confidence': 0.0,
                'validation_method': f'{method}_failed'
            }
        return results
    
    def _update_clusters_with_verification(self, clusters: List[Dict[str, Any]], 
                                          verification_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Update clusters with verification results
        
        Args:
            clusters: Original clusters
            verification_results: Verification results by citation
            
        Returns:
            Updated clusters with verification data
        """
        updated_clusters = []
        
        for cluster in clusters:
            updated_cluster = cluster.copy()
            
            cluster_citations = cluster.get('citations', [])
            verified_citations = [
                citation for citation in cluster_citations
                if verification_results.get(citation, {}).get('verified', False)
            ]
            
            if verified_citations:
                first_verified = verification_results[verified_citations[0]]
                updated_cluster.update({
                    'verified': True,
                    'canonical_name': first_verified.get('canonical_name'),
                    'canonical_date': first_verified.get('canonical_date'),
                    'canonical_url': first_verified.get('canonical_url'),
                    'source': first_verified.get('source'),
                    'validation_method': first_verified.get('validation_method')
                })
            else:
                updated_cluster.update({
                    'verified': False,
                    'canonical_name': None,
                    'canonical_date': None,
                    'canonical_url': None,
                    'source': 'local_extraction',
                    'validation_method': 'local_clustering'
                })
            
            if 'detailed_citations' in updated_cluster:
                for citation_detail in updated_cluster['detailed_citations']:
                    citation_text = citation_detail.get('citation')
                    if citation_text in verification_results:
                        verification_data = verification_results[citation_text]
                        citation_detail.update({
                            'verified': verification_data.get('verified', False),
                            'canonical_name': verification_data.get('canonical_name'),
                            'canonical_date': verification_data.get('canonical_date'),
                            'canonical_url': verification_data.get('canonical_url'),
                            'source': verification_data.get('source'),
                            'validation_method': verification_data.get('validation_method')
                        })
            
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
