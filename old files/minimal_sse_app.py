from flask import Flask, Response, render_template_string
import time
import json

app = Flask(__name__)

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Minimal SSE Test</title>
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
        <h1>Minimal Server-Sent Events Test</h1>
        <button id="connect">Connect to SSE</button>
        <div id="log"></div>

        <script>
            const connectBtn = document.getElementById('connect');
            const logDiv = document.getElementById('log');
            
            function log(message, type = 'info') {
                const div = document.createElement('div');
                div.className = type;
                div.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
                logDiv.appendChild(div);
                logDiv.scrollTop = logDiv.scrollHeight;
            }
            
            connectBtn.addEventListener('click', function() {
                log('Connecting to SSE endpoint...', 'info');
                
                try {
                    // Create a new EventSource connection
                    const eventSource = new EventSource('/events');
                    
                    // Connection opened
                    eventSource.onopen = function(event) {
                        log('Connection established!', 'success');
                    };
                    
                    // Listen for messages
                    eventSource.addEventListener('message', function(event) {
                        try {
                            const data = JSON.parse(event.data);
                            log(`Received message: ${JSON.stringify(data)}`, 'success');
                        } catch (error) {
                            log(`Received raw message: ${event.data}`, 'info');
                        }
                    });
                    
                    // Error handling
                    eventSource.onerror = function(event) {
                        log('Error occurred with EventSource', 'error');
                    };
                } catch (error) {
                    log(`Error creating EventSource: ${error.message}`, 'error');
                }
            });
            
            // Log initial state
            log('Page loaded. Click "Connect to SSE" to start.', 'info');
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/events')
def events():
    def generate():
        yield "data: Hello SSE World!\\n\\n"
        time.sleep(1)
        
        for i in range(5):
            data = {
                'count': i,
                'message': f'Message {i+1}',
                'time': time.strftime('%H:%M:%S')
            }
            yield f"data: {json.dumps(data)}\\n\\n"
            time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
