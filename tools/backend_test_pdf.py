import json
import os
import sys
import shutil

# Ensure local project modules are importable
sys.path.insert(0, os.getcwd())

from src.unified_input_processor import UnifiedInputProcessor


class FS:
    def __init__(self, path: str):
        self.filename = os.path.basename(path)
        self._path = path

    def save(self, dest: str):
        shutil.copyfile(self._path, dest)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: backend_test_pdf.py <pdf_path>"}))
        sys.exit(2)

    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(json.dumps({"error": f"file not found: {file_path}"}))
        sys.exit(3)

    uip = UnifiedInputProcessor(verbose=False)
    req_id = "cli-backend-test"

    inp = {
        "file": FS(file_path),
        "filename": os.path.basename(file_path),
        "content_type": "application/pdf",
    }

    res = uip.process_any_input(inp, "file", req_id, force_mode="sync")

    # Build summary strictly from backend flags
    clusters = res.get("clusters", []) or []

    def build_details(cluster):
        cits = cluster.get("citations", []) or []
        indices = cluster.get("mismatch_indices", []) or [
            i for i, c in enumerate(cits) if c.get("name_mismatch") or c.get("date_mismatch")
        ]
        out = []
        for i in indices[:3]:
            if 0 <= i < len(cits):
                cit = cits[i]
                out.append(
                    {
                        "idx": i,
                        "citation": cit.get("citation"),
                        "extracted_case_name": cit.get("extracted_case_name"),
                        "extracted_date": cit.get("extracted_date"),
                        "canonical_name": cit.get("canonical_name"),
                        "canonical_date": cit.get("canonical_date"),
                        "name_mismatch": cit.get("name_mismatch"),
                        "date_mismatch": cit.get("date_mismatch"),
                        "possible_match": cit.get("possible_match"),
                        "verified": cit.get("verified"),
                        "canonical_url": cit.get("canonical_url"),
                    }
                )
        return out

    mismatch_clusters = [
        {
            "cluster_id": cl.get("cluster_id"),
            "has_name_mismatch": cl.get("has_name_mismatch"),
            "has_date_mismatch": cl.get("has_date_mismatch"),
            "mismatch_indices": cl.get("mismatch_indices"),
            "details": build_details(cl),
        }
        for cl in clusters
        if cl.get("has_name_mismatch") or cl.get("has_date_mismatch")
    ]

    possible_match_count = sum(
        1 for cl in clusters for cit in (cl.get("citations") or []) if cit.get("possible_match")
    )

    summary = {
        "cluster_count": len(clusters),
        "mismatch_cluster_count": len(mismatch_clusters),
        "possible_match_count": possible_match_count,
        "mismatch_clusters": mismatch_clusters[:15],
    }

    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
