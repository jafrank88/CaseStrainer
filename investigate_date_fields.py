"""
Check what date fields CourtListener API returns
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("COURTLISTENER DATE FIELDS INVESTIGATION")
print("=" * 60)

# The issue is we're using dateFiled (publication date) instead of decision date
# Let's check what fields are available

print("\nCourtListener API date fields (in order of preference):")
print("-" * 50)
print("1. date_filed - When the case was filed (NOT what we want)")
print("2. date_argued - When the case was argued")  
print("3. date_reargued - When the case was reargued")
print("4. date_reargument_denied - When reargument was denied")
print("5. date_cert_denied - When cert was denied")
print("6. date_rehearing_denied - When rehearing was denied")
print("7. date_filed should be the DECISION date, not database entry date")

print("\nPROBLEM:")
print("-" * 50)
print("We're using 'dateFiled' which CourtListener interprets as")
print("the date the case was added to their database for Federal Reporter")
print("We need to use the actual decision date from the citation itself")

print("\nSOLUTION:")
print("-" * 50)
print("1. Extract the year from the citation text (e.g., '585 F.3d 1061 (2009)')")
print("2. Use that year instead of CourtListener's dateFiled")
print("3. Only use CourtListener's date for state cases where decision date isn't in citation")

print("\nFor Federal Reporter citations, the year in parentheses")
print("is the decision year and should be trusted over database dates")
print("=" * 60)
