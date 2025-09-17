#!/usr/bin/env python3
"""
Test script to check the worker environment and dependencies.
"""
import os
import sys
import json
import importlib
from typing import Dict, Any

def check_imports() -> Dict[str, Any]:
    """Check if required modules can be imported."""
    modules = [
        'unified_extraction_architecture',
        'models',
        'worker_tasks',
        'rq',
        'redis',
        'flask',
        'sqlalchemy',
        'requests',
        'numpy',
        'pandas'
    ]
    
    results = {}
    
    # Add the src directory to the Python path
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
    if os.path.exists(src_dir) and src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    # Check each module
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            results[module_name] = {
                'status': 'success',
                'path': getattr(module, '__file__', 'unknown'),
                'version': getattr(module, '__version__', 'unknown')
            }
        except Exception as e:
            results[module_name] = {
                'status': 'error',
                'error': str(e)
            }
    
    # Add system information
    results['_system'] = {
        'python_version': sys.version,
        'python_path': sys.path,
        'cwd': os.getcwd(),
        'env': {k: v for k, v in os.environ.items() 
               if 'PASS' not in k and 'KEY' not in k and 'TOKEN' not in k}
    }
    
    return results

def main():
    """Main function to run the tests."""
    try:
        results = check_imports()
        print(json.dumps(results, indent=2, default=str))
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
