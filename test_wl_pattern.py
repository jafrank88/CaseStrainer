import re

def test_wl_pattern():
    # Test WL citation pattern
    pattern = r'\b(\d{4})\s+WL\s+(\d+)\b'
    
    test_cases = [
        ("2006 WL 3801910", ("2006", "3801910")),
        ("2023 WL 1234567", ("2023", "1234567")),
        ("2001 WL 1234567", ("2001", "1234567")),
        ("See 2006 WL 3801910 (W.D. Wash. 2006)", ("2006", "3801910")),
        ("In re Doe, 2023 WL 1234567 (9th Cir. 2023)", ("2023", "1234567")),
        ("(citing Example v. Test, 2001 WL 1234567)", ("2001", "1234567")),
        ("No WL citation here", None),
        ("Invalid WL 1234567", None),
        ("2006WL3801910", None),  # No spaces
    ]
    
    for text, expected in test_cases:
        match = re.search(pattern, text)
        if expected is None:
            assert match is None, f"Expected no match for '{text}', but got {match.groups() if match else 'None'}"
        else:
            assert match is not None, f"Expected match for '{text}', but got None"
            assert match.groups() == expected, f"For '{text}', expected {expected}, got {match.groups()}"
    
    print("All WL pattern tests passed!")

if __name__ == "__main__":
    test_wl_pattern()
