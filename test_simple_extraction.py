#!/usr/bin/env python3
"""
Simple test to understand the extraction issue.
"""

import re

def test_manual_pattern_matching():
    """Test manual pattern matching to understand the issue."""
    
    print("🔍 Manual Pattern Matching Test")
    print("=" * 50)
    
    test_text = '''Since the statute does not provide a definition of the term, we look to dictionary definitions "ʻto determine a word's plain and ordinary meaning.ʼ" State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) (quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991)).'''
    
    # Find the problematic citations
    citations = ["116 Wn.2d 1", "802 P.2d 784"]
    
    for citation in citations:
        pos = test_text.find(citation)
        print(f"\n📍 Citation '{citation}' at position {pos}")
        
        if pos != -1:
            # Method 1: Look for "quoting" pattern
            text_before = test_text[:pos]
            quoting_match = re.search(r'quoting\s+([^,]+(?:,\s*\d+\s+[A-Za-z.]+\s+\d+)?)', text_before)
            
            if quoting_match:
                quoted_text = quoting_match.group(1).strip()
                print(f"   Method 1 - Quoting pattern: '{quoted_text}'")
                
                # Extract case name from quoted text
                case_match = re.search(r'^([A-Z][^,]+v\.\s+[A-Z][^,]+)', quoted_text)
                if case_match:
                    case_name = case_match.group(1).strip()
                    print(f"   ✅ Extracted case name: '{case_name}'")
                else:
                    print(f"   ❌ Could not extract case name from quoted text")
            
            # Method 2: Look for parenthetical context
            # Find the last opening parenthesis before the citation
            paren_pos = text_before.rfind('(')
            if paren_pos != -1:
                paren_context = test_text[paren_pos:pos + len(citation) + 10]
                print(f"   Method 2 - Parenthetical context: '{paren_context}'")
                
                # Look for case name in parenthetical
                paren_case_match = re.search(r'\(\s*quoting\s+([A-Z][^,]+v\.\s+[A-Z][^,]+)', paren_context)
                if paren_case_match:
                    paren_case_name = paren_case_match.group(1).strip()
                    print(f"   ✅ Parenthetical case name: '{paren_case_name}'")

def create_improved_extraction_function():
    """Create an improved extraction function for nested citations."""
    
    print(f"\n🔧 Creating Improved Extraction Function")
    print("=" * 50)
    
    def extract_case_name_for_nested_citation(text, citation, start_index, end_index):
        """Extract case name for potentially nested citations."""
        
        # Check if this citation is in a "quoting" context
        text_before_citation = text[:start_index]
        
        # Look for "quoting" pattern
        quoting_match = re.search(r'quoting\s+([A-Z][^,]+v\.\s+[A-Z][^,]+)', text_before_citation)
        
        if quoting_match:
            # This appears to be a quoted/nested citation
            quoted_case_name = quoting_match.group(1).strip()
            
            # Verify this case name is close to our citation
            quoting_pos = quoting_match.start()
            distance_to_citation = start_index - quoting_pos
            
            # If the quoting is within reasonable distance (e.g., 200 chars), use it
            if distance_to_citation < 200:
                return quoted_case_name
        
        # Fallback to regular extraction
        # Look backwards for case name pattern
        context_start = max(0, start_index - 300)
        context = text[context_start:end_index + 50]
        
        # Standard case name patterns
        patterns = [
            r'([A-Z][a-zA-Z\'\.\&\s]+)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+)',
            r'(In\s+re\s+[A-Z][a-zA-Z\'\.\&\s]+)'
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, context))
            if matches:
                # Find closest match to citation
                citation_pos_in_context = start_index - context_start
                best_match = None
                min_distance = float('inf')
                
                for match in matches:
                    distance = abs(match.end() - citation_pos_in_context)
                    if distance < min_distance:
                        min_distance = distance
                        best_match = match
                
                if best_match:
                    if best_match.group(0).startswith('In re'):
                        return best_match.group(0)
                    else:
                        plaintiff = best_match.group(1).strip()
                        defendant = best_match.group(2).strip()
                        return f"{plaintiff} v. {defendant}"
        
        return None
    
    # Test the improved function
    test_text = '''Since the statute does not provide a definition of the term, we look to dictionary definitions "ʻto determine a word's plain and ordinary meaning.ʼ" State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) (quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991)).'''
    
    test_cases = [
        {"citation": "199 Wn.2d 528", "expected": "State v. M.Y.G."},
        {"citation": "509 P.3d 818", "expected": "State v. M.Y.G."},
        {"citation": "116 Wn.2d 1", "expected": "Am. Legion Post No. 32 v. City of Walla Walla"},
        {"citation": "802 P.2d 784", "expected": "Am. Legion Post No. 32 v. City of Walla Walla"}
    ]
    
    print(f"🧪 Testing Improved Function:")
    
    for test_case in test_cases:
        citation = test_case["citation"]
        expected = test_case["expected"]
        
        start_pos = test_text.find(citation)
        if start_pos != -1:
            end_pos = start_pos + len(citation)
            
            extracted = extract_case_name_for_nested_citation(test_text, citation, start_pos, end_pos)
            
            status = "✅" if extracted == expected else "❌"
            print(f"   {status} '{citation}': Expected '{expected}', Got '{extracted}'")
        else:
            print(f"   ❌ '{citation}': Not found in text")
    
    return extract_case_name_for_nested_citation

def main():
    """Run simple extraction tests."""
    
    print("🚀 Simple Extraction Analysis")
    print("=" * 60)
    
    # Test manual pattern matching
    test_manual_pattern_matching()
    
    # Create and test improved function
    improved_function = create_improved_extraction_function()
    
    print("\n" + "=" * 60)
    print("📋 ANALYSIS RESULTS")
    print("=" * 60)
    print("✅ Manual pattern matching shows the issue can be solved")
    print("✅ Improved extraction function created")
    print("🔧 Next step: Integrate this logic into the main extraction pipeline")

if __name__ == "__main__":
    main()
