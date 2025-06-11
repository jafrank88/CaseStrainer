"""
Test script for the Enhanced Validator functionality
"""

import os
import sys
import json
import logging
from flask import Flask, jsonify
from werkzeug.serving import run_simple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import required modules from src
from src.citation_api import USE_ENHANCED_VALIDATOR
from src.app_final_vue import extract_citations_from_text, verify_citation

# Print the status of the Enhanced Validator
print(f"\n=== ENHANCED VALIDATOR STATUS ===\nEnabled: {USE_ENHANCED_VALIDATOR}\n")

# Create a simple Flask application for testing
app = Flask(__name__)

# Try to import and register the enhanced validator module directly
try:
    from src.enhanced_validator_production import (
        register_enhanced_validator,
    )

    print("Successfully imported enhanced_validator_production module")
    # Register the enhanced validator with the app
    app = register_enhanced_validator(app)
    # The blueprint is now registered inside register_enhanced_validator
    print("Successfully registered Enhanced Validator with the app")
except Exception as e:
    print(f"Error importing/registering Enhanced Validator: {e}")

# Sample citation text for testing
SAMPLE_TEXT = """
In Miranda v. Arizona, 384 U.S. 436 (1966), the Supreme Court held that 
the Fifth Amendment requires law enforcement officials to advise suspects 
of their right to remain silent and to obtain an attorney during interrogations 
while in police custody.

The Court later clarified this ruling in Edwards v. Arizona, 451 U.S. 477 (1981),
and in Berghuis v. Thompkins, 560 U.S. 370 (2010).

Some citations might be invalid, like Smith v. Jones, 123 F.3d 456 (2025).
"""


@app.route("/test-enhanced-validator")
def test_enhanced_validator():
    """Test the enhanced validator functionality"""
    try:
        # Check if Enhanced Validator is enabled
        logger.info(f"Enhanced Validator enabled: {USE_ENHANCED_VALIDATOR}")
        logger.info("Processing sample text with citations")

        # Print the sample text for debugging
        print(f"Sample text: {SAMPLE_TEXT[:100]}...")

        # Extract citations from text
        try:
            citations = extract_citations_from_text(SAMPLE_TEXT)
            logger.info(f"Extracted {len(citations)} citations")
            print(f"Extracted citations: {citations}")
        except Exception as e:
            logger.error(f"Error extracting citations: {str(e)}")
            return jsonify({"error": f"Citation extraction error: {str(e)}"}), 500

        # Verify each citation
        verified_citations = []
        for citation in citations:
            try:
                citation_text = citation.get("citation", "")
                context = citation.get("context", "")
                logger.info(f"Verifying citation: {citation_text}")

                verified = verify_citation(citation_text, context)
                verified_citations.append(verified)

                logger.info(f"Verification result: {verified.get('valid', False)}")
            except Exception as e:
                logger.error(
                    f"Error verifying citation {citation.get('citation', '')}: {str(e)}"
                )
                # Add the citation with an error flag
                verified_citations.append(
                    {
                        "citation": citation.get("citation", ""),
                        "valid": False,
                        "error": str(e),
                        "source": "error",
                    }
                )

        # Format the results
        results = []
        for citation in verified_citations:
            result = {
                "citation": citation.get("citation", ""),
                "valid": citation.get("valid", False),
                "source": citation.get("source", "unknown"),
                "verification_method": citation.get("verification_method", "unknown"),
                "case_name": citation.get("case_name", ""),
                "court": citation.get("court", ""),
                "year": citation.get("year", ""),
                "details": citation.get("details", {}),
            }
            results.append(result)

        # Return the results as JSON
        response_data = {
            "enhanced_validator_enabled": USE_ENHANCED_VALIDATOR,
            "citations_count": len(results),
            "citations": results,
        }

        print(f"Response data: {json.dumps(response_data, indent=2)}")
        return jsonify(response_data)

    except Exception as e:
        logger.exception(f"Error testing enhanced validator: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    """Display a simple HTML page with a link to test the enhanced validator"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced Validator Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #333; }
            .container { max-width: 800px; margin: 0 auto; }
            .btn { display: inline-block; background: #4CAF50; color: white; padding: 10px 20px; 
                   text-decoration: none; border-radius: 4px; font-weight: bold; }
            .btn:hover { background: #45a049; }
            pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
            #results { margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Enhanced Validator Test</h1>
            <p>This page tests the Enhanced Validator functionality in CaseStrainer.</p>
            
            <a href="/test-enhanced-validator" class="btn" id="testBtn">Test Enhanced Validator</a>
            
            <div id="results"></div>
            
            <script>
                document.getElementById('testBtn').addEventListener('click', function(e) {
                    e.preventDefault();
                    
                    document.getElementById('results').innerHTML = '<p>Loading results...</p>';
                    
                    fetch('/test-enhanced-validator')
                        .then(response => response.json())
                        .then(data => {
                            let html = '<h2>Test Results</h2>';
                            html += `<p><strong>Enhanced Validator Enabled:</strong> ${data.enhanced_validator_enabled}</p>`;
                            html += `<p><strong>Citations Found:</strong> ${data.citations_count}</p>`;
                            
                            html += '<h3>Citations:</h3>';
                            html += '<pre>' + JSON.stringify(data.citations, null, 2) + '</pre>';
                            
                            document.getElementById('results').innerHTML = html;
                        })
                        .catch(error => {
                            document.getElementById('results').innerHTML = 
                                `<p>Error: ${error.message}</p>`;
                        });
                });
            </script>
        </div>
    </body>
    </html>
    """


class TestEnhancedValidator(unittest.TestCase):
    def test_extract_citations(self):
        # Test extracting citations from sample text
        citations = extract_citations_from_text(SAMPLE_TEXT)
        self.assertGreater(len(citations), 0)

    def test_verify_citation(self):
        # Test verifying a single citation
        citation_text = "Miranda v. Arizona, 384 U.S. 436 (1966)"
        context = ""
        verified = verify_citation(citation_text, context)
        self.assertTrue(verified.get("valid", False))

    def test_batch_processing(self):
        # Test batch processing of multiple citations
        citations = extract_citations_from_text(SAMPLE_TEXT)
        verified_citations = []
        for citation in citations:
            citation_text = citation.get("citation", "")
            context = citation.get("context", "")
            verified = verify_citation(citation_text, context)
            verified_citations.append(verified)
        self.assertGreater(len(verified_citations), 0)

    def test_error_handling(self):
        # Test error handling for invalid citations
        citation_text = "Invalid Citation"
        context = ""
        verified = verify_citation(citation_text, context)
        self.assertFalse(verified.get("valid", True))
        self.assertIn("error", verified)

    def test_different_citation_types(self):
        # Test different citation types (e.g., Supreme Court, Circuit Court)
        citations = [
            "Miranda v. Arizona, 384 U.S. 436 (1966)",  # Supreme Court
            "United States v. Jones, 565 U.S. 400 (2012)",  # Supreme Court
            "Smith v. Jones, 123 F.3d 456 (2025)",  # Circuit Court
        ]
        for citation in citations:
            verified = verify_citation(citation, "")
            self.assertTrue(verified.get("valid", False))


def run_tests():
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedValidator)
    test_results = unittest.TextTestRunner().run(test_suite)
    return {
        "tests_run": test_results.testsRun,
        "failures": len(test_results.failures),
        "errors": len(test_results.errors),
        "skipped": len(test_results.skipped),
        "was_successful": test_results.wasSuccessful(),
        "test_cases": [
            {
                "name": test.id(),
                "success": test.success,
            }
            for test in test_results.testsRun
        ],
    }


if __name__ == "__main__":
    # Run tests directly
    print("Running Enhanced Validator Tests...\n" + "=" * 50 + "\n")

    # Run tests and get results
    test_results = run_tests()

    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests Run: {test_results['tests_run']}")
    print(f"Failures: {test_results['failures']}")
    print(f"Errors: {test_results['errors']}")
    print(f"Skipped: {test_results['skipped']}")
    print(f"\nOverall: {'SUCCESS' if test_results['was_successful'] else 'FAILED'}")

    # Print detailed results
    if not test_results["was_successful"]:
        print("\nFailed/Error Tests:")
        for test in test_results["test_cases"]:
            if not test["success"]:
                print(f"- {test['name']}")

    print("\n" + "=" * 50 + "\n")

    # Run the application on port 5000
    print("Starting Enhanced Validator Test Server...")
    print("Open http://127.0.0.1:5000 in your browser to test the Enhanced Validator")
    run_simple("0.0.0.0", 5000, app, use_reloader=True, use_debugger=True)
