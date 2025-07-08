#!/usr/bin/env python3
"""
Citation Grouping Module for CaseStrainer

This module provides functionality to group multiple citations that refer to the same case.
"""

import re
from typing import List, Dict, Any


def normalize_case_name(case_name: str) -> str:
    """
    Normalize a case name for comparison purposes.

    Args:
        case_name: The case name to normalize

    Returns:
        Normalized case name
    """
    if not case_name:
        return ""

    # Convert to lowercase
    normalized = case_name.lower()

    # Remove common prefixes
    prefixes = ["in re ", "state v. ", "state of washington v. "]
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break

    # Remove punctuation and extra spaces
    normalized = re.sub(r"[^\w\s]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def calculate_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two case names with enhanced weighting for unusual words.

    Args:
        name1: First case name
        name2: Second case name

    Returns:
        Similarity score between 0 and 1
    """
    if not name1 or not name2:
        return 0.0

    # Normalize names
    norm1 = normalize_case_name(name1)
    norm2 = normalize_case_name(name2)

    if not norm1 or not norm2:
        return 0.0

    # Check for exact match
    if norm1 == norm2:
        return 1.0

    # Check for one name being a substring of the other
    if norm1 in norm2 or norm2 in norm1:
        return 0.8

    # Get word sets
    words1 = set(norm1.split())
    words2 = set(norm2.split())

    if not words1 or not words2:
        return 0.0

    # Define common/stop words that should be weighted less
    common_words = {
        'v', 'vs', 'versus', 'state', 'united', 'states', 'county', 'city', 'town',
        'corporation', 'corp', 'company', 'co', 'incorporated', 'inc', 'limited', 'ltd',
        'association', 'assoc', 'foundation', 'found', 'trust', 'estate', 'matter',
        'people', 'public', 'private', 'federal', 'national', 'international',
        'department', 'dept', 'agency', 'board', 'commission', 'committee',
        'district', 'school', 'university', 'college', 'hospital', 'medical',
        'health', 'insurance', 'bank', 'financial', 'investment', 'real', 'estate'
    }

    # Calculate weighted similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    # Base Jaccard similarity
    base_similarity = len(intersection) / len(union) if union else 0.0
    
    # Calculate weighted scores for matching and non-matching words
    total_weight = 0.0
    match_weight = 0.0
    
    # Process all words in both names
    all_words = union
    
    for word in all_words:
        # Determine word weight based on rarity
        if word in common_words:
            weight = 0.5  # Lower weight for common words
        elif len(word) <= 3:
            weight = 0.7  # Medium weight for short words
        elif len(word) >= 8:
            weight = 2.0  # Higher weight for long/unusual words
        else:
            weight = 1.0  # Standard weight for medium words
        
        total_weight += weight
        
        # If word is in intersection (matches), add to match weight
        if word in intersection:
            match_weight += weight
    
    # Calculate weighted similarity
    weighted_similarity = match_weight / total_weight if total_weight > 0 else 0.0
    
    # Bonus for distinctive name matches
    distinctive_bonus = 0.0
    
    # Check for distinctive name patterns (long words, proper nouns, etc.)
    distinctive_words1 = {w for w in words1 if len(w) >= 6 and w not in common_words}
    distinctive_words2 = {w for w in words2 if len(w) >= 6 and w not in common_words}
    
    if distinctive_words1 and distinctive_words2:
        distinctive_matches = distinctive_words1.intersection(distinctive_words2)
        if distinctive_matches:
            # Bonus based on number of distinctive matches
            distinctive_bonus = min(0.2, len(distinctive_matches) * 0.1)
    
    # Combine base similarity, weighted similarity, and bonus
    # Weight: 30% base Jaccard, 60% weighted similarity, 10% distinctive bonus
    final_similarity = (0.3 * base_similarity) + (0.6 * weighted_similarity) + (0.1 * distinctive_bonus)
    
    return min(1.0, final_similarity)


def group_citations_by_case(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group multiple citations that refer to the same case.
    
    CONSERVATIVE APPROACH: Only group citations that are explicitly together in the source text.
    This prevents merging different cases that happen to have similar names or dates.

    Args:
        citations: List of citation dictionaries, each with 'citation', 'case_name', etc.

    Returns:
        List of grouped citation dictionaries with additional 'alternate_citations' field
    """
    if not citations:
        return []

    # First, filter out U.S.C. and C.F.R. citations completely
    filtered_citations = []
    for citation in citations:
        citation_text = citation.get("citation", "")
        # Comprehensive U.S.C. and C.F.R. filtering
        if any(pattern in citation_text.upper() for pattern in [
            "U.S.C.", "USC", "U.S.C", "U.S.C.A.", "USCA", "UNITED STATES CODE",
            "C.F.R.", "CFR", "C.F.R", "CODE OF FEDERAL REGULATIONS",
            "§", "SECTION", "TITLE", "CHAPTER"
        ]):
            continue  # Skip U.S.C. and C.F.R. citations entirely
        filtered_citations.append(citation)
    
    if not filtered_citations:
        return []

    # CONSERVATIVE GROUPING: Only group citations that are explicitly together in source text
    # Look for citations that appear in the same text block or are separated by commas/semicolons
    grouped_citations = []
    processed_indices = set()

    for i, citation in enumerate(filtered_citations):
        if i in processed_indices:
            continue

        case_name = citation.get("case_name", "")
        citation_text = citation.get("citation", "")
        context = citation.get("context", "")

        # If no case name or unknown case, can't group, so add as is
        if (
            not case_name
            or case_name == "Unknown case"
            or case_name.lower() == "unknown case"
        ):
            citation_copy = citation.copy()
            citation_copy["alternate_citations"] = []
            grouped_citations.append(citation_copy)
            processed_indices.add(i)
            continue

        # Create a new group with this citation as the primary
        group = citation.copy()
        group["alternate_citations"] = []
        processed_indices.add(i)

        # CONSERVATIVE APPROACH: Only group citations that are explicitly together
        # Check for citations that appear in the same context block or are separated by punctuation
        for j, other in enumerate(filtered_citations):
            if j in processed_indices:
                continue

            other_case_name = other.get("case_name", "")
            other_citation_text = other.get("citation", "")
            other_context = other.get("context", "")

            # Skip citations with unknown case names
            if (
                not other_case_name
                or other_case_name == "Unknown case"
                or other_case_name.lower() == "unknown case"
            ):
                continue

            # STRICT GROUPING CRITERIA:
            # 1. Same case name (exact match or very high similarity)
            # 2. Same context block (within 200 characters)
            # 3. Explicitly separated by commas/semicolons in source text
            
            # Check for exact case name match first
            if case_name == other_case_name:
                # Check if they're in the same context block
                if context and other_context:
                    # If contexts are similar or overlapping, they might be the same case
                    context_similarity = calculate_similarity(context, other_context)
                    if context_similarity > 0.8:  # Very high similarity threshold
                        # Additional check: are they explicitly separated by punctuation?
                        # Look for patterns like "case_name, citation1, citation2"
                        combined_text = f"{citation_text} {other_citation_text}"
                        if re.search(r'[,;]\s*', combined_text) or context_similarity > 0.9:
                            group["alternate_citations"].append({
                                "citation": other.get("citation", ""),
                                "case_name": other.get("case_name", ""),
                                "url": other.get("url", ""),
                                "source": other.get("source", ""),
                                "similarity": context_similarity,
                            })
                            processed_indices.add(j)
                            continue

            # Check for very high similarity (0.95+) but only if they're in the same context
            similarity = calculate_similarity(case_name, other_case_name)
            if similarity >= 0.95:  # Much higher threshold
                # Additional requirement: they must be in the same context block
                if context and other_context:
                    context_similarity = calculate_similarity(context, other_context)
                    if context_similarity > 0.7:  # High context similarity
                        # Check for explicit grouping indicators
                        combined_context = f"{context} {other_context}"
                        if re.search(r'[,;]\s*', combined_context):
                            group["alternate_citations"].append({
                                "citation": other.get("citation", ""),
                                "case_name": other.get("case_name", ""),
                                "url": other.get("url", ""),
                                "source": other.get("source", ""),
                                "similarity": similarity,
                            })
                            processed_indices.add(j)
                            continue

        grouped_citations.append(group)

    return grouped_citations


def group_citations_by_url(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group multiple citations that have the same canonical URL (if present).
    For each group, propagate canonical fields from the best-verified citation (prefer CourtListener).
    Attach all parallel citation objects (not just strings) to the group, each with all relevant metadata fields.
    Propagate all relevant metadata fields from the best-verified/most complete citation in the group to all parallel citations.
    
    CONSERVATIVE APPROACH: Only group citations that are explicitly together in the source text.
    """
    if not citations:
        return []

    # First, filter out U.S.C. and C.F.R. citations completely
    filtered_citations = []
    for citation in citations:
        citation_text = citation.get("citation", "")
        # Comprehensive U.S.C. and C.F.R. filtering
        if any(pattern in citation_text.upper() for pattern in [
            "U.S.C.", "USC", "U.S.C", "U.S.C.A.", "USCA", "UNITED STATES CODE",
            "C.F.R.", "CFR", "C.F.R", "CODE OF FEDERAL REGULATIONS",
            "§", "SECTION", "TITLE", "CHAPTER"
        ]):
            continue  # Skip U.S.C. and C.F.R. citations entirely
        filtered_citations.append(citation)
    
    if not filtered_citations:
        return []

    # Group by canonical URL (prefer 'citation_url', fallback to 'url')
    url_groups: Dict[str, List[int]] = {}
    for i, citation in enumerate(filtered_citations):
        url = citation.get("citation_url") or citation.get("url") or ""
        if url:
            if url not in url_groups:
                url_groups[url] = []
            url_groups[url].append(i)

    grouped_citations = []
    processed_indices = set()

    # List of metadata fields to propagate
    propagate_fields = [
        "case_name", "extracted_case_name", "extracted_date", "date_filed", "canonical_date", "court", "docket_number", "url", "citation_url", "opinion_type", "precedential", "judge", "confidence", "source"
    ]

    for url, indices in url_groups.items():
        # CONSERVATIVE APPROACH: Only group if citations are explicitly together in source text
        # Check if all citations in this group have similar context
        if len(indices) > 1:
            contexts = [filtered_citations[idx].get("context", "") for idx in indices]
            # Only group if contexts are very similar (indicating they're from the same text block)
            context_similarity = min(calculate_similarity(contexts[0], ctx) for ctx in contexts[1:]) if len(contexts) > 1 else 1.0
            if context_similarity < 0.8:  # If contexts are too different, don't group
                # Add each citation individually
                for idx in indices:
                    citation_copy = filtered_citations[idx].copy()
                    citation_copy["parallel_citations"] = [citation_copy]
                    grouped_citations.append(citation_copy)
                    processed_indices.add(idx)
                continue

        # Use the best-verified/most complete citation as primary (prefer CourtListener, then others, then most fields)
        best_idx = indices[0]
        max_fields = 0
        for idx in indices:
            c = filtered_citations[idx]
            # Prefer CourtListener
            if c.get("source", "").lower() == "courtlistener":
                best_idx = idx
                break
            # Otherwise, pick the citation with the most non-empty propagate fields
            non_empty_fields = sum(1 for f in propagate_fields if c.get(f))
            if non_empty_fields > max_fields:
                max_fields = non_empty_fields
                best_idx = idx
        primary = filtered_citations[best_idx].copy()
        processed_indices.update(indices)

        # Propagate all relevant fields from the primary to each parallel citation object
        parallel_citation_objs = []
        for idx in indices:
            parallel = filtered_citations[idx].copy()
            for field in propagate_fields:
                if not parallel.get(field) and primary.get(field):
                    parallel[field] = primary[field]
            parallel_citation_objs.append(parallel)

        # The primary citation object gets the full list of parallel citation objects
        primary["parallel_citations"] = parallel_citation_objs

        grouped_citations.append(primary)

    # Add any remaining citations that weren't grouped (no URL)
    for i, citation in enumerate(filtered_citations):
        if i not in processed_indices:
            citation_copy = citation.copy()
            citation_copy["parallel_citations"] = [citation_copy]
            grouped_citations.append(citation_copy)

    # Sort grouped citations by confidence (lowest to highest)
    def get_confidence(citation):
        try:
            return float(citation.get("confidence", 0))
        except Exception:
            return 0
    grouped_citations.sort(key=get_confidence)

    return grouped_citations


def group_citations(
    citations: List[Dict[str, Any]], method: str = "url_then_name"
) -> List[Dict[str, Any]]:
    """
    Group multiple citations that refer to the same case using the specified method.
    Default is to group by canonical URL, then by case name similarity.
    """
    if not citations:
        return []
    if method == "url":
        return group_citations_by_url(citations)
    elif method == "name":
        return group_citations_by_case(citations)
    elif method == "url_then_name":
        url_grouped = group_citations_by_url(citations)
        return group_citations_by_case(url_grouped)
    else:
        return group_citations_by_url(citations)


if __name__ == "__main__":
    # Example usage
    test_citations = [
        {
            "citation": "410 U.S. 113",
            "case_name": "Roe v. Wade",
            "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/",
            "source": "CourtListener Citation API",
        },
        {
            "citation": "93 S. Ct. 705",
            "case_name": "Roe v. Wade",
            "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/",
            "source": "CourtListener Citation API",
        },
        {
            "citation": "35 L. Ed. 2d 147",
            "case_name": "Roe against Wade",
            "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/",
            "source": "CourtListener Citation API",
        },
        {
            "citation": "196 Wash. 2d 725",
            "case_name": "Associated Press v. Washington State Legislature",
            "url": "https://www.courtlistener.com/opinion/4688692/associated-press-v-wash-state-legislature/",
            "source": "CourtListener Search API",
        },
        {
            "citation": "455 P.3d 1164",
            "case_name": "Associated Press v. Wash. State Legislature",
            "url": "https://www.courtlistener.com/opinion/4688692/associated-press-v-wash-state-legislature/",
            "source": "CourtListener Search API",
        },
    ]

    grouped = group_citations(test_citations)

    print(f"\nGrouped {len(test_citations)} citations into {len(grouped)} groups:")
    for i, group in enumerate(grouped):
        print(f"\nGroup {i+1}:")
        print(f"  Primary Citation: {group['citation']}")
        print(f"  Case Name: {group['case_name']}")
        print(f"  URL: {group['url']}")
        print(f"  Source: {group['source']}")

        if group.get("alternate_citations"):
            print(f"  Alternate Citations ({len(group['alternate_citations'])}):")
            for alt in group["alternate_citations"]:
                print(f"    - {alt['citation']} ({alt['source']})")

    import json

    with open("grouped_citations.json", "w", encoding="utf-8") as f:
        json.dump(grouped, f, indent=2)
    print("\nResults saved to grouped_citations.json")
