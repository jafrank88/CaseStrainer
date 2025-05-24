"""
Analyze Citation Verification Results

This script analyzes the verification results from the multi-source verifier
and updates the CaseStrainer database with the findings.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Constants
DATABASE_FILE = "citations.db"
VERIFICATION_RESULTS_FILE = "verification_results.json"
ANALYSIS_REPORT_FILE = "verification_analysis_report.html"


def load_verification_results():
    """Load verification results from the JSON file."""
    try:
        with open(VERIFICATION_RESULTS_FILE, "r") as f:
            results = json.load(f)
        print(f"Loaded {len(results)} verification results")
        return results
    except Exception as e:
        print(f"Error loading verification results: {e}")
        return []


def update_database_with_results(results):
    """Update the database with verification results."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Add verification_status column if it doesn't exist
    cursor.execute("PRAGMA table_info(unconfirmed_citations)")
    columns = [column[1] for column in cursor.fetchall()]

    if "verification_status" not in columns:
        cursor.execute(
            "ALTER TABLE unconfirmed_citations ADD COLUMN verification_status TEXT"
        )

    if "verification_confidence" not in columns:
        cursor.execute(
            "ALTER TABLE unconfirmed_citations ADD COLUMN verification_confidence REAL"
        )

    if "verification_source" not in columns:
        cursor.execute(
            "ALTER TABLE unconfirmed_citations ADD COLUMN verification_source TEXT"
        )

    if "verification_tag" not in columns:
        cursor.execute(
            "ALTER TABLE unconfirmed_citations ADD COLUMN verification_tag TEXT"
        )

    # Update each citation with verification results
    for result in results:
        citation_id = result.get("citation_id")
        verification_result = result.get("verification_result", {})

        found = verification_result.get("found", False)
        confidence = verification_result.get("confidence", 0.0)
        source = verification_result.get("source", "unknown")

        status = "VERIFIED" if found else "UNVERIFIED"

        # Add a special tag for citations verified by multi-source but not by CourtListener
        tag = None
        if found and source != "CourtListener" and source != "unknown":
            tag = "MULTI_SOURCE_ONLY"

        cursor.execute(
            "UPDATE unconfirmed_citations SET verification_status = ?, verification_confidence = ?, verification_source = ?, verification_tag = ? WHERE id = ?",
            (status, confidence, source, tag, citation_id),
        )

    conn.commit()
    conn.close()

    print(f"Updated database with verification results for {len(results)} citations")


def analyze_results(results):
    """Analyze verification results and generate statistics."""
    if not results:
        print("No results to analyze")
        return {}

    # Extract key information
    total_citations = len(results)
    verified_citations = sum(
        1 for r in results if r.get("verification_result", {}).get("found", False)
    )
    unverified_citations = total_citations - verified_citations

    # Count multi-source only verifications
    multi_source_only = 0
    for r in results:
        result = r.get("verification_result", {})
        found = result.get("found", False)
        source = result.get("source", "unknown")
        if found and source != "CourtListener" and source != "unknown":
            multi_source_only += 1

    # Group by source
    sources = {}
    for r in results:
        source = r.get("verification_result", {}).get("source", "unknown")
        if source not in sources:
            sources[source] = 0
        sources[source] += 1

    # Group by confidence
    confidence_ranges = {
        "0.0-0.2": 0,
        "0.2-0.4": 0,
        "0.4-0.6": 0,
        "0.6-0.8": 0,
        "0.8-1.0": 0,
    }

    for r in results:
        confidence = r.get("verification_result", {}).get("confidence", 0.0)
        if 0.0 <= confidence < 0.2:
            confidence_ranges["0.0-0.2"] += 1
        elif 0.2 <= confidence < 0.4:
            confidence_ranges["0.2-0.4"] += 1
        elif 0.4 <= confidence < 0.6:
            confidence_ranges["0.4-0.6"] += 1
        elif 0.6 <= confidence < 0.8:
            confidence_ranges["0.6-0.8"] += 1
        elif 0.8 <= confidence <= 1.0:
            confidence_ranges["0.8-1.0"] += 1

    # Analyze citation types
    citation_types = {}
    for r in results:
        citation_text = r.get("citation_text", "")

        # Determine citation type based on text pattern
        if "U.S." in citation_text:
            citation_type = "US Reports"
        elif "F." in citation_text and "Supp." in citation_text:
            citation_type = "Federal Supplement"
        elif "F." in citation_text:
            citation_type = "Federal Reporter"
        elif "S.Ct." in citation_text:
            citation_type = "Supreme Court Reporter"
        elif "WL" in citation_text:
            citation_type = "Westlaw"
        elif "L.Ed." in citation_text:
            citation_type = "Lawyers Edition"
        else:
            citation_type = "Other"

        if citation_type not in citation_types:
            citation_types[citation_type] = 0
        citation_types[citation_type] += 1

    # Compile analysis
    analysis = {
        "total_citations": total_citations,
        "verified_citations": verified_citations,
        "unverified_citations": unverified_citations,
        "multi_source_only": multi_source_only,
        "verification_rate": (
            verified_citations / total_citations if total_citations > 0 else 0
        ),
        "multi_source_rate": (
            multi_source_only / verified_citations if verified_citations > 0 else 0
        ),
        "sources": sources,
        "confidence_ranges": confidence_ranges,
        "citation_types": citation_types,
    }

    print("Analysis complete:")
    print(f"Total citations: {total_citations}")
    print(
        f"Verified citations: {verified_citations} ({analysis['verification_rate']:.2%})"
    )
    print(f"Unverified citations: {unverified_citations}")
    print(
        f"Multi-source only verifications: {multi_source_only} ({analysis['multi_source_rate']:.2%} of verified)"
    )

    return analysis


def generate_report(analysis, results):
    """Generate an HTML report with visualizations."""
    try:
        # Create DataFrame for easier manipulation
        df = pd.DataFrame(results)
        df["found"] = df["verification_result"].apply(lambda x: x.get("found", False))
        df["confidence"] = df["verification_result"].apply(
            lambda x: x.get("confidence", 0.0)
        )
        df["source"] = df["verification_result"].apply(
            lambda x: x.get("source", "unknown")
        )

        # Create visualizations
        plt.figure(figsize=(10, 6))
        plt.pie(
            [analysis["verified_citations"], analysis["unverified_citations"]],
            labels=["Verified", "Unverified"],
            autopct="%1.1f%%",
            colors=["#4CAF50", "#F44336"],
        )
        plt.title("Citation Verification Results")
        plt.savefig("verification_pie_chart.png")

        plt.figure(figsize=(12, 6))
        sources = analysis["sources"]
        plt.bar(sources.keys(), sources.values())
        plt.title("Verification Sources")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig("verification_sources.png")

        plt.figure(figsize=(10, 6))
        citation_types = analysis["citation_types"]
        plt.bar(citation_types.keys(), citation_types.values())
        plt.title("Citation Types")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig("citation_types.png")

        # Generate HTML report
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Citation Verification Analysis</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .chart {{ margin: 20px 0; text-align: center; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Citation Verification Analysis Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="summary">
                    <h2>Summary</h2>
                    <p>Total Citations: {analysis['total_citations']}</p>
                    <p>Verified Citations: {analysis['verified_citations']} ({analysis['verification_rate']:.2%})</p>
                    <p>Unverified Citations: {analysis['unverified_citations']}</p>
                    <p>Multi-source Only Verifications: {analysis['multi_source_only']} ({analysis['multi_source_rate']:.2%} of verified)</p>
                </div>
                
                <div class="chart">
                    <h2>Verification Results</h2>
                    <img src="verification_pie_chart.png" alt="Verification Results">
                </div>
                
                <div class="chart">
                    <h2>Verification Sources</h2>
                    <img src="verification_sources.png" alt="Verification Sources">
                </div>
                
                <div class="chart">
                    <h2>Citation Types</h2>
                    <img src="citation_types.png" alt="Citation Types">
                </div>
                
                <h2>Detailed Results</h2>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Citation</th>
                        <th>Status</th>
                        <th>Confidence</th>
                        <th>Source</th>
                        <th>Multi-source Only</th>
                    </tr>
        """

        # Add table rows for each citation
        for r in results:
            citation_id = r.get("citation_id")
            citation_text = r.get("citation_text", "")
            verification_result = r.get("verification_result", {})
            found = verification_result.get("found", False)
            confidence = verification_result.get("confidence", 0.0)
            source = verification_result.get("source", "unknown")
            status = "VERIFIED" if found else "UNVERIFIED"

            # Determine if this is a multi-source only verification
            is_multi_source_only = (
                found and source != "CourtListener" and source != "unknown"
            )
            multi_source_tag = "YES" if is_multi_source_only else "NO"

            html += f"""
                    <tr>
                        <td>{citation_id}</td>
                        <td>{citation_text}</td>
                        <td>{status}</td>
                        <td>{confidence:.2f}</td>
                        <td>{source}</td>
                        <td>{multi_source_tag}</td>
                    </tr>
            """

        html += """
                </table>
            </div>
        </body>
        </html>
        """

        with open(ANALYSIS_REPORT_FILE, "w") as f:
            f.write(html)

        print(f"Generated analysis report: {ANALYSIS_REPORT_FILE}")
        return True
    except Exception as e:
        print(f"Error generating report: {e}")
        return False


def main():
    """Main function to analyze verification results."""
    print("Starting analysis of citation verification results...")

    # Load verification results
    results = load_verification_results()

    if not results:
        print("No verification results to analyze")
        return

    # Update database with results
    update_database_with_results(results)

    # Analyze results
    analysis = analyze_results(results)

    # Generate report
    generate_report(analysis, results)

    print("Analysis complete")


if __name__ == "__main__":
    main()
