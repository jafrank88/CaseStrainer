"""
Extracted citation processing business logic from the main API file.
This separates concerns and makes the code more testable and maintainable.
"""

import os
import logging
import time
from typing import Dict, List, Any, Optional
from src.redis_distributed_processor import DockerOptimizedProcessor

logger = logging.getLogger(__name__)

class CitationService:
    """Service for processing citations with Redis-distributed processing."""
    
    def __init__(self):
        self.processor = DockerOptimizedProcessor()
        self.cache_ttl = 3600  # 1 hour cache
    
    def should_process_immediately(self, input_data: Dict) -> bool:
        """Determine if input should be processed immediately vs queued."""
        if input_data.get('type') == 'text':
            text = input_data.get('text', '')
            # Process short texts immediately (< 10KB)
            return len(text) < 10 * 1024
        
        return False
    
    def process_immediately(self, input_data: Dict) -> Dict[str, Any]:
        """Process input immediately (for short texts)."""
        try:
            if input_data.get('type') == 'text':
                text = input_data.get('text', '')
                return self.process_citations_from_text(text)
            
            return {'status': 'error', 'message': 'Invalid input type for immediate processing'}
            
        except Exception as e:
            logger.error(f"Immediate processing failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def process_citation_task(self, task_id: str, input_type: str, input_data: Dict) -> Dict[str, Any]:
        print(f"[DEBUG PRINT] ENTERED process_citation_task for task_id={task_id}, input_type={input_type}, input_data_keys={list(input_data.keys())}")
        logger.info(f"[DEBUG] ENTERED process_citation_task for task_id={task_id}, input_type={input_type}, input_data_keys={list(input_data.keys())}")
        start_time = time.time()
        logger.info(f"Processing citation task {task_id} of type {input_type}")
        print(f"[DEBUG PRINT] About to dispatch to specific task type: {input_type}")
        try:
            if input_type == 'file':
                print(f"[DEBUG PRINT] Calling _process_file_task for task_id={task_id}")
                logger.info(f"[DEBUG] Calling _process_file_task for task_id={task_id}")
                result = await self._process_file_task(task_id, input_data)
                print(f"[DEBUG PRINT] Returned from _process_file_task for task_id={task_id}, result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                logger.info(f"[DEBUG] Returned from _process_file_task for task_id={task_id}, result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                return result
            elif input_type == 'url':
                print(f"[DEBUG PRINT] Calling _process_url_task for task_id={task_id}")
                return await self._process_url_task(task_id, input_data)
            elif input_type == 'text':
                print(f"[DEBUG PRINT] Calling _process_text_task for task_id={task_id}")
                return await self._process_text_task(task_id, input_data)
            else:
                print(f"[DEBUG PRINT] Unknown input type: {input_type} for task_id={task_id}")
                return {
                    'status': 'failed',
                    'error': f'Unknown input type: {input_type}',
                    'task_id': task_id
                }
        except Exception as e:
            print(f"[DEBUG PRINT] Exception in process_citation_task for task_id={task_id}: {e}")
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            return {
                'status': 'failed',
                'error': str(e),
                'task_id': task_id,
                'processing_time': time.time() - start_time
            }
    
    async def _process_file_task(self, task_id: str, input_data: Dict) -> Dict[str, Any]:
        print(f"[DEBUG PRINT] ENTERED _process_file_task for task_id={task_id}, input_data_keys={list(input_data.keys())}")
        logger.info(f"[DEBUG] ENTERED _process_file_task for task_id={task_id}, input_data_keys={list(input_data.keys())}")
        file_path = input_data.get('file_path')
        filename = input_data.get('filename', 'unknown')
        print(f"[DEBUG PRINT] file_path={file_path}, filename={filename}")
        logger.info(f"[DEBUG] file_path={file_path}, filename={filename}")
        if not file_path or not os.path.exists(file_path):
            print(f"[DEBUG PRINT] File not found: {file_path} for task_id={task_id}")
            logger.error(f"[DEBUG] File not found: {file_path} for task_id={task_id}")
            return {
                'status': 'failed',
                'error': f'File not found: {file_path}',
                'task_id': task_id
            }
        try:
            print(f"[DEBUG PRINT] Before calling process_document for file_path={file_path}")
            logger.info(f"[DEBUG] Before calling process_document for file_path={file_path}")
            result = await self.processor.process_document(file_path)
            print(f"[DEBUG PRINT] After process_document for file_path={file_path}, result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            logger.info(f"[DEBUG] After process_document for file_path={file_path}, result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            # Clean up temporary file
            try:
                os.remove(file_path)
                print(f"[DEBUG PRINT] Successfully removed file: {file_path}")
                logger.info(f"[DEBUG] Successfully removed file: {file_path}")
            except Exception as cleanup_exc:
                print(f"[DEBUG PRINT] Failed to remove file: {file_path} - {cleanup_exc}")
                logger.warning(f"[DEBUG] Failed to remove file: {file_path} - {cleanup_exc}")
            return {
                'status': 'completed',
                'task_id': task_id,
                'citations': result.get('citations', []),
                'statistics': result.get('statistics', {}),
                'metadata': {
                    'filename': filename,
                    'text_length': result.get('text_length', 0)
                },
                'processing_time': result.get('processing_time', 0)
            }
        except Exception as e:
            print(f"[DEBUG PRINT] Exception in _process_file_task for task_id={task_id}: {e}")
            logger.error(f"[DEBUG] Exception in _process_file_task for task_id={task_id}: {e}", exc_info=True)
            # Clean up on error
            try:
                os.remove(file_path)
                print(f"[DEBUG PRINT] Successfully removed file after exception: {file_path}")
                logger.info(f"[DEBUG] Successfully removed file after exception: {file_path}")
            except Exception as cleanup_exc:
                print(f"[DEBUG PRINT] Failed to remove file after exception: {file_path} - {cleanup_exc}")
                logger.warning(f"[DEBUG] Failed to remove file after exception: {file_path} - {cleanup_exc}")
            raise
    
    async def _process_url_task(self, task_id: str, input_data: Dict) -> Dict[str, Any]:
        """Process URL input task."""
        url = input_data.get('url')
        
        if not url:
            return {
                'status': 'failed',
                'error': 'No URL provided',
                'task_id': task_id
            }
        
        try:
            # Download and process URL
            import tempfile
            import requests
            
            # Download file
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            # Process using distributed processor
            result = await self.processor.process_document(temp_file_path)
            
            # Clean up
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            return {
                'status': 'completed',
                'task_id': task_id,
                'citations': result.get('citations', []),
                'statistics': result.get('statistics', {}),
                'metadata': {
                    'url': url,
                    'text_length': result.get('text_length', 0)
                },
                'processing_time': result.get('processing_time', 0)
            }
            
        except Exception as e:
            # Clean up on error
            try:
                os.remove(temp_file_path)
            except:
                pass
            raise
    
    async def _process_text_task(self, task_id: str, input_data: Dict) -> Dict[str, Any]:
        """Process text input task."""
        text = input_data.get('text', '')
        source_name = input_data.get('source_name', 'pasted_text')
        
        if not text:
            return {
                'status': 'failed',
                'error': 'No text provided',
                'task_id': task_id
            }

        try:
            # Process citations from text
            result = self.process_citations_from_text(text)

            return {
                'status': 'completed',
                'task_id': task_id,
                'citations': result.get('citations', []),
                'clusters': result.get('clusters', []),  # ✅ FIX: Include clusters in async response
                'statistics': result.get('statistics', {}),
                'metadata': {
                    'source_name': source_name,
                    'text_length': len(text)
                },
                'processing_time': time.time() - time.time()  # Will be set by caller
            }

        except Exception as e:
            raise
    
    def process_citations_from_text(self, text: str) -> Dict[str, Any]:
        print(f"[DEBUG PRINT] ENTERED process_citations_from_text, text_length={len(text)}")
        logger.info(f"[DEBUG] ENTERED process_citations_from_text, text_length={len(text)}")
        try:
            print(f"[DEBUG PRINT] About to import UnifiedCitationProcessorV2")
            logger.info(f"[DEBUG] About to import UnifiedCitationProcessorV2")
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            from src.citation_clustering import group_citations_into_clusters
            print(f"[DEBUG PRINT] Imported UnifiedCitationProcessorV2, about to instantiate")
            logger.info(f"[DEBUG] Imported UnifiedCitationProcessorV2, about to instantiate")
            processor = UnifiedCitationProcessorV2()
            print(f"[DEBUG PRINT] Instantiated UnifiedCitationProcessorV2, about to call process_text")
            logger.info(f"[DEBUG] Instantiated UnifiedCitationProcessorV2, about to call process_text")
            citation_results = processor.process_text(text)
            print(f"[DEBUG PRINT] Returned from process_text, results_count={len(citation_results['citations'])}")
            logger.info(f"[DEBUG] Returned from process_text, results_count={len(citation_results['citations'])}")

            # Ensure clusters are present
            if 'clusters' not in citation_results or not citation_results['clusters']:
                # Build clusters if not present
                clusters = group_citations_into_clusters(citation_results['citations'], original_text=text)
                citation_results['clusters'] = clusters
            else:
                clusters = citation_results['clusters']

            # Build a mapping from citation string to cluster members
            citation_to_members = {}
            try:
                for cluster in clusters:
                    if not isinstance(cluster, dict) or 'citations' not in cluster:
                        logger.warning(f"Invalid cluster structure: {type(cluster)}")
                        continue
                        
                    # Extract citation strings more robustly
                    member_citations = []
                    for c in cluster['citations']:
                        try:
                            if isinstance(c, dict):
                                cite_str = c.get('citation')
                            else:
                                cite_str = getattr(c, 'citation', None)
                            
                            if cite_str:
                                member_citations.append(cite_str)
                        except Exception as e:
                            logger.warning(f"Error processing citation in cluster: {e}")
                            continue
                    
                    # Map each citation to its cluster members
                    for c in cluster['citations']:
                        try:
                            if isinstance(c, dict):
                                cite_str = c.get('citation')
                            else:
                                cite_str = getattr(c, 'citation', None)
                                
                            if cite_str:
                                citation_to_members[cite_str] = member_citations
                        except Exception as e:
                            logger.warning(f"Error mapping citation to cluster members: {e}")
                            continue
                            
            except Exception as e:
                logger.error(f"Error processing clusters: {e}")
                citation_to_members = {}  # Fall back to empty mapping

            processed_citations = []
            for citation in citation_results['citations']:
                citation_dict = {
                    'citation': citation.citation,
                    'case_name': citation.canonical_name or citation.extracted_case_name or 'Unknown',
                    'extracted_case_name': citation.extracted_case_name,
                    'canonical_name': citation.canonical_name,
                    'extracted_date': citation.extracted_date,
                    'canonical_date': citation.canonical_date,
                    'verified': citation.verified,
                    'court': citation.court,
                    'confidence': citation.confidence,
                    'method': citation.method,
                    'pattern': citation.pattern,
                    'context': citation.context,
                    'start_index': citation.start_index,
                    'end_index': citation.end_index,
                    'is_parallel': citation.is_parallel,
                    'is_cluster': citation.is_cluster,
                    'parallel_citations': citation.parallel_citations,
                    'cluster_members': citation_to_members.get(citation.citation, []),
                    'pinpoint_pages': citation.pinpoint_pages,
                    'docket_numbers': citation.docket_numbers,
                    'case_history': citation.case_history,
                    'publication_status': citation.publication_status,
                    'url': citation.url,
                    'source': citation.source,
                    'error': citation.error,
                    'metadata': citation.metadata or {}
                }
                processed_citations.append(citation_dict)
            print(f"[DEBUG PRINT] Finished processing citations, processed_citations_count={len(processed_citations)}")
            logger.info(f"[DEBUG] Finished processing citations, processed_citations_count={len(processed_citations)}")
            
            # Debug cluster information
            print(f"[DEBUG PRINT] Final clusters count: {len(clusters)}")
            logger.info(f"[DEBUG] Final clusters count: {len(clusters)}")
            
            if not clusters:
                print(f"[DEBUG PRINT] No clusters found, checking if we can rebuild from citation metadata")
                logger.warning(f"No clusters found, checking if we can rebuild from citation metadata")
                
                # Try to rebuild clusters from citation metadata if clusters are empty
                cluster_map = {}
                for citation in citation_results['citations']:
                    cluster_id = getattr(citation, 'metadata', {}).get('cluster_id')
                    if cluster_id:
                        if cluster_id not in cluster_map:
                            cluster_map[cluster_id] = []
                        cluster_map[cluster_id].append(citation)
                
                if cluster_map:
                    print(f"[DEBUG PRINT] Rebuilt {len(cluster_map)} clusters from metadata")
                    logger.info(f"Rebuilt {len(cluster_map)} clusters from metadata")
                    # Convert to expected cluster format
                    rebuilt_clusters = []
                    for cluster_id, cluster_citations in cluster_map.items():
                        cluster_data = {
                            'cluster_id': cluster_id,
                            'citations': [
                                {
                                    'citation': c.citation,
                                    'extracted_case_name': c.extracted_case_name,
                                    'extracted_date': c.extracted_date,
                                    'canonical_name': c.canonical_name,
                                    'canonical_date': c.canonical_date,
                                    'confidence': c.confidence,
                                    'source': c.source,
                                    'url': c.url,
                                    'court': c.court or '',
                                    'context': c.context,
                                    'verified': c.verified,
                                    'parallel_citations': c.parallel_citations or []
                                } for c in cluster_citations
                            ],
                            'size': len(cluster_citations),
                            'has_parallel_citations': len(cluster_citations) > 1,
                            'canonical_name': cluster_citations[0].canonical_name if cluster_citations else None,
                            'canonical_date': cluster_citations[0].canonical_date if cluster_citations else None,
                            'extracted_case_name': cluster_citations[0].extracted_case_name if cluster_citations else None,
                            'extracted_date': cluster_citations[0].extracted_date if cluster_citations else None,
                            'url': cluster_citations[0].url if cluster_citations else None,
                            'source': cluster_citations[0].source if cluster_citations else 'fallback'
                        }
                        rebuilt_clusters.append(cluster_data)
                    clusters = rebuilt_clusters
                    print(f"[DEBUG PRINT] Using rebuilt clusters: {len(clusters)}")
                    logger.info(f"Using rebuilt clusters: {len(clusters)}")
            
            return {
                'status': 'completed',
                'citations': processed_citations,
                'clusters': clusters,
                'statistics': {
                    'total_citations': len(processed_citations),
                    'text_length': len(text)
                }
            }
        except Exception as e:
            print(f"[DEBUG PRINT] Exception in process_citations_from_text: {e}")
            logger.error(f"Citation processing failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'citations': [],
                'statistics': {}
            } 