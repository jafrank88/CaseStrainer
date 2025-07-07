#!/usr/bin/env python3
"""
Test JSON serialization of task result data
"""

import json
import redis

def test_json_serialization():
    """Test JSON serialization of task result data"""
    
    # Sample task result data similar to what the worker produces
    task_result = {
        'task_id': 'c142eef2-e07e-4d8c-95f7-c81fff96ceda',
        'type': 'text',
        'status': 'completed',
        'results': ['177 Wash. 2d 351', '302 P.3d 156'],
        'citations': ['177 Wash. 2d 351', '302 P.3d 156'],
        'case_names': [],
        'metadata': {},
        'statistics': {},
        'summary': {},
        'start_time': 1234567890.123,
        'end_time': 1234567890.456,
        'progress': 100,
        'current_step': 'Complete'
    }
    
    print("Testing JSON serialization...")
    print(f"Original data: {task_result}")
    
    try:
        # Test JSON serialization
        json_str = json.dumps(task_result)
        print(f"JSON serialized: {json_str}")
        
        # Test JSON deserialization
        parsed = json.loads(json_str)
        print(f"JSON deserialized: {parsed}")
        
        # Test Redis storage
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        
        # Store in Redis
        test_key = "test_task_result"
        r.setex(test_key, 60, json_str)  # 60 second TTL
        
        # Retrieve from Redis
        retrieved = r.get(test_key)
        if retrieved:
            retrieved_str = retrieved.decode('utf-8')
            print(f"Retrieved from Redis: {retrieved_str}")
            
            # Parse retrieved data
            parsed_retrieved = json.loads(retrieved_str)
            print(f"Parsed retrieved data: {parsed_retrieved}")
            
            # Clean up
            r.delete(test_key)
            print("✅ Redis test successful")
        else:
            print("❌ Failed to retrieve from Redis")
            
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_serialization() 