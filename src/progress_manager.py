"""
Progress Bar Solutions for CaseStrainer Citation Processing
Multiple approaches to provide real-time progress feedback to users
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Generator, Callable
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, Response
try:
    from flask_socketio import SocketIO, emit
    FLASK_SOCKETIO_AVAILABLE = True
except ImportError:
    FLASK_SOCKETIO_AVAILABLE = False
    SocketIO = None
    emit = None
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# SOLUTION 1: Server-Sent Events (SSE) - Recommended for most cases
# ============================================================================

class ProgressTracker:
    """Thread-safe progress tracking for citation processing"""
    
    def __init__(self, task_id: str, total_steps: int):
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
        self.status = "starting"
        self.message = "Initializing..."
        self.results = []
        self.errors = []
        self.start_time = datetime.now()
        self.estimated_completion = None
        
    def update(self, step: int, status: str, message: str, 
               partial_results: List = None, error: str = None):
        """Update progress and optionally add partial results"""
        self.current_step = step
        self.status = status
        self.message = message
        
        if partial_results:
            self.results.extend(partial_results)
            
        if error:
            self.errors.append(error)
            
        # Calculate estimated completion
        if step > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            estimated_total = (elapsed / step) * self.total_steps
            remaining = estimated_total - elapsed
            self.estimated_completion = remaining
    
    def get_progress_data(self) -> Dict:
        """Get current progress data for client updates"""
        progress_percent = (self.current_step / self.total_steps * 100) if self.total_steps > 0 else 0
        
        return {
            'task_id': self.task_id,
            'progress': round(progress_percent, 2),
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'status': self.status,
            'message': self.message,
            'results_count': len(self.results),
            'error_count': len(self.errors),
            'estimated_completion': self.estimated_completion,
            'timestamp': datetime.now().isoformat()
        }
    
    def is_complete(self) -> bool:
        return self.status in ['completed', 'failed']


class SSEProgressManager:
    """Manages Server-Sent Events for real-time progress updates"""
    
    def __init__(self):
        self.active_tasks: Dict[str, ProgressTracker] = {}
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                # Optional Redis for multi-instance deployment
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            except:
                logger.warning("Redis not available, using in-memory progress tracking")
                self.redis_client = None
        else:
            logger.info("Redis not installed, using in-memory progress tracking")
    
    def start_task(self, total_steps: int) -> str:
        """Start a new task and return task ID"""
        task_id = str(uuid.uuid4())
        tracker = ProgressTracker(task_id, total_steps)
        self.active_tasks[task_id] = tracker
        
        if self.redis_client:
            self._store_progress_in_redis(task_id, tracker)
            
        return task_id
    
    def update_progress(self, task_id: str, step: int, status: str, 
                       message: str, partial_results: List = None, error: str = None):
        """Update task progress"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update(step, status, message, partial_results, error)
            
            if self.redis_client:
                self._store_progress_in_redis(task_id, self.active_tasks[task_id])
    
    def get_progress(self, task_id: str) -> Dict:
        """Get current progress for a task"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].get_progress_data()
        
        if self.redis_client:
            return self._get_progress_from_redis(task_id)
            
        return {'error': 'Task not found'}
    
    def get_results(self, task_id: str) -> Dict:
        """Get final results for a completed task"""
        if task_id in self.active_tasks:
            tracker = self.active_tasks[task_id]
            return {
                'task_id': task_id,
                'status': tracker.status,
                'results': tracker.results,
                'errors': tracker.errors,
                'progress_data': tracker.get_progress_data()
            }
        return {'error': 'Task not found'}
    
    def cleanup_task(self, task_id: str):
        """Clean up completed task"""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            
        if self.redis_client:
            self.redis_client.delete(f"progress:{task_id}")
    
    def _store_progress_in_redis(self, task_id: str, tracker: ProgressTracker):
        """Store progress in Redis for multi-instance support"""
        try:
            data = tracker.get_progress_data()
            data['results'] = tracker.results
            data['errors'] = tracker.errors
            self.redis_client.setex(
                f"progress:{task_id}", 
                3600,  # 1 hour expiration
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.error(f"Failed to store progress in Redis: {e}")
    
    def _get_progress_from_redis(self, task_id: str) -> Dict:
        """Get progress from Redis"""
        try:
            data = self.redis_client.get(f"progress:{task_id}")
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to get progress from Redis: {e}")
        return {'error': 'Task not found'}


# ============================================================================
# SOLUTION 2: WebSocket Implementation
# ============================================================================

class WebSocketProgressManager:
    """WebSocket-based real-time progress updates"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.active_tasks: Dict[str, ProgressTracker] = {}
    
    def start_task(self, total_steps: int, client_id: str) -> str:
        """Start task and join client to room for updates"""
        task_id = str(uuid.uuid4())
        tracker = ProgressTracker(task_id, total_steps)
        self.active_tasks[task_id] = tracker
        
        # Join client to task-specific room
        self.socketio.server.enter_room(client_id, f"task_{task_id}")
        
        # Send initial progress
        self.socketio.emit('progress_update', 
                          tracker.get_progress_data(), 
                          room=f"task_{task_id}")
        
        return task_id
    
    def update_progress(self, task_id: str, step: int, status: str, 
                       message: str, partial_results: List = None, error: str = None):
        """Update progress and emit to all clients watching this task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update(step, status, message, partial_results, error)
            
            # Emit progress update to all clients in task room
            progress_data = self.active_tasks[task_id].get_progress_data()
            
            # Include partial results if available
            if partial_results:
                progress_data['partial_results'] = partial_results
            
            self.socketio.emit('progress_update', 
                              progress_data, 
                              room=f"task_{task_id}")


# ============================================================================
# SOLUTION 3: Chunked Citation Processing
# ============================================================================

class ChunkedCitationProcessor:
    """Process citations in chunks to provide incremental progress"""
    
    def __init__(self, progress_manager: SSEProgressManager):
        self.progress_manager = progress_manager
        self.chunk_size = 1000  # Characters per chunk
    
    async def process_document_with_progress(self, 
                                           document_text: str, 
                                           document_type: str = "legal_brief") -> str:
        """Process document in chunks with progress updates"""
        
        # Calculate processing steps
        chunks = self._split_into_chunks(document_text)
        total_steps = len(chunks) + 3  # +3 for preprocessing, analysis, and final processing
        
        # Start progress tracking
        task_id = self.progress_manager.start_task(total_steps)
        
        try:
            # Step 1: Preprocessing
            self.progress_manager.update_progress(
                task_id, 1, "processing", "Preprocessing document..."
            )
            
            processed_chunks = await self._preprocess_chunks(chunks)
            await asyncio.sleep(0.1)  # Allow UI update
            
            # Step 2: Process each chunk
            all_citations = []
            for i, chunk in enumerate(processed_chunks):
                step = i + 2
                self.progress_manager.update_progress(
                    task_id, step, "processing", 
                    f"Processing chunk {i+1} of {len(chunks)}..."
                )
                
                chunk_citations = await self._process_chunk(chunk, document_type)
                all_citations.extend(chunk_citations)
                
                # Update progress with partial results
                self.progress_manager.update_progress(
                    task_id, step, "processing",
                    f"Found {len(chunk_citations)} citations in chunk {i+1}",
                    partial_results=chunk_citations
                )
                
                # Small delay to allow UI updates
                await asyncio.sleep(0.05)
            
            # Step 3: Final analysis
            final_step = len(chunks) + 2
            self.progress_manager.update_progress(
                task_id, final_step, "analyzing", 
                "Performing final analysis..."
            )
            
            analysis_results = await self._perform_final_analysis(all_citations)
            
            # Step 4: Complete
            self.progress_manager.update_progress(
                task_id, total_steps, "completed", 
                f"Processing complete! Found {len(all_citations)} citations.",
                partial_results=[]
            )
            
            return task_id
            
        except Exception as e:
            self.progress_manager.update_progress(
                task_id, 0, "failed", f"Processing failed: {str(e)}", error=str(e)
            )
            raise
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Split document into processable chunks"""
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunk = text[i:i + self.chunk_size]
            
            # Don't split in the middle of a potential citation
            if i + self.chunk_size < len(text):
                # Look for a good break point (sentence end, paragraph, etc.)
                break_points = ['. ', '\n\n', '\n', '. ']
                for bp in break_points:
                    last_bp = chunk.rfind(bp)
                    if last_bp > self.chunk_size * 0.8:  # Don't make chunks too small
                        chunk = chunk[:last_bp + len(bp)]
                        break
            
            chunks.append(chunk)
        
        return chunks
    
    async def _preprocess_chunks(self, chunks: List[str]) -> List[str]:
        """Preprocess chunks for better citation extraction"""
        # Normalize text, fix common OCR errors, etc.
        processed = []
        for chunk in chunks:
            # Simulate preprocessing work
            processed_chunk = chunk.replace('  ', ' ').strip()
            processed.append(processed_chunk)
        
        return processed
    
    async def _process_chunk(self, chunk: str, document_type: str) -> List[Dict]:
        """Process a single chunk for citations using the canonical UnifiedCitationProcessorV2."""
        try:
            # Use the canonical UnifiedCitationProcessorV2 for real citation extraction
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
            
            config = ProcessingConfig(
                use_eyecite=True,
                use_regex=True,
                extract_case_names=True,
                extract_dates=True,
                enable_clustering=False,  # Disable clustering for chunk processing
                enable_verification=False  # Disable verification for faster processing
            )
            
            processor = UnifiedCitationProcessorV2(config)
            results = processor.process_text(chunk)
            
            # Convert CitationResult objects to dictionaries
            citations = []
            for result in results:
                citations.append({
                    'id': len(citations) + 1,
                    'raw_text': result.citation,
                    'case_name': result.canonical_name or result.extracted_case_name or 'Unknown Case',
                    'year': result.canonical_date or result.extracted_date or 'No year',
                    'confidence_score': 0.85,  # Default confidence
                    'chunk_index': hash(chunk) % 1000,
                    'extracted_case_name': result.extracted_case_name,
                    'canonical_name': result.canonical_name,
                    'extracted_date': result.extracted_date,
                    'canonical_date': result.canonical_date,
                    'verified': result.verified,
                    'source': result.source,
                    'method': result.method
                })
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Error processing chunk: {e}")
            return []
    
    async def _perform_final_analysis(self, citations: List[Dict]) -> Dict:
        """Perform final analysis on all collected citations"""
        await asyncio.sleep(0.2)  # Simulate analysis time
        
        return {
            'total_citations': len(citations),
            'high_confidence': len([c for c in citations if c.get('confidence_score', 0) > 0.8]),
            'needs_review': len([c for c in citations if c.get('confidence_score', 0) < 0.6])
        }


# ============================================================================
# SOLUTION 4: Flask Route Implementations
# ============================================================================

def create_progress_routes(app: Flask, progress_manager: SSEProgressManager, 
                          citation_processor: ChunkedCitationProcessor):
    """Create Flask routes for progress-enabled citation processing"""
    
    @app.route('/casestrainer/api/analyze/start', methods=['POST'])
    async def start_citation_analysis():
        """Start citation analysis and return task ID"""
        try:
            data = request.get_json()
            document_text = data.get('text', '')
            document_type = data.get('document_type', 'legal_brief')
            
            if not document_text:
                return jsonify({'error': 'No document text provided'}), 400
            
            # Start processing asynchronously
            task_id = await citation_processor.process_document_with_progress(
                document_text, document_type
            )
            
            return jsonify({
                'task_id': task_id,
                'status': 'started',
                'message': 'Citation analysis started'
            })
            
        except Exception as e:
            logger.error(f"Error starting citation analysis: {e}")
            return jsonify({'error': 'Failed to start analysis'}), 500
    
    @app.route('/casestrainer/api/analyze/progress/<task_id>')
    def get_progress(task_id: str):
        """Get current progress for a task"""
        try:
            progress_data = progress_manager.get_progress(task_id)
            return jsonify(progress_data)
        except Exception as e:
            logger.error(f"Error getting progress: {e}")
            return jsonify({'error': 'Failed to get progress'}), 500
    
    @app.route('/casestrainer/api/analyze/results/<task_id>')
    def get_results(task_id: str):
        """Get final results for a completed task"""
        try:
            results = progress_manager.get_results(task_id)
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error getting results: {e}")
            return jsonify({'error': 'Failed to get results'}), 500
    
    @app.route('/casestrainer/api/analyze/progress-stream/<task_id>')
    def progress_stream(task_id: str):
        """Server-Sent Events stream for real-time progress"""
        def generate_progress_events():
            """Generator for SSE progress events"""
            while True:
                try:
                    progress_data = progress_manager.get_progress(task_id)
                    
                    if 'error' in progress_data:
                        yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                        break
                    
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    
                    if progress_data.get('status') in ['completed', 'failed']:
                        # Send final results
                        final_results = progress_manager.get_results(task_id)
                        yield f"data: {json.dumps(final_results)}\n\n"
                        break
                    
                    time.sleep(0.5)  # Update every 500ms
                    
                except Exception as e:
                    logger.error(f"Error in progress stream: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    break
        
        return Response(
            generate_progress_events(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Nginx compatibility
            }
        )


# ============================================================================
# SOLUTION 5: Frontend JavaScript Integration
# ============================================================================

frontend_js_example = '''
// Frontend JavaScript for progress tracking
class CitationProgressTracker {
    constructor() {
        this.taskId = null;
        this.eventSource = null;
        this.progressCallback = null;
        this.completeCallback = null;
    }
    
    // Method 1: Server-Sent Events (Recommended)
    startAnalysisWithSSE(documentText, documentType, progressCallback, completeCallback) {
        this.progressCallback = progressCallback;
        this.completeCallback = completeCallback;
        
        // Start the analysis
        fetch('/casestrainer/api/analyze/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: documentText,
                document_type: documentType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                this.taskId = data.task_id;
                this.connectToProgressStream();
            } else {
                throw new Error(data.error || 'Failed to start analysis');
            }
        })
        .catch(error => {
            console.error('Error starting analysis:', error);
            this.completeCallback({ error: error.message });
        });
    }
    
    connectToProgressStream() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        this.eventSource = new EventSource(
            `/casestrainer/api/analyze/progress-stream/${this.taskId}`
        );
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    this.handleError(data.error);
                    return;
                }
                
                if (data.results) {
                    // Final results received
                    this.handleComplete(data);
                } else {
                    // Progress update
                    this.handleProgress(data);
                }
                
            } catch (error) {
                console.error('Error parsing progress data:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            this.eventSource.close();
            // Fallback to polling
            this.startPolling();
        };
    }
    
    // Method 2: Polling Fallback
    startPolling() {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/casestrainer/api/analyze/progress/${this.taskId}`);
                const data = await response.json();
                
                if (data.error) {
                    clearInterval(pollInterval);
                    this.handleError(data.error);
                    return;
                }
                
                this.handleProgress(data);
                
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollInterval);
                    
                    // Get final results
                    const resultsResponse = await fetch(`/casestrainer/api/analyze/results/${this.taskId}`);
                    const results = await resultsResponse.json();
                    this.handleComplete(results);
                }
                
            } catch (error) {
                clearInterval(pollInterval);
                this.handleError(error.message);
            }
        }, 1000); // Poll every second
    }
    
    handleProgress(progressData) {
        if (this.progressCallback) {
            this.progressCallback({
                progress: progressData.progress,
                message: progressData.message,
                currentStep: progressData.current_step,
                totalSteps: progressData.total_steps,
                resultsCount: progressData.results_count,
                estimatedCompletion: progressData.estimated_completion
            });
        }
        
        // Update UI
        this.updateProgressBar(progressData.progress);
        this.updateStatusMessage(progressData.message);
        
        // Show partial results if available
        if (progressData.partial_results) {
            this.showPartialResults(progressData.partial_results);
        }
    }
    
    handleComplete(results) {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        if (this.completeCallback) {
            this.completeCallback(results);
        }
        
        // Hide progress bar, show final results
        this.hideProgressBar();
        this.showFinalResults(results);
    }
    
    handleError(error) {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        console.error('Citation analysis error:', error);
        this.hideProgressBar();
        this.showError(error);
    }
    
    updateProgressBar(progress) {
        const progressBar = document.getElementById('citation-progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }
        
        const progressText = document.getElementById('progress-text');
        if (progressText) {
            progressText.textContent = `${Math.round(progress)}%`;
        }
    }
    
    updateStatusMessage(message) {
        const statusElement = document.getElementById('progress-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }
    
    showPartialResults(partialResults) {
        // Show citations as they're found
        const partialContainer = document.getElementById('partial-results');
        if (partialContainer && partialResults.length > 0) {
            partialResults.forEach(citation => {
                const citationElement = this.createCitationElement(citation);
                partialContainer.appendChild(citationElement);
            });
        }
    }
    
    createCitationElement(citation) {
        const div = document.createElement('div');
        div.className = 'citation-preview';
        div.innerHTML = `
            <div class="citation-case-name">${citation.case_name || 'Unknown Case'}</div>
            <div class="citation-details">
                <span class="year">${citation.year || 'No year'}</span>
                <span class="confidence">Confidence: ${Math.round((citation.confidence_score || 0) * 100)}%</span>
            </div>
        `;
        return div;
    }
    
    hideProgressBar() {
        const progressContainer = document.getElementById('progress-container');
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    }
    
    showFinalResults(results) {
        const resultsContainer = document.getElementById('final-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = this.formatFinalResults(results);
            resultsContainer.style.display = 'block';
        }
    }
    
    formatFinalResults(results) {
        return `
            <h3>Citation Analysis Complete</h3>
            <p>Found ${results.results.length} citations</p>
            <div class="citations-list">
                ${results.results.map(citation => this.formatCitation(citation)).join('')}
            </div>
        `;
    }
    
    showError(error) {
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
            errorContainer.style.display = 'block';
        }
    }
}

// Usage example
const tracker = new CitationProgressTracker();

document.getElementById('analyze-button').addEventListener('click', () => {
    const documentText = document.getElementById('document-text').value;
    const documentType = document.getElementById('document-type').value;
    
    // Show progress container
    document.getElementById('progress-container').style.display = 'block';
    
    tracker.startAnalysisWithSSE(
        documentText,
        documentType,
        // Progress callback
        (progressData) => {
            console.log('Progress:', progressData);
        },
        // Complete callback
        (results) => {
            console.log('Analysis complete:', results);
        }
    );
});
'''


# ============================================================================
# SOLUTION 6: Configuration and Setup
# ============================================================================

def setup_progress_enabled_app():
    """Complete setup example for progress-enabled citation processing"""
    app = Flask(__name__)
    
    # Option 1: Server-Sent Events setup
    progress_manager = SSEProgressManager()
    citation_processor = ChunkedCitationProcessor(progress_manager)
    create_progress_routes(app, progress_manager, citation_processor)
    
    # Option 2: WebSocket setup (alternative)
    # socketio = SocketIO(app, cors_allowed_origins="*")
    # ws_progress_manager = WebSocketProgressManager(socketio)
    
    return app

# Example usage
if __name__ == "__main__":
    app = setup_progress_enabled_app()
    app.run(debug=True, threaded=True)


# Configuration for different deployment scenarios
PROGRESS_CONFIG = {
    'sse': {
        'description': 'Server-Sent Events - Best for most cases',
        'pros': ['Simple to implement', 'Works with load balancers', 'Automatic reconnection'],
        'cons': ['HTTP/1.1 connection limit', 'Some proxy issues'],
        'recommended_for': 'Most web applications'
    },
    'websockets': {
        'description': 'WebSocket - Best for real-time applications',
        'pros': ['Full bidirectional', 'Lower latency', 'More efficient'],
        'cons': ['More complex', 'Load balancer challenges', 'Sticky sessions needed'],
        'recommended_for': 'Real-time collaborative features'
    },
    'polling': {
        'description': 'HTTP Polling - Most compatible fallback',
        'pros': ['Universal compatibility', 'Simple to implement', 'Works everywhere'],
        'cons': ['Higher server load', 'Delayed updates', 'Less efficient'],
        'recommended_for': 'Fallback mechanism'
    }
} 