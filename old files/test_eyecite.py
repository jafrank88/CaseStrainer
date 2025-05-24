"""
Test script to check if eyecite is working properly.
"""

try:
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer, default_tokenizer

    print("Successfully imported eyecite")

    # Test with a simple citation
    test_text = "The court in Barnes v. Yahoo!, Inc., 570 F.3d 1096 (9th Cir. 2009) held that..."

    # Use the default tokenizer
    tokenizer = default_tokenizer

    # Extract citations
    citations = get_citations(test_text, tokenizer=tokenizer)

    print(f"Found {len(citations)} citations:")
    for citation in citations:
        print(f"- {citation}")
        if hasattr(citation, "corrected_citation") and citation.corrected_citation():
            print(f"  Corrected: {citation.corrected_citation()}")
        elif hasattr(citation, "matched_text") and citation.matched_text:
            print(f"  Matched text: {citation.matched_text}")

except ImportError as e:
    print(f"Error importing eyecite: {e}")
except Exception as e:
    print(f"Error using eyecite: {e}")
