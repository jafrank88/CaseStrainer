#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Enhanced Citation Validator

This module provides a simplified version of the Enhanced Citation Validator
that doesn't require the problematic modules.
"""

import os
import sys
import json
import random
import re
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
    "576 U.S. 644": "Obergefell v. Hodges"
}

# Sample citation contexts
CITATION_CONTEXTS = {
    "410 U.S. 113": "The Court held in Roe v. Wade, 410 U.S. 113 (1973), that a woman's right to an abortion was protected by the right to privacy under the Fourteenth Amendment.",
    "347 U.S. 483": "In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court unanimously ruled that racial segregation in public schools was unconstitutional.",
    "5 U.S. 137": "Marbury v. Madison, 5 U.S. 137 (1803), established the principle of judicial review in the United States, giving the Supreme Court the power to invalidate acts of Congress that conflict with the Constitution.",
    "531 U.S. 98": "The Supreme Court's decision in Bush v. Gore, 531 U.S. 98 (2000), effectively resolved the 2000 presidential election in favor of George W. Bush.",
    "384 U.S. 436": "Miranda v. Arizona, 384 U.S. 436 (1966), established that prior to police interrogation, a person must be informed of their right to consult with an attorney and of their right against self-incrimination."
}

def parse_citation_components(citation_text):
    """Parse a citation into its component parts."""
    """
    components = {}
    
    # Common patterns for different citation formats
    # U.S. Reports pattern: <volume> U.S. <page>
    us_pattern = r'(\d+)\s+U\.?S\.?\s+(\d+)'
    # Federal Reporter pattern: <volume> F.<edition> <page>
    f_pattern = r'(\d+)\s+F\.?(\d*)\.?\s+(\d+)'
    # State reporter pattern: <volume> <state> <page>
    state_pattern = r'(\d+)\s+([A-Za-z\.]+)\s+(\d+)'
    # Year pattern: (YYYY)
    year_pattern = r'\((\d{4})\)'
    
    # Try to extract volume, reporter, and page
    us_match = re.search(us_pattern, citation_text)
    if us_match:
        components['volume'] = us_match.group(1)
        components['reporter'] = 'U.S.'
        components['page'] = us_match.group(2)
        components['court'] = 'Supreme Court of the United States'
    else:
        f_match = re.search(f_pattern, citation_text)
        if f_match:
            components['volume'] = f_match.group(1)
            edition = f_match.group(2)
            if edition:
                components['reporter'] = f'F.{edition}d'
            else:
                components['reporter'] = 'F.'
            components['page'] = f_match.group(3)
            components['court'] = 'Federal Court'
        else:
            state_match = re.search(state_pattern, citation_text)
            if state_match:
                components['volume'] = state_match.group(1)
                components['reporter'] = state_match.group(2)
                components['page'] = state_match.group(3)
                # Try to determine court from reporter
                state_abbr = components['reporter'].split('.')[0]
                components['court'] = f'{state_abbr} Court'
    
    # Try to extract year
    year_match = re.search(year_pattern, citation_text)
    if year_match:
        components['year'] = year_match.group(1)
    
    return components

# Function to check if a citation is a landmark case
def is_landmark_case(citation_text):
    """
    Check if a citation refers to a landmark case.
    """
    # Define some landmark cases
    landmark_cases = {
        "347 U.S. 483": {
            "name": "Brown v. Board of Education",
            "year": "1954",
            "description": "Landmark civil rights case that declared segregation in public schools unconstitutional",
            "url": "https://supreme.justia.com/cases/federal/us/347/483/"
        },
        "410 U.S. 113": {
            "name": "Roe v. Wade",
            "year": "1973",
            "description": "Landmark case establishing the right to abortion",
            "url": "https://supreme.justia.com/cases/federal/us/410/113/"
        },
        "5 U.S. 137": {
            "name": "Marbury v. Madison",
            "year": "1803",
            "description": "Established the principle of judicial review",
            "url": "https://supreme.justia.com/cases/federal/us/5/137/"
        },
        "384 U.S. 436": {
            "name": "Miranda v. Arizona",
            "year": "1966",
            "description": "Established the Miranda rights for criminal suspects",
            "url": "https://supreme.justia.com/cases/federal/us/384/436/"
        },
        "551 F.3d 1315": {
            "name": "Wyeth v. Kappos",
            "year": "2010",
            "description": "Important patent law case regarding term adjustments",
            "url": "https://casetext.com/case/wyeth-v-kappos"
        }
    }
    
    # Normalize citation
    citation_text = re.sub(r'\s+', ' ', citation_text.strip())
    
    # Check if citation is in landmark cases
    if citation_text in landmark_cases:
        return landmark_cases[citation_text]
    
    return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/enhanced-validator')
def enhanced_validator():
    """
    Display the Enhanced Citation Validator page.
    This provides a comprehensive interface for validating citations with multiple sources,
    displaying detailed citation information, and suggesting corrections.
    """
    return render_template('enhanced_validator.html')

@app.route('/api/enhanced-validate-citation', methods=['POST'])
def api_enhanced_validate_citation():
    """
    API endpoint to validate a citation with enhanced information.
    """
    try:
        data = request.get_json()
        citation = data.get('citation')
        
        if not citation:
            return jsonify({'error': 'Citation is required'}), 400
        
        # Initialize result with basic structure
        result = {
            'citation': citation,
            'verified': False,
            'components': {}
        }
        
        # Try to parse citation components
        components = parse_citation_components(citation)
        if components:
            result['components'] = components
        
        # Check if it's a landmark case
        landmark_info = is_landmark_case(citation)
        if landmark_info:
            result.update({
                'verified': True,
                'verified_by': 'Landmark Cases Database',
                'confidence': 0.95,
                'case_name': landmark_info['name'],
                'url': landmark_info['url']
            })
            return jsonify(result)
        
        # Check database for the citation
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM citations WHERE citation_text = ?', (citation,))
        citation_data = cursor.fetchone()
        conn.close()
        
        if citation_data:
            result.update({
                'verified': citation_data['found'] == 1,
                'verified_by': citation_data['source'] if citation_data['found'] == 1 else None,
                'confidence': 0.9 if citation_data['found'] == 1 else 0.1,
                'case_name': citation_data['case_name']
            })
        
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Error validating citation: {str(e)}'}), 500

@app.route('/api/citation-context', methods=['POST'])
def api_citation_context():
    """
    API endpoint to get the context surrounding a citation.
    """
    try:
        data = request.get_json()
        citation = data.get('citation')
        
        if not citation:
            return jsonify({'error': 'Citation is required'}), 400
        
        # Get citation from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM citations WHERE citation_text = ?', (citation,))
        citation_data = cursor.fetchone()
        conn.close()
        
        result = {
            'citation': citation,
            'context': None,
            'file_link': None
        }
        
        if citation_data:
            # Get context if available
            if 'context' in citation_data.keys() and citation_data['context']:
                result['context'] = citation_data['context']
            else:
                # If no context in database, provide a sample context
                landmark_info = is_landmark_case(citation)
                if landmark_info:
                    result['context'] = f"As the Court held in {landmark_info['name']}, {citation}, {landmark_info['description']}."
            
            # Get file link if available
            if 'file_path' in citation_data.keys() and citation_data['file_path']:
                file_path = citation_data['file_path']
                if os.path.exists(file_path):
                    # Create a relative URL to the file
                    file_name = os.path.basename(file_path)
                    result['file_link'] = f'/casestrainer/downloaded_briefs/{file_name}'
        
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Error getting citation context: {str(e)}'}), 500

@app.route('/api/suggest-citation-corrections', methods=['POST'])
def api_suggest_citation_corrections():
    """
    API endpoint to suggest corrections for a potentially invalid citation.
    """
    try:
        data = request.get_json()
        citation = data.get('citation')
        
        if not citation:
            return jsonify({'error': 'Citation is required'}), 400
        
        # Simple correction suggestions based on common patterns
        suggestions = []
        
        # Check for missing periods in "U.S."
        if "US " in citation:
            corrected = citation.replace("US ", "U.S. ")
            suggestions.append({
                'corrected_citation': corrected,
                'similarity': 0.9,
                'explanation': 'Added periods to "U.S." abbreviation',
                'correction_type': 'Format correction'
            })
        
        # Check for landmark cases with similar citations
        for landmark_citation, info in {
            "347 U.S. 483": {"name": "Brown v. Board of Education"},
            "410 U.S. 113": {"name": "Roe v. Wade"},
            "5 U.S. 137": {"name": "Marbury v. Madison"},
            "384 U.S. 436": {"name": "Miranda v. Arizona"}
        }.items():
            # Simple similarity check
            if landmark_citation[0:3] == citation[0:3]:
                suggestions.append({
                    'corrected_citation': landmark_citation,
                    'similarity': 0.7,
                    'explanation': f'Similar to landmark case: {info["name"]}',
                    'correction_type': 'Landmark case suggestion'
                })
        
        return jsonify({
            'citation': citation,
            'suggestions': suggestions
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Error suggesting corrections: {str(e)}'}), 500

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
