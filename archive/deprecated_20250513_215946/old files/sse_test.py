from flask import Flask, Response, render_template_string
import time
import json

app = Flask(__name__)


@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SSE Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            #events-container {
                height: 300px;
                overflow-y: auto;
                border: 1px solid #ddd;
                padding: 10px;
                margin-top: 20px;
                background-color: #f8f9fa;
            }
            .event-item {
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 5px;
            }
            .event-started { background-color: #d1e7dd; }
            .event-progress { background-color: #cfe2ff; }
            .event-result { background-color: #fff3cd; }
            .event-complete { background-color: #d1e7dd; }
            .event-error { background-color: #f8d7da; }
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <h1>Server-Sent Events Test</h1>
            <p>This page tests if Server-Sent Events (SSE) are working correctly.</p>
            
            <div class="row">
                <div class="col-md-6">
                    <button id="start-test" class="btn btn-primary">Start SSE Test</button>
                    <button id="stop-test" class="btn btn-danger ms-2" disabled>Stop Connection</button>
                </div>
                <div class="col-md-6">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="auto-reconnect" checked>
                        <label class="form-check-label" for="auto-reconnect">
                            Auto-reconnect if connection lost
                        </label>
                    </div>
                </div>
            </div>
            
            <div class="mt-3">
                <div class="alert alert-info" id="connection-status">
                    Not connected
                </div>
            </div>
            
            <h3 class="mt-4">Events Received:</h3>
            <div id="events-container"></div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const startButton = document.getElementById('start-test');
                const stopButton = document.getElementById('stop-test');
                const autoReconnect = document.getElementById('auto-reconnect');
                const connectionStatus = document.getElementById('connection-status');
                const eventsContainer = document.getElementById('events-container');
                
                let eventSource = null;
                let reconnectAttempts = 0;
                const MAX_RECONNECT_ATTEMPTS = 5;
                
                function setupEventSource() {
                    // Close any existing connection
                    if (eventSource) {
                        eventSource.close();
                        eventSource = null;
                    }
                    
                    // Update UI
                    connectionStatus.className = 'alert alert-info';
                    connectionStatus.textContent = 'Connecting...';
                    
                    // Create new EventSource
                    eventSource = new EventSource('/sse-stream');
                    
                    // Event handlers
                    eventSource.onopen = function(e) {
                        console.log('Connection opened', e);
                        connectionStatus.className = 'alert alert-success';
                        connectionStatus.textContent = 'Connected';
                        startButton.disabled = true;
                        stopButton.disabled = false;
                        reconnectAttempts = 0;
                        
                        addEventToLog('system', 'Connection established');
                    };
                    
                    eventSource.onerror = function(e) {
                        console.error('EventSource error:', e);
                        connectionStatus.className = 'alert alert-danger';
                        connectionStatus.textContent = 'Connection error';
                        
                        addEventToLog('error', 'Connection error occurred');
                        
                        // Auto-reconnect logic
                        if (autoReconnect.checked && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                            reconnectAttempts++;
                            const delay = Math.min(1000 * reconnectAttempts, 5000);
                            
                            connectionStatus.textContent = `Connection error. Reconnecting in ${delay/1000} seconds... (Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`;
                            
                            setTimeout(function() {
                                if (eventSource) {
                                    eventSource.close();
                                    eventSource = null;
                                }
                                setupEventSource();
                            }, delay);
                        } else {
                            startButton.disabled = false;
                            stopButton.disabled = true;
                        }
                    };
                    
                    // Listen for different event types
                    eventSource.addEventListener('started', function(e) {
                        handleEvent('started', e);
                    });
                    
                    eventSource.addEventListener('progress', function(e) {
                        handleEvent('progress', e);
                    });
                    
                    eventSource.addEventListener('result', function(e) {
                        handleEvent('result', e);
                    });
                    
                    eventSource.addEventListener('complete', function(e) {
                        handleEvent('complete', e);
                    });
                    
                    eventSource.addEventListener('error', function(e) {
                        handleEvent('error', e);
                    });
                    
                    // Default message handler
                    eventSource.onmessage = function(e) {
                        console.log('Default message received:', e.data);
                        addEventToLog('default', e.data);
                    };
                }
                
                function handleEvent(type, event) {
                    console.log(`${type} event received:`, event.data);
                    try {
                        const data = JSON.parse(event.data);
                        addEventToLog(type, data);
                    } catch (e) {
                        console.error('Error parsing event data:', e);
                        addEventToLog(type, event.data, true);
                    }
                }
                
                function addEventToLog(type, data, isError = false) {
                    const eventItem = document.createElement('div');
                    eventItem.className = `event-item event-${type}`;
                    
                    const timestamp = new Date().toLocaleTimeString();
                    let content = '';
                    
                    if (isError) {
                        content = `<strong>[${timestamp}] ${type.toUpperCase()}:</strong> Error parsing data: ${data}`;
                    } else if (typeof data === 'object') {
                        content = `<strong>[${timestamp}] ${type.toUpperCase()}:</strong> <pre>${JSON.stringify(data, null, 2)}</pre>`;
                    } else {
                        content = `<strong>[${timestamp}] ${type.toUpperCase()}:</strong> ${data}`;
                    }
                    
                    eventItem.innerHTML = content;
                    eventsContainer.appendChild(eventItem);
                    eventsContainer.scrollTop = eventsContainer.scrollHeight;
                }
                
                // Button event handlers
                startButton.addEventListener('click', function() {
                    setupEventSource();
                });
                
                stopButton.addEventListener('click', function() {
                    if (eventSource) {
                        eventSource.close();
                        eventSource = null;
                    }
                    
                    connectionStatus.className = 'alert alert-warning';
                    connectionStatus.textContent = 'Disconnected';
                    startButton.disabled = false;
                    stopButton.disabled = true;
                    
                    addEventToLog('system', 'Connection closed by user');
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/sse-stream")
def sse_stream():
    def generate():
        # Send initial event
        yield 'event: started\ndata: {"status": "started", "total_citations": 3}\n\n'
        time.sleep(1)

        # Send progress events
        for i in range(1, 4):
            yield f'event: progress\ndata: {{"status": "progress", "current": {i}, "total": 3, "message": "Processing citation {i} of 3"}}\n\n'
            time.sleep(1)

        # Send result events
        citations = [
            {
                "citation_text": "347 U.S. 483",
                "is_hallucinated": False,
                "confidence": 0.95,
                "explanation": "This is a real citation to Brown v. Board of Education.",
            },
            {
                "citation_text": "410 U.S. 113",
                "is_hallucinated": False,
                "confidence": 0.92,
                "explanation": "This is a real citation to Roe v. Wade.",
            },
            {
                "citation_text": "2099 WL 123456",
                "is_hallucinated": True,
                "confidence": 0.88,
                "explanation": "This appears to be a hallucinated citation as the year 2099 is in the future.",
            },
        ]

        for i, citation in enumerate(citations):
            yield f'event: result\ndata: {{"status": "result", "citation_index": {i}, "result": {json.dumps(citation)}, "total": 3}}\n\n'
            time.sleep(1)

        # Send complete event
        yield 'event: complete\ndata: {"status": "complete", "total_citations": 3, "hallucinated_count": 1, "message": "Analysis complete"}\n\n'

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
