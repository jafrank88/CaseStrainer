from flask import Flask, request, render_template_string, jsonify
import os
import PyPDF2
import traceback

app = Flask(__name__)

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple File Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Simple File Test</h1>
            
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
                            <div id="pathResult" class="mt-3"></div>
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
                            <div id="uploadResult" class="mt-3"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">Debug Information</div>
                <div class="card-body">
                    <pre id="debugInfo" style="max-height: 300px; overflow-y: auto;"></pre>
                </div>
            </div>
        </div>
        
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script>
            function appendDebug(message) {
                const debugInfo = $('#debugInfo');
                const timestamp = new Date().toLocaleTimeString();
                debugInfo.append(`[${timestamp}] ${message}\\n`);
                debugInfo.scrollTop(debugInfo[0].scrollHeight);
            }
            
            $(document).ready(function() {
                appendDebug('Page loaded');
                
                // File Path Form
                $('#pathForm').submit(function(event) {
                    event.preventDefault();
                    appendDebug('Path form submitted');
                    
                    const filePath = $('#filePath').val();
                    appendDebug(`Testing file path: ${filePath}`);
                    
                    $('#pathResult').html('<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>');
                    
                    $.ajax({
                        url: '/test_path',
                        type: 'POST',
                        data: {file_path: filePath},
                        success: function(response) {
                            appendDebug(`Path test response received: ${JSON.stringify(response)}`);
                            
                            if (response.error) {
                                $('#pathResult').html(`<div class="alert alert-danger">${response.error}</div>`);
                                return;
                            }
                            
                            let resultHtml = `
                                <div class="alert alert-success">
                                    <h5>File exists: ${response.file_exists}</h5>
                                    <p>File path: ${response.file_path}</p>
                                    <p>File size: ${response.file_size} bytes</p>
                                </div>
                            `;
                            
                            if (response.text_sample) {
                                resultHtml += `
                                    <div class="mt-3">
                                        <h5>Text Sample:</h5>
                                        <pre class="bg-light p-2" style="max-height: 200px; overflow-y: auto;">${response.text_sample}</pre>
                                    </div>
                                `;
                            }
                            
                            $('#pathResult').html(resultHtml);
                        },
                        error: function(xhr, status, error) {
                            appendDebug(`Path test error: ${error}`);
                            $('#pathResult').html(`<div class="alert alert-danger">Error: ${error}</div>`);
                        }
                    });
                });
                
                // File Upload Form
                $('#uploadForm').submit(function(event) {
                    event.preventDefault();
                    appendDebug('Upload form submitted');
                    
                    const fileInput = $('#fileUpload')[0];
                    if (!fileInput.files || fileInput.files.length === 0) {
                        appendDebug('No file selected');
                        $('#uploadResult').html('<div class="alert alert-warning">Please select a file</div>');
                        return;
                    }
                    
                    const file = fileInput.files[0];
                    appendDebug(`Uploading file: ${file.name}, size: ${file.size} bytes, type: ${file.type}`);
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    $('#uploadResult').html('<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>');
                    
                    $.ajax({
                        url: '/test_upload',
                        type: 'POST',
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(response) {
                            appendDebug(`Upload response received: ${JSON.stringify(response)}`);
                            
                            if (response.error) {
                                $('#uploadResult').html(`<div class="alert alert-danger">${response.error}</div>`);
                                return;
                            }
                            
                            let resultHtml = `
                                <div class="alert alert-success">
                                    <h5>File uploaded successfully</h5>
                                    <p>Filename: ${response.filename}</p>
                                    <p>File size: ${response.file_size} bytes</p>
                                </div>
                            `;
                            
                            if (response.text_sample) {
                                resultHtml += `
                                    <div class="mt-3">
                                        <h5>Text Sample:</h5>
                                        <pre class="bg-light p-2" style="max-height: 200px; overflow-y: auto;">${response.text_sample}</pre>
                                    </div>
                                `;
                            }
                            
                            $('#uploadResult').html(resultHtml);
                        },
                        error: function(xhr, status, error) {
                            appendDebug(`Upload error: ${error}`);
                            $('#uploadResult').html(`<div class="alert alert-danger">Error: ${error}</div>`);
                        }
                    });
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/test_path', methods=['POST'])
def test_path():
    try:
        file_path = request.form.get('file_path')
        print(f"Testing file path: {file_path}")
        
        if not file_path:
            return jsonify({
                'error': 'No file path provided'
            })
        
        # Check if file exists
        file_exists = os.path.isfile(file_path)
        print(f"File exists: {file_exists}")
        
        result = {
            'file_path': file_path,
            'file_exists': file_exists,
            'file_size': 0
        }
        
        if file_exists:
            file_size = os.path.getsize(file_path)
            result['file_size'] = file_size
            print(f"File size: {file_size} bytes")
            
            # If it's a PDF, try to extract text
            if file_path.lower().endswith('.pdf'):
                try:
                    with open(file_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        print(f"PDF has {len(reader.pages)} pages")
                        
                        text = ''
                        for i, page in enumerate(reader.pages):
                            if i >= 1:  # Only extract text from the first page
                                break
                            text += page.extract_text() + '\n'
                        
                        result['text_sample'] = text[:500] + '...' if len(text) > 500 else text
                        print(f"Extracted {len(text)} characters of text")
                except Exception as e:
                    print(f"Error extracting text from PDF: {e}")
                    traceback.print_exc()
                    result['error'] = f"Error extracting text from PDF: {str(e)}"
        else:
            result['error'] = f"File not found: {file_path}"
            print(f"File not found: {file_path}")
        
        return jsonify(result)
    except Exception as e:
        print(f"Error in test_path: {e}")
        traceback.print_exc()
        return jsonify({
            'error': f"Server error: {str(e)}"
        })

@app.route('/test_upload', methods=['POST'])
def test_upload():
    try:
        if 'file' not in request.files:
            print("No file part in the request")
            return jsonify({
                'error': 'No file part in the request'
            })
        
        file = request.files['file']
        
        if file.filename == '':
            print("No file selected")
            return jsonify({
                'error': 'No file selected'
            })
        
        print(f"File uploaded: {file.filename}")
        
        # Save the file temporarily
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)
        
        file_size = os.path.getsize(file_path)
        print(f"File saved to {file_path}, size: {file_size} bytes")
        
        result = {
            'filename': file.filename,
            'file_size': file_size
        }
        
        # If it's a PDF, try to extract text
        if file.filename.lower().endswith('.pdf'):
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    print(f"PDF has {len(reader.pages)} pages")
                    
                    text = ''
                    for i, page in enumerate(reader.pages):
                        if i >= 1:  # Only extract text from the first page
                            break
                        text += page.extract_text() + '\n'
                    
                    result['text_sample'] = text[:500] + '...' if len(text) > 500 else text
                    print(f"Extracted {len(text)} characters of text")
            except Exception as e:
                print(f"Error extracting text from PDF: {e}")
                traceback.print_exc()
                result['error'] = f"Error extracting text from PDF: {str(e)}"
        
        return jsonify(result)
    except Exception as e:
        print(f"Error in test_upload: {e}")
        traceback.print_exc()
        return jsonify({
            'error': f"Server error: {str(e)}"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
