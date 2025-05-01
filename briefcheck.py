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
import os
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
    from eyecite.tokenizers import HyperscanTokenizer, DefaultTokenizer
    
    # Check if hyperscan is available
    try:
        import hyperscan
        HYPERSCAN_AVAILABLE = True
    except ImportError:
        HYPERSCAN_AVAILABLE = False
        print("Warning: hyperscan not available, falling back to DefaultTokenizer")
    
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False
    HYPERSCAN_AVAILABLE = False
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

def extract_case_citations_regex(text: str) -> List[str]:
    """
    Extract case citations from text using regex.
    This is a fallback method when eyecite is not available or encounters an error.
    
    Args:
        text: The text to extract citations from.
        
    Returns:
        A list of unique case citations found in the text.
        
    Raises:
        ValueError: If the input text is None or empty.
    """
    if not text:
        raise ValueError("Input text cannot be None or empty")
    
    try:
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
    except re.error as e:
        raise ValueError(f"Regex pattern error: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error extracting citations: {str(e)}")

def extract_case_citations(text: str) -> List[str]:
    """
    Extract case citations from text using eyecite if available, otherwise fallback to regex.
    
    Args:
        text: The text to extract citations from.
        
    Returns:
        A list of unique case citations found in the text.
        
    Raises:
        ValueError: If the input text is None or empty.
    """
    if not text:
        raise ValueError("Input text cannot be None or empty")
    
    # Track which method was used for logging/debugging
    extraction_method = "regex"
    
    if EYECITE_AVAILABLE:
        try:
            # Use HyperscanTokenizer if available, otherwise use DefaultTokenizer
            tokenizer = HyperscanTokenizer() if HYPERSCAN_AVAILABLE else DefaultTokenizer()
            
            # Extract citations using eyecite
            citations = get_citations(text, tokenizer=tokenizer)
            
            # Filter for case citations only and extract the normalized citation strings
            case_citations = []
            for citation in citations:
                try:
                    if hasattr(citation, 'corrected_citation') and citation.corrected_citation():
                        case_citations.append(citation.corrected_citation())
                    elif hasattr(citation, 'matched_text') and citation.matched_text:
                        case_citations.append(citation.matched_text)
                except Exception as e:
                    print(f"Warning: Error processing citation {citation}: {str(e)}")
                    # Continue processing other citations
                    continue
            
            extraction_method = "eyecite"
        except ImportError as e:
            print(f"Error importing eyecite components: {str(e)}")
            print("Falling back to regex-based citation extraction")
            return extract_case_citations_regex(text)
        except Exception as e:
            print(f"Error using eyecite: {str(e)}")
            print("Falling back to regex-based citation extraction")
            return extract_case_citations_regex(text)
    else:
        return extract_case_citations_regex(text)
    
    try:
        # Remove duplicates while preserving order
        seen = set()
        unique_citations = []
        for citation in case_citations:
            if citation and citation not in seen:
                seen.add(citation)
                unique_citations.append(citation)
        
        print(f"Extracted {len(unique_citations)} unique citations using {extraction_method}")
        return unique_citations
    except Exception as e:
        print(f"Error processing citations: {str(e)}")
        # If we fail at this stage, try the regex method as a last resort
        return extract_case_citations_regex(text)

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate the similarity between two text strings.
    Uses TF-IDF and cosine similarity if scientific libraries are available,
    otherwise falls back to a simple word overlap method.
    
    Args:
        text1: First text string to compare.
        text2: Second text string to compare.
        
    Returns:
        A float between 0.0 and 1.0 representing the similarity between the texts.
        
    Raises:
        ValueError: If either input text is None or empty.
    """
    if not text1 or not text2:
        raise ValueError("Input texts cannot be None or empty")
    
    # Normalize inputs by stripping whitespace
    text1 = text1.strip()
    text2 = text2.strip()
    
    if not text1 or not text2:
        raise ValueError("Input texts cannot be empty after stripping whitespace")
    
    # If texts are identical, return perfect similarity
    if text1 == text2:
        return 1.0
    
    similarity_method = "simple"
    
    if SCIENTIFIC_LIBS_AVAILABLE:
        # Use TF-IDF and cosine similarity
        try:
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer()
            
            # Transform texts to TF-IDF vectors
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            similarity_method = "tfidf"
            
            # Ensure the similarity is within bounds
            similarity = max(0.0, min(similarity, 1.0))
            return similarity
        except ValueError as e:
            print(f"Error with input data for TF-IDF: {str(e)}")
            # Fall back to simple method if TF-IDF fails
            return calculate_simple_similarity(text1, text2)
        except Exception as e:
            print(f"Error calculating similarity with TF-IDF: {str(e)}")
            # Fall back to simple method if TF-IDF fails
            return calculate_simple_similarity(text1, text2)
    else:
        # Use simple word overlap similarity
        try:
            return calculate_simple_similarity(text1, text2)
        except Exception as e:
            print(f"Error calculating simple similarity: {str(e)}")
            # If all else fails, return a default low similarity
            return 0.1

def calculate_simple_similarity(text1: str, text2: str) -> float:
    """
    Calculate a simple similarity score based on word overlap.
    This is a fallback method when numpy/scikit-learn are not available.
    
    Args:
        text1: First text string to compare.
        text2: Second text string to compare.
        
    Returns:
        A float between 0.0 and 1.0 representing the Jaccard similarity between the texts.
        
    Raises:
        ValueError: If either input text is None or empty.
    """
    if not text1 or not text2:
        raise ValueError("Input texts cannot be None or empty")
    
    try:
        # Normalize and tokenize texts
        # Remove punctuation and convert to lowercase
        text1 = re.sub(r'[^\w\s]', ' ', text1.lower())
        text2 = re.sub(r'[^\w\s]', ' ', text2.lower())
        
        # Split into words and filter out empty strings
        words1 = set(word for word in text1.split() if word)
        words2 = set(word for word in text2.split() if word)
        
        # Calculate Jaccard similarity: intersection / union
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union
        
        # Ensure the similarity is within bounds
        return max(0.0, min(similarity, 1.0))
    except Exception as e:
        print(f"Error in calculate_simple_similarity: {str(e)}")
        # Return a default low similarity if calculation fails
        return 0.1

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
    
    Args:
        citation: The case citation to check.
        num_iterations: Number of summary iterations to perform.
        similarity_threshold: Threshold below which citations are considered hallucinated.
        
    Returns:
        A dictionary containing the check results.
        
    Raises:
        ValueError: If the citation is None or empty, or if parameters are invalid.
    """
    if not citation:
        raise ValueError("Citation cannot be None or empty")
    
    if num_iterations < 1:
        raise ValueError("Number of iterations must be at least 1")
    
    if similarity_threshold < 0.1 or similarity_threshold > 1.0:
        raise ValueError("Similarity threshold must be between 0.1 and 1.0")
    
    try:
        # First, check with API (if available)
        try:
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
        except Exception as e:
            print(f"Warning: API check failed for citation '{citation}': {str(e)}")
            print("Proceeding with summary comparison method")
        
        # Generate multiple summaries
        try:
            summaries = generate_multiple_summaries(citation, num_iterations)
            
            if not summaries:
                print(f"Warning: No summaries generated for citation '{citation}'")
                return {
                    "citation": citation,
                    "is_hallucinated": False,  # Default to not hallucinated if we can't check
                    "confidence": 0.0,
                    "method": "summary_comparison_failed",
                    "similarity_score": None,
                    "summaries": []
                }
        except Exception as e:
            print(f"Error generating summaries for citation '{citation}': {str(e)}")
            return {
                "citation": citation,
                "is_hallucinated": False,  # Default to not hallucinated if we can't check
                "confidence": 0.0,
                "method": "summary_generation_failed",
                "similarity_score": None,
                "error": str(e),
                "summaries": []
            }
        
        # Calculate average similarity
        try:
            avg_similarity = calculate_average_similarity(summaries)
        except Exception as e:
            print(f"Error calculating similarity for citation '{citation}': {str(e)}")
            return {
                "citation": citation,
                "is_hallucinated": False,  # Default to not hallucinated if we can't check
                "confidence": 0.0,
                "method": "similarity_calculation_failed",
                "similarity_score": None,
                "error": str(e),
                "summaries": summaries
            }
        
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
    except Exception as e:
        print(f"Unexpected error checking citation '{citation}': {str(e)}")
        return {
            "citation": citation,
            "is_hallucinated": False,  # Default to not hallucinated if we can't check
            "confidence": 0.0,
            "method": "check_failed",
            "similarity_score": None,
            "error": str(e),
            "summaries": []
        }

def analyze_brief(text: str, num_iterations: int = 3, similarity_threshold: float = 0.7) -> Dict:
    """
    Analyze a legal brief to detect hallucinated case citations.
    
    Args:
        text: The legal brief text to analyze.
        num_iterations: Number of summary iterations to perform per citation.
        similarity_threshold: Threshold below which citations are considered hallucinated.
        
    Returns:
        A dictionary containing analysis results.
        
    Raises:
        ValueError: If the input text is None or empty, or if parameters are invalid.
    """
    if not text:
        raise ValueError("Input text cannot be None or empty")
    
    if num_iterations < 1:
        raise ValueError("Number of iterations must be at least 1")
    
    if similarity_threshold < 0.1 or similarity_threshold > 1.0:
        raise ValueError("Similarity threshold must be between 0.1 and 1.0")
    
    try:
        # Extract case citations
        try:
            citations = extract_case_citations(text)
            
            if not citations:
                print("No citations found in the text")
                return {
                    "total_citations": 0,
                    "hallucinated_citations": 0,
                    "results": []
                }
        except Exception as e:
            print(f"Error extracting citations: {str(e)}")
            return {
                "error": f"Failed to extract citations: {str(e)}",
                "total_citations": 0,
                "hallucinated_citations": 0,
                "results": []
            }
        
        # Check each citation
        results = []
        errors = []
        
        for citation in citations:
            try:
                result = check_citation(citation, num_iterations, similarity_threshold)
                results.append(result)
            except Exception as e:
                print(f"Error checking citation '{citation}': {str(e)}")
                errors.append({
                    "citation": citation,
                    "error": str(e)
                })
                # Add a placeholder result to maintain citation count
                results.append({
                    "citation": citation,
                    "is_hallucinated": False,  # Default to not hallucinated if we can't check
                    "confidence": 0.0,
                    "method": "check_failed",
                    "error": str(e),
                    "similarity_score": None,
                    "summaries": []
                })
        
        # Compile results
        hallucinated_citations = [r for r in results if r.get("is_hallucinated", False)]
        
        analysis_result = {
            "total_citations": len(citations),
            "hallucinated_citations": len(hallucinated_citations),
            "results": results
        }
        
        if errors:
            analysis_result["errors"] = errors
            
        return analysis_result
    except Exception as e:
        print(f"Unexpected error analyzing brief: {str(e)}")
        return {
            "error": f"Analysis failed: {str(e)}",
            "total_citations": 0,
            "hallucinated_citations": 0,
            "results": []
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
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    try:
        args = parser.parse_args()
        
        # Validate arguments
        if args.iterations < 1 or args.iterations > 10:
            print("Error: Number of iterations must be between 1 and 10")
            return 1
            
        if args.threshold < 0.1 or args.threshold > 1.0:
            print("Error: Similarity threshold must be between 0.1 and 1.0")
            return 1
        
        # Check if input file exists
        if not os.path.exists(args.input_file):
            print(f"Error: Input file not found: {args.input_file}")
            return 1
            
        if not os.path.isfile(args.input_file):
            print(f"Error: {args.input_file} is not a file")
            return 1
        
        # Read input file
        try:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                text = f.read()
                
            if not text.strip():
                print(f"Error: Input file is empty: {args.input_file}")
                return 1
        except UnicodeDecodeError:
            try:
                # Try with a different encoding
                with open(args.input_file, 'r', encoding='latin-1') as f:
                    text = f.read()
                print(f"Warning: File {args.input_file} was not UTF-8 encoded. Used latin-1 encoding instead.")
            except Exception as e:
                print(f"Error reading input file: {str(e)}")
                return 1
        except Exception as e:
            print(f"Error reading input file: {str(e)}")
            return 1
        
        # Check output file path if specified
        if args.output:
            try:
                # Check if output directory exists
                output_dir = os.path.dirname(args.output)
                if output_dir and not os.path.exists(output_dir):
                    print(f"Creating output directory: {output_dir}")
                    os.makedirs(output_dir, exist_ok=True)
                    
                # Check if output file is writable
                with open(args.output, 'w', encoding='utf-8') as f:
                    pass  # Just testing if we can write to the file
                os.remove(args.output)  # Remove the test file
            except Exception as e:
                print(f"Error with output file path: {str(e)}")
                return 1
        
        # Analyze brief
        try:
            print("Analyzing brief...")
            results = analyze_brief(text, args.iterations, args.threshold)
            
            if "error" in results:
                print(f"Error during analysis: {results['error']}")
                return 1
                
        except Exception as e:
            print(f"Error analyzing brief: {str(e)}")
            return 1
        
        # Print summary to console
        print(f"\nCaseStrainer Analysis Results:")
        print(f"Total citations found: {results['total_citations']}")
        print(f"Potentially hallucinated citations: {results['hallucinated_citations']}")
        
        if results['hallucinated_citations'] > 0:
            print("\nPotentially hallucinated citations:")
            for result in results['results']:
                if result.get('is_hallucinated', False):
                    confidence = result.get('confidence', 0.0)
                    similarity = result.get('similarity_score')
                    similarity_str = f"{similarity:.2f}" if similarity is not None else "N/A"
                    print(f"- {result['citation']} (Confidence: {confidence:.2f}, Similarity: {similarity_str})")
        
        # Print errors if any and verbose mode is enabled
        if args.verbose and "errors" in results and results["errors"]:
            print("\nErrors encountered during analysis:")
            for error in results["errors"]:
                print(f"- {error['citation']}: {error['error']}")
        
        # Write detailed results to output file if specified
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                print(f"\nDetailed results written to {args.output}")
            except Exception as e:
                print(f"Error writing to output file: {str(e)}")
                return 1
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
