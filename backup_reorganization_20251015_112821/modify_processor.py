#!/usr/bin/env python3
"""
Modify the unified_citation_processor_v2.py to fix context extraction.
"""

def modify_file():
    with open('src/unified_citation_processor_v2.py', 'r') as f:
        content = f.read()
    
    # Find the isolated_context assignment in _extract_metadata
    lines = content.split('\n')
    
    # Look for the specific pattern
    target_pattern = 'isolated_context = text[context_start:citation_pos].strip()'
    
    for i, line in enumerate(lines):
        if target_pattern in line and 'citation_pos' in lines[i-2]:  # Make sure it's the right one
            print(f"Found target line at {i+1}: {line.strip()}")
            
            # Replace with improved logic
            improved_logic = '''                            # Smart context extraction that respects parentheses
                            context_start = max(0, citation_pos - 300)
                            full_context = text[context_start:citation_pos].strip()
                            
                            # Check if citation is in parentheses with legal keywords
                            before_citation = text[:citation_pos]
                            legal_keywords = ['quoting', 'citing', 'cited in', 'see', 'accord', 'but see', 'cf.', 'compare', 'contrast']
                            
                            # Find innermost parentheses containing legal keywords
                            paren_start = -1
                            i_idx = len(before_citation) - 1
                            while i_idx >= 0:
                                if before_citation[i_idx] == ')':
                                    # Find matching opening paren
                                    nest_level = 1
                                    j = i_idx - 1
                                    while j >= 0:
                                        if before_citation[j] == ')':
                                            nest_level += 1
                                        elif before_citation[j] == '(':
                                            nest_level -= 1
                                            if nest_level == 0:
                                                paren_content = text[j:i_idx+1].lower()
                                                if any(keyword in paren_content for keyword in legal_keywords):
                                                    paren_start = j
                                                    break
                                        j -= 1
                                    break
                                i_idx -= 1
                            
                            if paren_start != -1:
                                # Use context within the legal parentheses
                                isolated_context = text[paren_start:citation_pos].strip()
                            else:
                                isolated_context = full_context'''
            
            # Replace the line
            lines[i] = improved_logic
            break
    
    # Write back
    with open('src/unified_citation_processor_v2.py', 'w') as f:
        f.write('\n'.join(lines))
    
    print("Modified file successfully")

if __name__ == "__main__":
    modify_file()
