import os
import json
import time
import uuid
import threading
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Global storage for analysis results
analysis_results = {}

# Function to generate a unique analysis ID
def generate_analysis_id():
    return str(uuid.uuid4())

# Function to simulate analysis process
def run_analysis(analysis_id, text):
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
    
    # Simulate processing time
    time.sleep(2)
    
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
        'citation_text': text,
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
    
    # Simulate processing time
    time.sleep(2)
    
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
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Polling Test</title>
        <style>
            #log {
                height: 300px;
                overflow-y: auto;
                border: 1px solid #ccc;
                padding: 10px;
                margin-top: 10px;
            }
            .error { color: red; }
            .success { color: green; }
            .info { color: blue; }
        </style>
    </head>
    <body>
        <h1>Polling Test</h1>
        <input type="text" id="citation" placeholder="Enter citation" value="2016 WL 165971">
        <button id="analyze">Analyze</button>
        <div id="log"></div>

        <script>
            const analyzeBtn = document.getElementById('analyze');
            const citationInput = document.getElementById('citation');
            const logDiv = document.getElementById('log');
            
            // Track processed events
            let processedEvents = 0;
            
            function log(message, type = 'info') {
                const div = document.createElement('div');
                div.className = type;
                div.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
                logDiv.appendChild(div);
                logDiv.scrollTop = logDiv.scrollHeight;
            }
            
            analyzeBtn.addEventListener('click', function() {
                const citation = citationInput.value.trim();
                if (!citation) {
                    log('Please enter a citation', 'error');
                    return;
                }
                
                log(`Starting analysis for: ${citation}`, 'info');
                
                // Reset processed events
                processedEvents = 0;
                
                // Send the request to start analysis
                fetch('/start_analysis', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: citation })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        log(`Analysis started with ID: ${data.analysis_id}`, 'success');
                        
                        // Start polling for results
                        pollForResults(data.analysis_id);
                    } else {
                        log(`Error starting analysis: ${data.message}`, 'error');
                    }
                })
                .catch(error => {
                    log(`Error starting analysis: ${error.message}`, 'error');
                });
            });
            
            function pollForResults(analysisId) {
                log(`Polling for results (processed ${processedEvents} events)`, 'info');
                
                fetch(`/check_analysis?id=${analysisId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'error') {
                        log(`Error checking analysis: ${data.message}`, 'error');
                        return;
                    }
                    
                    // Process new events
                    if (data.events && data.events.length > processedEvents) {
                        const newEvents = data.events.slice(processedEvents);
                        log(`Found ${newEvents.length} new events`, 'info');
                        
                        newEvents.forEach(event => {
                            switch (event.status) {
                                case 'started':
                                    log(`Analysis started, found ${event.total_citations} citations`, 'info');
                                    break;
                                case 'progress':
                                    log(`Progress: ${event.message}`, 'info');
                                    break;
                                case 'result':
                                    log(`Result: ${event.result.citation_text} - ${event.result.is_hallucinated ? 'Hallucinated' : 'Real'}`, 'success');
                                    break;
                                case 'complete':
                                    log(`Analysis complete: ${event.total_citations} citations, ${event.hallucinated_citations} hallucinated`, 'success');
                                    break;
                                default:
                                    log(`Unknown event: ${JSON.stringify(event)}`, 'info');
                            }
                        });
                        
                        // Update processed events count
                        processedEvents = data.events.length;
                    }
                    
                    // Continue polling if not complete
                    if (!data.completed) {
                        setTimeout(() => pollForResults(analysisId), 1000);
                    } else {
                        log('Analysis is complete!', 'success');
                    }
                })
                .catch(error => {
                    log(`Error polling for results: ${error.message}`, 'error');
                    
                    // Retry after a delay
                    setTimeout(() => pollForResults(analysisId), 3000);
                });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'status': 'error', 'message': 'No text provided'}), 400
    
    text = data['text']
    print(f"Starting analysis for text: {text}")
    
    # Generate a unique ID for this analysis
    analysis_id = generate_analysis_id()
    print(f"Generated analysis ID: {analysis_id}")
    
    # Start the analysis in a background thread
    threading.Thread(target=run_analysis, args=(analysis_id, text)).start()
    
    # Return the analysis ID to the client
    return jsonify({
        'status': 'success',
        'message': 'Analysis started',
        'analysis_id': analysis_id
    })

@app.route('/check_analysis')
def check_analysis():
    analysis_id = request.args.get('id')
    if not analysis_id:
        return jsonify({'status': 'error', 'message': 'No analysis ID provided'}), 400
    
    if analysis_id not in analysis_results:
        return jsonify({'status': 'error', 'message': 'Analysis not found'}), 404
    
    # Return the current status and events
    return jsonify({
        'status': analysis_results[analysis_id]['status'],
        'events': analysis_results[analysis_id]['events'],
        'completed': analysis_results[analysis_id]['completed']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
