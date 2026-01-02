#!/usr/bin/env python3
"""
Comprehensive contamination check to identify and fix remaining contamination issues
"""

import requests
import json
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_contamination_scenarios():
    """Test multiple contamination scenarios to identify patterns"""
    
    print("🔍 COMPREHENSIVE CONTAMINATION CHECK")
    print("=" * 60)
    
    # Test scenarios with different document structures
    test_cases = [
        {
            "name": "Simple Document with Clear Primary Case",
            "document": """
            IN THE SUPREME COURT OF THE UNITED STATES
            
            Smith v. Jones
            
            No. 23-456
            
            Filed: January 15, 2024
            
            The court considered precedent from Brown v. Board, 347 U.S. 483 (1954) 
            and also referenced Roe v. Wade, 410 U.S. 113 (1973).
            """,
            "primary_case": "Smith v. Jones",
            "expected_citations": ["347 U.S. 483", "410 U.S. 113"],
            "should_not_contain": ["Smith v. Jones"]
        },
        {
            "name": "Washington Court Document",
            "document": """
            IN THE COURT OF APPEALS OF THE STATE OF WASHINGTON
            DIVISION II
            
            CITY OF BELLEVUE v. LORANG
            
            No. 59366-1-II
            
            Filed: November 4, 2002
            
            In this case involving municipal liability, the court considered 
            precedent from Berst v. Snohomish County, 114 Wn. App. 245 and 
            related cases like 57 P.3d 273. Additionally, the court referenced 
            State v. Manussier, 129 Wn.2d 652 in its analysis.
            
            The court also considered federal precedent including 161 F.3d 584 
            in its environmental law analysis.
            """,
            "primary_case": "CITY OF BELLEVUE v. LORANG",
            "expected_citations": ["114 Wn. App. 245", "57 P.3d 273", "129 Wn.2d 652", "161 F.3d 584"],
            "should_not_contain": ["CITY OF BELLEVUE", "BELLEVUE v. LORANG"]
        },
        {
            "name": "Federal Document with Multiple Citations",
            "document": """
            UNITED STATES COURT OF APPEALS
            FOR THE NINTH CIRCUIT
            
            Google LLC v. Oracle America, Inc.
            
            No. 18-956
            
            Argued and Submitted March 24, 2020
            Filed April 5, 2021
            
            The court analyzed copyright issues in technology, referencing 
            earlier cases like Sony Corp. v. Universal City Studios, 464 U.S. 417 (1984)
            and Apple Computer, Inc. v. Franklin Computer Corp., 714 F.2d 1240 (3d Cir. 1983).
            """,
            "primary_case": "Google LLC v. Oracle America, Inc.",
            "expected_citations": ["464 U.S. 417", "714 F.2d 1240"],
            "should_not_contain": ["Google LLC", "Google v. Oracle"]
        }
    ]
    
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    total_contamination = 0
    total_citations = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print("-" * 50)
        
        try:
            response = requests.post(
                api_url,
                json={"text": test_case['document']},
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                citations = result.get('citations', [])
                
                print(f"Found {len(citations)} citations")
                
                case_contamination = 0
                for cit in citations:
                    citation_text = cit.get('citation', 'N/A')
                    case_name = cit.get('extracted_case_name', 'N/A')
                    
                    # Check for contamination
                    is_contaminated = False
                    for forbidden in test_case['should_not_contain']:
                        if forbidden.upper() in case_name.upper():
                            is_contaminated = True
                            break
                    
                    if is_contaminated:
                        case_contamination += 1
                        total_contamination += 1
                        print(f"  ❌ {citation_text} → '{case_name}' (CONTAMINATED)")
                    elif case_name == 'N/A':
                        print(f"  ⚠️  {citation_text} → '{case_name}' (no extraction)")
                    else:
                        print(f"  ✅ {citation_text} → '{case_name}' (clean)")
                    
                    total_citations += 1
                
                contamination_rate = (case_contamination / len(citations) * 100) if citations else 0
                print(f"Contamination rate: {contamination_rate:.1f}% ({case_contamination}/{len(citations)})")
                
            else:
                print(f"❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("📊 OVERALL CONTAMINATION SUMMARY")
    print("=" * 60)
    print(f"Total citations tested: {total_citations}")
    print(f"Total contaminated: {total_contamination}")
    
    if total_citations > 0:
        overall_rate = (total_contamination / total_citations) * 100
        print(f"Overall contamination rate: {overall_rate:.1f}%")
        
        if overall_rate == 0:
            print("🎉 PERFECT! No contamination detected!")
        elif overall_rate < 10:
            print("✅ GOOD! Low contamination rate")
        elif overall_rate < 25:
            print("⚠️  MODERATE contamination - needs attention")
        else:
            print("❌ HIGH contamination - needs immediate fix")
    
    return total_contamination, total_citations

def identify_contamination_patterns():
    """Identify specific patterns causing contamination"""
    
    print("\n🔍 ANALYZING CONTAMINATION PATTERNS")
    print("=" * 50)
    
    # Test the problematic URL to see specific patterns
    pdf_url = "http://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    try:
        response = requests.post(
            api_url,
            json={"url": pdf_url},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            contaminated = []
            clean = []
            
            for cit in citations:
                citation_text = cit.get('citation', 'N/A')
                case_name = cit.get('extracted_case_name', 'N/A')
                
                if 'BELLEVUE' in case_name.upper() or 'LORANG' in case_name.upper():
                    contaminated.append((citation_text, case_name))
                else:
                    clean.append((citation_text, case_name))
            
            print(f"Analysis of PDF with {len(citations)} citations:")
            print(f"Contaminated: {len(contaminated)}")
            print(f"Clean: {len(clean)}")
            
            if contaminated:
                print("\n❌ CONTAMINATED CITATIONS:")
                for citation, case_name in contaminated:
                    print(f"  {citation} → '{case_name}'")
                
                # Analyze patterns
                print("\n🔧 PATTERN ANALYSIS:")
                bellevue_citations = [c for c in contaminated if 'BELLEVUE' in c[1].upper()]
                lorang_citations = [c for c in contaminated if 'LORANG' in c[1].upper()]
                
                print(f"Citations with 'BELLEVUE': {len(bellevue_citations)}")
                print(f"Citations with 'LORANG': {len(lorang_citations)}")
                
                # Check if these are actually parallel citations to the main case
                print("\n🤔 CHECKING IF CONTAMINATION IS VALID:")
                for citation, case_name in contaminated:
                    # These might actually be legitimate parallel citations
                    if any(x in citation for x in ['140 Wn.2d 19', '992 P.2d 496']):
                        print(f"  {citation} → '{case_name}' (likely LEGITIMATE parallel citation)")
                    else:
                        print(f"  {citation} → '{case_name}' (likely INVALID contamination)")
            
            return contaminated, clean
            
    except Exception as e:
        print(f"❌ Error analyzing PDF: {e}")
        return [], []

if __name__ == "__main__":
    # Run comprehensive check
    total_contam, total_cits = test_contamination_scenarios()
    
    # Analyze specific patterns
    contaminated, clean = identify_contamination_patterns()
    
    # Provide recommendations
    print("\n🎯 RECOMMENDATIONS")
    print("=" * 30)
    
    if total_contam == 0:
        print("✅ No contamination fixes needed!")
    else:
        print(f"⚠️  {total_contam} contaminated citations need fixing")
        print("\nPotential fixes:")
        print("1. Improve document primary case name detection")
        print("2. Enhance contamination filter patterns")
        print("3. Add parallel citation detection logic")
        print("4. Fine-tune context isolation boundaries")
