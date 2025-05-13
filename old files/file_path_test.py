from flask import Flask, request, render_template_string, jsonify
import os
import PyPDF2

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>File Path Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>File Path Test</h1>
            
            <form id="testForm" class="mb-4">
                <div class="mb-3">
                    <label for="filePath" class="form-label">File Path:</label>
                    <input type="text" class="form-control" id="filePath" name="file_path" 
                           value="C:/Users/jafrank/Downloads/gov.uscourts.wyd.64014.141.0_1.pdf">
                </div>
                <button type="submit" class="btn btn-primary">Test File Path</button>
            </form>
            
            <div id="loading" style="display: none;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Processing...</span>
            </div>
            
            <div id="result" class="mt-4"></div>
        </div>
        
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script>
            $(document).ready(function() {
                $('#testForm').submit(function(event) {
                    event.preventDefault();
                    
                    const filePath = $('#filePath').val();
                    console.log('Testing file path:', filePath);
                    
                    // Show loading indicator
                    $('#loading').show();
                    $('#result').html('');
                    
                    $.ajax({
                        url: '/test_file_path',
                        type: 'POST',
                        data: {file_path: filePath},
                        success: function(response) {
                            console.log('Response:', response);
                            $('#loading').hide();
                            
                            if (response.error) {
                                $('#result').html(`<div class="alert alert-danger">${response.error}</div>`);
                                return;
                            }
                            
                            let resultHtml = `
                                <div class="alert alert-success">
                                    <h4>File exists: ${response.file_exists}</h4>
                                    <p>File path: ${response.file_path}</p>
                                    <p>File size: ${response.file_size} bytes</p>
                                </div>
                            `;
                            
                            if (response.text_sample) {
                                resultHtml += `
                                    <div class="card mt-3">
                                        <div class="card-header">Text Sample (first 500 chars)</div>
                                        <div class="card-body">
                                            <pre>${response.text_sample}</pre>
                                        </div>
                                    </div>
                                `;
                            }
                            
                            $('#result').html(resultHtml);
                        },
                        error: function(xhr, status, error) {
                            console.error('Error:', error);
                            $('#loading').hide();
                            $('#result').html(`<div class="alert alert-danger">Error: ${error}</div>`);
                        }
                    });
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/test_file_path', methods=['POST'])
def test_file_path():
    file_path = request.form.get('file_path')
    
    if not file_path:
        return jsonify({
            'error': 'No file path provided'
        })
    
    # Check if file exists
    file_exists = os.path.isfile(file_path)
    
    result = {
        'file_path': file_path,
        'file_exists': file_exists,
        'file_size': 0
    }
    
    if file_exists:
        result['file_size'] = os.path.getsize(file_path)
        
        # If it's a PDF, try to extract text
        if file_path.lower().endswith('.pdf'):
            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ''
                    for i, page in enumerate(reader.pages):
                        if i >= 1:  # Only extract text from the first page
                            break
                        text += page.extract_text() + '\n'
                    
                    result['text_sample'] = text[:500] + '...' if len(text) > 500 else text
            except Exception as e:
                result['error'] = f"Error extracting text from PDF: {str(e)}"
    else:
        result['error'] = f"File not found: {file_path}"
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
