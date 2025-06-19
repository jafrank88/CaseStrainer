#!/usr/bin/env python3
"""
Export highlighted (potentially mismatched) citations to CSV for review.
"""
import json
import csv
import sys
import os

# Configurable input/output
DEFAULT_INPUT = "citation_verification_results.json"
DEFAULT_OUTPUT = "highlighted_citations_report.csv"


def load_results(input_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Support both list and dict with 'results' or 'citations' key
    if isinstance(data, dict):
        if "results" in data:
            return data["results"]
        if "citations" in data:
            return data["citations"]
        if "validation_results" in data:
            return data["validation_results"]
    return data


def export_highlighted(results, output_path):
    fields = [
        "citation",
        "case_name_extracted",
        "case_name_verified",
        "name_similarity",
        "url",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            if r.get("highlight"):
                writer.writerow({
                    "citation": r.get("citation", ""),
                    "case_name_extracted": r.get("case_name_extracted", ""),
                    "case_name_verified": r.get("case_name_verified", ""),
                    "name_similarity": r.get("name_similarity", ""),
                    "url": r.get("url", ""),
                })
    print(f"Exported {sum(1 for r in results if r.get('highlight'))} highlighted citations to {output_path}")


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    output_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        sys.exit(1)
    results = load_results(input_path)
    export_highlighted(results, output_path)

if __name__ == "__main__":
    main() 