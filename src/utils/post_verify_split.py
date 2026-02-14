"""Post-verification cluster split by canonical name."""
import logging
logger = logging.getLogger(__name__)

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
            nc["has_name_mismatch"] = any(x.get("name_mismatch",False) for x in cl_list if isinstance(x,dict))
            result.append(nc)
        if unv:
            nc2 = dict(cl)
            nc2["cluster_id"] = f"{bid}_cnsplit_unv"
            nc2["citations"] = unv
            nc2["cluster_size"] = len(unv)
            nc2["verified"] = False
            nc2["canonical_name"] = ""
            nc2["canonical_url"] = None
            result.append(nc2)
    if len(result) != len(clusters):
        logger.info(f"[TASK:{task_id}] POST-VERIFY-SPLIT: {len(clusters)} -> {len(result)} clusters")
    return result
