#!/usr/bin/env python3
"""
Analyze exact character requirements for citation context
"""

def analyze_bourguignon_example():
    """Analyze the exact character requirements for the Bourguignon citation"""
    
    # The actual text from the PDF
    text = """Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)"""
    
    # Find the citation position
    citation = "114 A.D.3d 947"
    citation_pos = text.find(citation)
    
    print("=== Character Analysis for Bourguignon Example ===")
    print(f"Full text: '{text}'")
    print(f"Citation: '{citation}'")
    print(f"Citation position: {citation_pos}")
    print()
    
    # Calculate characters needed before citation
    case_name = "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc."
    case_name_start = text.find(case_name)
    case_name_end = case_name_start + len(case_name)
    
    print(f"Case name: '{case_name}'")
    print(f"Case name position: {case_name_start} to {case_name_end}")
    print(f"Case name length: {len(case_name)} characters")
    print()
    
    # Calculate characters needed after citation
    year_text = "(3d Dep't 2014)"
    year_start = text.find(year_text)
    year_end = year_start + len(year_text)
    
    print(f"Year text: '{year_text}'")
    print(f"Year position: {year_start} to {year_end}")
    print(f"Year length: {len(year_text)} characters")
    print()
    
    # Calculate exact requirements
    chars_before_citation = citation_pos - case_name_start
    chars_after_citation = year_end - (citation_pos + len(citation))
    
    print("=== Exact Character Requirements ===")
    print(f"Characters needed BEFORE citation: {chars_before_citation}")
    print(f"  (from case name start to citation start)")
    print(f"Characters needed AFTER citation: {chars_after_citation}")
    print(f"  (from citation end to year end)")
    print()
    
    # Show what each window would capture
    print("=== What Each Window Captures ===")
    
    # Before citation window
    before_start = max(0, citation_pos - chars_before_citation)
    before_text = text[before_start:citation_pos]
    print(f"Before citation ({chars_before_citation} chars): '{before_text}'")
    
    # After citation window
    after_end = min(len(text), citation_pos + len(citation) + chars_after_citation)
    after_text = text[citation_pos + len(citation):after_end]
    print(f"After citation ({chars_after_citation} chars): '{after_text}'")
    
    # Combined context
    combined_text = text[before_start:after_end]
    print(f"Combined context ({len(combined_text)} chars): '{combined_text}'")
    print()
    
    # Compare with our current settings
    print("=== Comparison with Current Settings ===")
    print(f"Current before window: 300 characters")
    print(f"Current after window: 100 characters")
    print(f"Required before window: {chars_before_citation} characters")
    print(f"Required after window: {chars_after_citation} characters")
    print()
    
    if chars_before_citation <= 300:
        print("✅ Current before window (300) is sufficient")
    else:
        print(f"❌ Current before window (300) is too small, need {chars_before_citation}")
        
    if chars_after_citation <= 100:
        print("✅ Current after window (100) is sufficient")
    else:
        print(f"❌ Current after window (100) is too small, need {chars_after_citation}")
    
    return chars_before_citation, chars_after_citation

def analyze_realistic_example():
    """Analyze a more realistic document context"""
    
    # More realistic text with surrounding content
    text = """The district court, however, misinterpreted the law relating to the loss of earnings, ignoring Section 14 of the New York workers' Compensation Law, which permits compensation as a minimum wage worker when an injured worker lacks wage records for the prior year. Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014). Specifically, the District Court overlooked key factors before its dismissal."""
    
    citation = "114 A.D.3d 947"
    citation_pos = text.find(citation)
    
    print("\n=== Realistic Document Analysis ===")
    print(f"Citation position: {citation_pos}")
    print()
    
    # Find the case name in the realistic context
    case_name = "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc."
    case_name_start = text.find(case_name)
    
    # Find the year in the realistic context
    year_text = "(3d Dep't 2014)"
    year_start = text.find(year_text)
    year_end = year_start + len(year_text)
    
    # Calculate requirements
    chars_before_citation = citation_pos - case_name_start
    chars_after_citation = year_end - (citation_pos + len(citation))
    
    print(f"Case name position: {case_name_start}")
    print(f"Year position: {year_start} to {year_end}")
    print(f"Characters needed BEFORE citation: {chars_before_citation}")
    print(f"Characters needed AFTER citation: {chars_after_citation}")
    print()
    
    # Show what a 300/100 window would capture
    before_start = max(0, citation_pos - 300)
    after_end = min(len(text), citation_pos + len(citation) + 100)
    
    before_text = text[before_start:citation_pos]
    after_text = text[citation_pos + len(citation):after_end]
    
    print("=== What 300/100 Window Captures ===")
    print(f"Before (300 chars): '{before_text}'")
    print(f"After (100 chars): '{after_text}'")
    print()
    
    # Check if case name and year are captured
    case_name_in_before = case_name in before_text
    year_in_after = year_text in after_text
    
    print("=== Capture Analysis ===")
    print(f"Case name captured in before window: {'✅ YES' if case_name_in_before else '❌ NO'}")
    print(f"Year captured in after window: {'✅ YES' if year_in_after else '❌ NO'}")
    
    if case_name_in_before and year_in_after:
        print("\n🎉 SUCCESS: Both case name and year would be captured!")
    else:
        print("\n⚠️  ISSUE: One or both elements would be missed!")
    
    return chars_before_citation, chars_after_citation

if __name__ == "__main__":
    print("Analyzing character requirements for citation context...")
    print()
    
    # Analyze the simple example
    simple_before, simple_after = analyze_bourguignon_example()
    
    # Analyze the realistic example
    realistic_before, realistic_after = analyze_realistic_example()
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print(f"Simple example - Before: {simple_before} chars, After: {simple_after} chars")
    print(f"Realistic example - Before: {realistic_before} chars, After: {realistic_after} chars")
    print()
    print("Current settings (300/100) should be sufficient for both examples.") 