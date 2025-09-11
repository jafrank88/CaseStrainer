from unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_case_name_validation():
    processor = UnifiedCitationProcessorV2()
    
    test_cases = [
        # Valid cases
        ("Smith v. Jones", True),
        ("Roe v. Wade", True),
        ("In re Gault", True),
        ("State v. Smith", True),
        ("United States v. Nixon", True),
        ("Ex parte Milligan", True),
        ("People v. Anderson", True),
        ("Commonwealth v. Johnson", True),
        ("In the Matter of Baby M", True),
        ("Ex rel. Smith v. Jones", True),
        
        # Invalid cases
        ("v. Smith", False),
        ("Smith v.", False),
        ("In re", False),
        ("Court of Appeals", False),
        ("Federal Rules of Civil Procedure", False),
        ("Title 42 U.S. Code § 1983", False),
        ("The court finds that the defendant", False),
        ("See Smith v. Jones", False),
        ("Id. at 123", False),
        ("", False),
        (" ", False),
        ("v. ", False),
        ("In re ", False),
    ]
    
    print("Testing case name validation:")
    print("-" * 80)
    
    for case_name, expected in test_cases:
        result = processor._is_valid_case_name(case_name)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status}: '{case_name}' -> Expected: {expected}, Got: {result}")

if __name__ == "__main__":
    test_case_name_validation()
