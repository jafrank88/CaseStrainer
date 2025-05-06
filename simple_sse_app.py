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
        <title>Simple SSE Test</title>
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
        <h1>Simple Server-Sent Events Test</h1>
        <button id="connect">Connect to SSE</button>
        <button id="disconnect" disabled>Disconnect</button>
        <div id="log"></div>

        <script>
            const connectBtn = document.getElementById('connect');
            const disconnectBtn = document.getElementById('disconnect');
            const logDiv = document.getElementById('log');
            
            let eventSource = null;
            
            function log(message, type = 'info') {
                const div = document.createElement('div');
                div.className = type;
                div.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
                logDiv.appendChild(div);
                logDiv.scrollTop = logDiv.scrollHeight;
            }
            
            connectBtn.addEventListener('click', function() {
                // Close any existing connection
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                
                log('Connecting to SSE endpoint...', 'info');
                
                try {
                    // Create a new EventSource connection
                    eventSource = new EventSource('/stream');
                    
                    // Connection opened
                    eventSource.onopen = function(event) {
                        log('Connection established!', 'success');
                        connectBtn.disabled = true;
                        disconnectBtn.disabled = false;
                    };
                    
                    // Listen for messages
                    eventSource.onmessage = function(event) {
                        try {
                            const data = JSON.parse(event.data);
                            log(`Received message: ${JSON.stringify(data)}`, 'success');
                        } catch (error) {
                            log(`Error parsing message: ${event.data}`, 'error');
                        }
                    };
                    
                    // Error handling
                    eventSource.onerror = function(event) {
                        log('Error occurred. Connection closed.', 'error');
                        connectBtn.disabled = false;
                        disconnectBtn.disabled = true;
                        eventSource.close();
                        eventSource = null;
                    };
                } catch (error) {
                    log(`Error creating EventSource: ${error.message}`, 'error');
                }
            });
            
            disconnectBtn.addEventListener('click', function() {
                if (eventSource) {
                    log('Disconnecting...', 'info');
                    eventSource.close();
                    eventSource = null;
                    connectBtn.disabled = false;
                    disconnectBtn.disabled = true;
                }
            });
            
            // Log initial state
            log('Page loaded. Click "Connect to SSE" to start.', 'info');
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/stream')
def stream():
    def generate():
        # Send a message every second for 5 seconds
        for i in range(5):
            data = {
                'message': f'Message {i+1}',
                'timestamp': time.strftime('%H:%M:%S')
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)
        
        # Send a final message
        data = {
            'message': 'complete',
            'timestamp': time.strftime('%H:%M:%S')
        }
        yield f"data: {json.dumps(data)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
