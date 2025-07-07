
#!/usr/bin/env python3
"""
Simple test server without worker threads
"""

from flask import Flask, jsonify, request
import time

app = Flask(__name__)

@app.route('/casestrainer/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'CaseStrainer Test API',
        'timestamp': time.time(),
        'worker_disabled': True
    })

@app.route('/casestrainer/api/analyze', methods=['POST'])
def analyze():
    try:
        if request.is_json:
            data = request.get_json()
            text = data.get('text', '')
            url = data.get('url', '')
            input_type = data.get('type', 'text')
        else:
            # Handle file upload
            file = request.files.get('file')
            if file:
                text = file.read().decode('utf-8', errors='ignore')
                input_type = 'file'
            else:
                return jsonify({'error': 'No input provided'}), 400
        
        # Simple citation extraction (mock)
        citations = [
            {
                'citation': '97 Wn.2d 30',
                'case_name': 'Seattle Times Co. v. Ishikawa',
                'verified': True,
                'source': 'Test',
                'url': 'https://example.com'
            }
        ]
        
        return jsonify({
            'status': 'completed',
            'citations': citations,
            'total_citations': len(citations),
            'verified_citations': len([c for c in citations if c.get('verified')])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/casestrainer/api/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    return jsonify({
        'status': 'completed',
        'task_id': task_id,
        'results': []
    })

if __name__ == '__main__':
    print("Starting simple test server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
