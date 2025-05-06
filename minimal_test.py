from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Minimal Test</title>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    </head>
    <body>
        <h1>Minimal Test</h1>
        <form id="test-form">
            <input type="text" id="text-input" name="text" value="test">
            <button type="submit">Submit</button>
        </form>
        <div id="result"></div>
        
        <script>
            $(document).ready(function() {
                $('#test-form').submit(function(event) {
                    event.preventDefault();
                    console.log('Form submitted');
                    
                    const text = $('#text-input').val();
                    console.log('Text:', text);
                    
                    $.ajax({
                        url: '/test',
                        type: 'POST',
                        data: {text: text},
                        success: function(response) {
                            console.log('Response:', response);
                            $('#result').html('Response: ' + JSON.stringify(response));
                        },
                        error: function(xhr, status, error) {
                            console.error('Error:', error);
                            $('#result').html('Error: ' + error);
                        }
                    });
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/test', methods=['POST'])
def test():
    print("==== TEST ENDPOINT CALLED =====")
    print(f"Request method: {request.method}")
    print(f"Request form: {request.form}")
    
    text = request.form.get('text', '')
    print(f"Received text: {text}")
    
    return jsonify({
        'status': 'success',
        'message': f'Received: {text}'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
