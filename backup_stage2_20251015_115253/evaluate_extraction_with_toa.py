"""
Evaluate case name extraction quality using Table of Authorities as ground truth
Uses Washington legal briefs from wa_briefs_text directory
"""
import os
import re
from pathlib import Path
from difflib import SequenceMatcher

def extract_table_of_authorities(text):
    """Extract case names from Table of Authorities section"""
    # Find TOA section
    toa_patterns = [
        r'TABLE OF AUTHORITIES(.*?)(?=TABLE OF|INTRODUCTION|STATEMENT OF|I\.|A\.|^[A-Z][A-Z\s]{10,}$)',
        r'Table of Authorities(.*?)(?=Table of|Introduction|Statement of|I\.|A\.|^[A-Z][A-Z\s]{10,}$)',
    ]
    
    toa_text = None
    for pattern in toa_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            toa_text = match.group(1)
            break
    
    if not toa_text:
        return []
    
    # Extract case names (typically in format: Case Name v. Case Name, citation)
    # Common patterns in TOA:
    # - Name v. Name, citation
    # - Name v. Name
    case_pattern = r'([A-Z][A-Za-z\.\s,&]+?\s+v\.?\s+[A-Z][A-Za-z\.\s,&]+?)(?:,|\s+\d+)'
    
    cases = re.findall(case_pattern, toa_text)
    
    # Clean up case names
    cleaned_cases = []
    for case in cases:
        # Remove extra whitespace
        case = re.sub(r'\s+', ' ', case.strip())
        # Remove trailing punctuation
        case = case.rstrip('.,;:')
        # Skip if too short or doesn't look like a case name
        if len(case) > 10 and ' v' in case.lower():
            cleaned_cases.append(case)
    
    return list(set(cleaned_cases))  # Remove duplicates

def similarity(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def evaluate_extraction(brief_path):
    """Evaluate extraction quality for a single brief"""
    print(f"\n{'='*80}")
    print(f"EVALUATING: {os.path.basename(brief_path)}")
    print(f"{'='*80}")
    
    # Read the brief
    with open(brief_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    print(f"📄 Brief length: {len(text):,} characters")
    
    # Extract ground truth from TOA
    toa_cases = extract_table_of_authorities(text)
    print(f"\n✅ Found {len(toa_cases)} cases in Table of Authorities (ground truth)")
    
    if len(toa_cases) > 0:
        print(f"\nFirst 5 from TOA:")
        for i, case in enumerate(toa_cases[:5], 1):
            print(f"  {i}. {case}")
    
    if len(toa_cases) == 0:
        print("⚠️  No Table of Authorities found - skipping this brief")
        return None
    
    # Extract using our tools (NO VERIFICATION)
    print(f"\n🔧 Running our extraction...")
    from src.citation_extraction_endpoint import extract_citations_production
    
    result = extract_citations_production(text)
    extracted = result.get('citations', [])
    
    print(f"✅ Found {len(extracted)} citations with our extractor")
    
    # Compare extracted case names to TOA
    print(f"\n📊 COMPARING EXTRACTION TO GROUND TRUTH")
    print(f"{'='*80}")
    
    matches = []
    partial_matches = []
    mismatches = []
    
    for toa_case in toa_cases:
        best_match = None
        best_score = 0
        best_extracted = None
        
        # Find best matching extracted case name
        for cite in extracted:
            extracted_name = cite.get('extracted_case_name', '')
            if not extracted_name or extracted_name == 'N/A':
                continue
            
            score = similarity(toa_case, extracted_name)
            if score > best_score:
                best_score = score
                best_match = extracted_name
                best_extracted = cite
        
        if best_score >= 0.8:
            matches.append((toa_case, best_match, best_score))
        elif best_score >= 0.5:
            partial_matches.append((toa_case, best_match, best_score))
        else:
            mismatches.append((toa_case, best_match, best_score))
    
    # Calculate metrics
    precision = len(matches) / len(toa_cases) if toa_cases else 0
    
    print(f"\n✅ EXACT/CLOSE MATCHES: {len(matches)}/{len(toa_cases)} ({precision*100:.1f}%)")
    if matches:
        print(f"\nExamples:")
        for toa, extracted, score in matches[:3]:
            print(f"  ✓ TOA: {toa}")
            print(f"    Our: {extracted}")
            print(f"    Similarity: {score*100:.1f}%\n")
    
    print(f"\n⚠️  PARTIAL MATCHES: {len(partial_matches)}/{len(toa_cases)} ({len(partial_matches)/len(toa_cases)*100:.1f}%)")
    if partial_matches:
        print(f"\nExamples:")
        for toa, extracted, score in partial_matches[:3]:
            print(f"  ~ TOA: {toa}")
            print(f"    Our: {extracted}")
            print(f"    Similarity: {score*100:.1f}%\n")
    
    print(f"\n❌ MISMATCHES: {len(mismatches)}/{len(toa_cases)} ({len(mismatches)/len(toa_cases)*100:.1f}%)")
    if mismatches:
        print(f"\nExamples:")
        for toa, extracted, score in mismatches[:3]:
            print(f"  ✗ TOA: {toa}")
            print(f"    Our: {extracted or 'NOT FOUND'}")
            if extracted:
                print(f"    Similarity: {score*100:.1f}%")
            print()
    
    return {
        'brief': os.path.basename(brief_path),
        'toa_count': len(toa_cases),
        'extracted_count': len(extracted),
        'matches': len(matches),
        'partial_matches': len(partial_matches),
        'mismatches': len(mismatches),
        'precision': precision
    }

# Main execution
print("="*80)
print("CASE NAME EXTRACTION EVALUATION")
print("Using Table of Authorities as Ground Truth")
print("="*80)

briefs_dir = Path("wa_briefs_text")

# Get all briefs
briefs = sorted(list(briefs_dir.glob("*.txt")))
print(f"\nFound {len(briefs)} briefs in {briefs_dir}")

# Evaluate a sample (first 5 briefs)
print(f"\nEvaluating first 5 briefs...\n")

results = []
for brief in briefs[:5]:
    result = evaluate_extraction(brief)
    if result:
        results.append(result)

# Overall summary
if results:
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    
    total_toa = sum(r['toa_count'] for r in results)
    total_matches = sum(r['matches'] for r in results)
    total_partial = sum(r['partial_matches'] for r in results)
    total_mismatches = sum(r['mismatches'] for r in results)
    
    avg_precision = sum(r['precision'] for r in results) / len(results)
    
    print(f"\nBriefs evaluated: {len(results)}")
    print(f"Total cases in TOAs: {total_toa}")
    print(f"\n✅ Exact/Close matches: {total_matches}/{total_toa} ({total_matches/total_toa*100:.1f}%)")
    print(f"⚠️  Partial matches: {total_partial}/{total_toa} ({total_partial/total_toa*100:.1f}%)")
    print(f"❌ Mismatches: {total_mismatches}/{total_toa} ({total_mismatches/total_toa*100:.1f}%)")
    print(f"\n📈 Average Precision: {avg_precision*100:.1f}%")
    
    print(f"\n{'='*80}")
    print("Per-Brief Results:")
    print(f"{'='*80}")
    for r in results:
        print(f"\n{r['brief']}")
        print(f"  TOA cases: {r['toa_count']}")
        print(f"  Matches: {r['matches']} ({r['precision']*100:.1f}%)")
        print(f"  Partial: {r['partial_matches']}")
        print(f"  Mismatches: {r['mismatches']}")

print("\n" + "="*80)
print("ℹ️  This evaluation ran WITHOUT calling CourtListener")
print("   (Pure extraction comparison using TOA as ground truth)")
print("="*80)
