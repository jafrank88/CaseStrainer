"""
Check the debug logs to see what enable_verification value is being passed
"""

import os

print("=" * 80)
print("CHECKING DEBUG LOGS FOR VERIFICATION FLAG")
print("=" * 80)

log_files = [
    'D:/dev/casestrainer/logs/casestrainer.log',
    'D:/dev/casestrainer/logs/docker_daemon_monitor.log'
]

print("\nSearching for debug messages about enable_verification...")

for log_file in log_files:
    if os.path.exists(log_file):
        print(f"\n{os.path.basename(log_file)}:")
        print("-" * 40)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # Look for the debug messages we added
            for line in lines:
                if any(keyword in line for keyword in [
                    'enable_verification=',
                    'ABOUT TO CALL process_citations_unified',
                    'Phase 4.75'
                ]):
                    print(f"  {line.strip()}")

print("\n" + "=" * 80)
print("ANALYSIS:")
print("-" * 40)
print("If the logs show enable_verification=True but verification still fails,")
print("the issue might be in:")
print("1. The UnifiedCitationProcessorV2 initialization")
print("2. The verification methods themselves")
print("3. API connectivity issues")
print("=" * 80)
