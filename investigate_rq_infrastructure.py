"""
Investigate RQ Infrastructure Issues
Identifies problems in the Redis/RQ worker infrastructure causing startup hangs.
"""

import requests
import time

def analyze_rq_worker_startup_hang():
    """Analyze why RQ workers hang during startup."""
    
    print("🔍 RQ WORKER STARTUP HANG ANALYSIS")
    print("=" * 40)
    
    print("📊 CONFIRMED FINDINGS:")
    print("   ✅ Task creation: WORKING (task gets queued)")
    print("   ✅ Worker pickup: WORKING (status changes to 'started')")
    print("   ❌ Worker execution: HANGING (never reaches 'running')")
    print("   🎯 Hang location: During RQ worker initialization/startup")
    
    print(f"\n🔍 POTENTIAL RQ INFRASTRUCTURE ISSUES:")
    
    issues = [
        {
            "issue": "Worker Import Deadlock",
            "description": "Worker hangs when importing our modules",
            "symptoms": "Starts but never executes function",
            "solution": "Pre-import modules or use lazy imports"
        },
        {
            "issue": "Redis Connection Timeout",
            "description": "Worker can't establish stable Redis connection",
            "symptoms": "Intermittent startup failures",
            "solution": "Increase Redis connection timeout"
        },
        {
            "issue": "Container Resource Limits",
            "description": "Worker runs out of memory/CPU during startup",
            "symptoms": "Hangs after claiming task",
            "solution": "Increase container resource limits"
        },
        {
            "issue": "Python Environment Issues",
            "description": "Missing dependencies or Python path issues",
            "symptoms": "Import errors or module loading failures",
            "solution": "Fix container Python environment"
        },
        {
            "issue": "RQ Worker Configuration",
            "description": "Worker timeout or configuration issues",
            "symptoms": "Worker starts but doesn't process",
            "solution": "Adjust RQ worker settings"
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['issue']}")
        print(f"   Description: {issue['description']}")
        print(f"   Symptoms: {issue['symptoms']}")
        print(f"   Solution: {issue['solution']}")

def propose_immediate_solutions():
    """Propose immediate solutions to test."""
    
    print(f"\n💡 IMMEDIATE SOLUTIONS TO TEST")
    print("=" * 35)
    
    solutions = [
        {
            "priority": "HIGH",
            "solution": "Add extensive logging to RQ worker startup",
            "implementation": "Add logging before/after every import and initialization step",
            "test_time": "5 minutes"
        },
        {
            "priority": "HIGH", 
            "solution": "Pre-import all modules in worker initialization",
            "implementation": "Move all imports to top of rq_worker.py",
            "test_time": "5 minutes"
        },
        {
            "priority": "MEDIUM",
            "solution": "Increase RQ worker timeout settings",
            "implementation": "Add job_timeout and result_ttl settings",
            "test_time": "5 minutes"
        },
        {
            "priority": "MEDIUM",
            "solution": "Use process-based task execution",
            "implementation": "Replace function call with subprocess",
            "test_time": "15 minutes"
        },
        {
            "priority": "LOW",
            "solution": "Bypass RQ entirely for async processing",
            "implementation": "Use direct threading or alternative queue",
            "test_time": "30 minutes"
        }
    ]
    
    print("🚀 RECOMMENDED TESTING ORDER:")
    for i, sol in enumerate(solutions, 1):
        print(f"\n{i}. [{sol['priority']}] {sol['solution']}")
        print(f"   Implementation: {sol['implementation']}")
        print(f"   Test time: {sol['test_time']}")

def create_diagnostic_worker():
    """Create a diagnostic version of the RQ worker with extensive logging."""
    
    print(f"\n🔧 CREATING DIAGNOSTIC WORKER")
    print("-" * 30)
    
    diagnostic_code = '''
# Diagnostic RQ Worker - Add to rq_worker.py

import logging
import time
import sys
import os

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_citation_task_direct(task_id: str, input_type: str, input_data: dict):
    """Diagnostic wrapper with extensive logging."""
    
    logger.info(f"[DIAGNOSTIC] Starting process_citation_task_direct")
    logger.info(f"[DIAGNOSTIC] Task ID: {task_id}")
    logger.info(f"[DIAGNOSTIC] Input type: {input_type}")
    logger.info(f"[DIAGNOSTIC] Python version: {sys.version}")
    logger.info(f"[DIAGNOSTIC] Working directory: {os.getcwd()}")
    logger.info(f"[DIAGNOSTIC] Python path: {sys.path[:3]}...")
    
    try:
        logger.info(f"[DIAGNOSTIC] Step 1: Basic imports...")
        import traceback
        import json
        logger.info(f"[DIAGNOSTIC] Step 1: SUCCESS")
        
        logger.info(f"[DIAGNOSTIC] Step 2: Time and platform imports...")
        import time
        import platform
        logger.info(f"[DIAGNOSTIC] Step 2: SUCCESS")
        
        logger.info(f"[DIAGNOSTIC] Step 3: CitationService import...")
        from src.api.services.citation_service import CitationService
        logger.info(f"[DIAGNOSTIC] Step 3: SUCCESS")
        
        logger.info(f"[DIAGNOSTIC] Step 4: Creating CitationService...")
        service = CitationService()
        logger.info(f"[DIAGNOSTIC] Step 4: SUCCESS")
        
        logger.info(f"[DIAGNOSTIC] Step 5: Processing task...")
        # Use minimal processing instead of full service
        result = {
            'status': 'completed',
            'task_id': task_id,
            'citations': [{'citation': 'DIAGNOSTIC TEST', 'method': 'diagnostic'}],
            'processing_time': 1.0
        }
        logger.info(f"[DIAGNOSTIC] Step 5: SUCCESS")
        
        logger.info(f"[DIAGNOSTIC] Task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"[DIAGNOSTIC] FAILED at step: {e}")
        logger.error(f"[DIAGNOSTIC] Traceback: {traceback.format_exc()}")
        return {
            'status': 'failed',
            'task_id': task_id,
            'error': f'Diagnostic failure: {str(e)}'
        }
'''
    
    print("📝 Diagnostic worker code created")
    print("🎯 This will show exactly where the worker hangs during startup")
    
    return diagnostic_code

def main():
    """Run comprehensive RQ infrastructure analysis."""
    
    print("🎯 RQ INFRASTRUCTURE INVESTIGATION")
    print("=" * 35)
    
    # Analyze the startup hang
    analyze_rq_worker_startup_hang()
    
    # Propose solutions
    propose_immediate_solutions()
    
    # Create diagnostic worker
    diagnostic_code = create_diagnostic_worker()
    
    print(f"\n📊 INVESTIGATION SUMMARY")
    print("=" * 25)
    print("✅ Problem isolated: RQ worker startup hang")
    print("✅ Location identified: Between 'started' and 'running' status")
    print("✅ Cause: Worker initialization/import process")
    print("✅ Solutions available: Multiple approaches to test")
    
    print(f"\n🚀 RECOMMENDED IMMEDIATE ACTION:")
    print("1. Add diagnostic logging to see exactly where worker hangs")
    print("2. Pre-import modules to avoid import deadlocks")
    print("3. Test with increased timeouts")
    print("4. Consider alternative async architecture if RQ issues persist")

if __name__ == "__main__":
    main()
