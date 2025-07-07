#!/usr/bin/env python3
"""
Test Redis connection and manually check task result
"""

import redis
import json

def test_redis_connection():
    """Test Redis connection and check for task result"""
    
    print("Testing Redis connection...")
    
    try:
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        
        # Check for the specific task result
        task_id = "c142eef2-e07e-4d8c-95f7-c81fff96ceda"
        
        # Check task_result key
        result_key = f"task_result:{task_id}"
        result = r.get(result_key)
        print(f"Task result key '{result_key}': {'EXISTS' if result else 'NOT FOUND'}")
        
        if result:
            print(f"Task result: {result.decode('utf-8')[:200]}...")
        
        # Check task_to_job mapping
        job_key = f"task_to_job:{task_id}"
        job_id = r.get(job_key)
        print(f"Job mapping key '{job_key}': {'EXISTS' if job_id else 'NOT FOUND'}")
        
        if job_id:
            job_id = job_id.decode('utf-8')
            print(f"Job ID: {job_id}")
            
            # Check RQ result
            rq_result_key = f"rq:results:{job_id}"
            rq_result = r.get(rq_result_key)
            print(f"RQ result key '{rq_result_key}': {'EXISTS' if rq_result else 'NOT FOUND'}")
            
            if rq_result:
                print(f"RQ result type: {type(rq_result)}")
                print(f"RQ result: {rq_result.decode('utf-8')[:200]}...")
        
        # List all keys related to this task
        print("\nAll keys related to this task:")
        all_keys = r.keys(f"*{task_id}*")
        for key in all_keys:
            key_str = key.decode('utf-8')
            print(f"  {key_str}")
        
        # List all task_result keys
        print("\nAll task_result keys:")
        task_result_keys = r.keys("task_result:*")
        for key in task_result_keys:
            key_str = key.decode('utf-8')
            print(f"  {key_str}")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

if __name__ == "__main__":
    test_redis_connection() 