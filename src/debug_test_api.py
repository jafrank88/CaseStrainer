"""
Minimal Debug Test API for CaseStrainer
Ultra-simple endpoint to test basic connectivity and isolate 500 error issues
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# Create the blueprint
debug_api = Blueprint('debug_api', __name__)

@debug_api.route('/health', methods=['GET'])
def health_check():
    """Ultra-simple health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Debug API is working'
    })

@debug_api.route('/analyze', methods=['POST'])
def analyze():
    """Ultra-minimal analyze endpoint for debugging"""
    try:
        # Log the incoming request
        logger.info("=== DEBUG ANALYZE ENDPOINT CALLED ===")
        
        # Get request data
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        # Return response format that frontend expects
        # For text input like Ratliff citation, return realistic mock data
        input_text = data.get('text', '')
        if 'Ratliff' in input_text:
            result = {
                'citations': [
                    {
                        'citation': 'City of Seattle v. Ratliff, 100 Wn.2d 212, 218, 667 P.2d 630 (1983)',
                        'status': 'verified',
                        'case_name': 'City of Seattle v. Ratliff',
                        'verified': True,
                        'court': 'Washington Supreme Court',
                        'year': '1983',
                        'volume': '100',
                        'reporter': 'Wn.2d',
                        'page': '212'
                    }
                ],
                'validation_results': [
                    {
                        'citation': 'City of Seattle v. Ratliff, 100 Wn.2d 212, 218, 667 P.2d 630 (1983)',
                        'verified': True,
                        'confidence': 0.95,
                        'explanation': 'Citation verified against Washington Supreme Court records'
                    }
                ],
                'message': 'Analysis completed successfully',
                'total_citations': 1,
                'verified_count': 1,
                'unverified_count': 0
            }
        else:
            # Generic mock response for other inputs
            result = {
                'citations': [
                    {
                        'citation': 'DEBUG-TEST-123',
                        'status': 'verified',
                        'case_name': 'Debug Test Case',
                        'verified': True
                    }
                ],
                'validation_results': [
                    {
                        'citation': 'DEBUG-TEST-123',
                        'verified': True,
                        'confidence': 0.90,
                        'explanation': 'Debug test citation - mock verification'
                    }
                ],
                'message': 'Debug analysis completed successfully',
                'total_citations': 1,
                'verified_count': 1,
                'unverified_count': 0
            }
        
        logger.info(f"Returning result: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"DEBUG API ERROR: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Debug API error: {str(e)}'}), 500

@debug_api.route('/test', methods=['GET', 'POST'])
def test():
    """Ultra-simple test endpoint"""
    return jsonify({'message': 'Debug test endpoint working', 'method': request.method})
