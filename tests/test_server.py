from flask import Flask, render_template_string

app = Flask(__name__)


@app.route("/")
def home():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CaseStrainer Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            .header {
                background-color: #0055ff;
                color: white;
                padding: 30px;
                text-align: center;
                font-size: 28px;
                font-weight: bold;
                position: relative;
            }
            .version {
                position: absolute;
                top: 10px;
                right: 10px;
                background-color: red;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 18px;
            }
            .content {
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
            }
            .success {
                background-color: #d4edda;
                color: #155724;
                padding: 20px;
                border-radius: 5px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            CaseStrainer Test Server
            <div class="version">VERSION 3.0.0</div>
        </div>
        
        <div class="content">
            <h1>Test Server Running Successfully</h1>
            <p>If you can see this page with:</p>
            <ul>
                <li>A bright blue header bar at the top</li>
                <li>A red "VERSION 3.0.0" badge in the top right</li>
            </ul>
            <div class="success">
                <h2>Success!</h2>
                <p>The test server is working correctly and you're seeing the latest version.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


if __name__ == "__main__":
    print("Starting test server on port 5005...")
    print("Access the test page at: http://127.0.0.1:5005")
    app.run(host="0.0.0.0", port=5005, debug=True)
