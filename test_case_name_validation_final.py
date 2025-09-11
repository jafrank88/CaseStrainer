import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_case_name_validation():
    print("Initializing processor...")
    processor = UnifiedCitationProcessorV2()
    print("Processor initialized successfully")
    
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
    
    print("\nTesting case name validation:")
    print("=" * 80)
    
    for case_name, expected in test_cases:
        try:
            result = processor._is_valid_case_name(case_name)
            status = "PASS" if result == expected else "FAIL"
            print(f"{status}: '{case_name}' -> Expected: {expected}, Got: {result}")
        except Exception as e:
            print(f"ERROR: Failed to validate '{case_name}': {str(e)}")
            raise

if __name__ == "__main__":
    print("Starting case name validation tests...")
    test_case_name_validation()
    print("\nTest completed.")
