"""
Investigate why file uploads aren't verifying while text input works
"""

import logging

print("=" * 80)
print("INVESTIGATING FILE vs TEXT VERIFICATION DIFFERENCE")
print("=" * 80)

print("\nOBSERVATION:")
print("- Simple text citation '578 U.S. 5' verifies successfully ✅")
print("- PDF file citations do not verify ❌")
print("")
print("This suggests different code paths for text vs file processing")

# Check the most recent logs for verification attempts
import os

log_files = [
    'D:/dev/casestrainer/logs/casestrainer.log',
    'D:/dev/casestrainer/logs/docker_daemon_monitor.log'
]

print("\nCHECKING RECENT LOGS FOR VERIFICATION MESSAGES:")
print("-" * 40)

for log_file in log_files:
    if os.path.exists(log_file):
        print(f"\n{os.path.basename(log_file)} (last 30 lines):")
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-30:]:
                if any(keyword in line.lower() for keyword in ['verification', 'enable_verification', 'phase 4.75', '578 u.s.']):
                    print(f"  {line.strip()}")

print("\n" + "=" * 80)
print("POSSIBLE CAUSES:")
print("-" * 40)
print("1. File upload uses a different processor instance")
print("2. File upload might be using cached processor from before the fix")
print("3. Different code path in CitationService for files vs text")
print("4. File processing might have its own config override")

print("\nNEXT STEP:")
print("-" * 40)
print("Check if CitationService is creating UnifiedCitationProcessorV2()")
print("without passing the config parameter for file uploads")
print("=" * 80)
