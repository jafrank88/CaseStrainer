# DEPRECATED: This file has been consolidated into src/citation_utils_consolidated.py
# Please use: from src.citation_utils_consolidated import validate_citation
import warnings
warnings.warn(
    "validate_citation.py is deprecated. Use citation_utils_consolidated.py instead.",
    DeprecationWarning,
    stacklevel=2
)

from eyecite import get_citations
from eyecite.tokenizers import AhocorasickTokenizer


def validate_citation(citation_text):
    """Validate a citation using eyecite."""
    # Initialize the tokenizer
    tokenizer = AhocorasickTokenizer()

    # Get citations
    citations = get_citations(citation_text, tokenizer=tokenizer)

    # Process the results
    if citations:
        citation = citations[0]  # Get the first citation
        return {
            "valid": True,
            "citation_text": citation.matched_text(),
            "corrected_citation": (
                citation.corrected_citation()
                if hasattr(citation, "corrected_citation")
                else None
            ),
            "citation_type": type(citation).__name__,
            "metadata": {
                "reporter": getattr(citation, "reporter", None),
                "volume": getattr(citation, "volume", None),
                "page": getattr(citation, "page", None),
                "year": getattr(citation, "year", None),
                "court": getattr(citation, "court", None),
            },
        }
    else:
        return {"valid": False, "error": "No valid citation found"}


if __name__ == "__main__":
    # Test the citation
    citation = "National Cable & Telecommunications Assn. v. Brand X Internet Services, 545 U. S. 967, 982"
    result = validate_citation(citation)

    # Print the results
    print("\nCitation Validation Results:")
    print("-" * 50)
    print(f"Original citation: {citation}")
    print(f"Valid: {result['valid']}")
    if result["valid"]:
        print(f"Matched text: {result['citation_text']}")
        print(f"Corrected citation: {result['corrected_citation']}")
        print(f"Citation type: {result['citation_type']}")
        print("\nMetadata:")
        for key, value in result["metadata"].items():
            print(f"  {key}: {value}")
    else:
        print(f"Error: {result['error']}")
