"""Test eyecite metadata extraction"""
from eyecite import get_citations

text = "See Erie Railroad Co. v. Tompkins, 304 U.S. 64 (1938)"

citations = list(get_citations(text))
for cit in citations:
    print(f"\nCitation: {cit}")
    print(f"  Type: {type(cit).__name__}")
    print(f"  Has metadata: {hasattr(cit, 'metadata')}")
    if hasattr(cit, 'metadata'):
        print(f"  Metadata type: {type(cit.metadata)}")
        print(f"  Metadata: {cit.metadata}")
        if cit.metadata:
            print(f"  Plaintiff: {getattr(cit.metadata, 'plaintiff', None)}")
            print(f"  Defendant: {getattr(cit.metadata, 'defendant', None)}")
            print(f"  Year: {getattr(cit.metadata, 'year', None)}")
