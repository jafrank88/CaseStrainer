from flask import Flask, jsonify
import sys
import os

print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("Files in directory:", os.listdir('.'))

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/test')
def test():
    return jsonify({"status": "success", "message": "Test endpoint works!"})

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
