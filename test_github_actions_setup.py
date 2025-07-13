#!/usr/bin/env python3
"""
Test script to verify GitHub Actions setup for CaseStrainer.
This script runs basic checks that should pass in the CI environment.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def test_python_environment():
    """Test that Python environment is set up correctly."""
    print("🐍 Testing Python environment...")
    
    # Check Python version
    version = sys.version_info
    print(f"   Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 8:
        print("   ❌ Python 3.8+ required")
        return False
    
    print("   ✅ Python version OK")
    return True

def test_required_packages():
    """Test that required packages are available."""
    print("📦 Testing required packages...")
    
    required_packages = [
        'flask',
        'redis',
        'rq',
        'requests',
        'pytest',
        'eyecite',
        'courts-db',
        'reporters-db'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"   ❌ Missing packages: {', '.join(missing_packages)}")
        return False
    
    print("   ✅ All required packages available")
    return True

def test_file_structure():
    """Test that required files and directories exist."""
    print("📁 Testing file structure...")
    
    required_files = [
        'requirements.txt',
        'docker-compose.yml',
        'src/app_final_vue.py',
        'casestrainer-vue-new/package.json',
        'casestrainer-vue-new/Dockerfile.prod'
    ]
    
    required_dirs = [
        'src',
        'casestrainer-vue-new/src',
        '.github/workflows'
    ]
    
    missing_items = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"   ❌ {file_path} - missing")
            missing_items.append(file_path)
        else:
            print(f"   ✅ {file_path}")
    
    for dir_path in required_dirs:
        if not Path(dir_path).is_dir():
            print(f"   ❌ {dir_path} - missing")
            missing_items.append(dir_path)
        else:
            print(f"   ✅ {dir_path}")
    
    if missing_items:
        print(f"   ❌ Missing items: {', '.join(missing_items)}")
        return False
    
    print("   ✅ File structure OK")
    return True

def test_github_actions_files():
    """Test that GitHub Actions workflow files exist."""
    print("🔧 Testing GitHub Actions setup...")
    
    workflow_files = [
        '.github/workflows/ci.yml',
        '.github/workflows/pr-check.yml',
        '.github/workflows/deploy.yml',
        '.github/README.md'
    ]
    
    missing_files = []
    
    for workflow_file in workflow_files:
        if not Path(workflow_file).exists():
            print(f"   ❌ {workflow_file} - missing")
            missing_files.append(workflow_file)
        else:
            print(f"   ✅ {workflow_file}")
    
    if missing_files:
        print(f"   ❌ Missing workflow files: {', '.join(missing_files)}")
        return False
    
    print("   ✅ GitHub Actions setup OK")
    return True

def test_basic_imports():
    """Test that core modules can be imported."""
    print("🔌 Testing basic imports...")
    
    try:
        # Test core application imports
        sys.path.insert(0, 'src')
        
        # Test basic Flask app import
        from app_final_vue import app
        print("   ✅ Flask app import OK")
        
        # Test citation processing imports
        from unified_citation_processor_v2 import process_citations
        print("   ✅ Citation processor import OK")
        
        # Test case name extraction
        from case_name_extraction_core import extract_case_name_triple_comprehensive
        print("   ✅ Case name extraction import OK")
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False
    
    print("   ✅ All core imports OK")
    return True

def test_environment_variables():
    """Test that environment variables are set correctly."""
    print("🌍 Testing environment variables...")
    
    # Check if we're in CI environment
    if os.getenv('CI'):
        print("   ✅ Running in CI environment")
        
        # Check for required CI variables
        ci_vars = ['GITHUB_WORKFLOW', 'GITHUB_RUN_ID']
        for var in ci_vars:
            if os.getenv(var):
                print(f"   ✅ {var} = {os.getenv(var)}")
            else:
                print(f"   ⚠️  {var} not set")
    else:
        print("   ℹ️  Running in local environment")
    
    # Check application-specific variables
    app_vars = ['FLASK_ENV', 'CASTRAINER_ENV', 'REDIS_URL']
    for var in app_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var} = {value}")
        else:
            print(f"   ⚠️  {var} not set")
    
    print("   ✅ Environment variables check complete")
    return True

def main():
    """Run all tests and report results."""
    print("🚀 CaseStrainer GitHub Actions Setup Test")
    print("=" * 50)
    
    tests = [
        test_python_environment,
        test_required_packages,
        test_file_structure,
        test_github_actions_files,
        test_basic_imports,
        test_environment_variables
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! GitHub Actions setup is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 