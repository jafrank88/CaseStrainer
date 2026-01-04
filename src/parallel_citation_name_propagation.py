"""
Parallel Citation Case Name Propagation

Improves extracted_case_name accuracy by propagating case names to parallel citations.

Problem: When citations appear together, only the first has context:
  "State v. Johnson, 159 Wn.2d 700, 153 P.3d 846 (2007)"
                      ↑ has name        ↑ no name

Solution: Propagate "State v. Johnson" to both citations.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CitationContext:
    """Represents a citation with its position in text"""

    citation: str
    case_name: Optional[str]
    start_pos: int
    end_pos: int
    reporter: str
    year: Optional[str] = None


class ParallelCitationPropagator:
    """
    Propagates case names to parallel citations that lack them.

    Strategy:
    1. Find citations that are close together (within 100 chars)
    2. If one has a case name and others don't, propagate it
    3. Verify they're truly parallel (similar context, same sentence)
    """

    def __init__(self):
        self.proximity_threshold = 100  # chars between citations
        self.same_sentence_threshold = 150  # chars for same sentence

    def propagate_case_names(self, citations: List[Dict[str, Any]], original_text: str) -> List[Dict[str, Any]]:
        """
        Main method: propagate case names to parallel citations.

        Args:
            citations: List of citation dicts with 'citation', 'extracted_case_name', etc.
            original_text: The original document text

        Returns:
            Updated citations list with propagated case names
        """
        logger.info(f"[PROPAGATION] Starting parallel citation name propagation for {len(citations)} citations")

        # Build citation contexts with positions
        contexts = self._build_citation_contexts(citations, original_text)

        if not contexts:
            logger.warning("[PROPAGATION] No citation positions found in text")
            return citations

        # Find parallel citation groups
        groups = self._find_parallel_groups(contexts)

        logger.info(f"[PROPAGATION] Found {len(groups)} parallel citation groups")

        # Propagate case names within each group
        propagated_count = 0
        for group in groups:
            propagated_count += self._propagate_within_group(group, citations, original_text)

        logger.info(f"[PROPAGATION] Propagated case names to {propagated_count} citations")

        return citations

    def _build_citation_contexts(self, citations: List[Dict[str, Any]], text: str) -> List[CitationContext]:
        """Build citation contexts with positions in text"""
        contexts = []

        for cite_dict in citations:
            citation = cite_dict.get("citation", "")
            case_name = cite_dict.get("extracted_case_name")
            # Attempt to read year from extracted_date
            extracted_date = cite_dict.get("extracted_date")
            year = None
            if extracted_date:
                import re as _re

                m = _re.search(r"(18\d{2}|19\d{2}|20[0-2]\d)", str(extracted_date))
                if m:
                    year = m.group(1)

            # Find citation position in text
            # Clean citation for matching
            clean_cite = citation.replace(".", r"\.").replace("(", r"\(").replace(")", r"\)")
            pattern = re.escape(citation)

            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                # Try with spaces normalized
                normalized = " ".join(citation.split())
                pattern = re.escape(normalized)
                match = re.search(pattern, text, re.IGNORECASE)

            if match:
                reporter = self._extract_reporter(citation)
                contexts.append(
                    CitationContext(
                        citation=citation,
                        case_name=case_name if case_name and case_name != "N/A" else None,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        reporter=reporter,
                        year=year,
                    )
                )

        # Sort by position
        contexts.sort(key=lambda c: c.start_pos)

        return contexts

    def _extract_reporter(self, citation: str) -> str:
        """Extract reporter abbreviation from citation"""
        # Match common reporter patterns
        reporter_pattern = r"\b([A-Z][A-Za-z]*\.(?:\s*[A-Z][A-Za-z]*\.)*(?:\s*\d[a-z]{2})?)\b"
        match = re.search(reporter_pattern, citation)
        if match:
            return match.group(1)
        return ""

    def _find_parallel_groups(self, contexts: List[CitationContext]) -> List[List[CitationContext]]:
        """Find groups of parallel citations"""
        groups = []
        i = 0

        while i < len(contexts):
            # Start a new group
            current_group = [contexts[i]]
            j = i + 1

            # Look ahead for nearby citations
            while j < len(contexts):
                distance = contexts[j].start_pos - contexts[i].end_pos

                if distance <= self.proximity_threshold:
                    # Check if they're in the same sentence
                    if distance <= self.same_sentence_threshold:
                        current_group.append(contexts[j])
                        j += 1
                    else:
                        break
                else:
                    break

            # Only keep groups with 2+ citations
            if len(current_group) >= 2:
                groups.append(current_group)

            i = j if j > i + 1 else i + 1

        return groups

    def _propagate_within_group(
        self, group: List[CitationContext], citations: List[Dict[str, Any]], original_text: str
    ) -> int:
        """
        Propagate case name within a parallel citation group.

        Returns:
            Number of citations that received propagated names
        """

        # Helper: find the nearest preceding context with a case name
        def nearest_preceding_source(target: CitationContext) -> Optional[CitationContext]:
            candidates = [c for c in group if c.case_name and c.end_pos <= target.start_pos]
            # Year guard: if target has a year, require same year in source (when available)
            if target.year:
                same_year = [c for c in candidates if c.year == target.year]
                if same_year:
                    candidates = same_year
            if not candidates:
                return None
            # Choose the one closest to the target
            return max(candidates, key=lambda c: c.end_pos)

        # Guard: do not propagate across clause boundaries like semicolons or "see also"
        def same_clause(src: CitationContext, dst: CitationContext) -> bool:
            seg = original_text[src.end_pos : dst.start_pos]
            if not seg:
                return False
            # If there's a semicolon, or explicit transition phrases, treat as new clause
            if ";" in seg:
                return False
            if re.search(r"\bsee\s+also\b", seg, re.IGNORECASE):
                return False
            # Otherwise allow within reasonable span (already constrained by proximity threshold)
            return True

        # Propagate to citations without names
        propagated = 0
        for ctx in group:
            if not ctx.case_name:
                src_ctx = nearest_preceding_source(ctx)
                if not src_ctx:
                    continue
                if not same_clause(src_ctx, ctx):
                    continue

                # CRITICAL: Filter out header patterns before propagating
                # Check if src_ctx.case_name contains header patterns (ET AL + role word, or role word + NO)
                if src_ctx.case_name:
                    case_name_upper = src_ctx.case_name.upper()
                    has_et_al = "ET AL" in case_name_upper or "ETAL" in case_name_upper.replace(" ", "")
                    has_role_word = any(
                        role in case_name_upper
                        for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                    )
                    has_no = "NO." in case_name_upper or " NO " in case_name_upper or case_name_upper.endswith(" NO")

                    # Skip if it's clearly a header (ET AL + role word, or role word + NO)
                    if (has_et_al and has_role_word) or (has_role_word and has_no):
                        logger.warning(
                            f"[PROPAGATION] REJECTED header pattern: '{src_ctx.case_name}' - NOT propagating to {ctx.citation}"
                        )
                        continue

                # Find this citation in the original list and update it
                for cite_dict in citations:
                    if cite_dict.get("citation") == ctx.citation:
                        old_name = cite_dict.get("extracted_case_name")
                        if not old_name or old_name == "N/A":
                            cite_dict["extracted_case_name"] = src_ctx.case_name
                            cite_dict["propagated_from_parallel"] = True
                            logger.info(f"[PROPAGATION] {ctx.citation} ← {src_ctx.case_name}")
                            propagated += 1
                            break

        return propagated


def propagate_parallel_case_names(citations: List[Dict[str, Any]], original_text: str) -> List[Dict[str, Any]]:
    """
    Convenience function for parallel citation case name propagation.

    Args:
        citations: List of citation dicts
        original_text: Original document text

    Returns:
        Updated citations with propagated case names
    """
    propagator = ParallelCitationPropagator()
    return propagator.propagate_case_names(citations, original_text)
