"""
Test the health check endpoints locally.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.health_check_endpoint import get_health_status

print("=" * 100)
print("HEALTH CHECK TEST")
print("=" * 100)
print()

# Get health status
health = get_health_status()

print(f"Overall Status: {health['status']}")
print(f"Version: {health['version']}")
print(f"Timestamp: {health['timestamp']}")
print()

print("Component Status:")
print("-" * 100)

for component, status in health['components'].items():
    comp_status = status.get('status', 'unknown')
    symbol = "OK" if comp_status == 'healthy' else ("WARN" if comp_status == 'degraded' else "FAIL")
    
    print(f"[{symbol}] {component}: {comp_status}")
    
    if 'version' in status:
        print(f"     Version: {status['version']}")
    if 'accuracy' in status:
        print(f"     Accuracy: {status['accuracy']}")
    if 'method' in status:
        print(f"     Method: {status['method']}")
    if 'test' in status:
        print(f"     Test: {status['test']}")
    if 'citations_found' in status:
        print(f"     Citations Found: {status['citations_found']}")
    if 'error' in status:
        print(f"     Error: {status['error']}")
    print()

print("=" * 100)
if health['status'] == 'healthy':
    print("SUCCESS! All systems healthy and ready for production.")
elif health['status'] == 'degraded':
    print("WARNING: System is degraded but operational.")
else:
    print("ERROR: System is unhealthy.")
print("=" * 100)
