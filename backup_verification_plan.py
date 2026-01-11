"""
Add backup verification method for case name + year + court search
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("BACKUP VERIFICATION METHOD: Case Name + Year + Court")
print("=" * 60)

print("\nPROBLEM:")
print("-" * 50)
print("Some citations are too recent for database citation lookup")
print("But the case exists and can be found by:")
print("1. Case name")
print("2. Decision year") 
print("3. Court identifier")

print("\nEXAMPLE:")
print("-" * 50)
print("Citation: 146 F.4th 165 (2nd Cir. 2025)")
print("Found at: https://law.justia.com/cases/federal/appellate-courts/ca2/24-182/24-182-2025-07-23.html")
print("Case: Giuffre v. Maxwell")
print("Court: 2nd Circuit (ca2)")
print("Year: 2025")

print("\nSOLUTION:")
print("-" * 50)
print("Add backup verification that:")
print("1. Extracts case name from citation")
print("2. Extracts year from citation")
print("3. Detects court from citation or context")
print("4. Searches Justia/CourtListener by name+year+court")
print("5. Verifies if match found with correct court and year")

print("\nIMPLEMENTATION PLAN:")
print("-" * 50)
print("1. Create _verify_with_backup_search() method")
print("2. Parse citation for:")
print("   - Case name (already extracted)")
print("   - Year (from parentheses)")
print("   - Court (from citation like '2nd Cir.' or context)")
print("3. Build search URLs:")
print("   - Justia: /cases/federal/appellate-courts/{court}/{year}/")
print("   - CourtListener: search/?q={name}&court={court}&decision_date_min={year}")
print("4. Verify match if:")
print("   - Same case name (or similar)")
print("   - Same year")
print("   - Same court")

print("\nFILES TO MODIFY:")
print("-" * 50)
print("- src/unified_verification_master.py")
print("- src/enhanced_fallback_verifier.py")
print("- Add to verification sources as last resort")

print("\n" + "=" * 60)
print("This would allow verification of recent cases that")
print("exist but aren't in citation databases yet.")
print("=" * 60)
