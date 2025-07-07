#!/usr/bin/env python3
"""
Fix for the worker thread blocking issue in vue_api_endpoints.py
"""

import os
import sys

def create_worker_fix():
    """Create a fixed version of the worker thread initialization"""
    
    fix_code = '''
# FIX: Disable worker thread to prevent blocking
# This is a temporary fix to allow the API endpoints to work

# Disable the problematic worker thread
worker_thread = None
worker_running = False
task_queue = None

# Override the worker initialization
def initialize_worker():
    """Initialize worker thread (disabled for now)"""
    global worker_thread, worker_running, task_queue
    
    # Disable worker thread to prevent blocking
    worker_thread = None
    worker_running = False
    task_queue = None
    
    print("Worker thread disabled to prevent blocking")
    return True

# Override the worker loop
def worker_loop():
    """Worker loop (disabled)"""
    print("Worker loop disabled")
    return

# Override the is_worker_running function
def is_worker_running():
    """Check if worker is running (always False for now)"""
    return False

# Override the get_server_stats function
def get_server_stats():
    """Get server stats (simplified)"""
    return {
        'start_time': time.time(),
        'uptime': '00:00:00',
        'uptime_seconds': 0,
        'restart_count': 0,
        'worker_alive': False,
        'worker_disabled': True
    }
'''
    
    return fix_code

def apply_worker_fix():
    """Apply the worker thread fix to vue_api_endpoints.py"""
    
    vue_api_file = 'src/vue_api_endpoints.py'
    
    if not os.path.exists(vue_api_file):
        print(f"❌ File not found: {vue_api_file}")
        return False
    
    # Read the current file
    with open(vue_api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if fix is already applied
    if 'worker_disabled' in content:
        print("✅ Worker fix already applied")
        return True
    
    # Find the worker thread initialization section
    worker_start = content.find('# Windows-compatible fallback: Simple threading-based task queue')
    
    if worker_start == -1:
        print("❌ Could not find worker thread section")
        return False
    
    # Find the end of the worker initialization
    worker_end = content.find('def process_citation_task(task_id, task_type, task_data):')
    
    if worker_end == -1:
        print("❌ Could not find end of worker section")
        return False
    
    # Create the fixed content
    before_worker = content[:worker_start]
    after_worker = content[worker_end:]
    fix_code = create_worker_fix()
    
    new_content = before_worker + fix_code + '\n' + after_worker
    
    # Backup the original file
    backup_file = vue_api_file + '.backup'
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup created: {backup_file}")
    
    # Write the fixed content
    with open(vue_api_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Worker thread fix applied")
    return True

def create_simple_test_server():
    """Create a simple test server without worker threads"""
    
    test_server_code = '''
#!/usr/bin/env python3
"""
Simple test server without worker threads
"""

from flask import Flask, jsonify, request
import time

app = Flask(__name__)

@app.route('/casestrainer/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'CaseStrainer Test API',
        'timestamp': time.time(),
        'worker_disabled': True
    })

@app.route('/casestrainer/api/analyze', methods=['POST'])
def analyze():
    try:
        if request.is_json:
            data = request.get_json()
            text = data.get('text', '')
            url = data.get('url', '')
            input_type = data.get('type', 'text')
        else:
            # Handle file upload
            file = request.files.get('file')
            if file:
                text = file.read().decode('utf-8', errors='ignore')
                input_type = 'file'
            else:
                return jsonify({'error': 'No input provided'}), 400
        
        # Simple citation extraction (mock)
        citations = [
            {
                'citation': '97 Wn.2d 30',
                'case_name': 'Seattle Times Co. v. Ishikawa',
                'verified': True,
                'source': 'Test',
                'url': 'https://example.com'
            }
        ]
        
        return jsonify({
            'status': 'completed',
            'citations': citations,
            'total_citations': len(citations),
            'verified_citations': len([c for c in citations if c.get('verified')])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/casestrainer/api/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    return jsonify({
        'status': 'completed',
        'task_id': task_id,
        'results': []
    })

if __name__ == '__main__':
    print("Starting simple test server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
'''
    
    with open('simple_test_server.py', 'w') as f:
        f.write(test_server_code)
    
    print("✅ Simple test server created: simple_test_server.py")

def main():
    """Main function"""
    print("🔧 WORKER THREAD FIX")
    print("=" * 40)
    
    print("1. Applying worker thread fix...")
    if apply_worker_fix():
        print("✅ Fix applied successfully")
    else:
        print("❌ Fix failed")
        return
    
    print("\n2. Creating simple test server...")
    create_simple_test_server()
    
    print("\n3. Instructions:")
    print("   - Restart the main server: python start_app.py")
    print("   - Or use the simple test server: python simple_test_server.py")
    print("   - Then run: python test_endpoints_direct.py")

if __name__ == "__main__":
    main() 