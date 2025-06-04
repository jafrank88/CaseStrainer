from flask import Flask, request, jsonify, render_template_string
import re
import os
import PyPDF2

app = Flask(__name__)


# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return f"Error: {str(e)}"


# Function to extract citations
def extract_citations(text):
    # Normalize the text to make citation matching more reliable
    text = re.sub(r"\s+", " ", text)

    # Example patterns for common citation formats
    patterns = [
        # US Reports (e.g., 347 U.S. 483)
        r"\b\d+\s+U\.?\s*S\.?\s+\d+\b",
        # Supreme Court Reporter (e.g., 98 S.Ct. 2733)
        r"\b\d+\s+S\.?\s*Ct\.?\s+\d+\b",
        # Federal Reporter (e.g., 410 F.2d 701, 723 F.3d 1067)
        r"\b\d+\s+F\.?\s*(?:2d|3d)?\s+\d+\b",
        # Federal Supplement (e.g., 595 F.Supp.2d 735)
        r"\b\d+\s+F\.?\s*Supp\.?\s*(?:2d|3d)?\s+\d+\b",
        # Westlaw citations (e.g., 2011 WL 2160468)
        r"\b\d{4}\s+WL\s+\d+\b",
    ]

    citations = []
    for pattern in patterns:
        try:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citation = match.group(0).strip()
                if citation not in citations:
                    citations.append(citation)
        except Exception as e:
            print(f"Error searching for pattern {pattern}: {e}")

    return citations


@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Citation Extractor Test</title>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Citation Extractor Test</h1>
            <form id="test-form" class="mb-4">
                <div class="mb-3">
                    <label for="file-path" class="form-label">PDF File Path:</label>
                    <input type="text" class="form-control" id="file-path" name="file_path" 
                           value="C:/Users/jafrank/Downloads/gov.uscourts.wyd.64014.141.0_1.pdf">
                </div>
                <button type="submit" class="btn btn-primary">Extract Citations</button>
            </form>
            
            <div id="loading" style="display: none;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Processing...</span>
            </div>
            
            <div id="result" class="mt-4"></div>
        </div>
        
        <script>
            $(document).ready(function() {
                $('#test-form').submit(function(event) {
                    event.preventDefault();
                    console.log('Form submitted');
                    
                    const filePath = $('#file-path').val();
                    console.log('File path:', filePath);
                    
                    // Show loading indicator
                    $('#loading').show();
                    $('#result').html('');
                    
                    $.ajax({
                        url: '/extract_citations',
                        type: 'POST',
                        data: {file_path: filePath},
                        success: function(response) {
                            console.log('Response:', response);
                            $('#loading').hide();
                            
                            if (response.error) {
                                $('#result').html(`<div class="alert alert-danger">${response.error}</div>`);
                                return;
                            }
                            
                            // Display the extracted text sample
                            let resultHtml = `
                                <div class="card mb-4">
                                    <div class="card-header">Extracted Text Sample (first 500 chars)</div>
                                    <div class="card-body">
                                        <pre>${response.text_sample}</pre>
                                    </div>
                                </div>
                            `;
                            
                            // Display the citations
                            resultHtml += `
                                <div class="card">
                                    <div class="card-header">Extracted Citations (${response.citations.length})</div>
                                    <div class="card-body">
                                        <ol>
                                            ${response.citations.map(citation => `<li>${citation}</li>`).join('')}
                                        </ol>
                                    </div>
                                </div>
                            `;
                            
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


@app.route("/extract_citations", methods=["POST"])
def extract_citations_endpoint():
    try:
        file_path = request.form.get("file_path")

        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": f"File not found: {file_path}"})

        # Extract text from PDF
        text = extract_text_from_pdf(file_path)

        # Extract citations
        citations = extract_citations(text)

        # Save the extracted text to a file for inspection
        with open("extracted_text_simple.txt", "w", encoding="utf-8") as f:
            f.write(text)

        # Save the extracted citations to a file for inspection
        with open("extracted_citations_simple.txt", "w", encoding="utf-8") as f:
            for i, citation in enumerate(citations):
                f.write(f"{i+1}. {citation}\n")

        return jsonify(
            {
                "text_sample": text[:500] + "...",
                "citations": citations,
                "total_citations": len(citations),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/test", methods=["POST"])
def test():
    print("==== TEST ENDPOINT CALLED =====")
    print(f"Request method: {request.method}")
    print(f"Request form: {request.form}")

    text = request.form.get("text", "")
    print(f"Received text: {text}")

    return jsonify({"status": "success", "message": f"Received: {text}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
