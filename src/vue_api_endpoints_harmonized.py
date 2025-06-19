import os
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, make_response, current_app

vue_api = Blueprint('vue_api', __name__)

def make_error_response(error_type, message, details=None, source_type=None, source_name=None, status_code=400, metadata=None):
    response = {
        'status': 'error',
        'error_type': error_type,
        'message': message,
        'details': details,
        'source_type': source_type,
        'source_name': source_name,
        'metadata': metadata or {}
    }
    return jsonify(response), status_code

@vue_api.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    """
    Harmonized API endpoint for document analysis and citation verification.
    Handles file uploads, direct text, URLs, and single citation analysis.
    """
    start_time = time.time()
    source_type = None
    source_name = None
    file_ext = None
    content_type = None
    text = None
    try:
        # Robust debug logging
        debug_log_path = '/tmp/analyze_debug.log'
        with open(debug_log_path, 'a') as f:
            f.write(f"[ANALYZE] Received {request.method} request to /api/analyze\n")
            f.write(f"[ANALYZE] RAW request.data: {request.data}\n")
            f.write(f"[ANALYZE] request.get_json(silent=True): {request.get_json(silent=True)}\n")
            f.write(f"[ANALYZE] request.form: {request.form.to_dict() if request.form else 'No form data'}\n")
            f.write(f"[ANALYZE] request.files: {list(request.files.keys()) if request.files else 'No files'}\n")
            f.write(f"[ANALYZE] Headers: {dict(request.headers)}\n")

        # Handle OPTIONS request for CORS preflight
        if request.method == 'OPTIONS':
            response = make_response(jsonify({'status': 'ok'}), 200)
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response

        # Parse input type
        input_type = None
        data = None
        if request.is_json:
            data = request.get_json(silent=True) or {}
            input_type = data.get('type')
        elif request.form:
            data = request.form.to_dict()
            input_type = data.get('type')
        else:
            data = {}

        # Handle file upload (multipart/form-data)
        if (input_type == 'file' and 'file' in request.files) or ('file' in request.files):
            file = request.files['file']
            filename = file.filename
            file_ext = os.path.splitext(filename)[1].lower()
            from src.file_utils import extract_text_from_file
            try:
                text = extract_text_from_file(file, file_ext=file_ext)
            except Exception as e:
                processing_time = time.time() - start_time
                metadata = {
                    "source_type": "file",
                    "source_name": filename,
                    "length": 0,
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "file_type": file_ext,
                    "user_agent": request.headers.get("User-Agent")
                }
                return make_error_response(
                    "pdf_extraction" if file_ext == ".pdf" else "file_extraction",
                    f"Failed to extract text from file ({filename})",
                    details=str(e),
                    source_type="file",
                    source_name=filename,
                    status_code=400,
                    metadata=metadata
                )
            source_type = 'file'
            source_name = filename
        # Handle URL input
        elif input_type == 'url' or ('url' in data and data['url']):
            from src.enhanced_validator_production import extract_text_from_url
            url = data.get('url')
            try:
                text_result = extract_text_from_url(url)
                content_type = text_result.get('content_type')
            except Exception as e:
                processing_time = time.time() - start_time
                metadata = {
                    "source_type": "url",
                    "source_name": url,
                    "length": 0,
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "content_type": content_type,
                    "user_agent": request.headers.get("User-Agent")
                }
                return make_error_response(
                    "url_fetch",
                    f"Failed to fetch or process URL: {url}",
                    details=str(e),
                    source_type="url",
                    source_name=url,
                    status_code=400,
                    metadata=metadata
                )
            if text_result.get('status') != 'success' or not text_result.get('text'):
                processing_time = time.time() - start_time
                metadata = {
                    "source_type": "url",
                    "source_name": url,
                    "length": 0,
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "content_type": content_type,
                    "user_agent": request.headers.get("User-Agent")
                }
                return make_error_response(
                    "url_extraction",
                    text_result.get('error', 'Failed to extract text from URL'),
                    details=text_result.get('details'),
                    source_type="url",
                    source_name=url,
                    status_code=400,
                    metadata=metadata
                )
            text = text_result['text']
            source_type = 'url'
            source_name = url
        # Handle pasted text
        elif input_type == 'text' or ('text' in data and data['text']):
            text = data.get('text')
            if not text or not isinstance(text, str):
                processing_time = time.time() - start_time
                metadata = {
                    "source_type": "text",
                    "source_name": "pasted_text",
                    "length": 0,
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "user_agent": request.headers.get("User-Agent")
                }
                return make_error_response(
                    "input_validation",
                    "No valid text provided.",
                    source_type="text",
                    source_name="pasted_text",
                    status_code=400,
                    metadata=metadata
                )
            source_type = 'text'
            source_name = 'pasted_text'
        # Handle single citation
        elif input_type == 'citation' or ('citation' in data and data['citation']):
            citation = data.get('citation')
            if not citation or not isinstance(citation, str):
                processing_time = time.time() - start_time
                metadata = {
                    "source_type": "citation",
                    "source_name": "single_citation",
                    "length": 0,
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "user_agent": request.headers.get("User-Agent")
                }
                return make_error_response(
                    "input_validation",
                    "No valid citation provided.",
                    source_type="citation",
                    source_name="single_citation",
                    status_code=400,
                    metadata=metadata
                )
            text = citation
            source_type = 'citation'
            source_name = 'single_citation'
        else:
            processing_time = time.time() - start_time
            metadata = {
                "source_type": None,
                "source_name": None,
                "length": 0,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "user_agent": request.headers.get("User-Agent")
            }
            return make_error_response(
                "input_validation",
                "No valid input provided. Please provide a file, text, url, or citation.",
                status_code=400,
                metadata=metadata
            )

        # Format assessment & conversion to markdown if needed
        from src.enhanced_validator_production import preprocess_markdown
        try:
            text = preprocess_markdown(text)
        except Exception as e:
            processing_time = time.time() - start_time
            metadata = {
                "source_type": source_type,
                "source_name": source_name,
                "length": len(text) if text else 0,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "file_type": file_ext if source_type == "file" else None,
                "content_type": content_type if source_type == "url" else None,
                "user_agent": request.headers.get("User-Agent")
            }
            return make_error_response(
                "markdown_conversion",
                "Failed to preprocess text as markdown.",
                details=str(e),
                status_code=500,
                metadata=metadata
            )

        # --- Insert your citation extraction, chunking, deduplication, and verification logic here ---
        # For demonstration, return a dummy response
        processing_time = time.time() - start_time
        metadata = {
            "source_type": source_type,
            "source_name": source_name,
            "length": len(text) if text else 0,
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "file_type": file_ext if source_type == "file" else None,
            "content_type": content_type if source_type == "url" else None,
            "user_agent": request.headers.get("User-Agent")
        }
        return jsonify({
            'status': 'success',
            'citations': [],  # Replace with actual results
            'stats': {},
            'metadata': metadata,
            'errors': []
        })
    except Exception as e:
        processing_time = time.time() - start_time
        metadata = {
            "source_type": source_type,
            "source_name": source_name,
            "length": len(text) if text else 0,
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "file_type": file_ext if source_type == "file" else None,
            "content_type": content_type if source_type == "url" else None,
            "user_agent": request.headers.get("User-Agent")
        }
        return make_error_response(
            "internal",
            "An internal server error occurred.",
            details=str(e),
            status_code=500,
            metadata=metadata
        ) 