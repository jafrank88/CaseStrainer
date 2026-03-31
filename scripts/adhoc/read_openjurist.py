"""
Script to refactor _verify_with_openjurist to use shared utilities.
This eliminates redundant code patterns.
"""

# Read the current function
with open('/app/src/unified_verification_master.py', 'r') as f:
    content = f.read()

# Find the _verify_with_openjurist function
import re

# Pattern to match the entire _verify_with_openjurist function
pattern = r'(    async def _verify_with_openjurist\([^)]+\)[^:]*:.*?)(?=\n    async def |\n    def |\Z)'

match = re.search(pattern, content, re.DOTALL)
if match:
    old_func = match.group(1)
    print(f"Found _verify_with_openjurist ({len(old_func)} chars)")
    print("First 500 chars:")
    print(old_func[:500])
    print("\n...\n")
    print("Last 500 chars:")
    print(old_func[-500:])
else:
    print("Could not find _verify_with_openjurist function")
