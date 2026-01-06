"""
Check for year mismatch issues in verification
"""

import os

print("=" * 80)
print("CHECKING FOR YEAR MISMATCH ISSUES")
print("=" * 80)

log_files = [
    'D:/dev/casestrainer/logs/casestrainer.log',
]

for log_file in log_files:
    if os.path.exists(log_file):
        print(f"\n{os.path.basename(log_file)}:")
        print("-" * 40)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # Look for year mismatch messages
            for line in lines[-200:]:  # Last 200 lines
                if any(keyword in line for keyword in [
                    'YEAR-MISMATCH',
                    'year mismatch',
                    'BATCH-YEAR',
                    'extracted=None',
                    '963 F.3d 130'
                ]):
                    print(f"  {line.strip()}")

print("\n" + "=" * 80)
print("ANALYSIS:")
print("-" * 40)
print("The issue might be that extracted_date is None for many citations.")
print("When extracted_date is None, the year match logic might not work correctly.")
print("")
print("Let's check what happens when extracted_date is None...")
print("=" * 80)
