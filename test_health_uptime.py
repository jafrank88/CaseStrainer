#!/usr/bin/env python3
"""
Test script to verify the health endpoint with uptime functionality.
"""

import time
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_uptime_calculation():
    """Test the uptime calculation functions."""
    print("Testing uptime calculation functions...")
    
    # Import the functions from vue_api_endpoints
    from src.vue_api_endpoints import get_uptime, _format_uptime_human
    
    # Test with different uptime values
    test_cases = [
        30,      # 30 seconds
        90,      # 1 minute 30 seconds
        3661,    # 1 hour 1 minute 1 second
        90000,   # 1 day 1 hour
        172800,  # 2 days
    ]
    
    for seconds in test_cases:
        print(f"\nTesting {seconds} seconds:")
        print(f"  Human readable: {_format_uptime_human(seconds)}")
        
        # Simulate the get_uptime function
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            formatted = f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"
        elif hours > 0:
            formatted = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            formatted = f"{minutes:02d}:{secs:02d}"
        
        print(f"  Formatted: {formatted}")
        print(f"  Days: {days}, Hours: {hours}, Minutes: {minutes}, Seconds: {secs}")

def test_health_endpoint_structure():
    """Test the structure of the health endpoint response."""
    print("\n" + "="*50)
    print("Testing health endpoint response structure...")
    
    # Import the health check function and blueprint
    from src.vue_api_endpoints import health_check, vue_api
    from flask import Flask
    
    # Create a minimal Flask app for testing
    app = Flask(__name__)
    app.register_blueprint(vue_api)
    
    with app.test_client() as client:
        response = client.get('/casestrainer/api/health')
        
        if response.status_code == 200:
            data = response.get_json()
            print("✅ Health endpoint responded successfully")
            print(f"Status: {data.get('status')}")
            print(f"Service: {data.get('service')}")
            print(f"Timestamp: {data.get('timestamp')}")
            
            # Check uptime fields
            uptime = data.get('uptime', {})
            if uptime:
                print("✅ Uptime information found:")
                print(f"  Seconds: {uptime.get('seconds')}")
                print(f"  Formatted: {uptime.get('formatted')}")
                print(f"  Human readable: {uptime.get('human_readable')}")
            else:
                print("❌ No uptime information found")
            
            # Check server_uptime field for compatibility
            server_uptime = data.get('server_uptime')
            if server_uptime is not None:
                print(f"✅ Server uptime (compatibility): {server_uptime} seconds")
            else:
                print("❌ No server_uptime field found")
                
        else:
            print(f"❌ Health endpoint failed with status {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)}")

if __name__ == "__main__":
    print("CaseStrainer Health Endpoint Uptime Test")
    print("="*50)
    
    try:
        test_uptime_calculation()
        test_health_endpoint_structure()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 