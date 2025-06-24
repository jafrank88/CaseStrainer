#!/usr/bin/env python3
"""
Debug script to test case name extraction against problematic citations
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from extract_case_name import extract_case_name_from_context

def test_problematic_citations():
    """Test extraction against the problematic citations from the user's results"""
    
    # Test cases based on the user's results
    test_cases = [
        {
            'citation': '544 P.3d 533',
            'context': 'Some context here with a case name',
            'expected': 'Not extracted',
            'issue': 'No case name found'
        },
        {
            'citation': '544 P.3d 486',
            'context': 'I to issue a formal order for payment of a sum certain',
            'expected': 'Should not extract this',
            'issue': 'Extracted non-case text'
        },
        {
            'citation': '195 Wn.2d 198',
            'context': 'Black v. Cent. Puget Sound Reg',
            'expected': 'Black v. Cent. Puget Sound Reg',
            'issue': 'Incomplete extraction'
        },
        {
            'citation': '457 P.3d 453',
            'context': 'Black v. Cent. Puget Sound Reg',
            'expected': 'Black v. Cent. Puget Sound Reg',
            'issue': 'Incomplete extraction'
        },
        {
            'citation': '540 P.3d 93',
            'context': 'We construe statutes in light of their purpose. Nwauzor v. GEO Grp',
            'expected': 'Nwauzor v. GEO Grp',
            'issue': 'Extracted sentence instead of case name'
        },
        {
            'citation': '140 Wn.2d 291',
            'context': 'Drinkwitz v. Alliant Techsystems',
            'expected': 'Drinkwitz v. Alliant Techsystems',
            'issue': 'Missing Inc. in extraction'
        },
        {
            'citation': '996 P.2d 582',
            'context': 'Drinkwitz v. Alliant Techsystems',
            'expected': 'Drinkwitz v. Alliant Techsystems',
            'issue': 'Missing Inc. in extraction'
        },
        {
            'citation': '67 Wn. App. 24',
            'context': 'Industries v. Overnite Transportation Co',
            'expected': 'Industries v. Overnite Transportation Co',
            'issue': 'Missing Department of Labor & in extraction'
        },
        {
            'citation': '834 P.2d 638',
            'context': 'Industries v. Overnite Transportation Co',
            'expected': 'Industries v. Overnite Transportation Co',
            'issue': 'Missing Department of Labor & in extraction'
        },
        {
            'citation': '146 Wn.2d 1',
            'context': 'Ecology v. Campbell',
            'expected': 'Ecology v. Campbell',
            'issue': 'Missing Department of in extraction'
        },
        {
            'citation': '43 P.3d 4',
            'context': 'Ecology v. Campbell',
            'expected': 'Ecology v. Campbell',
            'issue': 'Missing State, Dept. of in extraction'
        },
        {
            'citation': '182 Wn.2d 342',
            'context': 'Some context here',
            'expected': 'Not extracted',
            'issue': 'No case name found'
        },
        {
            'citation': '340 P.3d 849',
            'context': 'Some context here',
            'expected': 'Not extracted',
            'issue': 'No case name found'
        },
        {
            'citation': '136 Wn.2d 152',
            'context': 'Schilling v. Radio Holdings',
            'expected': 'Schilling v. Radio Holdings',
            'issue': 'Missing Inc. in extraction'
        },
        {
            'citation': '961 P.2d 371',
            'context': 'Schilling v. Radio Holdings',
            'expected': 'Schilling v. Radio Holdings',
            'issue': 'Missing Inc. in extraction'
        },
        {
            'citation': '1 Wn. App. 678',
            'context': 'Brandt v. Impero',
            'expected': 'Brandt v. Impero',
            'issue': 'Should work correctly'
        },
        {
            'citation': '463 P.2d 197',
            'context': 'Brandt v. Impero',
            'expected': 'Brandt v. Impero',
            'issue': 'Should work correctly'
        },
        {
            'citation': '109 Wn.2d 467',
            'context': 'Dennis v. Dep',
            'expected': 'Dennis v. Dep',
            'issue': 'Missing Department of Labor & Industries in extraction'
        },
        {
            'citation': '745 P.2d 1295',
            'context': 'Dennis v. Dep',
            'expected': 'Dennis v. Dep',
            'issue': 'Missing Department of Labor & Industries in extraction'
        },
        {
            'citation': '183 Wn.2d 237',
            'context': 'Darkenwald v. Emp',
            'expected': 'Darkenwald v. Emp',
            'issue': 'Missing Employment Security Department in extraction'
        },
        {
            'citation': '350 P.3d 647',
            'context': 'Darkenwald v. Emp',
            'issue': 'Missing Employment Security Department in extraction'
        },
        {
            'citation': '166 Wn.2d 834',
            'context': 'In re Forfeiture of One',
            'expected': 'In re Forfeiture of One',
            'issue': 'Incomplete In re extraction'
        },
        {
            'citation': '215 P.3d 166',
            'context': 'In re Forfeiture of One',
            'expected': 'In re Forfeiture of One',
            'issue': 'Incomplete In re extraction'
        },
        {
            'citation': '162 Wn.2d 210',
            'context': 'Densley v. Dep',
            'expected': 'Densley v. Dep',
            'issue': 'Missing Department of Retirement Systems in extraction'
        },
        {
            'citation': '173 P.3d 885',
            'context': 'Densley v. Dep',
            'expected': 'Densley v. Dep',
            'issue': 'Missing Department of Retirement Systems in extraction'
        },
        {
            'citation': '135 Wn.2d 193',
            'context': 'Millay v. Cam',
            'expected': 'Millay v. Cam',
            'issue': 'Should work correctly'
        },
        {
            'citation': '955 P.2d 791',
            'context': 'Millay v. Cam',
            'expected': 'Millay v. Cam',
            'issue': 'Should work correctly'
        },
        {
            'citation': '130 Wn.2d 594',
            'context': 'State v. Bash',
            'expected': 'State v. Bash',
            'issue': 'Should work correctly'
        },
        {
            'citation': '925 P.2d 978',
            'context': 'Some context here',
            'expected': 'Not extracted',
            'issue': 'No case name found'
        },
        {
            'citation': '125 Wn.2d 472',
            'context': 'State v. Silva-Baltazar',
            'expected': 'State v. Silva-Baltazar',
            'issue': 'Should work correctly'
        },
        {
            'citation': '886 P.2d 138',
            'context': 'State v. Silva-Baltazar',
            'expected': 'State v. Silva-Baltazar',
            'issue': 'Should work correctly'
        },
        {
            'citation': '154 Wn. App. 752',
            'context': 'Corey v. Pierce County',
            'expected': 'Corey v. Pierce County',
            'issue': 'Should work correctly'
        },
        {
            'citation': '225 P.3d 367',
            'context': 'Corey v. Pierce County',
            'expected': 'Corey v. Pierce County',
            'issue': 'Should work correctly'
        },
        {
            'citation': '134 Wn.2d 692',
            'context': 'Some context here',
            'expected': 'Not extracted',
            'issue': 'No case name found'
        },
        {
            'citation': '952 P.2d 590',
            'context': 'Some context here',
            'expected': 'Not extracted',
            'issue': 'No case name found'
        },
        {
            'citation': '166 Wn.2d 974',
            'context': 'I note that prefiling requirements raise serious constitutional concerns. See Putman v',
            'expected': 'Putman v',
            'issue': 'Incomplete extraction'
        },
        {
            'citation': '216 P.3d 374',
            'context': 'I note that prefiling requirements raise serious constitutional concerns. See Putman v',
            'expected': 'Putman v',
            'issue': 'Incomplete extraction'
        },
        {
            'citation': '182 Wn.2d 398',
            'context': 'Id. We should view claims that the legislature created procedural prerequisites to',
            'expected': 'Not extracted',
            'issue': 'No case name found'
        },
        {
            'citation': '341 P.3d 953',
            'context': 'Id. We should view claims that the legislature created procedural prerequisites to',
            'expected': 'Not extracted',
            'issue': 'No case name found'
        },
        {
            'citation': '153 Wn.2d 689',
            'context': 'State v. Robinson',
            'expected': 'State v. Robinson',
            'issue': 'Should work correctly'
        },
        {
            'citation': '107 P.3d 90',
            'context': 'State v. Robinson',
            'expected': 'State v. Robinson',
            'issue': 'Should work correctly'
        }
    ]
    
    print("Testing case name extraction against problematic citations...")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['citation']}")
        print(f"Context: {test_case['context']}")
        print(f"Issue: {test_case['issue']}")
        
        try:
            result = extract_case_name_from_context(test_case['context'], test_case['citation'])
            print(f"Result: {result}")
            
            if result == test_case['expected']:
                print("✅ PASS")
                passed += 1
            else:
                print("❌ FAIL")
                print(f"Expected: '{test_case['expected']}'")
                print(f"Got: '{result}'")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
        
        print("-" * 50)
    
    print(f"\nSummary: {passed} passed, {failed} failed")
    print("=" * 80)

if __name__ == "__main__":
    test_problematic_citations() 