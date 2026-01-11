"""
Test the actual pattern from the file
"""

import re

print("TESTING ACTUAL PATTERN FROM FILE")
print("=" * 60)

# Context after signal word removal
context = "Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"
print(f"Context: '{context}'")
print()

# The pattern I updated (line 857)
pattern = r"([A-Z][a-zA-Z\'\.\&\-\s]*?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\-\s]*?)(?=\s*,\s*(?:No\.|\d+)|\s*[;\(,]|$)"
print(f"Pattern: {pattern}")
print()

match = re.search(pattern, context)
if match:
    print("✅ Pattern matches!")
    print(f"   Full match: '{match.group()}'")
    print(f"   Plaintiff: '{match.group(1)}'")
    print(f"   Defendant: '{match.group(2)}'")
    
    # Apply signal word cleanup
    case_name = f"{match.group(1)} v. {match.group(2)}"
    signal_words = ["see also", "see", "cf.", "e.g.", "accord", "compare", "but see", "quoting"]
    case_name_lower = case_name.lower()
    for signal in signal_words:
        if case_name_lower.startswith(signal):
            case_name = case_name[len(signal):].strip(" ,;")
            break
    
    print(f"   Final case name: '{case_name}'")
else:
    print("❌ Pattern doesn't match")
    
    # Debug why
    print("\nDebugging:")
    v_pos = context.find(" v. ")
    if v_pos != -1:
        print(f"Found ' v.' at position {v_pos}")
        
        # Check lookahead
        after_defendant = context[v_pos:]
        print(f"Text from 'v.': '{after_defendant}'")
        
        # Check if lookahead matches
        import re
        lookahead_pattern = r"(?=\s*,\s*(?:No\.|\d+)|\s*[;\(,]|$)"
        if re.search(lookahead_pattern, context[v_pos:]):
            print("✅ Lookahead matches")
        else:
            print("❌ Lookahead doesn't match")
            # Find where it should match
            no_pos = context.find(", No.")
            if no_pos != -1:
                print(f"Found ', No.' at position {no_pos}")
                defendant = context[v_pos + 3:no_pos]
                print(f"Defendant: '{defendant.strip()}'")

print("\n" + "=" * 60)
print("The pattern should work. If it's not matching in the actual code,")
print("there might be an issue with how it's being applied or the context")
print("is different when processed by the actual function.")
