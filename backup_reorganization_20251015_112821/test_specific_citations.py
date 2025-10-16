"""Test specific citations from Robert Cassell document."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from unified_case_name_extractor_v2 import UnifiedCaseNameExtractorV2

# Test cases from the document
test_cases = [
    {
        'citation': '617 B.R. 636',
        'context': 'The Seventh Circuit has found that chapter 12 relief is specifically designed for those farmers whose activities involved the inherent risks and cyclical uncertainties that are associated with farming. In re Hoel, 617 B.R. 636, 638-639 (Bankr. W.D. Wis.) (citing In re Armstrong',
        'expected': 'In re Hoel'
    },
    {
        'citation': '812 F.2d 1024',
        'context': 'In re Hoel, 617 B.R. 636, 638-639 (Bankr. W.D. Wis.) (citing In re Armstrong, 812 F.2d 1024, 1027 (7th Cir. 1987). Only a handful of Courts',
        'expected': 'In re Armstrong'
    },
    {
        'citation': '101 B.R. 691',
        'context': 'Courts in Illinois and Oklahoma found that horse breeding, boarding, and training was a service-oriented business, not one that produced agricultural goods for consumption like a traditional farm. In re Cluck, 101 B.R. 691 (Bankr. E.D. Okla. 1989); In re McKillips',
        'expected': 'In re Cluck'
    },
    {
        'citation': '72 B.R. 565',
        'context': 'In re Cluck, 101 B.R. 691 (Bankr. E.D. Okla. 1989); In re McKillips, 72 B.R. 565 (Bankr. N.D. Ill. 1987). These Courts found',
        'expected': 'In re McKillips'
    },
]

def main():
    print("=" * 80)
    print("CASE NAME EXTRACTION TEST - Specific Citations")
    print("=" * 80)
    
    extractor = UnifiedCaseNameExtractorV2()
    
    correct = 0
    total = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing citation: {test['citation']}")
        print(f"   Expected case name: {test['expected']}")
        
        # Extract case name
        result = extractor.extract_case_name_and_date(test['context'], test['citation'])
        extracted = result.case_name if result else 'N/A'
        
        # Strip trailing punctuation for comparison
        extracted_clean = extracted.rstrip('.,;: ')
        expected_clean = test['expected'].rstrip('.,;: ')
        
        print(f"   Extracted case name: {extracted}")
        print(f"   Extraction method: {result.method if result else 'N/A'}")
        
        # Check if correct
        if extracted_clean == expected_clean:
            print("   Result: MATCH ✓")
            correct += 1
        elif extracted_clean.lower() == expected_clean.lower():
            print("   Result: MATCH (case insensitive) ~")
            correct += 0.5
        else:
            print("   Result: MISMATCH ✗")
            print(f"   Context preview: ...{test['context'][max(0,test['context'].find(test['citation'])-50):test['context'].find(test['citation'])+len(test['citation'])+20]}...")
        
        total += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {correct}/{total} correct ({correct/total*100:.1f}%)")
    print("=" * 80)

if __name__ == '__main__':
    main()
