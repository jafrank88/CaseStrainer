"""
Create Confirmed with Multitool Tab

This script creates a new tab in CaseStrainer for citations that were confirmed
with the multi-source tool but not with CourtListener, along with all context.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# Constants
DATABASE_FILE = "citations.db"
VERIFICATION_RESULTS_FILE = "verification_results.json"


def setup_multitool_confirmed_table():
    """Set up the multitool_confirmed_citations table."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Create multitool_confirmed_citations table if it doesn't exist
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS multitool_confirmed_citations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        citation_text TEXT NOT NULL,
        brief_url TEXT,
        context TEXT,
        verification_source TEXT,
        verification_confidence REAL,
        verification_explanation TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    conn.commit()
    conn.close()

    print("Multitool confirmed citations table set up successfully")


def get_multitool_confirmed_citations():
    """Get citations that were confirmed with the multi-source tool but not with CourtListener."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get citations with the MULTI_SOURCE_ONLY tag
    cursor.execute(
        """
    SELECT * FROM unconfirmed_citations 
    WHERE verification_tag = 'MULTI_SOURCE_ONLY' 
    AND verification_status = 'VERIFIED'
    """
    )

    citations = [dict(row) for row in cursor.fetchall()]

    conn.close()

    print(f"Retrieved {len(citations)} citations confirmed only by multi-source tool")
    return citations


def load_verification_results():
    """Load verification results to get additional context."""
    try:
        with open(VERIFICATION_RESULTS_FILE, "r") as f:
            results = json.load(f)
        return results
    except Exception as e:
        print(f"Error loading verification results: {e}")
        return []


def populate_multitool_confirmed_tab(citations, verification_results):
    """Populate the Confirmed with Multitool tab with citations and context."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Clear existing entries
    cursor.execute("DELETE FROM multitool_confirmed_citations")

    # Create a lookup dictionary for verification results
    results_lookup = {}
    for result in verification_results:
        citation_id = result.get("citation_id")
        if citation_id:
            results_lookup[citation_id] = result.get("verification_result", {})

    # Add each citation to the table
    count = 0
    for citation in citations:
        citation_id = citation["id"]
        citation_text = citation["citation_text"]
        brief_url = citation.get("brief_url", "")
        context = citation.get("context", "")

        # Get additional verification details from results
        verification_result = results_lookup.get(citation_id, {})
        verification_source = verification_result.get(
            "source", citation.get("verification_source", "Unknown")
        )
        verification_confidence = verification_result.get(
            "confidence", citation.get("verification_confidence", 0.0)
        )
        verification_explanation = verification_result.get(
            "explanation", "No explanation available"
        )

        cursor.execute(
            """
        INSERT INTO multitool_confirmed_citations 
        (citation_text, brief_url, context, verification_source, verification_confidence, verification_explanation, date_added) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                citation_text,
                brief_url,
                context,
                verification_source,
                verification_confidence,
                verification_explanation,
                datetime.now(),
            ),
        )

        count += 1

    conn.commit()
    conn.close()

    print(f"Added {count} citations to the Confirmed with Multitool tab")


def export_to_tab_delimited(citations, verification_results):
    """Export the multitool confirmed citations to a tab-delimited file for easy import."""
    output_file = "Multitool_Confirmed_Citations_Tab.txt"

    # Create a lookup dictionary for verification results
    results_lookup = {}
    for result in verification_results:
        citation_id = result.get("citation_id")
        if citation_id:
            results_lookup[citation_id] = result.get("verification_result", {})

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            # Write header
            f.write(
                "Citation\tBrief URL\tContext\tVerification Source\tConfidence\tExplanation\n"
            )

            # Write each citation
            for citation in citations:
                citation_id = citation["id"]
                citation_text = citation["citation_text"]
                brief_url = citation.get("brief_url", "")
                context = citation.get("context", "")

                # Get additional verification details from results
                verification_result = results_lookup.get(citation_id, {})
                verification_source = verification_result.get(
                    "source", citation.get("verification_source", "Unknown")
                )
                verification_confidence = verification_result.get(
                    "confidence", citation.get("verification_confidence", 0.0)
                )
                verification_explanation = verification_result.get(
                    "explanation", "No explanation available"
                )

                # Write tab-delimited line
                f.write(
                    f"{citation_text}\t{brief_url}\t{context}\t{verification_source}\t{verification_confidence}\t{verification_explanation}\n"
                )

        print(f"Exported multitool confirmed citations to {output_file}")
        return True
    except Exception as e:
        print(f"Error exporting to tab-delimited file: {e}")
        return False


def generate_summary_report(citations, verification_results):
    """Generate a summary report of the multitool confirmed citations."""
    # Create a lookup dictionary for verification results
    results_lookup = {}
    for result in verification_results:
        citation_id = result.get("citation_id")
        if citation_id:
            results_lookup[citation_id] = result.get("verification_result", {})

    # Count by verification source
    sources = {}
    for citation in citations:
        citation_id = citation["id"]
        verification_result = results_lookup.get(citation_id, {})
        source = verification_result.get(
            "source", citation.get("verification_source", "Unknown")
        )

        if source not in sources:
            sources[source] = 0
        sources[source] += 1

    # Count by confidence range
    confidence_ranges = {
        "0.0-0.2": 0,
        "0.2-0.4": 0,
        "0.4-0.6": 0,
        "0.6-0.8": 0,
        "0.8-1.0": 0,
    }

    for citation in citations:
        citation_id = citation["id"]
        verification_result = results_lookup.get(citation_id, {})
        confidence = verification_result.get(
            "confidence", citation.get("verification_confidence", 0.0)
        )

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

    # Generate report
    report_file = "Multitool_Confirmed_Citations_Report.txt"

    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("Multitool Confirmed Citations Summary Report\n")
            f.write("===========================================\n\n")

            f.write(f"Total Citations: {len(citations)}\n\n")

            f.write("Verification Sources:\n")
            for source, count in sources.items():
                f.write(f"  {source}: {count} ({count/len(citations):.2%})\n")
            f.write("\n")

            f.write("Confidence Ranges:\n")
            for range_name, count in confidence_ranges.items():
                if count > 0:
                    f.write(f"  {range_name}: {count} ({count/len(citations):.2%})\n")
            f.write("\n")

            f.write("Citation List:\n")
            for i, citation in enumerate(citations, 1):
                citation_text = citation["citation_text"]
                citation_id = citation["id"]
                verification_result = results_lookup.get(citation_id, {})
                source = verification_result.get(
                    "source", citation.get("verification_source", "Unknown")
                )
                confidence = verification_result.get(
                    "confidence", citation.get("verification_confidence", 0.0)
                )

                f.write(
                    f"  {i}. {citation_text} (Source: {source}, Confidence: {confidence:.2f})\n"
                )

        print(f"Generated summary report: {report_file}")
        return True
    except Exception as e:
        print(f"Error generating summary report: {e}")
        return False


def update_app_to_include_new_tab():
    """Update app_final.py to include the new Confirmed with Multitool tab."""
    app_file = "app_final.py"

    if not os.path.exists(app_file):
        print(f"Warning: {app_file} not found. Cannot update app to include new tab.")
        return False

    try:
        with open(app_file, "r", encoding="utf-8") as f:
            app_code = f.read()

        # Check if the tab already exists
        if "Confirmed with Multitool" in app_code:
            print("The Confirmed with Multitool tab already exists in the app.")
            return True

        # Find the tabs definition section
        tabs_section = "@app.route('/tabs')"
        if tabs_section not in app_code:
            print("Could not find tabs section in app_final.py")
            return False

        # Add the new tab to the tabs list
        tabs_code = """@app.route('/tabs')
def tabs():
    return render_template('tabs.html', tabs=[
        'Home', 
        'Citation Extractor', 
        'Citation Verifier',
        'Unconfirmed Citations',
        'Confirmed with Multitool',
        'Citation Database'
    ])"""

        # Replace the existing tabs section
        app_code = app_code.replace(
            app_code[app_code.find(tabs_section) : app_code.find("])") + 2], tabs_code
        )

        # Add route for the new tab
        new_tab_route = """
@app.route('/confirmed_with_multitool')
def confirmed_with_multitool():
    conn = get_db_connection()
    citations = conn.execute('SELECT * FROM multitool_confirmed_citations ORDER BY date_added DESC').fetchall()
    conn.close()
    return render_template('confirmed_with_multitool.html', citations=citations)
"""

        # Add the new route before the main function
        if "if __name__ == '__main__':" in app_code:
            insert_point = app_code.find("if __name__ == '__main__':")
            app_code = app_code[:insert_point] + new_tab_route + app_code[insert_point:]

        # Write the updated code back to the file
        with open(app_file, "w", encoding="utf-8") as f:
            f.write(app_code)

        print(f"Updated {app_file} to include the Confirmed with Multitool tab")

        # Create the template file for the new tab
        templates_dir = "templates"
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)

        template_file = os.path.join(templates_dir, "confirmed_with_multitool.html")

        with open(template_file, "w", encoding="utf-8") as f:
            f.write(
                """{% extends 'base.html' %}

{% block content %}
<div class="container mt-4">
    <h1>Confirmed with Multitool</h1>
    <p class="lead">Citations that were confirmed with the multi-source tool but not with CourtListener.</p>
    
    <div class="alert alert-info">
        <strong>Info:</strong> This tab shows {{ citations|length }} citations that were verified using alternative sources beyond CourtListener.
    </div>
    
    {% if citations %}
    <table class="table table-striped">
        <thead>
            <tr>
                <th>Citation</th>
                <th>Brief URL</th>
                <th>Context</th>
                <th>Verification Source</th>
                <th>Confidence</th>
                <th>Explanation</th>
            </tr>
        </thead>
        <tbody>
            {% for citation in citations %}
            <tr>
                <td>{{ citation.citation_text }}</td>
                <td>
                    {% if citation.brief_url %}
                    <a href="{{ citation.brief_url }}" target="_blank">{{ citation.brief_url }}</a>
                    {% else %}
                    N/A
                    {% endif %}
                </td>
                <td>{{ citation.context }}</td>
                <td>{{ citation.verification_source }}</td>
                <td>{{ citation.verification_confidence }}</td>
                <td>{{ citation.verification_explanation }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class="alert alert-warning">
        No citations found that were confirmed only by the multi-source tool.
    </div>
    {% endif %}
</div>
{% endblock %}"""
            )

        print(f"Created template file: {template_file}")
        return True
    except Exception as e:
        print(f"Error updating app to include new tab: {e}")
        return False


def main():
    """Main function to create the Confirmed with Multitool tab."""
    print("Creating Confirmed with Multitool tab...")

    # Set up the multitool_confirmed_citations table
    setup_multitool_confirmed_table()

    # Get citations that were confirmed with the multi-source tool but not with CourtListener
    citations = get_multitool_confirmed_citations()

    if not citations:
        print("No citations found that were confirmed only by the multi-source tool.")
        return

    # Load verification results for additional context
    verification_results = load_verification_results()

    # Populate the Confirmed with Multitool tab
    populate_multitool_confirmed_tab(citations, verification_results)

    # Export to tab-delimited file
    export_to_tab_delimited(citations, verification_results)

    # Generate summary report
    generate_summary_report(citations, verification_results)

    # Update app to include the new tab
    update_app_to_include_new_tab()

    print("\nConfirmed with Multitool tab creation complete")
    print("You can now restart CaseStrainer to see the new tab")


if __name__ == "__main__":
    main()
