import os
import json
import time
import uuid
import threading
from flask import Flask, request, jsonify, render_template, send_from_directory, Response, session
from flask_cors import CORS

# Create Flask app
app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())  # Set a secret key for sessions
CORS(app)  # Enable CORS for Word add-in support

# Global storage for analysis results
analysis_results = {}

# Function to generate a unique analysis ID
def generate_analysis_id():
    return str(uuid.uuid4())

# Function to simulate analysis process
def run_analysis(analysis_id, brief_text):
    print(f"Starting analysis for ID: {analysis_id}")
    
    # Initialize the results for this analysis
    analysis_results[analysis_id] = {
        'status': 'running',
        'events': [],
        'completed': False
    }
    
    # Add initial event
    analysis_results[analysis_id]['events'].append({
        'status': 'started',
        'total_citations': 1
    })
    
    # Add progress event
    analysis_results[analysis_id]['events'].append({
        'status': 'progress',
        'current': 1,
        'total': 1,
        'message': 'Checking citation...'
    })
    
    # Simulate processing time
    time.sleep(2)
    
    # Add result event
    result = {
        'citation_text': brief_text if brief_text else "2016 WL 165971",
        'is_hallucinated': False,
        'confidence': 0.85,
        'context': 'This is a test citation.',
        'explanation': 'This citation was found in the database.'
    }
    
    analysis_results[analysis_id]['events'].append({
        'status': 'result',
        'citation_index': 0,
        'result': result,
        'total': 1
    })
    
    # Simulate more processing time
    time.sleep(1)
    
    # Add completion event
    analysis_results[analysis_id]['events'].append({
        'status': 'complete',
        'total_citations': 1,
        'hallucinated_citations': 0
    })
    
    # Mark as completed
    analysis_results[analysis_id]['status'] = 'complete'
    analysis_results[analysis_id]['completed'] = True
    
    print(f"Analysis completed for ID: {analysis_id}")
    
    # Clean up old analyses after some time
    threading.Timer(300, lambda: analysis_results.pop(analysis_id, None)).start()

@app.route('/')
def index():
    return render_template('index_fixed.html')

@app.route('/test_sse.html')
def test_sse():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'test_sse.html')

@app.route('/test_sse_simple.html')
def test_sse_simple():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'test_sse_simple.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Analyze a brief for hallucinated case citations."""
    print("\n\n==== ANALYZE ENDPOINT CALLED =====")
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Request path: {request.path}")
    print(f"Request query string: {request.query_string}")
    
    # For POST requests, start a new analysis
    if request.method == 'POST':
        print("POST request detected - starting analysis")
        
        # Get the brief text from the form data
        if 'briefText' in request.form:
            brief_text = request.form['briefText']
            print(f"Brief text from form: {brief_text[:100]}...")
            
            # Generate a unique ID for this analysis
            analysis_id = generate_analysis_id()
            print(f"Generated analysis ID: {analysis_id}")
            
            # Start the analysis in a background thread
            threading.Thread(target=run_analysis, args=(analysis_id, brief_text)).start()
            
            # Return the analysis ID to the client
            return jsonify({
                'status': 'success',
                'message': 'Analysis started',
                'analysis_id': analysis_id
            })
        else:
            return jsonify({'status': 'error', 'message': 'No brief text provided'}), 400
    else:
        # For GET requests, return an error
        return jsonify({'status': 'error', 'message': 'Use POST to start analysis and GET /analyze_status to check status'}), 400

@app.route('/analyze_status')
def analyze_status():
    """Check the status of an analysis."""
    print("\n\n==== ANALYZE_STATUS ENDPOINT CALLED =====")
    
    # Get the analysis ID from the query string
    analysis_id = request.args.get('id')
    if not analysis_id:
        return jsonify({'status': 'error', 'message': 'No analysis ID provided'}), 400
    
    # Check if the analysis exists
    if analysis_id not in analysis_results:
        return jsonify({'status': 'error', 'message': 'Analysis not found'}), 404
    
    # Return the current status and events
    return jsonify({
        'status': analysis_results[analysis_id]['status'],
        'events': analysis_results[analysis_id]['events'],
        'completed': analysis_results[analysis_id]['completed']
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
