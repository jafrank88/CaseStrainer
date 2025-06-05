#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Enhanced Citation Validator

This module provides a simplified version of the Enhanced Citation Validator
that doesn't require the problematic modules.
"""

import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Sample data for demonstration purposes
LANDMARK_CASES = {
    "410 U.S. 113": "Roe v. Wade",
    "347 U.S. 483": "Brown v. Board of Education",
    "5 U.S. 137": "Marbury v. Madison",
    "531 U.S. 98": "Bush v. Gore",
    "384 U.S. 436": "Miranda v. Arizona",
    "163 U.S. 537": "Plessy v. Ferguson",
    "198 U.S. 45": "Lochner v. New York",
    "323 U.S. 214": "Korematsu v. United States",
    "558 U.S. 310": "Citizens United v. FEC",
    "576 U.S. 644": "Obergefell v. Hodges",
}

# Sample citation contexts
CITATION_CONTEXTS = {
    "410 U.S. 113": "The Court held in Roe v. Wade, 410 U.S. 113 (1973), that a woman's right to an abortion was protected by the right to privacy under the Fourteenth Amendment.",
    "347 U.S. 483": "In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court unanimously ruled that racial segregation in public schools was unconstitutional.",
    "5 U.S. 137": "Marbury v. Madison, 5 U.S. 137 (1803), established the principle of judicial review in the United States, giving the Supreme Court the power to invalidate acts of Congress that conflict with the Constitution.",
    "531 U.S. 98": "The Supreme Court's decision in Bush v. Gore, 531 U.S. 98 (2000), effectively resolved the 2000 presidential election in favor of George W. Bush.",
    "384 U.S. 436": "Miranda v. Arizona, 384 U.S. 436 (1966), established that prior to police interrogation, a person must be informed of their right to consult with an attorney and of their right against self-incrimination.",
}


def parse_citation_components(citation_text):
    """Parse a citation into its component parts."""
    components = {}

    # Simple parsing logic for U.S. Reporter citations
    parts = citation_text.split()
    if len(parts) >= 3 and parts[1].upper() == "U.S.":
        components["volume"] = parts[0]
        components["reporter"] = parts[1]
        components["page"] = parts[2]
        components["court"] = "U.S. Supreme Court"

        # Extract year if available (e.g., from "410 U.S. 113 (1973)")
        if (
            len(citation_text) > len(" ".join(parts[:3]))
            and "(" in citation_text
            and ")" in citation_text
        ):
            year_part = citation_text.split("(")[1].split(")")[0]
            if year_part.isdigit() and 1700 < int(year_part) < 2100:
                components["year"] = year_part

    return components


def is_landmark_case(citation_text):
    """Check if a citation refers to a landmark case."""
    return citation_text in LANDMARK_CASES


@app.route("/")
def index():
    return render_template("enhanced_validator.html")


@app.route("/enhanced-validator")
def enhanced_validator():
    return render_template("enhanced_validator.html")


@app.route("/casestrainer/enhanced-validator")
def casestrainer_enhanced_validator():
    return render_template("enhanced_validator.html")


@app.route("/casestrainer/api/enhanced-validate-citation", methods=["POST"])
def validate_citation():
    data = request.json
    citation = data.get("citation", "")

    # Simple validation logic
    is_valid = is_landmark_case(citation)

    result = {
        "citation": citation,
        "verified": is_valid,
        "verified_by": "Enhanced Validator" if is_valid else None,
        "components": parse_citation_components(citation) if is_valid else None,
        "error": None if is_valid else "Citation not found in landmark cases database",
    }

    return jsonify(result)


@app.route("/casestrainer/api/citation-context", methods=["POST"])
def get_citation_context():
    data = request.json
    citation = data.get("citation", "")

    context = CITATION_CONTEXTS.get(citation, f"No context available for {citation}")

    result = {
        "citation": citation,
        "context": context,
        "file_link": (
            f"https://www.courtlistener.com/opinion/search/?q={citation.replace(' ', '+')}"
            if is_landmark_case(citation)
            else None
        ),
    }

    return jsonify(result)


@app.route("/casestrainer/api/classify-citation", methods=["POST"])
def classify_citation():
    data = request.json
    citation = data.get("citation", "")

    # Simple classification logic
    is_landmark = is_landmark_case(citation)
    confidence = 0.95 if is_landmark else 0.3 + random.random() * 0.3

    explanations = []
    if is_landmark:
        explanations.append(f"Citation format is valid: {citation}")
        explanations.append(
            f"Citation refers to a landmark case: {LANDMARK_CASES.get(citation, '')}"
        )
        explanations.append("Citation appears in verified database")
    else:
        explanations.append(f"Citation format appears unusual: {citation}")
        explanations.append("Citation not found in landmark cases database")

    result = {
        "citation": citation,
        "confidence": confidence,
        "explanation": explanations,
    }

    return jsonify(result)


@app.route("/casestrainer/api/suggest-citation-corrections", methods=["POST"])
def suggest_corrections():
    data = request.json
    citation = data.get("citation", "")

    # Simple correction logic
    suggestions = []

    # Check if it's close to a landmark case
    for landmark in LANDMARK_CASES.keys():
        # Simple string similarity check
        if citation.split()[0] == landmark.split()[0] and citation != landmark:
            suggestions.append(
                {
                    "corrected_citation": landmark,
                    "similarity": 0.8,
                    "explanation": f"Did you mean {landmark} ({LANDMARK_CASES[landmark]})?",
                    "correction_type": "Reporter Correction",
                }
            )
        elif citation.split()[1] == landmark.split()[1] and citation != landmark:
            suggestions.append(
                {
                    "corrected_citation": landmark,
                    "similarity": 0.7,
                    "explanation": f"Did you mean {landmark} ({LANDMARK_CASES[landmark]})?",
                    "correction_type": "Volume Correction",
                }
            )

    result = {"citation": citation, "suggestions": suggestions}

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
