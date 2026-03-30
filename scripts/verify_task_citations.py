#!/usr/bin/env python3
"""
Verify task result: (1) all citations found appear in the document,
(2) no obvious citations missed, (3) clustering looks correct.
Usage: python scripts/verify_task_citations.py <task_id> [path_to.pdf]
"""
import re
import sys
from pathlib import Path

def load_task_result(task_id: str, base_url: str = "http://localhost:5000/casestrainer/api"):
    import requests
    r = requests.get(f"{base_url}/task_status/{task_id}", timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("citations") or [], data.get("clusters") or []

def get_document_text(pdf_path: Path) -> str:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.unified_text_extractor import extract_text_from_file_unified
    text, _ = extract_text_from_file_unified(str(pdf_path), verbose=False)
    return text or ""

def normalize_for_match(s: str) -> str:
    """Collapse whitespace, strip, for containment check."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", str(s).strip())

def citation_core(ct: str) -> str:
    """Volume + reporter + page core (digits and reporter abbrev) for fuzzy match."""
    ct = normalize_for_match(ct)
    # Keep digits, letters, dots (e.g. 181 Wn.2d 391 -> 181 Wn.2d 391)
    return ct

def main():
    task_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not task_id:
        print("Usage: python scripts/verify_task_citations.py <task_id> [path_to.pdf]")
        sys.exit(1)
    pdf_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "1028814.pdf"
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        sys.exit(1)

    citations, clusters = load_task_result(task_id)
    doc_text = get_document_text(pdf_path)
    doc_norm = normalize_for_match(doc_text)

    # (1) All found citations: check that the core (volume + reporter + page) appears in document
    not_found = []
    for i, c in enumerate(citations):
        ct = c.get("citation", "") if isinstance(c, dict) else getattr(c, "citation", "")
        if not ct or not ct.strip():
            continue
        ct_norm = normalize_for_match(ct)
        found = False
        if ct_norm in doc_norm or ct_norm[:80] in doc_norm:
            found = True
        if not found:
            # Extract one or more "vol reporter page" cores (e.g. 181 Wn.2d 391, 334 P.3d 519)
            cores = re.findall(
                r"(\d{1,4}\s+(?:Wn\.?\s*2d|Wash\.?\s*2d|Wn\.?\s*App\.?\s*2d|P\.\s*[23]d|F\.\s*[234]d|N\.W\.\s*2d|S\.E\.\s*2d|U\.\s*S\.\s+\d+|S\.\s*Ct\.\s+\d+)\s+\d{1,5})",
                ct_norm,
                re.IGNORECASE
            )
            for core in cores:
                core_n = normalize_for_match(core)
                if core_n in doc_norm:
                    found = True
                    break
                alt = core_n.replace("Wn. ", "Wash. ").replace("Wash. ", "Wn. ")
                if alt in doc_norm:
                    found = True
                    break
        if not found and len(ct_norm) > 25:
            if ct_norm[-40:] in doc_norm:
                found = True
        if not found:
            not_found.append((i, ct_norm[:70]))

    # (2) Missed: find reporter-like patterns in doc and count how many we have
    reporter_pattern = re.compile(
        r"\b(\d{1,4}\s+(?:Wn\.?\s*2d|Wash\.?\s*2d|P\.\s*3d|P\.\s*2d|F\.\s*3d|U\.\s*S\.\s+\d+)\s+\d{1,5})\b",
        re.IGNORECASE
    )
    in_doc = set()
    for m in reporter_pattern.finditer(doc_norm):
        in_doc.add(normalize_for_match(m.group(1)))
    # How many of those appear in our citations (as substring)?
    found_in_result = 0
    for doc_cit in in_doc:
        for c in citations:
            ct = (c.get("citation") or "") if isinstance(c, dict) else getattr(c, "citation", "")
            if doc_cit in normalize_for_match(ct) or normalize_for_match(ct).endswith(doc_cit):
                found_in_result += 1
                break

    # (3) Clustering: Kustura (1 cluster), Mercer (1), Deggs (no 115 S.Ct.), Walston (334 not 34)
    kustura_clusters = []
    mercer_clusters = []
    deggs_clusters = []
    walston_clusters = []
    for i, cl in enumerate(clusters):
        name = (cl.get("canonical_name") or cl.get("extracted_case_name") or "").lower()
        cits = cl.get("citations") or []
        cite_strs = [x.get("citation", "") if isinstance(x, dict) else "" for x in cits]
        if "kustura" in name:
            kustura_clusters.append((i, len(cits), cite_strs))
        if "mercer" in name and "personal restraint" in name:
            mercer_clusters.append((i, len(cits), cite_strs))
        if "deggs" in name or "asbestos" in name.lower():
            deggs_clusters.append((i, len(cits), cite_strs))
        if "walston" in name:
            walston_clusters.append((i, len(cits), cite_strs))

    # Report
    print("=" * 60)
    print("CITATION VERIFICATION")
    print("=" * 60)
    print(f"Task ID: {task_id}")
    print(f"PDF: {pdf_path}")
    print(f"Document length: {len(doc_text)} chars")
    print(f"Citations in result: {len(citations)}")
    print(f"Clusters: {len(clusters)}")
    print()
    print("(1) Citations NOT found in document (by substring/core match):")
    if not_found:
        for i, ct in not_found[:25]:
            print(f"  [{i}] {ct}...")
        if len(not_found) > 25:
            print(f"  ... and {len(not_found) - 25} more")
        print(f"  Total: {len(not_found)} / {len(citations)}")
    else:
        print("  All checked citations appear in the document.")
    print()
    print("(2) Reporter-style strings in document vs in result:")
    print(f"  In doc (pattern match): {len(in_doc)}")
    print(f"  Matched to result: {found_in_result}")
    print()
    print("(3) Clustering spot checks:")
    print(f"  Kustura: {len(kustura_clusters)} cluster(s)")
    for i, n, strs in kustura_clusters:
        has_169 = any("169" in s and "Wn" in s for s in strs)
        has_233 = any("233 P" in s for s in strs)
        print(f"    Cluster {i}: {n} citations, has 169 Wn.2d={has_169}, has 233 P.3d={has_233}")
    print(f"  Mercer (In re Pers. Restraint): {len(mercer_clusters)} cluster(s)")
    for i, n, strs in mercer_clusters:
        print(f"    Cluster {i}: {n} citations")
    print(f"  Deggs: {len(deggs_clusters)} cluster(s)")
    for i, n, strs in deggs_clusters:
        has_sct = any("S. Ct." in s or "S.Ct." in s for s in strs)
        print(f"    Cluster {i}: {n} citations, contains S.Ct. (Hubbard)={has_sct}")
    print(f"  Walston: {len(walston_clusters)} cluster(s)")
    for i, n, strs in walston_clusters:
        has_34_bad = any("34 P.3d" in s and "334" not in s and "134" not in s for s in strs)
        has_334 = any("334 P.3d" in s for s in strs)
        print(f"    Cluster {i}: {n} citations, bogus 34 P.3d={has_34_bad}, has 334 P.3d={has_334}")

if __name__ == "__main__":
    main()
