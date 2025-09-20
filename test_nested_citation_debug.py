#!/usr/bin/env python3
"""
Debug test for nested citation extraction with detailed logging.
"""

import requests
import json

def test_nested_citation_with_debug():
    """Test nested citation extraction with debug enabled."""
    
    print("🔍 Testing Nested Citation Extraction with Debug")
    print("=" * 60)
    
    test_text = '''Since the statute does not provide a definition of the term, we look to dictionary definitions "ʻto determine a word's plain and ordinary meaning.ʼ" State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) (quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991)).'''
    
    print(f"📝 Input Text:")
    print(f"   {test_text}")
    print(f"   Length: {len(test_text)} characters")
    
    # Let's analyze the structure manually first
    print(f"\n🔍 Manual Analysis:")
    print(f"   Expected case 1: 'State v. M.Y.G.' for citations 199 Wn.2d 528, 509 P.3d 818 (2022)")
    print(f"   Expected case 2: 'Am. Legion Post No. 32 v. City of Walla Walla' for citations 116 Wn.2d 1, 802 P.2d 784 (1991)")
    
    # Find the positions of the citations
    citations_to_find = [
        "199 Wn.2d 528",
        "509 P.3d 818", 
        "116 Wn.2d 1",
        "802 P.2d 784"
    ]
    
    print(f"\n📍 Citation Positions:")
    for citation in citations_to_find:
        pos = test_text.find(citation)
        if pos != -1:
            print(f"   '{citation}' at position {pos}")
            # Show context around citation
            context_start = max(0, pos - 100)
            context_end = min(len(test_text), pos + len(citation) + 50)
            context = test_text[context_start:context_end]
            print(f"     Context: '...{context}...'")
        else:
            print(f"   '{citation}' NOT FOUND")
    
    # Check for parenthetical structure
    print(f"\n🔍 Parenthetical Analysis:")
    quoting_pos = test_text.find("quoting")
    if quoting_pos != -1:
        print(f"   'quoting' found at position {quoting_pos}")
        after_quoting = test_text[quoting_pos:]
        print(f"   Text after 'quoting': '{after_quoting}'")
    
    # Find parentheses
    paren_positions = []
    for i, char in enumerate(test_text):
        if char == '(':
            paren_positions.append(('open', i))
        elif char == ')':
            paren_positions.append(('close', i))
    
    print(f"   Parentheses positions: {paren_positions}")
    
    try:
        print(f"\n📤 Submitting to API...")
        
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text, "type": "text"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        citations = data.get('citations', [])
        
        print(f"\n📊 API Results:")
        print(f"   Citations found: {len(citations)}")
        
        # Analyze each citation in detail
        for i, citation in enumerate(citations, 1):
            citation_text = citation.get('citation', 'N/A')
            extracted_name = citation.get('extracted_case_name', 'N/A')
            extracted_date = citation.get('extracted_date', 'N/A')
            
            print(f"\n   Citation {i}: '{citation_text}'")
            print(f"     Extracted name: '{extracted_name}'")
            print(f"     Extracted date: '{extracted_date}'")
            
            # Check if this is correct
            if citation_text in ["116 Wn.2d 1", "802 P.2d 784"]:
                expected_name = "Am. Legion Post No. 32 v. City of Walla Walla"
                if extracted_name == expected_name:
                    print(f"     ✅ CORRECT: Expected '{expected_name}'")
                else:
                    print(f"     ❌ INCORRECT: Expected '{expected_name}', got '{extracted_name}'")
            elif citation_text in ["199 Wn.2d 528", "509 P.3d 818"]:
                expected_name = "State v. M.Y.G."
                if extracted_name == expected_name:
                    print(f"     ✅ CORRECT: Expected '{expected_name}'")
                else:
                    print(f"     ❌ INCORRECT: Expected '{expected_name}', got '{extracted_name}'")
        
        return True
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run nested citation debug test."""
    
    print("🚀 Nested Citation Extraction Debug")
    print("=" * 70)
    
    success = test_nested_citation_with_debug()
    
    print("\n" + "=" * 70)
    print("📋 DEBUG TEST RESULTS")
    print("=" * 70)
    
    if success:
        print("✅ Test completed - check results above")
        print("🔍 If case names are still wrong, the fix needs more work")
    else:
        print("❌ Test failed - check error messages above")
    
    return success

if __name__ == "__main__":
    main()
