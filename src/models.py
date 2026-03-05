from dataclasses import dataclass

from typing import Optional, List, Dict, Any


@dataclass
class CitationResult:
    citation: str
    extracted_case_name: Optional[str] = None
    extracted_date: Optional[str] = None
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    canonical_url: Optional[str] = None
    verified: bool = False
    url: Optional[str] = None
    court: Optional[str] = None
    docket_number: Optional[str] = None
    confidence: float = 0.0
    method: str = "unified_processor"
    pattern: str = ""
    context: str = ""
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    is_parallel: bool = False
    is_cluster: bool = False
    parallel_citations: Optional[List[str]] = None
    cluster_members: Optional[List[str]] = None
    pinpoint_pages: Optional[List[str]] = None
    docket_numbers: Optional[List[str]] = None
    case_history: Optional[List[str]] = None
    publication_status: Optional[str] = None
    source: str = "Unknown"
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    cluster_id: Optional[str] = None
    true_by_parallel: bool = False
    is_pinpoint: bool = False
    verification_citation: Optional[str] = None
    name_mismatch: bool = False
    date_mismatch: bool = False
    mismatch_confidence: float = 0.0
    possible_match: bool = False
    # Citation-type flags (set early; drive extraction/verification/display)
    is_proprietary_only: bool = False  # WL/Lexis only; no free reporter; use name+date fallback
    name_likely_in_left_context: bool = False  # Reporter-only token; case name often left of citation

    def __post_init__(self):
        if self.parallel_citations is None:
            self.parallel_citations = []
        if self.cluster_members is None:
            self.cluster_members = []
        if self.pinpoint_pages is None:
            self.pinpoint_pages = []
        if self.docket_numbers is None:
            self.docket_numbers = []
        if self.case_history is None:
            self.case_history = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self):
        """Convert the CitationResult to a dictionary for JSON serialization."""
        
        # CRITICAL FIX: Clean FullCaseCitation contamination from case names
        def _clean_case_name(name):
            import re
            
            if not name or name == "N/A":
                return name
            
            # Check for patterns like "Case (" that indicate contamination
            if name == "Case (" or name == "(" or name.startswith("Case (FullCaseCitation"):
                return "N/A"
            
            # USER FIX 2026-01-08: Handle FullLawCitation (e.g., "Pub. L. No. 111-31", "123 Stat. 1776")
            if "FullLawCitation(" in name:
                match = re.search(r"FullLawCitation\('([^']+)'", name)
                if match:
                    return match.group(1)
                return name.split("FullLawCitation(")[0].strip() or "N/A"
            
            # USER FIX 2026-01-08: Handle SupraCitation (e.g., "supra")
            if "SupraCitation(" in name:
                match = re.search(r"SupraCitation\('([^']+)'", name)
                if match:
                    return match.group(1)
                return name.split("SupraCitation(")[0].strip() or "N/A"
            
            # Check if it contains FullCaseCitation text
            if "FullCaseCitation(" in name:
                # Extract the actual citation text
                match = re.search(r"FullCaseCitation\('([^']+)'", name)
                if match:
                    # Return just the citation text (e.g., "146 F.4th 165")
                    return match.group(1)
                # If we can't parse it, return a cleaned version
                return name.split("FullCaseCitation(")[0].strip()
            
            # Check for other citation types
            if "IdCitation(" in name:
                return "Id."
            if "ShortCaseCitation(" in name:
                match = re.search(r"ShortCaseCitation\('([^']+)'", name)
                if match:
                    return match.group(1)
                return name.split("ShortCaseCitation(")[0].strip()
            if "FullJournalCitation(" in name:
                match = re.search(r"FullJournalCitation\('([^']+)'", name)
                if match:
                    return match.group(1)
                return name.split("FullJournalCitation(")[0].strip()
            
            return name

        # Get cluster case name from attribute or metadata
        cluster_case_name = getattr(self, "cluster_case_name", None)
        # Also check metadata if direct attribute is not set
        if not cluster_case_name and hasattr(self, "metadata") and self.metadata:
            cluster_case_name = self.metadata.get("cluster_case_name")
        
        # CRITICAL FIX: Clean cluster_case_name if it contains citation objects
        if cluster_case_name and "FullCaseCitation(" in str(cluster_case_name):
            cluster_case_name = _clean_case_name(cluster_case_name)

        extracted_case_name = self.extracted_case_name
        canonical_name = self.canonical_name

        # FIX #13: Add case_name field with intelligent fallback
        # Priority: canonical_name (verified) > extracted_case_name (unverified) > N/A
        
        # Clean both canonical and extracted names
        cleaned_canonical_name = _clean_case_name(canonical_name)
        cleaned_extracted_name = _clean_case_name(extracted_case_name)
        # Repair truncated LLC (e.g. "Consumer First Legal Group, LL" -> "LLC")
        try:
            from src.utils.cluster_display_utils import _repair_truncated_llc
            cleaned_canonical_name = _repair_truncated_llc(cleaned_canonical_name or "") or cleaned_canonical_name
        except Exception:
            pass
        case_name = cleaned_canonical_name or cleaned_extracted_name or "N/A"
        
        # CRITICAL FIX: Clean the citation field itself
        citation_text = self.citation
        if citation_text and isinstance(citation_text, str):
            # Check if it's a Python object representation
            if "Citation(" in citation_text:
                citation_text = _clean_case_name(citation_text)

            # USER FIX 2026-03-02: Fix citation text contamination from preceding citations
            # When citations appear in a list ("A, 404 U.S. 336, and B, 543 U.S. 335"), extraction
            # can grab the wrong case name (e.g. "Mor, 404 U.S. 336" for United States v. Bass).
            # If we have canonical_name from verification, replace wrong prefix with canonical.
            if cleaned_canonical_name and "," in citation_text and self.verified:
                import re
                parts = citation_text.split(",", 1)
                prefix = parts[0].strip()
                reporter_part = parts[1].strip()
                # Reporter should look like "404 U.S. 336 (scotus)" or "543 U.S. 335"
                if re.match(r"^\d+\s+U\.?\s*S\.?", reporter_part, re.I):
                    canonical_lower = (cleaned_canonical_name or "").lower()
                    prefix_lower = prefix.lower()
                    # Prefix is contaminated if short and not a substring of canonical
                    if len(prefix) < 30 and prefix_lower not in canonical_lower:
                        citation_text = cleaned_canonical_name + ", " + reporter_part

        # USER FIX 2026-01-08: Clean parallel_citations and cluster_members lists
        parallel_citations = self.parallel_citations or []
        if parallel_citations:
            parallel_citations = [_clean_case_name(str(c)) if "Citation(" in str(c) else c for c in parallel_citations]
        
        cluster_members = self.cluster_members or []
        if cluster_members:
            cluster_members = [_clean_case_name(str(c)) if "Citation(" in str(c) else c for c in cluster_members]

        # Debug logging for data separation
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(
            f"DATA_SEPARATION: case_name='{case_name}', cluster='{cluster_case_name}', extracted='{extracted_case_name}', canonical='{canonical_name}'"
        )

        # CRITICAL FIX: DO NOT override verified status!
        # A citation with verified=False should stay False even if it has canonical data
        # This is because canonical data can come from true_by_parallel propagation
        # (unverified citation inherits canonical data from verified parallel citation)
        verified_status = self.verified  # Use the actual verification status

        result = {
            "citation": citation_text,
            "case_name": case_name,  # FIX #13: Intelligent fallback (canonical > extracted > N/A)
            "extracted_case_name": cleaned_extracted_name,  # CRITICAL FIX: Return cleaned name
            "extracted_date": self.extracted_date,
            "canonical_name": cleaned_canonical_name,  # CRITICAL FIX: Return cleaned name
            "canonical_date": self.canonical_date,
            "canonical_url": self.canonical_url,
            "cluster_case_name": cluster_case_name,  # FIXED: Add cluster_case_name field
            "verified": verified_status,  # Use actual verification status (not overridden)
            "url": self.url,
            "court": self.court,
            "docket_number": self.docket_number,
            "confidence": self.confidence,
            "method": self.method,
            "pattern": self.pattern,
            "context": self.context,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "is_parallel": self.is_parallel,
            "is_cluster": self.is_cluster,
            "parallel_citations": parallel_citations,  # USER FIX 2026-01-08: Use cleaned list
            "cluster_members": cluster_members,  # USER FIX 2026-01-08: Use cleaned list
            "pinpoint_pages": self.pinpoint_pages,
            "docket_numbers": self.docket_numbers,
            "case_history": self.case_history,
            "publication_status": self.publication_status,
            "source": self.source,
            "error": self.error,
            "metadata": self.metadata,
            "cluster_id": self.cluster_id,
            "true_by_parallel": self.true_by_parallel,  # Useful for tracking verification by parallel citations
            "is_verified": self.verified,  # Add is_verified alias for backward compatibility
            "name_mismatch": self.name_mismatch,  # Flag when extracted != canonical
            "date_mismatch": self.date_mismatch,
            "mismatch_confidence": self.mismatch_confidence,
            "possible_match": self.possible_match,
            "is_proprietary_only": getattr(self, "is_proprietary_only", False),
            "name_likely_in_left_context": getattr(self, "name_likely_in_left_context", False),
        }
        return result


@dataclass
class ProcessingConfig:
    use_eyecite: bool = True
    use_regex: bool = True
    extract_case_names: bool = True
    extract_dates: bool = True
    enable_clustering: bool = True
    enable_deduplication: bool = True
    enable_verification: bool = True   # Changed default to True for verification
    context_window: int = 400
    min_confidence: float = 0.5
    max_citations_per_text: int = 1000
    debug_mode: bool = False
