"""
Update backup verification to use CourtListener Search API more effectively
"""

print("UPDATING BACKUP VERIFICATION FOR COURTLISTENER SEARCH API")
print("=" * 60)

print("\nCourtListener URL Found:")
print("-" * 50)
print("https://www.courtlistener.com/opinion/10639374/giuffre-v-maxwell/?q=giuffre+v.+maxwell")
print("Opinion ID: 10639374")
print("Search query: giuffre+v.+maxwell")

print("\nIMPROVED APPROACH:")
print("-" * 50)
print("1. Use CourtListener Search API with case name")
print("2. Filter by court and year")
print("3. No need to scrape Justia HTML")
print("4. More reliable and faster")

print("\nUPDATED SEARCH STRATEGY:")
print("-" * 50)
print("For Giuffre v. Maxwell, 146 F.4th 165 (2nd Cir. 2025):")
print("1. Search: https://www.courtlistener.com/api/rest/v4/search/?q=\"Giuffre v. Maxwell\"&court=ca2&decision_date_min=2025-01-01&decision_date_max=2025-12-31")
print("2. Should return opinion ID 10639374")
print("3. Extract case details and verify match")

print("\nCODE CHANGES NEEDED:")
print("-" * 50)
print("1. Update _verify_with_backup_search() method")
print("2. Prioritize CourtListener Search API")
print("3. Use specific court and date filters")
print("4. Parse search results more carefully")

print("\nADVANTAGES:")
print("-" * 50)
print("✅ Uses existing API (no HTML scraping)")
print("✅ More reliable than Justia scraping")
print("✅ Faster response times")
print("✅ Better data structure from API")
print("✅ Can find cases before they get official citations")

print("\n" + "=" * 60)
print("This will make backup verification much more effective!")
print("=" * 60)
