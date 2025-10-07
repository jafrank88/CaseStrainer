import sys
sys.path.append('src')
from pdfminer.high_level import extract_text as pdfminer_extract_text

try:
    from eyecite import get_citations
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

print('🔍 HUNTING FOR OFF-BY-ONE ERROR CREATING PHANTOM CITATION')
print('=' * 60)

text = pdfminer_extract_text('1033940.pdf')

# Let's simulate the exact eyecite processing logic to find the bug
if EYECITE_AVAILABLE:
    print('📋 SIMULATING EYECITE PROCESSING:')
    
    # Get eyecite results for the problem area
    context_start = 25000
    context_end = 25100
    context_text = text[context_start:context_end]
    
    citations = get_citations(context_text)
    
    for citation in citations:
        citation_str = str(citation)
        if '59 P.3d 655' in citation_str:
            print(f'\n🎯 Found target citation: {citation}')
            
            # Extract citation text (simulate _extract_citation_text_from_eyecite)
            import re
            full_case_match = re.search(r"FullCaseCitation\('([^']+)'", citation_str)
            if full_case_match:
                citation_text = full_case_match.group(1)
                print(f'   Extracted text: "{citation_text}"')
                
                # Simulate the problematic text.find() logic
                print(f'\n🔍 SIMULATING text.find() LOGIC:')
                
                # This is the exact logic from _extract_with_eyecite
                start_pos = text.find(citation_text)
                print(f'   text.find("{citation_text}") = {start_pos}')
                
                if start_pos != -1:
                    end_pos = start_pos + len(citation_text)
                    print(f'   Calculated end_pos: {end_pos}')
                    print(f'   Citation length: {len(citation_text)}')
                    
                    # Extract what would be stored
                    extracted = text[start_pos:end_pos]
                    print(f'   Extracted from text[{start_pos}:{end_pos}]: "{extracted}"')
                    
                    # Check for off-by-one errors in nearby positions
                    print(f'\n🔍 CHECKING NEARBY POSITIONS FOR OFF-BY-ONE:')
                    for offset in [-2, -1, 0, 1, 2]:
                        test_start = start_pos + offset
                        test_end = test_start + len(citation_text)
                        if test_start >= 0 and test_end < len(text):
                            test_extracted = text[test_start:test_end]
                            print(f'   Offset {offset:+d}: text[{test_start}:{test_end}] = "{test_extracted}"')
                            if test_extracted == "9 P.3d 655":
                                print(f'     🎯 PHANTOM FOUND AT OFFSET {offset}!')
                
                else:
                    print('   text.find() returned -1, would trigger normalization')

# Now let's check if there are any string slicing operations that could cause this
print(f'\n🔍 CHECKING FOR PROBLEMATIC STRING OPERATIONS:')

# Test the exact positions we know about
correct_pos = 25037  # Position of "59 P.3d 655"
phantom_pos = 25038   # Position of "9 P.3d 655"

print(f'Correct citation at {correct_pos}: "{text[correct_pos:correct_pos+11]}"')
print(f'Phantom citation at {phantom_pos}: "{text[phantom_pos:phantom_pos+10]}"')

# Check if any code might be doing text[pos+1:] instead of text[pos:]
print(f'\n🔍 TESTING COMMON OFF-BY-ONE PATTERNS:')
test_patterns = [
    ("text[pos:]", text[correct_pos:correct_pos+11]),
    ("text[pos+1:]", text[correct_pos+1:correct_pos+1+11]),
    ("text[pos-1:]", text[correct_pos-1:correct_pos-1+11]),
    ("Wrong end calc", text[correct_pos:correct_pos+10]),  # len-1 error
    ("Wrong start+end", text[correct_pos+1:correct_pos+11]),  # start+1, same end
]

for description, result in test_patterns:
    print(f'   {description}: "{result}"')
    if result == "9 P.3d 655":
        print(f'     🎯 PHANTOM PATTERN FOUND: {description}')
    elif "9 P.3d 655" in result:
        print(f'     🎯 PHANTOM SUBSTRING FOUND: {description}')

print(f'\n💡 ANALYSIS:')
print('The phantom "9 P.3d 655" is exactly "59 P.3d 655"[1:] (first character removed)')
print('This suggests the bug is in position calculation where:')
print('- start_pos is calculated correctly')
print('- But the text extraction uses start_pos+1 instead of start_pos')
print('- OR the text slicing has an off-by-one error')






