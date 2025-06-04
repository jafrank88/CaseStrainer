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
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const resultDiv = document.getElementById('result');
                const startButton = document.getElementById('start');
                
                startButton.addEventListener('click', function() {
                    resultDiv.innerHTML = '<div>Connecting to event stream...</div>';
                    
                    // Create EventSource
                    const eventSource = new EventSource('/stream');
                    
                    // Connection opened
                    eventSource.onopen = function(event) {
                        resultDiv.innerHTML += '<div>Connection established!</div>';
                    };
                    
                    // Listen for messages
                    eventSource.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        resultDiv.innerHTML += `<div>Message received: ${data.message} (${data.timestamp})</div>`;
                        
                        // Close the connection after receiving the complete message
                        if (data.message === 'complete') {
                            eventSource.close();
                            resultDiv.innerHTML += '<div>Stream closed.</div>';
                        }
                    };
                    
                    // Error handling
                    eventSource.onerror = function(event) {
                        resultDiv.innerHTML += '<div style="color: red;">Error occurred. Connection closed.</div>';
                        eventSource.close();
                    };
                });
            });
        </script>
    </head>
    <body>
        <h1>Server-Sent Events Test</h1>
        <button id="start">Start Stream</button>
        <div id="result" style="margin-top: 20px; padding: 10px; border: 1px solid #ccc;"></div>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/stream")
def stream():
    def generate():
        # Send a message every second for 5 seconds
        for i in range(5):
            data = {"message": f"Message {i+1}", "timestamp": time.strftime("%H:%M:%S")}
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)

        # Send a final message
        data = {"message": "complete", "timestamp": time.strftime("%H:%M:%S")}
        yield f"data: {json.dumps(data)}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
