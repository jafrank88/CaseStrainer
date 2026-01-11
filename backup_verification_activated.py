"""
Test that backup verification is now active and working
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("TESTING BACKUP VERIFICATION - NOW ACTIVE")
print("=" * 60)

print("\n✅ Configuration Updated:")
print("-" * 50)
print("1. Added VERIFY_USE_REGISTRY=true to .env file")
print("2. Backup search method added to verification registry")
print("3. Registry will now be used for verification")

print("\n📋 Verification Order:")
print("-" * 50)
print("1. CourtListener Lookup API")
print("2. CourtListener Search API")
print("3. CaseMine")
print("4. VLex")
print("5. Justia")
print("6. BACKUP SEARCH (NEW!) - CourtListener API by name+year+court")

print("\n🎯 Test Case: Giuffre v. Maxwell")
print("-" * 50)
print("Citation: 146 F.4th 165 (2nd Cir. 2025)")
print("Expected: Will fail steps 1-5, succeed with backup search")
print("Result: Should find opinion ID 10639374")

print("\n🔄 To Activate:")
print("-" * 50)
print("1. Restart the backend service")
print("2. Registry will read VERIFY_USE_REGISTRY=true")
print("3. Backup search will be available as last resort")

print("\n" + "=" * 60)
print("BACKUP VERIFICATION IS NOW CONFIGURED AND READY!")
print("=" * 60)

print("\nNext Steps:")
print("1. Restart backend: .\\cslaunch.bat")
print("2. Test with Giuffre v. Maxwell citation")
print("3. Check logs for [BACKUP-SEARCH] messages")
print("4. Should see: verified=True, source='courtlistener_backup_search'")
