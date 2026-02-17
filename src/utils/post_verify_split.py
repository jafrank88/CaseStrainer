"""Post-verification cluster split by canonical name and by reporter tier (Supreme vs District)."""
import logging
import re

from src.utils.mismatch_utils import compute_cluster_mismatch_flags

logger = logging.getLogger(__name__)


def _reporter_tier(citation_text):
    """
    Return reporter tier for a citation: 'supreme' (U.S., S.Ct., L.Ed.),
    'district' (F. Supp., F. Supp. 2d, F. Supp. 3d), 'circuit' (F.2d, F.3d, F.4th), or 'other'.
    Used to avoid grouping Supreme Court and District Court citations as the same case.
    """
    if not citation_text or not isinstance(citation_text, str):
        return "other"
    c = citation_text.strip().upper()
    # Supreme Court
    if re.search(r"\d+\s+U\.?\s*S\.?\s+\d+", c) or re.search(r"\d+\s+U\.?\s*S\.?\s+_+", c):
        return "supreme"
    if re.search(r"\d+\s+S\.?\s*CT\.?\s+\d+", c) or re.search(r"\d+\s+S\.?\s*CT\.?\s+_+", c):
        return "supreme"
    if re.search(r"\d+\s+L\.?\s*ED\.?\s*(?:2D\s+)?\d+", c):
        return "supreme"
    # District (Federal Supplement)
    if re.search(r"\d+\s+F\.?\s*SUPP\.?\s*(?:2D\s+|3D\s+)?\d+", c):
        return "district"
    # Circuit (Federal Reporter)
    if re.search(r"\d+\s+F\.?\s*(?:2D|3D|4TH)\s+\d+", c):
        return "circuit"
    return "other"


def split_clusters_by_reporter_tier(clusters, task_id=""):
    """
    Split clusters that mix Supreme Court (U.S., S.Ct.) and District Court (F. Supp.)
    citations into separate clusters. They are different courts and cannot be the same case.
    E.g. 606 U.S. 831 (Supreme) and 763 F. Supp. 3d 723 (District) must not be in one cluster.
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
        if not (has_supreme and has_district):
            result.append(cl)
            continue
        # Only split out District. Keep Supreme + WL/other together (same case, e.g. "606 U.S. ----, 2025 WL 1773631").
        bid = cl.get("cluster_id", "c0")
        logger.info(
            f"[TASK:{task_id}] POST-VERIFY-SPLIT-TIER: '{bid}' mixes Supreme and District; splitting out District only (Supreme+WL stay together)"
        )
        non_district = by_tier["supreme"] + by_tier["circuit"] + by_tier["other"]
        for label, tier_cits in [("non_district", non_district), ("district", by_tier["district"])]:
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
    "939 F.3d 310 (1st Cir. 2019), cert. denied, 2020 WL 129919" — the circuit opinion
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


def split_clusters_by_canonical_name(clusters, task_id=""):
    if not clusters:
        return clusters
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
            if cn and cn != "N/A" and c.get("verified"):
                cn_map.setdefault(cn, []).append(c)
            else:
                unv.append(c)
        if len(cn_map) <= 1:
            result.append(cl); continue
        bid = cl.get("cluster_id", "c0")
        logger.info(f"[TASK:{task_id}] POST-VERIFY-SPLIT: '{bid}' -> {list(cn_map.keys())}")
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
                nc["cluster_year"] = str(cd)
            cu = next((x.get("canonical_url") for x in cl_list if x.get("canonical_url")), None)
            if cu:
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
