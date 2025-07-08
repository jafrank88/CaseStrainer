"""
API wrapper for integrating enhanced citation processing with Flask routes
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, Optional
import asyncio

from src.citation_processor import CaseStrainerCitationProcessor
from src.citation_services import ExtractionConfig

logger = logging.getLogger(__name__)

# Create Blueprint for citation API
citation_api = Blueprint('citation_api', __name__)

# Global processor instance
_processor = None

def get_citation_processor() -> CaseStrainerCitationProcessor:
    """Get or create citation processor instance"""
    global _processor
    if _processor is None:
        _processor = CaseStrainerCitationProcessor()
    return _processor

@citation_api.route('/citations/analyze', methods=['POST'])
def analyze_document_citations():
    """API endpoint for analyzing citations in documents"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        document_text = data.get('text', '')
        document_type = data.get('document_type', 'legal_brief')
        user_context = data.get('context', {})
        
        if not document_text:
            return jsonify({'error': 'No document text provided'}), 400
        
        # Get processor and run analysis
        processor = get_citation_processor()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                processor.process_document_citations(document_text, document_type, user_context)
            )
        finally:
            loop.close()
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in citation analysis API: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@citation_api.route('/citations/validate', methods=['POST'])
def validate_single_citation():
    """API endpoint for validating a single citation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        citation_text = data.get('citation', '')
        
        if not citation_text:
            return jsonify({'error': 'No citation provided'}), 400
        
        # Get processor and validate citation
        processor = get_citation_processor()
        
        # Extract and validate single citation
        config = ExtractionConfig(min_confidence_threshold=0.5)
        citations = processor.citation_service.extract_citations(citation_text, config)
        
        if citations:
            citation = citations[0]
            
            # Run async validation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                validation_status = loop.run_until_complete(
                    processor._validate_citation(citation)
                )
                enhanced_data = loop.run_until_complete(
                    processor._enhance_citation_data(citation)
                )
            finally:
                loop.close()
            
            result = {
                'valid': validation_status == 'valid',
                'validation_status': validation_status,
                'citation_data': {
                    'case_name': citation.case_name,
                    'year': citation.year,
                    'court': citation.court,
                    'reporter': citation.reporter,
                    'confidence_score': citation.confidence_score
                },
                'enhancements': enhanced_data
            }
        else:
            result = {
                'valid': False,
                'validation_status': 'not_found',
                'error': 'Could not extract citation from provided text'
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in citation validation API: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@citation_api.route('/citations/extract', methods=['POST'])
def extract_citations():
    """API endpoint for extracting citations from text"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        text = data.get('text', '')
        config_data = data.get('config', {})
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Create extraction config
        config = ExtractionConfig(**config_data) if config_data else ExtractionConfig()
        
        # Extract citations
        processor = get_citation_processor()
        citations = processor.citation_service.extract_citations(text, config)
        
        # Convert to serializable format
        citation_data = []
        for citation in citations:
            citation_data.append({
                'raw_text': citation.raw_text,
                'case_name': citation.case_name,
                'year': citation.year,
                'court': citation.court,
                'reporter': citation.reporter,
                'volume': citation.volume,
                'page': citation.page,
                'confidence_score': citation.confidence_score,
                'citation_type': citation.citation_type,
                'bluebook_format': citation.get_bluebook_format()
            })
        
        return jsonify({
            'success': True,
            'citations': citation_data,
            'count': len(citation_data)
        })
        
    except Exception as e:
        logger.error(f"Error in citation extraction API: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@citation_api.route('/citations/stats', methods=['POST'])
def get_citation_statistics():
    """API endpoint for getting citation statistics"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Extract citations and get statistics
        processor = get_citation_processor()
        citations = processor.citation_service.extract_citations(text)
        stats = processor.citation_service.get_citation_statistics(citations)
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error in citation statistics API: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@citation_api.route('/citations/health', methods=['GET'])
def citation_health_check():
    """Health check endpoint for citation services"""
    try:
        processor = get_citation_processor()
        
        # Test basic functionality
        test_text = "See Brown v. Board of Education, 347 U.S. 483 (1954)."
        test_citations = processor.citation_service.extract_citations(test_text)
        
        health_status = {
            'status': 'healthy',
            'services': {
                'citation_extraction': len(test_citations) > 0,
                'citation_processor': processor is not None,
                'citation_service': processor.citation_service is not None
            },
            'test_citation_count': len(test_citations)
        }
        
        # Check if all services are working
        if all(health_status['services'].values()):
            return jsonify(health_status), 200
        else:
            health_status['status'] = 'degraded'
            return jsonify(health_status), 503
            
    except Exception as e:
        logger.error(f"Error in citation health check: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

# Legacy compatibility endpoint
@citation_api.route('/analyze_enhanced', methods=['POST'])
def enhanced_analyze():
    """Enhanced analyze endpoint with better citation extraction (legacy compatibility)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        input_type = data.get('type', 'text')
        
        if input_type == 'text':
            text = data.get('text', '')
            document_type = data.get('document_type', 'legal_brief')
            
            if not text:
                return jsonify({'error': 'No text provided'}), 400
            
            # Use the enhanced citation processor
            processor = get_citation_processor()
            
            # Run async processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                citation_results = loop.run_until_complete(
                    processor.process_document_citations(text, document_type)
                )
            finally:
                loop.close()
            
            # Maintain compatibility with existing response format
            legacy_format = {
                'success': citation_results['success'],
                'citations': [
                    {
                        'text': c['raw_text'],
                        'case_name': c['case_name'],
                        'year': c['year'],
                        'validation_status': c['validation_status'],
                        'confidence': c['confidence_score']
                    }
                    for c in citation_results['citations']
                ],
                'analysis': citation_results['analysis'],
                'recommendations': citation_results['recommendations']
            }
            
            return jsonify(legacy_format)
        
        else:
            return jsonify({'error': 'File upload processing not implemented in this endpoint'}), 501
            
    except Exception as e:
        logger.error(f"Error in enhanced analyze endpoint: {e}", exc_info=True)
        return jsonify({'error': 'Analysis failed', 'details': str(e)}), 500
