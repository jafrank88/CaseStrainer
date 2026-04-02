"""Post-verification cluster split by canonical name and by reporter tier (Supreme vs District)."""
import logging
import re

from src.utils.mismatch_utils import compute_cluster_mismatch_flags
from src.utils.same_case import names_are_same_case
from src.utils.cluster_display_utils import _is_google_search_url
from src.clustering.detection import _clean_ecn

logger = logging.getLogger(__name__)


_HISTORICAL_SCOTUS_RE = re.compile(
    r"\d+\s+(?:CRANCH|WHEAT|WALL|PET|HOW|BLACK|DALL)\b\.?\s+\d+", re.IGNORECASE
)


def _reporter_tier(citation_text):
    """
    Return reporter tier for a citation: 'supreme' (U.S., S.Ct., L.Ed.,
    and historical nominative reporters), 'district' (F. Supp. etc.),
    'circuit' (F.2d, F.3d, F.4th), or 'other'.
    """
    if not citation_text or not isinstance(citation_text, str):
        return "other"
    c = citation_text.strip().upper()
    # Supreme Court — modern reporters
    if re.search(r"\d+\s+U\.?\s*S\.?\s+\d+", c) or re.search(r"\d+\s+U\.?\s*S\.?\s+_+", c):
        return "supreme"
    if re.search(r"\d+\s+S\.?\s*CT\.?\s+\d+", c) or re.search(r"\d+\s+S\.?\s*CT\.?\s+_+", c):
        return "supreme"
    if re.search(r"\d+\s+L\.?\s*ED\.?\s*(?:2D\s+)?\d+", c):
        return "supreme"
    # Supreme Court — historical nominative reporters (pre-1875)
    # Dallas (Dall.), Cranch, Wheaton (Wheat.), Peters (Pet.),
    # Howard (How.), Black, Wallace (Wall.)
    if _HISTORICAL_SCOTUS_RE.search(c):
        return "supreme"
    # District (Federal Supplement)
    if re.search(r"\d+\s+F\.?\s*SUPP\.?\s*(?:2D\s+|3D\s+)?\d+", c):
        return "district"
    # Circuit (Federal Reporter)
    if re.search(r"\d+\s+F\.?\s*(?:2D|3D|4TH)\s+\d+", c):
        return "circuit"
    return "other"


def reporter_tier(citation_text):
    """Public wrapper for citation reporter tier classification."""
    return _reporter_tier(citation_text)


def reporter_court_label(citation_text):
    """
    Human-readable court label from reporter family.
    - district: F. Supp.
    - circuit: F.2d/F.3d/F.4th
    - supreme: U.S./S. Ct./L. Ed.
    """
    tier = _reporter_tier(citation_text)
    if tier == "district":
        return "District Court"
    if tier == "circuit":
        return "Appellate Court"
    if tier == "supreme":
        return "United States Supreme Court"
    return "Other Court"


def split_clusters_by_reporter_tier(clusters, task_id=""):
    """
    Split clusters that mix different federal court tiers into separate clusters.
    Tiers are:
      - supreme: U.S., S. Ct., L. Ed.
      - circuit: F.2d, F.3d, F.4th
      - district: F. Supp. (all series)
    These tiers must not be in the same cluster.
    WL citations are treated as "other" and, when Supreme is present, stay with Supreme.
    """
    if not clusters:
        return clusters
    result = []
    for cl in clusters:
        if not isinstance(cl, dict):
            result.append(cl)
            continue
        cits = cl.get("citations", [])
        by_tier = {"supreme": [], "district": [], "circuit": [], "other": []}
        for c in cits:
            if not isinstance(c, dict):
                by_tier["other"].append(c)
                continue
            ct = (c.get("citation") or "").strip()
            tier = _reporter_tier(ct)
            by_tier[tier].append(c)
        has_supreme = len(by_tier["supreme"]) > 0
        has_district = len(by_tier["district"]) > 0
        has_circuit = len(by_tier["circuit"]) > 0
        other = by_tier["other"]
        wl_other = []
        non_wl_other = []
        for c in other:
            if not isinstance(c, dict):
                non_wl_other.append(c)
                continue
            if _is_wl_citation((c.get("citation") or "").strip()):
                wl_other.append(c)
            else:
                non_wl_other.append(c)
        # Split state/other from federal supreme when both present (e.g. Deggs 2016 + Hubbard 115 S.Ct.).
        has_state_other = len(non_wl_other) > 0
        tier_count = sum([1 if has_supreme else 0, 1 if has_district else 0, 1 if has_circuit else 0])
        if tier_count <= 1 and not (has_supreme and has_state_other):
            result.append(cl)
            continue

        # Court-tier split required. Keep WL with Supreme when available.
        # Do NOT attach state reporters (Wn.2d, P.3d, etc.) to supreme — separate cluster.
        tier_groups = {
            "supreme": list(by_tier["supreme"]),
            "circuit": list(by_tier["circuit"]),
            "district": list(by_tier["district"]),
            "state_other": list(non_wl_other),
        }
        if has_supreme:
            tier_groups["supreme"].extend(wl_other)
        if not has_supreme:
            # No Supreme in cluster: keep "other" with the largest lower-court tier.
            dominant = "circuit" if len(tier_groups["circuit"]) >= len(tier_groups["district"]) else "district"
            tier_groups[dominant].extend(wl_other + non_wl_other)

        bid = cl.get("cluster_id", "c0")
        logger.info(
            f"[TASK:{task_id}] POST-VERIFY-SPLIT-TIER: '{bid}' mixes court tiers "
            f"(supreme={len(by_tier['supreme'])}, circuit={len(by_tier['circuit'])}, district={len(by_tier['district'])}, state_other={len(non_wl_other)}); splitting"
        )

        for label, tier_cits in [
            ("supreme", tier_groups["supreme"]),
            ("circuit", tier_groups["circuit"]),
            ("district", tier_groups["district"]),
            ("state_other", tier_groups["state_other"]),
        ]:
            if not tier_cits:
                continue
            nc = dict(cl)
            nc["cluster_id"] = f"{bid}_tier_{label}"
            nc["citations"] = tier_cits
            ct_set = {x.get("citation", "") for x in tier_cits if isinstance(x, dict)}
            nc["cluster_members"] = [
                m for m in cl.get("cluster_members", [])
                if (m.get("citation", "") if isinstance(m, dict) else str(m)) in ct_set
            ]
            nc["cluster_size"] = len(tier_cits)
            if tier_cits and isinstance(tier_cits[0], dict):
                nc["canonical_name"] = next((x.get("canonical_name") for x in tier_cits if x.get("canonical_name")), nc.get("canonical_name"))
                nc["canonical_url"] = next((x.get("canonical_url") for x in tier_cits if x.get("canonical_url")), nc.get("canonical_url"))
                nc["verified"] = any(x.get("verified") for x in tier_cits if isinstance(x, dict))
            result.append(nc)
    if len(result) != len(clusters):
        logger.info(f"[TASK:{task_id}] POST-VERIFY-SPLIT-TIER: {len(clusters)} -> {len(result)} clusters")
    return result


def _is_wl_citation(citation_text):
    """True if citation is Westlaw format (e.g. 2025 WL 2061447)."""
    if not citation_text or not isinstance(citation_text, str):
        return False
    return bool(re.search(r"\d{4}\s+WL\s+\d+", citation_text.strip()))


def split_clusters_wl_from_lower_federal(clusters, task_id=""):
    """
    Split clusters that mix a WL citation (e.g. cert. denied order) with a circuit/district
    citation (F.3d, F. Supp.) into two clusters. They are different documents: e.g.
    "939 F.3d 310 (1st Cir. 2019), cert. denied, 2020 WL 129919" - the circuit opinion
    and the cert. denial are not the same document, so the WL should not be "Verified by Parallel".
    Only applies when there is no Supreme (U.S.) citation in the cluster; Supreme+WL stay together.
    """
    if not clusters:
        return clusters
    result = []
    for cl in clusters:
        if not isinstance(cl, dict):
            result.append(cl)
            continue
        cits = cl.get("citations", [])
        wl_cits = []
        non_wl = []
        has_supreme = False
        for c in cits:
            if not isinstance(c, dict):
                non_wl.append(c)
                continue
            ct = (c.get("citation") or "").strip()
            tier = _reporter_tier(ct)
            if tier == "supreme":
                has_supreme = True
            if _is_wl_citation(ct):
                wl_cits.append(c)
            else:
                non_wl.append(c)
        # Split only when: has WL + has circuit or district (non-WL), and no Supreme
        has_lower_federal = any(
            _reporter_tier((c.get("citation") or "").strip()) in ("district", "circuit")
            for c in non_wl if isinstance(c, dict)
        )
        if not wl_cits or not has_lower_federal or has_supreme:
            result.append(cl)
            continue
        bid = cl.get("cluster_id", "c0")
        logger.info(
            f"[TASK:{task_id}] POST-VERIFY-SPLIT-WL-FED: '{bid}' mixes WL (e.g. cert. denied) with circuit/district; splitting"
        )
        for label, group in [("non_wl", non_wl), ("wl", wl_cits)]:
            if not group:
                continue
            nc = dict(cl)
            nc["cluster_id"] = f"{bid}_wlfed_{label}"
            nc["citations"] = group
            ct_set = {x.get("citation", "") for x in group if isinstance(x, dict)}
            nc["cluster_members"] = [
                m for m in cl.get("cluster_members", [])
                if (m.get("citation", "") if isinstance(m, dict) else str(m)) in ct_set
            ]
            nc["cluster_size"] = len(group)
            if group and isinstance(group[0], dict):
                nc["canonical_name"] = next((x.get("canonical_name") for x in group if x.get("canonical_name")), nc.get("canonical_name"))
                nc["canonical_url"] = next((x.get("canonical_url") for x in group if x.get("canonical_url")), nc.get("canonical_url"))
                nc["verified"] = any(x.get("verified") for x in group if isinstance(x, dict))
            result.append(nc)
    if len(result) != len(clusters):
        logger.info(f"[TASK:{task_id}] POST-VERIFY-SPLIT-WL-FED: {len(clusters)} -> {len(result)} clusters")
    return result


def split_clusters_by_distinct_wl(clusters, task_id=""):
    """
    Split clusters that contain multiple distinct WL citations (different WL document IDs)
    into one cluster per WL citation. Same case name + year does not mean same document:
    e.g. 2025 WL 2061447, 2025 WL 553485, 2025 WL 1649197 are three different documents
    (orders, opinions, etc.) and should not be grouped as one cluster.
    """
    if not clusters:
        return clusters
    result = []
    for cl in clusters:
        if not isinstance(cl, dict):
            result.append(cl)
            continue
        cits = cl.get("citations", [])
        wl_cits = []
        non_wl = []
        for c in cits:
            if not isinstance(c, dict):
                non_wl.append(c)
                continue
            ct = (c.get("citation") or "").strip()
            if _is_wl_citation(ct):
                wl_cits.append(c)
            else:
                non_wl.append(c)
        # Only split when there are 2+ distinct WL citations (different WL numbers)
        wl_ids = set()
        for c in wl_cits:
            ct = (c.get("citation") or "").strip()
            m = re.search(r"(\d{4}\s+WL\s+\d+)", ct)
            if m:
                wl_ids.add(m.group(1))
        if len(wl_ids) <= 1:
            result.append(cl)
            continue
        bid = cl.get("cluster_id", "c0")
        logger.info(
            f"[TASK:{task_id}] POST-VERIFY-SPLIT-WL: '{bid}' has {len(wl_ids)} distinct WL citations; splitting one per WL"
        )
        # One cluster per distinct WL ID (citations sharing same WL ID stay together)
        by_wl_id = {}
        for c in wl_cits:
            ct = (c.get("citation") or "").strip()
            m = re.search(r"(\d{4}\s+WL\s+\d+)", ct)
            key = m.group(1) if m else ct
            by_wl_id.setdefault(key, []).append(c)
        for wl_id, group in by_wl_id.items():
            nc = dict(cl)
            nc["cluster_id"] = f"{bid}_wl_{wl_id.replace(' ', '_')}"
            nc["citations"] = group
            ct_set = {x.get("citation", "") for x in group if isinstance(x, dict)}
            nc["cluster_members"] = [
                m for m in cl.get("cluster_members", [])
                if (m.get("citation", "") if isinstance(m, dict) else str(m)) in ct_set
            ]
            nc["cluster_size"] = len(group)
            if group and isinstance(group[0], dict):
                nc["canonical_name"] = next((x.get("canonical_name") for x in group if x.get("canonical_name")), nc.get("canonical_name"))
                nc["canonical_url"] = next((x.get("canonical_url") for x in group if x.get("canonical_url")), nc.get("canonical_url"))
                nc["verified"] = any(x.get("verified") for x in group if isinstance(x, dict))
            result.append(nc)
        if non_wl:
            nc = dict(cl)
            nc["cluster_id"] = f"{bid}_wl_nonwl"
            nc["citations"] = non_wl
            ct_set = {x.get("citation", "") for x in non_wl if isinstance(x, dict)}
            nc["cluster_members"] = [
                m for m in cl.get("cluster_members", [])
                if (m.get("citation", "") if isinstance(m, dict) else str(m)) in ct_set
            ]
            nc["cluster_size"] = len(non_wl)
            result.append(nc)
    if len(result) != len(clusters):
        logger.info(f"[TASK:{task_id}] POST-VERIFY-SPLIT-WL: {len(clusters)} -> {len(result)} clusters")
    return result


def split_clusters_by_court_tier_and_wl(clusters, task_id=""):
    """Single-pass replacement for split_clusters_by_reporter_tier + split_clusters_wl_from_lower_federal + split_clusters_by_distinct_wl.

    For each citation we compute tier + WL status + WL-id exactly once, then apply
    all three split decisions in one iteration over citations.
    """
    if not clusters:
        return clusters
    result = []
    for cl in clusters:
        if not isinstance(cl, dict):
            result.append(cl)
            continue
        cits = cl.get("citations", [])

        tier_map = {}  # citation index -> tier
        is_wl = {}     # citation index -> bool
        wl_id = {}     # citation index -> "YYYY WL NNNNN" or None

        for i, c in enumerate(cits):
            if not isinstance(c, dict):
                tier_map[i] = "other"
                is_wl[i] = False
                wl_id[i] = None
                continue
            ct = (c.get("citation") or "").strip()
            tier_map[i] = _reporter_tier(ct)
            w = re.search(r"(\d{4}\s+WL\s+\d+)", ct)
            is_wl[i] = bool(w)
            wl_id[i] = w.group(1) if w else None

        has_supreme = any(t == "supreme" for t in tier_map.values())
        has_district = any(t == "district" for t in tier_map.values())
        has_circuit = any(t == "circuit" for t in tier_map.values())
        wl_indices = [i for i, w in is_wl.items() if w]
        non_wl_other_indices = [i for i, t in tier_map.items() if t == "other" and not is_wl.get(i)]
        has_state_other = len(non_wl_other_indices) > 0
        tier_count = sum([has_supreme, has_district, has_circuit])

        needs_tier_split = tier_count > 1 or (has_supreme and has_state_other)
        has_lower_federal = any(tier_map[i] in ("district", "circuit") for i in range(len(cits)) if not is_wl.get(i))
        needs_wl_fed_split = (not needs_tier_split and wl_indices and has_lower_federal and not has_supreme)
        distinct_wl_ids = {wl_id[i] for i in wl_indices if wl_id[i]}
        needs_wl_distinct_split = len(distinct_wl_ids) > 1

        if not needs_tier_split and not needs_wl_fed_split and not needs_wl_distinct_split:
            result.append(cl)
            continue

        bid = cl.get("cluster_id", "c0")

        def _make_sub(label, indices):
            group = [cits[i] for i in indices]
            if not group:
                return None
            nc = dict(cl)
            nc["cluster_id"] = f"{bid}_{label}"
            nc["citations"] = group
            ct_set = {x.get("citation", "") for x in group if isinstance(x, dict)}
            nc["cluster_members"] = [
                m for m in cl.get("cluster_members", [])
                if (m.get("citation", "") if isinstance(m, dict) else str(m)) in ct_set
            ]
            nc["cluster_size"] = len(group)
            if group and isinstance(group[0], dict):
                nc["canonical_name"] = next(
                    (x.get("canonical_name") for x in group if x.get("canonical_name")), nc.get("canonical_name")
                )
                nc["canonical_url"] = next(
                    (x.get("canonical_url") for x in group if x.get("canonical_url")), nc.get("canonical_url")
                )
                nc["verified"] = any(x.get("verified") for x in group if isinstance(x, dict))
            return nc

        if needs_tier_split:
            logger.info(
                f"[TASK:{task_id}] SPLIT-TIER-WL: '{bid}' mixes court tiers "
                f"(supreme={sum(1 for t in tier_map.values() if t=='supreme')}, "
                f"circuit={sum(1 for t in tier_map.values() if t=='circuit')}, "
                f"district={sum(1 for t in tier_map.values() if t=='district')}, "
                f"state_other={len(non_wl_other_indices)}); splitting"
            )
            supreme_idx = [i for i, t in tier_map.items() if t == "supreme"]
            circuit_idx = [i for i, t in tier_map.items() if t == "circuit"]
            district_idx = [i for i, t in tier_map.items() if t == "district"]
            if has_supreme:
                supreme_idx.extend(wl_indices)
            elif len(circuit_idx) >= len(district_idx):
                circuit_idx.extend(wl_indices + non_wl_other_indices)
            else:
                district_idx.extend(wl_indices + non_wl_other_indices)
            state_idx = non_wl_other_indices if has_supreme else []
            for label, idx_list in [("tier_supreme", supreme_idx), ("tier_circuit", circuit_idx),
                                     ("tier_district", district_idx), ("tier_state", state_idx)]:
                nc = _make_sub(label, idx_list)
                if nc:
                    result.append(nc)

        elif needs_wl_fed_split:
            logger.info(
                f"[TASK:{task_id}] SPLIT-TIER-WL: '{bid}' mixes WL with circuit/district; splitting"
            )
            non_wl_idx = [i for i in range(len(cits)) if not is_wl.get(i)]
            nc = _make_sub("wlfed_non_wl", non_wl_idx)
            if nc:
                result.append(nc)
            if not needs_wl_distinct_split:
                nc = _make_sub("wlfed_wl", wl_indices)
                if nc:
                    result.append(nc)
            else:
                by_wl = {}
                for i in wl_indices:
                    by_wl.setdefault(wl_id[i] or f"unknown_{i}", []).append(i)
                for wid, idx_list in by_wl.items():
                    nc = _make_sub(f"wl_{wid.replace(' ', '_')}", idx_list)
                    if nc:
                        result.append(nc)

        elif needs_wl_distinct_split:
            logger.info(
                f"[TASK:{task_id}] SPLIT-TIER-WL: '{bid}' has {len(distinct_wl_ids)} distinct WL citations; splitting"
            )
            non_wl_idx = [i for i in range(len(cits)) if not is_wl.get(i)]
            by_wl = {}
            for i in wl_indices:
                by_wl.setdefault(wl_id[i] or f"unknown_{i}", []).append(i)
            for wid, idx_list in by_wl.items():
                nc = _make_sub(f"wl_{wid.replace(' ', '_')}", idx_list)
                if nc:
                    result.append(nc)
            if non_wl_idx:
                nc = _make_sub("wl_nonwl", non_wl_idx)
                if nc:
                    result.append(nc)

    if len(result) != len(clusters):
        logger.info(f"[TASK:{task_id}] SPLIT-TIER-WL: {len(clusters)} -> {len(result)} clusters")
    return result


def _year_from_citation(c):
    """Extract citation-local year from a citation dict (document-first)."""
    if not isinstance(c, dict):
        return None
    md = {}
    md_raw = c.get("metadata")
    if isinstance(md_raw, dict):
        md = md_raw
    md_year = str(md.get("year") or "").strip()
    md_src = str(md.get("extracted_date_source") or "").strip()
    if md_year.isdigit() and 1700 <= int(md_year) <= 2030 and md_src.startswith("citation_"):
        return int(md_year)
    ct = (c.get("citation") or c.get("text") or "")
    m = re.search(r"\(([^)]*?)\)\s*$", str(ct))
    if m:
        y = re.search(r"(19|20)\d{2}", m.group(1))
        if y:
            return int(y.group(0))
    for key in ("extracted_date", "extracted_year", "date", "canonical_date"):
        v = c.get(key)
        if v:
            m = re.search(r"(19|20)\d{2}", str(v))
            if m:
                return int(m.group(0))
    return None


def split_clusters_by_date_conflict(clusters, task_id="", max_year_diff=2):
    """
    Split a cluster when it contains citations from different cases by year (e.g. Deggs 2016 vs Hubbard 1995).
    When nested quoting merges two cases (Deggs quoting Hubbard), citations have different years; group
    citations by year (within max_year_diff) and split so each year-bucket becomes its own cluster.
    """
    if not clusters:
        return clusters
    result = []
    for cl in clusters:
        if not isinstance(cl, dict):
            result.append(cl)
            continue
        cits = cl.get("citations", [])
        if len(cits) <= 1:
            result.append(cl)
            continue
        # Bucket citations by year; years within max_year_diff go in same bucket
        buckets = []  # list of (repr_year, list of citations)
        no_year = []
        for c in cits:
            if not isinstance(c, dict):
                no_year.append(c)
                continue
            y = _year_from_citation(c)
            if y is None:
                no_year.append(c)
                continue
            placed = False
            for by, group in buckets:
                if by is not None and abs(by - y) <= max_year_diff:
                    group.append(c)
                    placed = True
                    break
            if not placed:
                buckets.append((y, [c]))
        # No-year citations: do NOT attach federal supreme (S.Ct., U.S., L.Ed.) to first bucket
        # when the cluster has state citations with years — e.g. Deggs 2016 quoting Hubbard 1995;
        # the S.Ct. cite may have no year in text but is a different case (nested quote).
        if no_year and buckets:
            supreme_no_year = []
            other_no_year = []
            for c in no_year:
                if not isinstance(c, dict):
                    other_no_year.append(c)
                    continue
                ct = (c.get("citation") or "").strip()
                if _reporter_tier(ct) == "supreme":
                    supreme_no_year.append(c)
                else:
                    other_no_year.append(c)
            if supreme_no_year and buckets:
                # Put supreme no-year in own bucket so we split (e.g. Hubbard S.Ct. out of Deggs).
                buckets.append((None, supreme_no_year))
            if other_no_year:
                buckets[0][1].extend(other_no_year)
        elif no_year:
            buckets.append((None, no_year))
        # Merge buckets that are within max_year_diff (e.g. 2015 and 2016)
        merged_buckets = []
        for by, group in buckets:
            if not group:
                continue
            years_in_group = {_year_from_citation(c) for c in group if isinstance(c, dict)}
            years_in_group.discard(None)
            merged = False
            for i, (m_y, m_group) in enumerate(merged_buckets):
                m_years = {_year_from_citation(c) for c in m_group if isinstance(c, dict)}
                m_years.discard(None)
                if not m_years or not years_in_group:
                    continue
                if any(
                    my is not None and gy is not None and abs(my - gy) <= max_year_diff
                    for my in m_years for gy in years_in_group
                ):
                    m_group.extend(group)
                    merged = True
                    break
            if not merged:
                merged_buckets.append((by, group))
        if len(merged_buckets) <= 1:
            result.append(cl)
            continue
        bid = cl.get("cluster_id", "c0")
        logger.info(
            f"[TASK:{task_id}] POST-VERIFY-SPLIT-DATE: '{bid}' has {len(merged_buckets)} year groups; splitting"
        )
        for si, (_, group) in enumerate(merged_buckets):
            nc = dict(cl)
            nc["cluster_id"] = f"{bid}_yr_{si}"
            nc["citations"] = group
            ct_set = {x.get("citation", "") for x in group if isinstance(x, dict)}
            nc["cluster_members"] = [
                m for m in cl.get("cluster_members", [])
                if (m.get("citation", "") if isinstance(m, dict) else str(m)) in ct_set
            ]
            nc["cluster_size"] = len(group)
            if group and isinstance(group[0], dict):
                nc["canonical_name"] = next(
                    (x.get("canonical_name") for x in group if x.get("canonical_name")), nc.get("canonical_name")
                )
                nc["canonical_url"] = next(
                    (x.get("canonical_url") for x in group if x.get("canonical_url")), nc.get("canonical_url")
                )
                yr = next((_year_from_citation(x) for x in group if isinstance(x, dict)), None)
                if yr:
                    nc["canonical_date"] = str(yr)
                nc["extracted_case_name"] = next(
                    (x.get("extracted_case_name") for x in group if x.get("extracted_case_name") and x.get("extracted_case_name") != "N/A"), ""
                )
                nc["verified"] = any(x.get("verified") for x in group if isinstance(x, dict))
            compute_cluster_mismatch_flags(nc)
            result.append(nc)
    if len(result) != len(clusters):
        logger.info(f"[TASK:{task_id}] POST-VERIFY-SPLIT-DATE: {len(clusters)} -> {len(result)} clusters")
    return result


def split_clusters_by_extracted_name(clusters, task_id=""):
    """
    Split clusters when citations have clearly different extracted case names
    (e.g. "Soo Line R.R. Co. v. Consol. Rail Corp." vs "In re Sw. Airlines Voucher Litig.").
    Uses same_case logic so two citations stay together only if names_are_same_case(ecn_a, ecn_b).
    Prevents one cluster showing a single wrong canonical when the document cites two different cases.
    """
    if not clusters:
        return clusters
    result = []
    for cl in clusters:
        if not isinstance(cl, dict):
            result.append(cl)
            continue
        cits = cl.get("citations", [])
        if len(cits) <= 1:
            result.append(cl)
            continue
        # Do not split when all citations share the same canonical_url (same case, e.g. Clements).
        # Different extracted_case_name variants (e.g. "Travelers Indemnity" vs "Travelers Indem.") should stay in one cluster.
        canon_urls = {
            (c.get("canonical_url") or "").strip()
            for c in cits
            if isinstance(c, dict) and (c.get("canonical_url") or "").strip()
        }
        if len(canon_urls) == 1:
            result.append(cl)
            continue
        # Group citations by extracted-case equivalence (same_case). Use cleaned names
        # so "Kustura v. Dep't..., 169 Wn. 2d 81" and "Kustura v. Dep't..., 233 P.3d 853" stay together.
        groups = []
        unv = []
        na_cits = []  # Citations with N/A or missing extracted_case_name
        for c in cits:
            if not isinstance(c, dict):
                unv.append(c)
                continue
            ecn = (c.get("extracted_case_name") or "").strip() or None
            if not ecn or ecn == "N/A":
                na_cits.append(c)
                continue
            ecn_clean = _clean_ecn(ecn) if ecn else None
            placed = False
            for _, group in groups:
                ref = next((x for x in group if isinstance(x, dict)), None)
                if not ref:
                    continue
                ref_ecn = (ref.get("extracted_case_name") or "").strip() or None
                ref_ecn_clean = _clean_ecn(ref_ecn) if ref_ecn else None
                if names_are_same_case(ecn_clean or ecn, ref_ecn_clean or ref_ecn):
                    group.append(c)
                    placed = True
                    break
            if not placed:
                groups.append((ecn, [c]))
        # Attach N/A citations to the largest group (unknown name ≠ different case)
        if na_cits:
            if groups:
                largest = max(groups, key=lambda g: len(g[1]))
                largest[1].extend(na_cits)
            else:
                groups.append((None, na_cits))
        if unv:
            # Attach non-dict citations to first group to avoid extra fragment cluster
            if groups:
                groups[0][1].extend(unv)
            else:
                groups.append((None, unv))
        if len(groups) <= 1:
            result.append(cl)
            continue
        bid = cl.get("cluster_id", "c0")
        logger.info(
            f"[TASK:{task_id}] POST-VERIFY-SPLIT-EXTRACTED: '{bid}' has {len(groups)} distinct extracted names; splitting"
        )
        for si, (ecn, group) in enumerate(groups):
            nc = dict(cl)
            nc["cluster_id"] = f"{bid}_ecn_{si}"
            nc["citations"] = group
            ct_set = {x.get("citation", "") for x in group if isinstance(x, dict)}
            nc["cluster_members"] = [
                m for m in cl.get("cluster_members", [])
                if (m.get("citation", "") if isinstance(m, dict) else str(m)) in ct_set
            ]
            nc["cluster_size"] = len(group)
            if group and isinstance(group[0], dict):
                nc["canonical_name"] = next((x.get("canonical_name") for x in group if x.get("canonical_name")), nc.get("canonical_name"))
                nc["canonical_url"] = next((x.get("canonical_url") for x in group if x.get("canonical_url")), nc.get("canonical_url"))
                nc["extracted_case_name"] = ecn or next((x.get("extracted_case_name") for x in group if x.get("extracted_case_name")), "")
                nc["verified"] = any(x.get("verified") for x in group if isinstance(x, dict))
            compute_cluster_mismatch_flags(nc)
            result.append(nc)
    if len(result) != len(clusters):
        logger.info(f"[TASK:{task_id}] POST-VERIFY-SPLIT-EXTRACTED: {len(clusters)} -> {len(result)} clusters")
    return result


def split_clusters_by_canonical_name(clusters, task_id=""):
    if not clusters:
        return clusters

    def _year_from_text(v):
        m = re.search(r"(19|20)\d{2}", str(v or ""))
        return int(m.group(0)) if m else 0

    def _first_party(name):
        s = str(name or "").strip()
        if not s or " v" not in s.lower():
            return ""
        parts = re.split(r"\s+v\.?\s+", s, maxsplit=1, flags=re.IGNORECASE)
        if not parts:
            return ""
        left = parts[0].strip()
        return left.split()[-1].lower() if left else ""

    result = []
    for cl in clusters:
        if not isinstance(cl, dict):
            result.append(cl)
            continue
        cits = cl.get("citations", [])
        cn_map, unv = {}, []
        for c in cits:
            if not isinstance(c, dict):
                unv.append(c); continue
            cn = (c.get("canonical_name") or "").strip()
            if not cn or cn == "N/A" or not c.get("verified"):
                unv.append(c)
                continue
            # Group by same case (names_are_same_case) so "Kustura v. Department..."
            # and "KUSTURA v. Dept. of Labor and Industries" stay in one cluster.
            placed = False
            c_url = (c.get("canonical_url") or "").strip()
            for existing_cn, group_list in list(cn_map.items()):
                # Hard split guard: if both cites are verified rows with different
                # non-google canonical URLs, they are different cases.
                # This prevents false merges like MCI 708 F.2d 1081 + S. Pac. 740 F.2d 980.
                ref = next((x for x in group_list if isinstance(x, dict)), None)
                if ref is not None:
                    ref_url = (ref.get("canonical_url") or "").strip()
                    if (
                        c_url and ref_url and c_url != ref_url
                        and not _is_google_search_url(c_url)
                        and not _is_google_search_url(ref_url)
                        and bool(c.get("verified"))
                        and bool(ref.get("verified"))
                    ):
                        continue
                if names_are_same_case(cn, existing_cn):
                    group_list.append(c)
                    placed = True
                    break
            if not placed:
                cn_map[cn] = [c]
        if len(cn_map) <= 1:
            result.append(cl); continue
        bid = cl.get("cluster_id", "c0")
        logger.info(f"[TASK:{task_id}] POST-VERIFY-SPLIT: '{bid}' -> {list(cn_map.keys())}")

        # Keep WL with its matching verified canonical cluster when name+year align.
        # This preserves intended groupings like U.S. + WL for the same case/year.
        if unv:
            still_unv = []
            for c in unv:
                if not isinstance(c, dict):
                    still_unv.append(c)
                    continue
                ct = (c.get("citation") or "").strip()
                is_wl = bool(re.search(r"\b\d{4}\s+WL\s+\d+\b", ct, re.IGNORECASE))
                if not is_wl:
                    still_unv.append(c)
                    continue
                ext_name = (c.get("extracted_case_name") or "").strip()
                ext_year = _year_from_text(c.get("extracted_date")) or _year_from_text(ct)
                ext_party = _first_party(ext_name)
                placed = False
                for cn, cl_list in cn_map.items():
                    grp_year = 0
                    for gc in cl_list:
                        grp_year = _year_from_text(gc.get("canonical_date")) or _year_from_text(gc.get("extracted_date"))
                        if grp_year:
                            break
                    grp_party = _first_party(cn)
                    party_ok = bool(ext_party and grp_party and ext_party == grp_party)
                    year_ok = bool(ext_year and grp_year and ext_year == grp_year)
                    if party_ok and year_ok:
                        cl_list.append(c)
                        placed = True
                        logger.info(
                            f"[TASK:{task_id}] POST-VERIFY-SPLIT: Kept WL '{ct}' with canonical '{cn}' "
                            f"(party/year aligned: {ext_party}/{ext_year})"
                        )
                        break
                if not placed:
                    still_unv.append(c)
            unv = still_unv

        for si, (cn, cl_list) in enumerate(cn_map.items()):
            nc = dict(cl)
            nc["cluster_id"] = f"{bid}_cnsplit_{si}"
            nc["citations"] = cl_list
            ct = {x.get("citation","") for x in cl_list}
            nc["cluster_members"] = [m for m in cl.get("cluster_members",[]) if (m.get("citation","") if isinstance(m,dict) else str(m)) in ct]
            nc["cluster_size"] = len(cl_list)
            nc["canonical_name"] = cn
            nc["verifying_display_name"] = cn
            cd = next((x.get("canonical_date") for x in cl_list if x.get("canonical_date")), None)
            if cd:
                nc["canonical_date"] = cd
            # Derive split cluster year from citation-local evidence in this split.
            ys = [y for y in (_year_from_citation(x) for x in cl_list if isinstance(x, dict)) if y]
            if ys:
                counts = {}
                for y in ys:
                    counts[y] = counts.get(y, 0) + 1
                nc["cluster_year"] = str(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0])
            elif cd:
                nc["cluster_year"] = str(cd)
            cu = next((x.get("canonical_url") for x in cl_list if x.get("canonical_url")), None)
            if cu and not _is_google_search_url(cu):
                nc["canonical_url"] = cu
                nc["display_canonical_url"] = cu
            ecn = next((x.get("extracted_case_name","") for x in cl_list if x.get("extracted_case_name") and x.get("extracted_case_name")!="N/A"), "")
            if ecn:
                nc["extracted_case_name"] = ecn
                nc["submitted_display_name"] = ecn
            nc["verified"] = bool(cu)
            compute_cluster_mismatch_flags(nc)
            result.append(nc)
        if unv:
            nc2 = dict(cl)
            nc2["cluster_id"] = f"{bid}_cnsplit_unv"
            nc2["citations"] = unv
            nc2["cluster_size"] = len(unv)
            nc2["verified"] = False
            nc2["canonical_name"] = ""
            nc2["canonical_url"] = None
            compute_cluster_mismatch_flags(nc2)
            result.append(nc2)
    if len(result) != len(clusters):
        logger.info(f"[TASK:{task_id}] POST-VERIFY-SPLIT: {len(clusters)} -> {len(result)} clusters")
    return result
