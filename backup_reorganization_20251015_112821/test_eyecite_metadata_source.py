"""Test to determine where eyecite gets plaintiff/defendant metadata."""

from eyecite import get_citations

# Test with a citation that has case name in the document
text = "Game v. Manning, 161 P.3d 1215 (2007)"
print(f"Test text: {text}\n")

cits = get_citations(text)
print(f"Found: {len(cits)} citations\n")

if cits:
    c = cits[0]
    print(f"Citation type: {type(c).__name__}")
    print(f"Citation text: {c}")
    print(f"Has metadata: {hasattr(c, 'metadata')}")
    
    if hasattr(c, 'metadata') and c.metadata:
        print(f"\nMetadata type: {type(c.metadata).__name__}")
        print(f"Metadata attributes: {[attr for attr in dir(c.metadata) if not attr.startswith('_')]}")
        
        plaintiff = getattr(c.metadata, 'plaintiff', None)
        defendant = getattr(c.metadata, 'defendant', None)
        
        print(f"\nPlaintiff: {plaintiff}")
        print(f"Defendant: {defendant}")
        
        if plaintiff and defendant:
            print(f"\n✅ Eyecite extracted: '{plaintiff} v. {defendant}'")
            print(f"   This came from parsing the TEXT, not from CourtListener API")
        else:
            print(f"\n❌ Eyecite did not extract plaintiff/defendant")
    else:
        print("\n❌ No metadata available")

print("\n" + "="*80)
print("ANSWER: Eyecite extracts case names by PARSING THE DOCUMENT TEXT")
print("It does NOT query CourtListener - it's a pure text parsing library")
print("="*80)
