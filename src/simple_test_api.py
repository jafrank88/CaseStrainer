"""
Ultra-Simple Test API for Testing Modernized CaseStrainer Frontend
This has NO backend processor dependencies - purely for testing unified progress system
"""

import time
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# Create the blueprint
test_api = Blueprint('test_api', __name__)

# No processor dependencies - just simple mock responses

@test_api.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '4.0.0-modernized',
        'components': {
            'citation_processor': 'mock',
            'unified_progress': 'healthy'
        }
    })

@test_api.route('/analyze', methods=['POST'])
def analyze():
    """Simplified analyze endpoint for testing unified progress system"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Handle different input types
        if 'text' in data:
            text = data['text']
            source_name = data.get('source_name', 'test_input')
            
            # Simulate processing time for progress testing
            time.sleep(1)
            
            # Simple mock processing - no dependencies
            result = {
                'citations': [
                    {
                        'citation': '123 F.3d 456',
                        'status': 'verified',
                        'case_name': 'Mock Case v. Test Case',
                        'court': 'Mock Court',
                        'year': '2023'
                    }
                ],
                'status': 'completed',
                'message': 'Mock processing completed successfully',
                'source_name': source_name,
                'processing_time': 1.0
            }
            
            return jsonify(result)
        
        elif 'url' in data:
            url = data['url']
            
            # Simulate URL processing
            time.sleep(2)
            
            # Return realistic mock citations for URL analysis
            result = {
                'citations': [
                    {
                        'citation': '60179-6 (Wash. 2025)',
                        'status': 'verified',
                        'case_name': 'Mock v. Test Case',
                        'court': 'Washington Supreme Court',
                        'year': '2025',
                        'verified': True,
                        'valid': True,
                        'data': {
                            'valid': True,
                            'found': True,
                            'case_name': 'Mock v. Test Case',
                            'court': 'Washington Supreme Court'
                        }
                    },
                    {
                        'citation': '123 F.3d 456',
                        'status': 'unverified',
                        'case_name': 'Another Mock Case',
                        'court': 'Federal Court',
                        'year': '2023',
                        'verified': False,
                        'valid': False,
                        'data': {
                            'valid': False,
                            'found': False
                        }
                    }
                ],
                'clusters': [
                    {
                        'primary_citation': '60179-6 (Wash. 2025)',
                        'citations': [{
                            'citation': '60179-6 (Wash. 2025)',
                            'status': 'verified',
                            'case_name': 'Mock v. Test Case'
                        }],
                        'size': 1
                    }
                ],
                'metadata': {
                    'source_url': url,
                    'processing_time': 2.0,
                    'total_citations': 2
                },
                'total_citations': 2,
                'verified_count': 1,
                'unverified_count': 1,
                'status': 'completed',
                'message': f'Successfully processed URL: {url}',
                'source_name': url,
                'processing_time': 2.0
            }
            
            return jsonify(result)
        
        else:
            return jsonify({'error': 'Invalid input type'}), 400
            
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@test_api.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Simple task status endpoint for compatibility"""
    return jsonify({
        'task_id': task_id,
        'status': 'completed',
        'result': {
            'citations': [],
            'message': 'Task completed successfully'
        }
    })

@test_api.route('/upload', methods=['POST'])
def upload():
    """Simple file upload endpoint for testing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Simulate file processing
        time.sleep(3)
        
        result = {
            'citations': [],
            'status': 'completed',
            'message': f'File processed: {file.filename}',
            'source_name': file.filename,
            'processing_time': 3.0
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in upload endpoint: {e}")
        return jsonify({'error': str(e)}), 500
