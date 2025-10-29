"""
Enhanced API Endpoints for CaseStrainer

This module provides improved API endpoints with better input processing
and enhanced async job management for concurrent processing.
"""

import os
import sys
import asyncio
import logging
from flask import Flask, request, jsonify, send_file
from typing import Dict, Any, List, Optional
import tempfile
import uuid
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from enhanced_input_processor import EnhancedInputProcessor, process_input, process_batch
from enhanced_async_manager import EnhancedAsyncManager, get_async_manager, JobStatus
from simplified_citation_processor import create_processor, ProcessingConfig


logger = logging.getLogger(__name__)

# Global instances
app = Flask(__name__)
input_processor = None
async_manager = None
citation_processor = None


async def initialize_services():
    """Initialize all services."""
    global input_processor, async_manager, citation_processor
    
    # Initialize input processor
    input_processor = EnhancedInputProcessor(
        max_concurrent_jobs=10,
        timeout_seconds=300
    )
    
    # Initialize async manager
    async_manager = EnhancedAsyncManager(
        redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        max_concurrent_jobs=int(os.getenv('MAX_CONCURRENT_JOBS', '10')),
        job_timeout=int(os.getenv('JOB_TIMEOUT', '300'))
    )
    await async_manager.start()
    
    # Initialize citation processor
    citation_processor = create_processor(
        enable_verification=os.getenv('ENABLE_VERIFICATION', 'true').lower() == 'true',
        enable_clustering=os.getenv('ENABLE_CLUSTERING', 'true').lower() == 'true',
        timeout_seconds=int(os.getenv('PROCESSOR_TIMEOUT', '120'))
    )
    
    logger.info("All services initialized successfully")


def create_error_response(message: str, status_code: int = 400, error_type: str = "Error") -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "success": False,
        "error": message,
        "error_type": error_type,
        "timestamp": datetime.now().isoformat()
    }, status_code


def create_success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create standardized success response."""
    response = {
        "success": True,
        "timestamp": datetime.now().isoformat()
    }
    response.update(data)
    return response, status_code


@app.route('/api/v2/process', methods=['POST'])
async def process_citations():
    """
    Enhanced endpoint for processing citations with improved input handling.
    
    Supports multiple input types:
    - Direct text
    - File upload
    - URL
    - Batch processing of multiple inputs
    """
    try:
        if not request.is_json:
            return create_error_response("Request must be JSON", 415, "InvalidContent")
        
        data = request.get_json()
        
        # Validate request
        if 'inputs' not in data and 'input' not in data:
            return create_error_response("Missing required field: 'input' or 'inputs'", 400, "MissingField")
        
        # Check if batch processing
        if 'inputs' in data:
            return await handle_batch_processing(data)
        else:
            return await handle_single_processing(data)
    
    except Exception as e:
        logger.error(f"Error in process_citations: {str(e)}")
        return create_error_response(str(e), 500, "ProcessingError")


async def handle_single_processing(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle single input processing."""
    
    input_data = data['input']
    options = data.get('options', {})
    
    # Validate input data
    if not isinstance(input_data, dict):
        return create_error_response("Input must be an object", 400, "InvalidInput")
    
    input_type = input_data.get('type', 'text')
    request_id = input_data.get('request_id', str(uuid.uuid4()))
    
    # Process input to text
    try:
        if input_type == 'text':
            text_result = await input_processor.process_text_input(
                input_data.get('text', ''),
                request_id
            )
        elif input_type == 'file':
            text_result = await input_processor.process_file_input(
                input_data.get('file_path', ''),
                request_id
            )
        elif input_type == 'url':
            text_result = await input_processor.process_url_input(
                input_data.get('url', ''),
                request_id
            )
        else:
            return create_error_response(f"Unsupported input type: {input_type}", 400, "UnsupportedInput")
        
        if not text_result['success']:
            return create_error_response(text_result['error'], 400, "InputProcessingError")
        
        # Process citations
        citation_result = await process_citations_from_text(
            text_result['text'],
            options,
            request_id
        )
        
        return create_success_response({
            "request_id": request_id,
            "input_processing": text_result,
            "citation_processing": citation_result
        })
        
    except Exception as e:
        logger.error(f"Error in single processing: {str(e)}")
        return create_error_response(str(e), 500, "ProcessingError")


async def handle_batch_processing(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle batch processing of multiple inputs."""
    
    inputs = data['inputs']
    options = data.get('options', {})
    batch_id = data.get('batch_id', str(uuid.uuid4()))
    
    if not isinstance(inputs, list):
        return create_error_response("Inputs must be an array", 400, "InvalidInput")
    
    if len(inputs) > 50:  # Limit batch size
        return create_error_response("Batch size limited to 50 inputs", 400, "BatchTooLarge")
    
    try:
        # Process all inputs concurrently
        input_results = await input_processor.process_multiple_inputs(inputs)
        
        # Process citations for each successful input
        citation_results = []
        successful_inputs = 0
        
        for i, input_result in enumerate(input_results):
            if input_result['success']:
                try:
                    citation_result = await process_citations_from_text(
                        input_result['text'],
                        options,
                        input_result['request_id']
                    )
                    citation_results.append({
                        "input_index": i,
                        "request_id": input_result['request_id'],
                        "input_processing": input_result,
                        "citation_processing": citation_result
                    })
                    successful_inputs += 1
                except Exception as e:
                    citation_results.append({
                        "input_index": i,
                        "request_id": input_result.get('request_id', f"input_{i}"),
                        "input_processing": input_result,
                        "citation_processing": {
                            "success": False,
                            "error": str(e)
                        }
                    })
            else:
                citation_results.append({
                    "input_index": i,
                    "request_id": input_result.get('request_id', f"input_{i}"),
                    "input_processing": input_result,
                    "citation_processing": {
                        "success": False,
                        "error": "Input processing failed"
                    }
                })
        
        return create_success_response({
            "batch_id": batch_id,
            "total_inputs": len(inputs),
            "successful_inputs": successful_inputs,
            "failed_inputs": len(inputs) - successful_inputs,
            "results": citation_results
        })
        
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        return create_error_response(str(e), 500, "BatchProcessingError")


async def process_citations_from_text(text: str, options: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """Process citations from extracted text."""
    
    try:
        # Configure processor based on options
        enable_verification = options.get('enable_verification', True)
        enable_clustering = options.get('enable_clustering', True)
        timeout_seconds = options.get('timeout_seconds', 120)
        
        # Update processor config if needed
        config = ProcessingConfig(
            enable_verification=enable_verification,
            enable_clustering=enable_clustering,
            timeout_seconds=timeout_seconds
        )
        citation_processor.config = config
        
        # Process citations
        result = citation_processor.process(
            {'type': 'text', 'text': text},
            request_id
        )
        
        # Prepare response
        processing_stats = {
            "citations_found": len(result.citations),
            "clusters_created": len(result.clusters),
            "verified_count": sum(1 for c in result.citations if c.get('verified', False)),
            "possible_matches": sum(1 for c in result.citations if c.get('possible_match', False))
        }
        
        return {
            "success": True,
            "citations": result.citations,
            "clusters": result.clusters,
            "processing_stats": processing_stats
        }
        
    except Exception as e:
        logger.error(f"Error processing citations: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "citations": [],
            "clusters": [],
            "processing_stats": {}
        }


@app.route('/api/v2/process/async', methods=['POST'])
async def process_citations_async():
    """
    Async endpoint for processing citations with job management.
    
    Returns a job ID that can be used to check status and retrieve results.
    """
    try:
        if not request.is_json:
            return create_error_response("Request must be JSON", 415, "InvalidContent")
        
        data = request.get_json()
        
        # Validate request
        if 'input' not in data:
            return create_error_response("Missing required field: 'input'", 400, "MissingField")
        
        input_data = data['input']
        options = data.get('options', {})
        job_id = data.get('job_id', str(uuid.uuid4()))
        
        # Create processing function
        async def process_job_func(job_input_data, progress_callback=None):
            # Process input to text
            input_type = job_input_data.get('type', 'text')
            
            if progress_callback:
                await progress_callback(10, "Input Processing", "Starting input processing")
            
            if input_type == 'text':
                text_result = await input_processor.process_text_input(
                    job_input_data.get('text', ''),
                    job_input_data.get('request_id')
                )
            elif input_type == 'file':
                text_result = await input_processor.process_file_input(
                    job_input_data.get('file_path', ''),
                    job_input_data.get('request_id')
                )
            elif input_type == 'url':
                text_result = await input_processor.process_url_input(
                    job_input_data.get('url', ''),
                    job_input_data.get('request_id')
                )
            else:
                raise Exception(f"Unsupported input type: {input_type}")
            
            if not text_result['success']:
                raise Exception(text_result['error'])
            
            if progress_callback:
                await progress_callback(30, "Citation Processing", "Extracting citations")
            
            # Process citations
            citation_result = await process_citations_from_text(
                text_result['text'],
                options,
                job_input_data.get('request_id')
            )
            
            if progress_callback:
                await progress_callback(100, "Completed", "Processing completed")
            
            return {
                "input_processing": text_result,
                "citation_processing": citation_result
            }
        
        # Submit job
        submitted_job_id = await async_manager.submit_job(
            input_data=input_data,
            processor_func=process_job_func,
            job_id=job_id
        )
        
        return create_success_response({
            "job_id": submitted_job_id,
            "status": "submitted",
            "message": "Job submitted for processing"
        })
        
    except Exception as e:
        logger.error(f"Error in process_citations_async: {str(e)}")
        return create_error_response(str(e), 500, "AsyncProcessingError")


@app.route('/api/v2/jobs/<job_id>', methods=['GET'])
async def get_job_status(job_id: str):
    """Get job status and progress."""
    try:
        job_status = await async_manager.get_job_status(job_id)
        
        if not job_status:
            return create_error_response(f"Job {job_id} not found", 404, "JobNotFound")
        
        return create_success_response({
            "job": job_status
        })
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return create_error_response(str(e), 500, "JobStatusError")


@app.route('/api/v2/jobs/<job_id>/result', methods=['GET'])
async def get_job_result(job_id: str):
    """Get job result if completed."""
    try:
        job_result = await async_manager.get_job_result(job_id)
        
        if job_result is None:
            # Check if job exists
            job_status = await async_manager.get_job_status(job_id)
            if not job_status:
                return create_error_response(f"Job {job_id} not found", 404, "JobNotFound")
            else:
                return create_error_response(f"Job {job_id} not completed", 400, "JobNotCompleted")
        
        return create_success_response({
            "job_id": job_id,
            "result": job_result
        })
        
    except Exception as e:
        logger.error(f"Error getting job result: {str(e)}")
        return create_error_response(str(e), 500, "JobResultError")


@app.route('/api/v2/jobs/<job_id>/cancel', methods=['POST'])
async def cancel_job(job_id: str):
    """Cancel a running job."""
    try:
        success = await async_manager.cancel_job(job_id)
        
        if not success:
            return create_error_response(f"Job {job_id} cannot be cancelled", 400, "JobNotCancellable")
        
        return create_success_response({
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        })
        
    except Exception as e:
        logger.error(f"Error cancelling job: {str(e)}")
        return create_error_response(str(e), 500, "JobCancelError")


@app.route('/api/v2/jobs', methods=['GET'])
async def list_jobs():
    """List jobs with optional filtering."""
    try:
        status_filter = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        # Convert status string to enum if provided
        status_enum = None
        if status_filter:
            try:
                status_enum = JobStatus(status_filter.lower())
            except ValueError:
                return create_error_response(f"Invalid status: {status_filter}", 400, "InvalidStatus")
        
        jobs = await async_manager.list_jobs(status=status_enum, limit=limit)
        
        return create_success_response({
            "jobs": jobs,
            "total_count": len(jobs)
        })
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return create_error_response(str(e), 500, "JobListError")


@app.route('/api/v2/stats', methods=['GET'])
async def get_stats():
    """Get system statistics."""
    try:
        # Get async manager stats
        manager_stats = await async_manager.get_stats()
        
        # Get input processor stats
        input_stats = input_processor.get_cache_stats()
        
        # Get system info
        system_stats = {
            "processor_type": "enhanced",
            "max_concurrent_jobs": async_manager.max_concurrent_jobs,
            "job_timeout": async_manager.job_timeout,
            "result_ttl": async_manager.result_ttl,
            "redis_connected": manager_stats['redis_connected']
        }
        
        return create_success_response({
            "async_manager": manager_stats,
            "input_processor": input_stats,
            "system": system_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return create_error_response(str(e), 500, "StatsError")


@app.route('/api/v2/health', methods=['GET'])
async def health_check():
    """Enhanced health check endpoint."""
    try:
        health_status = {
            "status": "healthy",
            "services": {
                "input_processor": input_processor is not None,
                "async_manager": async_manager is not None,
                "citation_processor": citation_processor is not None
            },
            "features": {
                "enhanced_input_processing": True,
                "async_job_management": True,
                "concurrent_processing": True,
                "batch_processing": True,
                "progress_tracking": True,
                "result_caching": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if all services are healthy
        all_healthy = all(health_status["services"].values())
        if not all_healthy:
            health_status["status"] = "unhealthy"
            return create_error_response("Some services are unhealthy", 503, "ServiceUnavailable")
        
        return create_success_response(health_status)
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return create_error_response(str(e), 503, "HealthCheckError")


@app.route('/api/v2/documentation', methods=['GET'])
def get_documentation():
    """Get enhanced API documentation."""
    docs = {
        "title": "Enhanced CaseStrainer API",
        "version": "2.0.0",
        "description": "Enhanced API for legal citation processing with improved input handling and async job management",
        "base_url": "/api/v2",
        "endpoints": {
            "/process": {
                "method": "POST",
                "description": "Process citations synchronously with enhanced input handling",
                "supports": ["text", "file", "url", "batch"],
                "features": ["enhanced_text_extraction", "unicode_normalization", "content_caching"]
            },
            "/process/async": {
                "method": "POST",
                "description": "Process citations asynchronously with job management",
                "features": ["job_tracking", "progress_callbacks", "concurrent_processing", "timeout_handling"]
            },
            "/jobs": {
                "method": "GET",
                "description": "List all jobs with optional filtering",
                "parameters": {
                    "status": "Filter by job status (pending, running, completed, failed, cancelled)",
                    "limit": "Maximum number of jobs to return (default: 100)"
                }
            },
            "/jobs/<job_id>": {
                "method": "GET",
                "description": "Get job status and progress information"
            },
            "/jobs/<job_id>/result": {
                "method": "GET",
                "description": "Get job result if completed"
            },
            "/jobs/<job_id>/cancel": {
                "method": "POST",
                "description": "Cancel a running job"
            },
            "/stats": {
                "method": "GET",
                "description": "Get system statistics and performance metrics"
            },
            "/health": {
                "method": "GET",
                "description": "Enhanced health check with service status"
            },
            "/documentation": {
                "method": "GET",
                "description": "Get this API documentation"
            }
        },
        "input_types": {
            "text": {
                "description": "Direct text input",
                "fields": {
                    "type": "text",
                    "text": "string (required) - Text containing citations"
                }
            },
            "file": {
                "description": "File input with enhanced extraction",
                "fields": {
                    "type": "file",
                    "file_path": "string (required) - Path to file",
                    "supported_formats": ["PDF", "TXT", "HTML", "DOCX"]
                }
            },
            "url": {
                "description": "URL input with download and extraction",
                "fields": {
                    "type": "url",
                    "url": "string (required) - URL to process"
                }
            },
            "batch": {
                "description": "Multiple inputs processed concurrently",
                "fields": {
                    "inputs": "array (required) - Array of input objects",
                    "batch_id": "string (optional) - Batch identifier"
                }
            }
        },
        "features": [
            "Enhanced PDF text extraction with multiple methods",
            "Unicode normalization and text cleaning",
            "Concurrent processing with configurable limits",
            "Async job management with progress tracking",
            "Result caching for improved performance",
            "Batch processing for multiple inputs",
            "Comprehensive error handling and logging",
            "Health monitoring and statistics"
        ],
        "limits": {
            "max_text_length": 1000000,
            "max_file_size": "50MB",
            "max_batch_size": 50,
            "max_concurrent_jobs": 10,
            "job_timeout": 300,
            "rate_limiting": "1000 requests per hour"
        },
        "improvements_v2": [
            "Enhanced input processing with multiple extraction methods",
            "Async job management for better scalability",
            "Concurrent processing with configurable limits",
            "Progress tracking and callbacks",
            "Result caching and performance optimization",
            "Batch processing capabilities",
            "Better error handling and logging"
        ]
    }
    
    return create_success_response(docs)


# Initialize services on startup
@app.before_first_request
async def startup():
    """Initialize services on first request."""
    await initialize_services()


# Cleanup on shutdown
@app.teardown_appcontext
async def shutdown(exception=None):
    """Cleanup resources on shutdown."""
    if async_manager:
        await async_manager.stop()


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the API server
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('API_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Enhanced CaseStrainer API v2 on port {port}")
    
    # Initialize services before starting server
    asyncio.run(initialize_services())
    
    app.run(host='0.0.0.0', port=port, debug=debug)
