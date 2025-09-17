"""
Test script to diagnose import issues in the worker environment.
"""
import os
import sys
import importlib
import json
from typing import Dict, Any

def test_imports() -> Dict[str, Dict[str, Any]]:
    """Test if required modules can be imported."""
    modules = [
        'unified_extraction_architecture',
        'models',
        'src.unified_extraction_architecture',
        'src.models',
        'src.worker_tasks',
        'rq',
        'redis',
        'flask',
        'sqlalchemy',
        'requests',
        'numpy',
        'pandas'
    ]
    
    results = {}
    
    # First, try to import from src directory
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    # Test each module
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
                'error': str(e),
                'python_path': sys.path,
                'cwd': os.getcwd()
            }
    
    # Add system information
    results['_system'] = {
        'python_version': sys.version,
        'python_path': sys.path,
        'cwd': os.getcwd(),
        'env': {k: v for k, v in os.environ.items() if 'PASS' not in k and 'KEY' not in k}
    }
    
    return results

if __name__ == "__main__":
    results = test_imports()
    print(json.dumps(results, indent=2, default=str))
