from flask import Flask, request, render_template_string, jsonify
import os
import json
import time
import uuid
import threading
import traceback
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Dictionary to store analysis results
analysis_results = {}

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Simulated analysis function
def run_analysis(analysis_id, file_path=None):
    print(f"Starting analysis for ID: {analysis_id}")
    print(f"File path: {file_path}" if file_path else "No file path provided")
    
    try:
        # Initialize the results for this analysis
        analysis_results[analysis_id] = {
            'status': 'running',
            'progress': 0,
            'total_steps': 3,
            'message': 'Analysis started',
            'completed': False,
            'results': None,
            'error': None
        }
        
        # Simulate file processing
        if file_path:
            # Check if file exists
            if not os.path.isfile(file_path):
                analysis_results[analysis_id]['status'] = 'error'
                analysis_results[analysis_id]['error'] = f'File not found: {file_path}'
                analysis_results[analysis_id]['completed'] = True
                return
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Update progress - Step 1
            analysis_results[analysis_id]['progress'] = 1
            analysis_results[analysis_id]['message'] = f'Processing file: {os.path.basename(file_path)} ({file_size} bytes)'
            
            # Simulate reading file
            time.sleep(2)
            
            # Update progress - Step 2
            analysis_results[analysis_id]['progress'] = 2
            analysis_results[analysis_id]['message'] = 'Extracting text from file'
            
            # Simulate text extraction
            time.sleep(2)
            
            # Update progress - Step 3
            analysis_results[analysis_id]['progress'] = 3
            analysis_results[analysis_id]['message'] = 'Analyzing citations'
            
            # Simulate citation analysis
            time.sleep(2)
            
            # Complete the analysis
            analysis_results[analysis_id]['status'] = 'complete'
            analysis_results[analysis_id]['progress'] = 3
            analysis_results[analysis_id]['message'] = 'Analysis complete'
            analysis_results[analysis_id]['completed'] = True
            analysis_results[analysis_id]['results'] = {
                'file_name': os.path.basename(file_path),
                'file_size': file_size,
                'citations_found': 5,
                'citations_verified': 3
            }
        else:
            # No file provided
            analysis_results[analysis_id]['status'] = 'error'
            analysis_results[analysis_id]['error'] = 'No file provided'
            analysis_results[analysis_id]['completed'] = True
    
    except Exception as e:
        print(f"Error running analysis: {e}")
        traceback.print_exc()
        
        # Update with error
        analysis_results[analysis_id]['status'] = 'error'
        analysis_results[analysis_id]['error'] = f"Error running analysis: {str(e)}"
        analysis_results[analysis_id]['completed'] = True

# HTML template for the application
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AJAX File Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        #progressBar {
            transition: width 0.3s ease;
        }
        #debugInfo {
            max-height: 300px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1>AJAX File Test</h1>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">File Path Test</div>
                    <div class="card-body">
                        <form id="pathForm">
                            <div class="mb-3">
                                <label for="filePath" class="form-label">File Path:</label>
                                <input type="text" class="form-control" id="filePath" name="file_path" 
                                       value="C:/Users/jafrank/Downloads/gov.uscourts.wyd.64014.141.0_1.pdf">
                            </div>
                            <button type="submit" class="btn btn-primary">Test File Path</button>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">File Upload Test</div>
                    <div class="card-body">
                        <form id="uploadForm" enctype="multipart/form-data">
                            <div class="mb-3">
                                <label for="fileUpload" class="form-label">Select File:</label>
                                <input type="file" class="form-control" id="fileUpload" name="file">
                            </div>
                            <button type="submit" class="btn btn-primary">Upload File</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="resultsContainer" style="display: none;">
            <h2>Results</h2>
            
            <div class="progress mb-3">
                <div id="progressBar" class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%"></div>
            </div>
            
            <div id="statusMessage" class="alert alert-info">Starting analysis...</div>
            
            <div id="resultsDetails" class="card mb-3">
                <div class="card-header">Analysis Results</div>
                <div class="card-body">
                    <p>Waiting for results...</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">Debug Information</div>
            <div class="card-body">
                <pre id="debugInfo"></pre>
            </div>
        </div>
    </div>
    
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
        // Helper function to append debug information
        function appendDebug(message) {
            const debugInfo = $('#debugInfo');
            const timestamp = new Date().toLocaleTimeString();
            debugInfo.append(`[${timestamp}] ${message}\\n`);
            debugInfo.scrollTop(debugInfo[0].scrollHeight);
        }
        
        // Helper function to update progress bar
        function updateProgress(current, total) {
            const percentage = Math.round((current / total) * 100);
            $('#progressBar').css('width', percentage + '%').attr('aria-valuenow', percentage);
        }
        
        // Helper function to show status message
        function showStatus(message, type = 'info') {
            $('#statusMessage').removeClass('alert-info alert-success alert-warning alert-danger')
                              .addClass('alert-' + type)
                              .text(message);
        }
        
        // Function to poll for status updates
        function pollStatus(analysisId) {
            appendDebug(`Polling for status of analysis: ${analysisId}`);
            
            // Set up polling interval
            const pollInterval = setInterval(function() {
                $.ajax({
                    url: `/status?id=${analysisId}`,
                    type: 'GET',
                    success: function(response) {
                        appendDebug(`Status update: ${JSON.stringify(response)}`);
                        
                        // Update progress
                        updateProgress(response.progress, response.total_steps);
                        
                        // Update status message
                        const statusType = response.status === 'error' ? 'danger' : 
                                          response.status === 'complete' ? 'success' : 'info';
                        showStatus(response.message, statusType);
                        
                        // If analysis is complete, show results
                        if (response.completed) {
                            clearInterval(pollInterval);
                            appendDebug('Analysis completed, stopping polling');
                            
                            if (response.status === 'complete' && response.results) {
                                const results = response.results;
                                let resultsHtml = `
                                    <h5>File: ${results.file_name}</h5>
                                    <p>Size: ${results.file_size} bytes</p>
                                    <p>Citations Found: ${results.citations_found}</p>
                                    <p>Citations Verified: ${results.citations_verified}</p>
                                `;
                                $('#resultsDetails .card-body').html(resultsHtml);
                            } else if (response.error) {
                                $('#resultsDetails .card-body').html(`<p class="text-danger">${response.error}</p>`);
                            }
                        }
                    },
                    error: function(xhr, status, error) {
                        appendDebug(`Error polling status: ${error}`);
                        showStatus(`Error polling status: ${error}`, 'danger');
                        clearInterval(pollInterval);
                    }
                });
            }, 1000); // Poll every second
        }
        
        $(document).ready(function() {
            appendDebug('Page loaded');
            
            // Handle file path form submission
            $('#pathForm').submit(function(e) {
                e.preventDefault();
                appendDebug('Path form submitted');
                
                const filePath = $('#filePath').val();
                if (!filePath) {
                    appendDebug('No file path provided');
                    showStatus('Please enter a file path', 'warning');
                    return;
                }
                
                appendDebug(`File path: ${filePath}`);
                
                // Show the results container
                $('#resultsContainer').show();
                
                // Reset the progress and status
                updateProgress(0, 1);
                showStatus('Starting analysis...', 'info');
                $('#resultsDetails .card-body').html('<p>Waiting for results...</p>');
                
                // Send the request to the server
                $.ajax({
                    url: '/analyze',
                    type: 'POST',
                    data: {file_path: filePath},
                    success: function(response) {
                        appendDebug(`Server response: ${JSON.stringify(response)}`);
                        
                        if (response.status === 'success') {
                            appendDebug(`Analysis started with ID: ${response.analysis_id}`);
                            pollStatus(response.analysis_id);
                        } else {
                            showStatus(`Error: ${response.message}`, 'danger');
                        }
                    },
                    error: function(xhr, status, error) {
                        appendDebug(`Error starting analysis: ${error}`);
                        appendDebug(`Response text: ${xhr.responseText}`);
                        showStatus(`Error starting analysis: ${error}`, 'danger');
                    }
                });
            });
            
            // Handle file upload form submission
            $('#uploadForm').submit(function(e) {
                e.preventDefault();
                appendDebug('Upload form submitted');
                
                const fileInput = $('#fileUpload')[0];
                if (!fileInput.files || fileInput.files.length === 0) {
                    appendDebug('No file selected');
                    showStatus('Please select a file', 'warning');
                    return;
                }
                
                const file = fileInput.files[0];
                appendDebug(`Selected file: ${file.name}, size: ${file.size} bytes, type: ${file.type}`);
                
                // Show the results container
                $('#resultsContainer').show();
                
                // Reset the progress and status
                updateProgress(0, 1);
                showStatus('Starting analysis...', 'info');
                $('#resultsDetails .card-body').html('<p>Waiting for results...</p>');
                
                // Create form data and append the file
                const formData = new FormData();
                formData.append('file', file);
                
                // Send the request to the server
                $.ajax({
                    url: '/analyze',
                    type: 'POST',
                    data: formData,
                    processData: false,
                    contentType: false,
                    success: function(response) {
                        appendDebug(`Server response: ${JSON.stringify(response)}`);
                        
                        if (response.status === 'success') {
                            appendDebug(`Analysis started with ID: ${response.analysis_id}`);
                            pollStatus(response.analysis_id);
                        } else {
                            showStatus(`Error: ${response.message}`, 'danger');
                        }
                    },
                    error: function(xhr, status, error) {
                        appendDebug(`Error starting analysis: ${error}`);
                        appendDebug(`Response text: ${xhr.responseText}`);
                        showStatus(`Error starting analysis: ${error}`, 'danger');
                    }
                });
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    print("\n\n==== ANALYZE ENDPOINT CALLED =====")
    print(f"Request method: {request.method}")
    print(f"Request headers: {request.headers}")
    print(f"Request form data: {request.form}")
    print(f"Request files: {request.files}")
    
    try:
        # Generate a unique analysis ID
        analysis_id = str(uuid.uuid4())
        print(f"Generated analysis ID: {analysis_id}")
        
        # Get file path if provided
        file_path = None
        
        # Check if a file was uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                print(f"File uploaded: {file.filename}")
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                print(f"File saved to: {file_path}")
        
        # Check if a file path was provided
        elif 'file_path' in request.form:
            file_path = request.form['file_path'].strip()
            print(f"File path provided: {file_path}")
            
            # Handle file:/// URLs
            if file_path.startswith('file:///'):
                file_path = file_path[8:]  # Remove 'file:///' prefix
        
        # Start the analysis in a background thread
        threading.Thread(target=run_analysis, args=(analysis_id, file_path)).start()
        
        # Return the analysis ID to the client
        return jsonify({
            'status': 'success',
            'message': 'Analysis started',
            'analysis_id': analysis_id
        })
    except Exception as e:
        print(f"Error in analyze endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/status')
def status():
    """Get the status of an analysis."""
    print("\n\n==== STATUS ENDPOINT CALLED =====")
    
    # Get the analysis ID from the query string
    analysis_id = request.args.get('id')
    if not analysis_id:
        return jsonify({'status': 'error', 'message': 'No analysis ID provided'}), 400
    
    # Check if the analysis exists
    if analysis_id not in analysis_results:
        return jsonify({'status': 'error', 'message': 'Analysis not found'}), 404
    
    # Return the current status
    return jsonify(analysis_results[analysis_id])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
