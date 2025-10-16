"""Test to verify truncation fix is working"""
import subprocess
import sys

print("=" * 80)
print("TRUNCATION FIX VERIFICATION TEST")
print("=" * 80)
print()

# Test sync processing
print("[TEST 1] SYNC Processing (PDF upload)")
print("-" * 80)
result = subprocess.run(
    [sys.executable, "test_upload.py"],
    capture_output=True,
    text=True
)

# Parse output for specific truncation fixes
output = result.stdout
lines = output.split('\n')

# Track specific fixes
fixes_to_check = {
    'Trump v. CASA, Inc': False,
    "Noem v. Nat'l TPS All": False,
    "Dep't of Army v. Blue Fox, Inc": False,
}

print("\n[CHECKING] Key truncation fixes:")
for line in lines:
    for fix_name in fixes_to_check:
        if fix_name in line and '->' in line and 'FAIL' not in line[:10]:
            fixes_to_check[fix_name] = True
            print(f"  ✅ {fix_name} - FIXED")

# Show any that are still truncated
print("\n[STATUS] Fix Summary:")
fixed_count = sum(1 for v in fixes_to_check.values() if v)
total_count = len(fixes_to_check)
print(f"  Fixed: {fixed_count}/{total_count} cases")

if fixed_count == total_count:
    print("  ✅ ALL KEY TRUNCATIONS FIXED!")
elif fixed_count > 0:
    print("  ⚠️  PARTIAL SUCCESS - Some truncations fixed")
    for name, fixed in fixes_to_check.items():
        if not fixed:
            print(f"    ❌ Still needs fix: {name}")
else:
    print("  ❌ NO FIXES DETECTED")

# Show sample of case names
print("\n[SAMPLE] Case names from output:")
in_case_names = False
count = 0
for line in lines:
    if '[ALL CASE NAMES]:' in line:
        in_case_names = True
    elif in_case_names and '->' in line and count < 10:
        print(f"  {line.strip()}")
        count += 1
    elif count >= 10:
        break

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
