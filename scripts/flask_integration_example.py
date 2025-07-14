
# In your Flask app (e.g., app.py or routes.py)

from scripts.enhanced_extraction_improvements import EnhancedExtractionProcessor

# Initialize the enhanced processor
enhanced_processor = EnhancedExtractionProcessor()

@app.route('/api/process_document', methods=['POST'])
def process_document():
    """Enhanced document processing endpoint."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Process with enhanced extraction
        result = enhanced_processor.process_text_enhanced(text)
        
        return jsonify({
            'success': True,
            'citations': result.get('citations', []),
            'case_names': result.get('case_names', []),
            'dates': result.get('dates', []),
            'clusters': result.get('clusters', []),
            'enhanced_features': {
                'case_name_extraction': len(result.get('case_names', [])) > 0,
                'date_extraction': len(result.get('dates', [])) > 0,
                'clustering': len(result.get('clusters', [])) > 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
