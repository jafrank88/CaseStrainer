import os
import json
import time
import uuid
import threading
from flask import Flask, request, jsonify, render_template, send_from_directory
from pathlib import Path

# Create Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global storage for analysis results
analysis_results = {}


# Function to generate a unique analysis ID
def generate_analysis_id():
    return str(uuid.uuid4())


# Function to run the analysis in a background thread
def run_analysis(analysis_id, text):
    print(f"Starting analysis for ID: {analysis_id}")

    try:
        # Initialize the results for this analysis
        analysis_results[analysis_id] = {
            "status": "running",
            "events": [],
            "completed": False,
        }

        # Add initial event
        analysis_results[analysis_id]["events"].append(
            {"status": "started", "total_citations": 1}
        )

        print(f"Analysis {analysis_id}: Started processing")

        # Simulate processing time
        time.sleep(2)

        # Add progress event
        analysis_results[analysis_id]["events"].append(
            {
                "status": "progress",
                "current": 1,
                "total": 1,
                "message": "Checking citation...",
            }
        )

        print(f"Analysis {analysis_id}: Progress update")

        # Simulate processing time
        time.sleep(2)

        # Add result event
        result = {
            "citation_text": text,
            "is_hallucinated": False,
            "confidence": 0.85,
            "context": "This is a test citation.",
            "explanation": "This citation was found in the database.",
        }

        analysis_results[analysis_id]["events"].append(
            {"status": "result", "citation_index": 0, "result": result, "total": 1}
        )

        print(f"Analysis {analysis_id}: Added result")

        # Simulate processing time
        time.sleep(2)

        # Add completion event
        analysis_results[analysis_id]["events"].append(
            {"status": "complete", "total_citations": 1, "hallucinated_citations": 0}
        )

        # Mark as completed
        analysis_results[analysis_id]["status"] = "complete"
        analysis_results[analysis_id]["completed"] = True

        print(f"Analysis {analysis_id}: Completed")

        # Clean up old analyses after some time
        threading.Timer(300, lambda: analysis_results.pop(analysis_id, None)).start()

    except Exception as e:
        print(f"Error in analysis {analysis_id}: {str(e)}")
        # If there's an error, mark the analysis as failed
        if analysis_id in analysis_results:
            analysis_results[analysis_id]["status"] = "error"
            analysis_results[analysis_id]["error"] = str(e)
            analysis_results[analysis_id]["completed"] = True


# Configure static folder for serving static files
@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)


# Route for the home page
@app.route("/")
def index():
    return render_template("simple.html")


# Route to start an analysis
@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    print("==== ANALYZE ENDPOINT CALLED =====")
    print(f"Request method: {request.method}")

    if request.method == "POST":
        print("POST request detected - starting analysis")

        try:
            # Get the text from the form data
            text = request.form.get("text", "")
            print(f"Received text: {text}")

            if not text:
                print("No text provided")
                return jsonify({"status": "error", "message": "No text provided"}), 400

            # Generate a unique ID for this analysis
            analysis_id = generate_analysis_id()
            print(f"Generated analysis ID: {analysis_id}")

            # Start the analysis in a background thread
            threading.Thread(target=run_analysis, args=(analysis_id, text)).start()

            # Return the analysis ID to the client
            return jsonify(
                {
                    "status": "success",
                    "message": "Analysis started",
                    "analysis_id": analysis_id,
                }
            )

        except Exception as e:
            print(f"Error starting analysis: {str(e)}")
            return (
                jsonify(
                    {"status": "error", "message": f"Error starting analysis: {str(e)}"}
                ),
                500,
            )

    else:
        print("GET request - returning empty response")
        return jsonify({})


# Route to check the status of an analysis
@app.route("/analyze_status")
def analyze_status():
    print("==== ANALYZE_STATUS ENDPOINT CALLED =====")
    print(f"Request args: {request.args}")

    try:
        # Get the analysis ID from the query parameters
        analysis_id = request.args.get("id")
        print(f"Checking status for analysis ID: {analysis_id}")

        if not analysis_id:
            print("No analysis ID provided")
            return (
                jsonify({"status": "error", "message": "No analysis ID provided"}),
                400,
            )

        # Check if the analysis exists
        if analysis_id not in analysis_results:
            print(f"Analysis ID not found: {analysis_id}")
            return jsonify({"status": "error", "message": "Analysis not found"}), 404

        # Return the current status and events
        result = {
            "status": analysis_results[analysis_id]["status"],
            "events": analysis_results[analysis_id]["events"],
            "completed": analysis_results[analysis_id]["completed"],
        }

        print(f"Returning status for analysis {analysis_id}: {result['status']}")
        return jsonify(result)

    except Exception as e:
        print(f"Error checking analysis status: {str(e)}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error checking analysis status: {str(e)}",
                }
            ),
            500,
        )


if __name__ == "__main__":
    print("Starting Simple CaseStrainer application")
    app.run(host="0.0.0.0", port=5001, debug=True)
