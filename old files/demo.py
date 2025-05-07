#!/usr/bin/env python3
"""
BriefCheck Demo

A simplified demonstration of the BriefCheck concept that doesn't require external dependencies.
This script shows how the tool would work without actually running a web server.
"""

# Standard library imports
import json
import re
import sys

def extract_case_citations(text):
    """Extract case citations from text using regex patterns."""
    # More flexible pattern to catch various citation formats
    pattern = r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+v\.?\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)'
    matches = re.findall(pattern, text)
    citations = [f"{match[0]} v {match[1]}" for match in matches]
    seen = set()
    unique_citations = []
    for citation in citations:
        if citation not in seen:
            seen.add(citation)
            unique_citations.append(citation)
    return unique_citations

def analyze_brief_demo(text):
    """Demo analysis of a brief."""
    citations = extract_case_citations(text)
    
    # Mock results for demonstration
    results = []
    for citation in citations:
        # Simulate different results for our test cases
        if "Pringle v JP Morgan Chase" in citation:
            # Our test hallucinated case
            results.append({
                "citation": citation,
                "is_hallucinated": True,
                "confidence": 0.85,
                "method": "summary_comparison",
                "similarity_score": 0.3,
                "summaries": [
                    "Pringle v JP Morgan Chase is about workplace discrimination...",
                    "Pringle v JP Morgan Chase is about mortgage foreclosure..."
                ]
            })
        elif "Barnes v Yahoo" in citation:
            # Our test real case
            results.append({
                "citation": citation,
                "is_hallucinated": False,
                "confidence": 0.9,
                "method": "summary_comparison",
                "similarity_score": 0.85,
                "summaries": [
                    "Barnes v Yahoo is about Section 230 immunity...",
                    "Barnes v Yahoo is about Section 230 immunity..."
                ]
            })
        else:
            # For any other case, assume it's real
            results.append({
                "citation": citation,
                "is_hallucinated": False,
                "confidence": 0.75,
                "method": "summary_comparison",
                "similarity_score": 0.8,
                "summaries": [
                    f"Summary of {citation}...",
                    f"Summary of {citation}..."
                ]
            })
    
    hallucinated_citations = [r for r in results if r["is_hallucinated"]]
    
    return {
        "total_citations": len(citations),
        "hallucinated_citations": len(hallucinated_citations),
        "results": results
    }

def main():
    """Main function to run the BriefCheck demo."""
    print("\n===== BriefCheck Demo =====\n")
    print("This is a simplified demonstration of the BriefCheck concept.")
    print("In a real implementation, you would need to install the dependencies listed in requirements.txt.")
    print("\nEnter a brief text with case citations (or use the sample):")
    print("1. Enter your own text")
    print("2. Use sample text")
    
    choice = input("\nChoice (1 or 2): ")
    
    if choice == "1":
        print("\nEnter your text (type 'END' on a new line when finished):")
        lines = []
        while True:
            line = input()
            if line == "END":
                break
            lines.append(line)
        text = "\n".join(lines)
    else:
        text = """In the case of Pringle v JP Morgan Chase, the court established an important precedent regarding workplace discrimination claims. This ruling was later cited in Barnes v Yahoo, where the court addressed the limits of Section 230 immunity for internet service providers. The Barnes decision has been influential in subsequent cases involving online platforms and user-generated content."""
        print("\nUsing sample text:")
        print(text)
    
    print("\nAnalyzing brief...")
    results = analyze_brief_demo(text)
    
    print("\n===== Analysis Results =====")
    print(f"Total citations found: {results['total_citations']}")
    print(f"Potentially hallucinated citations: {results['hallucinated_citations']}")
    
    if results['hallucinated_citations'] > 0:
        print("\nPotentially hallucinated citations:")
        for result in results['results']:
            if result['is_hallucinated']:
                print(f"- {result['citation']} (Confidence: {result['confidence']:.2f}, Similarity: {result['similarity_score']:.2f})")
    
    print("\nAll citations:")
    for i, result in enumerate(results['results']):
        status = "HALLUCINATED" if result['is_hallucinated'] else "REAL"
        print(f"{i+1}. {result['citation']} - {status} (Similarity: {result['similarity_score']:.2f})")
        print("   Summaries:")
        for j, summary in enumerate(result['summaries']):
            print(f"   - Summary {j+1}: {summary}")
        print()
    
    print("\n===== Installation Instructions =====")
    print("To run the full BriefCheck tool with web interface:")
    print("1. Install the dependencies:")
    print("   pip install -r requirements.txt")
    print("2. Run the web application:")
    print("   python app.py")
    print("3. Open your browser to http://localhost:5000")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
