#!/usr/bin/env python3
"""
IDENTIFIED THE EXACT CLUSTER DISPLAY ISSUE

Looking at CitationResults.vue lines 407-453, the getClusterSubmittedName function
is filtering out generic case names, which is causing clusters to not display.

THE PROBLEM:
1. Clusters ARE being created correctly (21 clusters found)
2. Parallel citations ARE being detected correctly 
3. But the frontend getClusterSubmittedName() function filters out generic names
4. This leaves nothing to display for most clusters

SPECIFIC ISSUE IN CODE:
Lines 420-424 in CitationResults.vue:
```javascript
if (cluster?.submitted_display_name && 
    cluster.submitted_display_name !== 'N/A' &&
    !isGenericCaseName(cluster.submitted_display_name)) {
  return cluster.submitted_display_name
}
```

The isGenericCaseName() function (lines 456-466) filters out:
- 'Washington State Case'
- 'Pacific Reporter Case' 
- 'Federal Appeals Case'
- etc.

But YOUR DATA shows these as the submitted_display_name for most clusters!

SOLUTION NEEDED:
Fix the frontend to use verifying_display_name instead of submitted_display_name
when the submitted name is generic but verification succeeded.
"""

def explain_fix_needed():
    print("CLUSTER DISPLAY ISSUE - EXACT PROBLEM IDENTIFIED")
    print("=" * 60)
    
    print("\nWHAT'S HAPPENING:")
    print("1. Backend creates 21 clusters correctly")
    print("2. Each cluster has submitted_display_name: 'Pacific Reporter Case'")
    print("3. Frontend isGenericCaseName() filters these out as 'generic'")
    print("4. Result: Clusters don't appear in frontend")
    
    print("\nSPECIFIC CODE ISSUE:")
    print("File: casestrainer-vue-new/src/components/CitationResults.vue")
    print("Lines: 420-424 in getClusterSubmittedName() function")
    print("Problem: !isGenericCaseName(cluster.submitted_display_name) filter")
    
    print("\nSIMPLE FIX:")
    print("Change the logic to use verifying_display_name when:")
    print("- submitted_display_name is generic AND")
    print("- cluster has verified citations")
    
    print("\nCURRENT BEHAVIOR:")
    print("- submitted_display_name: 'Pacific Reporter Case' -> filtered out")
    print("- verifying_display_name: 'In Re Marriage of Littlefield' -> not used")
    print("- Result: Nothing displayed")
    
    print("\nDESIRED BEHAVIOR:")
    print("- submitted_display_name: 'Pacific Reporter Case' (generic)")
    print("- verifying_display_name: 'In Re Marriage of Littlefield' (real name)")
    print("- Result: Display 'In Re Marriage of Littlefield'")

if __name__ == "__main__":
    explain_fix_needed()
