#!/usr/bin/env python3
"""
Test the vue_api_endpoints directly
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_vue_api_directly():
    # Import the vue_api_endpoints module
    from src.vue_api_endpoints import vue_api

    print("Vue API endpoints imported successfully")

    # Test the analyze endpoint function directly
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(vue_api, url_prefix='/casestrainer/api')

    # Create a test client
    client = app.test_client()

    # Test data
    test_data = {
        "type": "text",
        "text": """Five Corners Fam. Farmers v. State, 173 Wn.2d
296, 306, 268 P.3d 892 (2011) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150
Wn.2d 674, 682, 80 P.3d 598 (2003)); Bostain v. Food Express, Inc., 159 Wn.2d
700, 716, 153 P.3d 846 (2007) (collecting cases)."""
    }

    print("Testing analyze endpoint with test client...")
    response = client.post('/casestrainer/api/analyze',
                          json=test_data,
                          content_type='application/json')

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.get_json()
        print(f"Success: {result.get('success')}")
        print(f"Citations found: {len(result.get('citations', []))}")
        print(f"Clusters found: {len(result.get('clusters', []))}")
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.get_data(as_text=True))
        return None

if __name__ == "__main__":
    test_vue_api_directly()
