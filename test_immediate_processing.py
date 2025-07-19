#!/usr/bin/env python3
"""
Test to check immediate processing decision
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.services.citation_service import CitationService

def test_immediate_processing_decision():
    """Test the immediate processing decision logic"""
    print("🔍 Testing Immediate Processing Decision")
    print("=" * 50)
    
    service = CitationService()
    
    # Test cases
    test_cases = [
        {
            "name": "Simple citation",
            "data": {
                "text": "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that...",
                "type": "text"
            }
        },
        {
            "name": "Standard test text",
            "data": {
                "text": """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)""",
                "type": "text"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        print(f"Text length: {len(test_case['data']['text'])} characters")
        print(f"Word count: {len(test_case['data']['text'].split())} words")
        
        should_process = service.should_process_immediately(test_case['data'])
        print(f"Should process immediately: {should_process}")
        
        if should_process:
            print("✅ This should be processed immediately (fast)")
        else:
            print("❌ This will be queued (slow)")
        
        print("-" * 40)

if __name__ == "__main__":
    test_immediate_processing_decision() 