#!/usr/bin/env python3
"""
Quick fix for Redis URL syntax errors in vue_api_endpoints.py
"""

import re

def fix_redis_syntax():
    """Fix indentation and syntax errors in vue_api_endpoints.py"""
    file_path = 'src/vue_api_endpoints.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the specific indentation issues
    fixes = [
        # Fix task status section
        (r'        # Use correct Redis URL for local development \(Docker port mapping\)\n            redis_url = os\.environ\.get\(\'REDIS_URL\', \'redis://localhost:6380/0\'\)\n        redis_conn = Redis\.from_url\(redis_url\)',
         '        # Use correct Redis URL for local development (Docker port mapping)\n        redis_url = os.environ.get(\'REDIS_URL\', \'redis://localhost:6380/0\')\n        redis_conn = Redis.from_url(redis_url)'),
        
        # Fix any other similar patterns
        (r'            # Use correct Redis URL for local development \(Docker port mapping\)\n            redis_url = os\.environ\.get\(\'REDIS_URL\', \'redis://localhost:6380/0\'\)\n                redis_conn = Redis\.from_url\(redis_url\)',
         '                # Use correct Redis URL for local development (Docker port mapping)\n                redis_url = os.environ.get(\'REDIS_URL\', \'redis://localhost:6380/0\')\n                redis_conn = Redis.from_url(redis_url)'),
    ]
    
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Write the fixed content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed Redis syntax errors in vue_api_endpoints.py")

if __name__ == "__main__":
    fix_redis_syntax()
