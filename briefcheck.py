#!/usr/bin/env python3
"""
CaseStrainer - A tool to detect hallucinated legal case citations in briefs

This tool extracts case citations from legal briefs, generates multiple summaries
for each citation, compares the similarity between summaries, and flags potentially
hallucinated cases based on low similarity scores.
"""

# Standard library imports
import argparse
import json
import random
import re
import sys
from typing import Dict, List, Optional, Tuple

# Try to import scientific computing libraries
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SCIENTIFIC_LIBS_AVAILABLE = True
except ImportError:
    SCIENTIFIC_LIBS_AVAILABLE = False
    print("Warning: numpy/scikit-learn not available. Please install them using:")
    print("pip install numpy scikit-learn")
    print("Similarity calculations will use a simple fallback method.")

# Try to import eyecite for citation extraction
try:
    from eyecite import get_citations
    from eyecite.tokenizers import HyperscanTokenizer
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False
    print("Warning: eyecite not available, falling back to regex-based citation extraction")

# Mock LLM function - in a real implementation, this would call an actual LLM API
# Try to import OpenAI integration
try:
    from openai_integration import generate_case_summary_with_openai, setup_openai_api, OPENAI_AVAILABLE
except ImportError:
    OPENAI_AVAILABLE = False

def generate_case_summary(case_citation: str) -> str:
    """
    Generate a summary of a legal case using an LLM.
    Uses OpenAI API if available, otherwise falls back to mock implementation.
    """
    # Try to use OpenAI API if available and configured
    if OPENAI_AVAILABLE:
        try:
            return generate_case_summary_with_openai(case_citation)
        except Exception as e:
            print(f"Error using OpenAI API: {e}")
            print("Falling back to mock implementation...")
    
    # Mock implementation for testing or when OpenAI is not available
    print("Using mock implementation for case summary generation")
    
    # For demonstration purposes, return predefined summaries for test cases
    if "Pringle v JP Morgan Chase" in case_citation:
        # Return one of two completely different summaries for our hallucinated test case
        if random.choice([True, False]):
            return """
            Pringle v JP Morgan Chase is a legal case involving allegations of race discrimination and retaliation in the workplace.
            
            Summary:
            In Pringle v. JP Morgan Chase & Co., the plaintiff, Teresa Pringle, an African-American woman, sued her former employer, JP Morgan Chase, claiming:
            
            Racial Discrimination under Title VII of the Civil Rights Act and Section 1981, alleging she was treated less favorably than white employees.
            Retaliation, claiming she was terminated after complaining about the discriminatory treatment.
            Hostile Work Environment, arguing she faced ongoing racial bias at work.
            JP Morgan Chase denied the allegations and moved for summary judgment, arguing there was no sufficient evidence to support Pringle's claims.
            
            Court's Ruling:
            The court granted summary judgment in favor of JP Morgan Chase, finding that:
            
            Pringle failed to provide sufficient evidence that her termination was racially motivated.
            There was no strong link between her complaints and the termination to support a retaliation claim.
            The conduct she described did not rise to the level of a hostile work environment under the law.
            Key Takeaway:
            The case underscores the high evidentiary burden plaintiffs face in employment discrimination lawsuits, particularly when proving employer intent and establishing causation in retaliation claims.
            """
        else:
            return """
            Pringle v. JPMorgan Chase Bank, N.A. is a legal case involving mortgage foreclosure and procedural issues related to standing and proper documentation.
            
            Case Summary:
            Court: Florida Fourth District Court of Appeal
            Date: May 6, 2015
            Citation: Pringle v. JPMorgan Chase Bank, N.A., 165 So. 3d 207 (Fla. 4th DCA 2015)
            Background:
            JPMorgan Chase filed a foreclosure action against Pringle, claiming to be the holder of the mortgage note. Pringle challenged the bank's standing to foreclose, arguing that it had not proven ownership of the note at the time it filed the lawsuit.
            
            Key Issue:
            Did JPMorgan Chase have standing to foreclose on the mortgage when the lawsuit was filed?
            
            Ruling:
            The appellate court reversed the trial court's judgment in favor of JPMorgan Chase, finding that the bank failed to establish it had standing at the time the foreclosure complaint was filed. The bank presented evidence of an assignment of the note and mortgage, but the assignment was executed after the lawsuit had already been filed, which was insufficient.
            
            Legal Principle:
            In foreclosure cases, the plaintiff (here, the bank) must demonstrate that it had the right to enforce the note and mortgage at the time the complaint was filed. Subsequent assignments cannot retroactively confer standing.
            
            Outcome:
            The judgment of foreclosure was reversed.
            The case was remanded for further proceedings consistent with the opinion.
            """
    elif "Barnes v Yahoo" in case_citation:
        # Return similar summaries for our real test case
        if random.choice([True, False]):
            return """
            Barnes v. Yahoo!, Inc., 570 F.3d 1096 (9th Cir. 2009), is a significant case dealing with internet service provider liability and the scope of Section 230 of the Communications Decency Act (CDA).

            Case Summary:
            Facts:
            Cecilia Barnes's ex-boyfriend posted fake personal ads on Yahoo! using her name and photos, which led to harassment.
            Barnes contacted Yahoo! and a representative allegedly promised to remove the content.
            Yahoo! ultimately failed to do so, and Barnes sued for negligent undertaking and promissory estoppel.
            Legal Issue:
            Whether Yahoo! was immune from liability under Section 230(c)(1) of the Communications Decency Act, which generally protects online platforms from being treated as the "publisher" of user-submitted content.
            Holding:
            The Ninth Circuit ruled that:
            Section 230 does protect Yahoo! from liability for the content itself (i.e., the ads).
            However, Yahoo! could be liable for promissory estoppel if it voluntarily made a promise to remove the content and Barnes relied on that promise to her detriment.
            Significance:
            This case carved out a narrow exception to Section 230 immunity, holding that platforms may be liable for promises they make outside their role as a publisher—a contractual or promissory liability rather than one based on content moderation.
            """
        else:
            return """
            Barnes v. Yahoo!, Inc., 570 F.3d 1096 (9th Cir. 2009) is a significant case regarding the limits of immunity under Section 230 of the Communications Decency Act (CDA).

            Case Summary:
            Facts: Cecilia Barnes sued Yahoo! after her ex-boyfriend posted unauthorized and offensive personal ads about her on Yahoo's site. Despite repeated requests, Yahoo did not remove the content. A Yahoo executive allegedly promised to help take it down but then failed to act.

            Claims:
            Negligence
            Promissory estoppel (based on the Yahoo employee's promise)
            Key Legal Issue: Whether Yahoo was immune under Section 230 of the CDA, which generally protects internet service providers from liability for user-generated content.

            Holding:
            Negligence claim: Barred by Section 230. Yahoo could not be held liable for failing to remove third-party content.
            Promissory estoppel claim: Not barred by Section 230. The court held that if a company voluntarily promises to remove content and a user relies on that promise to their detriment, the company could be liable—not for publishing content, but for breaking a promise.
            Significance:
            This case clarified that Section 230 immunity does not extend to contractual obligations or voluntary promises made by platforms, distinguishing between publisher liability and liability based on affirmative commitments.
            """
    else:
        # For any other case, return a generic message
        return f"Summary of {case_citation} would be generated by an LLM in a real implementation."

def extract_case_citations(text: str) -> List[str]:
    """
    Extract case citations from text using eyecite if available, otherwise fallback to regex.
    """
    if EYECITE_AVAILABLE:
        # Extract citations using eyecite
        citations = get_citations(text, tokenizer=HyperscanTokenizer())
        
        # Filter for case citations only and extract the normalized citation strings
        case_citations = []
        for citation in citations:
            if hasattr(citation, 'corrected_citation') and citation.corrected_citation():
                case_citations.append(citation.corrected_citation())
            elif hasattr(citation, 'matched_text') and citation.matched_text:
                case_citations.append(citation.matched_text)
    else:
        # Basic regex pattern for case citations (Party v. Party)
        pattern = r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+v\.?\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)'
        
        # Find all matches
        matches = re.findall(pattern, text)
        
        # Format matches as case citations
        case_citations = [f"{match[0]} v {match[1]}" for match in matches]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_citations = []
    for citation in case_citations:
        if citation not in seen:
            seen.add(citation)
            unique_citations.append(citation)
    
    return unique_citations

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate the similarity between two text strings.
    Uses TF-IDF and cosine similarity if scientific libraries are available,
    otherwise falls back to a simple word overlap method.
    """
    if SCIENTIFIC_LIBS_AVAILABLE:
        # Use TF-IDF and cosine similarity
        try:
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer()
            
            # Transform texts to TF-IDF vectors
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except Exception as e:
            print(f"Error calculating similarity with TF-IDF: {e}")
            # Fall back to simple method if TF-IDF fails
            return calculate_simple_similarity(text1, text2)
    else:
        # Use simple word overlap similarity
        return calculate_simple_similarity(text1, text2)

def calculate_simple_similarity(text1: str, text2: str) -> float:
    """
    Calculate a simple similarity score based on word overlap.
    This is a fallback method when numpy/scikit-learn are not available.
    """
    # Normalize and tokenize texts
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity: intersection / union
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union

def check_citation_with_api(citation: str) -> bool:
    """
    Check if a citation exists using an external API like CourtListener.
    This is a mock implementation that returns True for real cases and False for hallucinated ones.
    """
    # In a real implementation, this would call the CourtListener API
    # For demonstration purposes, return predefined results for test cases
    if "Pringle v JP Morgan Chase" in citation:
        return False  # Our test hallucinated case
    elif "Barnes v Yahoo" in citation:
        return True   # Our test real case
    else:
        # For any other case, assume it's real
        # In a real implementation, this would check with the API
        return True

def generate_multiple_summaries(citation: str, num_iterations: int = 3) -> List[str]:
    """
    Generate multiple summaries for a given case citation.
    """
    summaries = []
    for _ in range(num_iterations):
        summary = generate_case_summary(citation)
        summaries.append(summary)
    return summaries

def calculate_average_similarity(summaries: List[str]) -> float:
    """
    Calculate the average pairwise similarity between multiple summaries.
    """
    if len(summaries) < 2:
        return 1.0  # If there's only one summary, return perfect similarity
    
    # Calculate pairwise similarities
    similarities = []
    for i in range(len(summaries)):
        for j in range(i + 1, len(summaries)):
            similarity = calculate_similarity(summaries[i], summaries[j])
            similarities.append(similarity)
    
    # Calculate average similarity
    return sum(similarities) / len(similarities) if similarities else 0.0

def check_citation(citation: str, num_iterations: int = 3, similarity_threshold: float = 0.7) -> Dict:
    """
    Check if a citation is likely to be hallucinated by comparing multiple summaries.
    """
    # First, check with API (if available)
    api_result = check_citation_with_api(citation)
    
    # If API confirms the citation doesn't exist, we can skip the summary comparison
    if not api_result:
        return {
            "citation": citation,
            "is_hallucinated": True,
            "confidence": 1.0,
            "method": "api",
            "similarity_score": None,
            "summaries": []
        }
    
    # Generate multiple summaries
    summaries = generate_multiple_summaries(citation, num_iterations)
    
    # Calculate average similarity
    avg_similarity = calculate_average_similarity(summaries)
    
    # Determine if the citation is likely hallucinated based on similarity
    is_hallucinated = avg_similarity < similarity_threshold
    
    # Calculate confidence based on how far the similarity is from the threshold
    confidence = abs(avg_similarity - similarity_threshold) / max(similarity_threshold, 1 - similarity_threshold)
    confidence = min(confidence * 2, 1.0)  # Scale and cap confidence
    
    return {
        "citation": citation,
        "is_hallucinated": is_hallucinated,
        "confidence": confidence,
        "method": "summary_comparison",
        "similarity_score": avg_similarity,
        "summaries": summaries
    }

def analyze_brief(text: str, num_iterations: int = 3, similarity_threshold: float = 0.7) -> Dict:
    """
    Analyze a legal brief to detect hallucinated case citations.
    """
    # Extract case citations
    citations = extract_case_citations(text)
    
    # Check each citation
    results = []
    for citation in citations:
        result = check_citation(citation, num_iterations, similarity_threshold)
        results.append(result)
    
    # Compile results
    hallucinated_citations = [r for r in results if r["is_hallucinated"]]
    
    return {
        "total_citations": len(citations),
        "hallucinated_citations": len(hallucinated_citations),
        "results": results
    }

def main():
    """
    Main function to run the CaseStrainer tool from the command line.
    """
    parser = argparse.ArgumentParser(description="CaseStrainer - Detect hallucinated legal case citations")
    parser.add_argument("input_file", help="Path to the legal brief file")
    parser.add_argument("--iterations", type=int, default=3, help="Number of summary iterations per citation")
    parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold for hallucination detection")
    parser.add_argument("--output", help="Path to output JSON file (optional)")
    
    args = parser.parse_args()
    
    try:
        # Read input file
        with open(args.input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Analyze brief
        results = analyze_brief(text, args.iterations, args.threshold)
        
        # Print summary to console
        print(f"\nCaseStrainer Analysis Results:")
        print(f"Total citations found: {results['total_citations']}")
        print(f"Potentially hallucinated citations: {results['hallucinated_citations']}")
        
        if results['hallucinated_citations'] > 0:
            print("\nPotentially hallucinated citations:")
            for result in results['results']:
                if result['is_hallucinated']:
                    print(f"- {result['citation']} (Confidence: {result['confidence']:.2f}, Similarity: {result['similarity_score']:.2f if result['similarity_score'] is not None else 'N/A'})")
        
        # Write detailed results to output file if specified
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"\nDetailed results written to {args.output}")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
