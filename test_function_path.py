#!/usr/bin/env python3
"""
Test what function paths RQ can see
"""
import sys
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app')

print("Testing function imports...")

# Test 1: Direct import from progress_manager
try:
    from src.progress_manager import process_citation_task_direct
    print("✓ Test 1: from src.progress_manager import process_citation_task_direct")
    print(f"  Module: {process_citation_task_direct.__module__}")
    print(f"  Name: {process_citation_task_direct.__name__}")
    print(f"  Qualname: {process_citation_task_direct.__qualname__}")
except Exception as e:
    print(f"✗ Test 1 failed: {e}")

# Test 2: Import from rq_worker  
try:
    from src.rq_worker import process_citation_task_direct as worker_func
    print("\n✓ Test 2: from src.rq_worker import process_citation_task_direct")
    print(f"  Module: {worker_func.__module__}")
    print(f"  Name: {worker_func.__name__}")
except Exception as e:
    print(f"\n✗ Test 2 failed: {e}")

# Test 3: Check if they're the same function
try:
    from src.progress_manager import process_citation_task_direct as pm_func
    from src.rq_worker import process_citation_task_direct as rq_func
    print(f"\n✓ Test 3: Comparison")
    print(f"  Same function? {pm_func is rq_func}")
    print(f"  PM module: {pm_func.__module__}")
    print(f"  RQ module: {rq_func.__module__}")
except Exception as e:
    print(f"\n✗ Test 3 failed: {e}")
