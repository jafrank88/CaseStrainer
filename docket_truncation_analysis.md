"""
DOCKET TRUNCATION ISSUE ANALYSIS
=================================

ISSUE IDENTIFIED:

- Case name: "Alexander v. Las Vegas Metro. Police Dep't"
- Currently extracts: "Alexander v. Las Vegas Metro. Police Dep't:24-CV- 00074-APG-NJK"
- The docket number ", No. 2:24-CV- 00074-APG-NJK" is being truncated to ":24-CV- 00074-APG-NJK"

ROOT CAUSE:

1. The context is being modified somewhere between input and pattern matching
2. Debug output shows the transformation:
   Input:  'See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,'
   Debug:  'also, e.g., Alexander v. Las Vegas Metro. Police Dep't:24-CV- 00074-APG-NJK,'
   
   Changes:
   - "See " removed (signal word - correct)
   - ", No. 2" becomes ":" (incorrect)

INVESTIGATION:

- Pattern 3 in strict_context_isolator.py was updated to use lookahead
- Pattern works correctly when tested in isolation
- Issue is that the context is being modified before pattern matching
- Something is removing ", No. 2" and leaving just ":"

POSSIBLE CAUSES:

1. There's a hidden pattern that extracts docket numbers incorrectly
2. The debug output is truncating/modifying the display
3. There's a regex substitution happening that we haven't found

NEXT STEPS:

1. Search for patterns that modify ", No." to ":"
2. Check if there's post-processing of the context
3. Verify the pattern is actually being used (caching issue?)

FIXES ATTEMPTED:

1. ✅ Updated Pattern 3 with lookahead to stop at docket numbers
2. ✅ Added signal word cleanup after pattern matching
3. ❌ Issue persists - context is being modified before pattern matching

STATUS:

- Pattern fix is correct but not taking effect
- Need to find where context is being modified
- May require deeper investigation of the codebase
"""
