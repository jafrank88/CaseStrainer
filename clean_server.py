#!/usr/bin/env python3
"""
Clean CaseStrainer server that processes citations directly without worker threads
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import citation processing modules
try:
    from src.citation_extractor import CitationExtractor
    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
    from src.database_manager import DatabaseManager
    print("✅ Successfully imported citation processing modules")
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)

app = Flask(__name__)

# Initialize components
print("🔧 Initializing components...")
citation_extractor = CitationExtractor()
verifier = EnhancedMultiSourceVerifier()
db_path = os.path.join(os.path.dirname(__file__), 'data', 'citations.db')
db_manager = DatabaseManager(db_path)

print("✅ All components initialized successfully")

@app.route('/casestrainer/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "CaseStrainer Clean API",
        "version": "0.5.8",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "production",
        "database": "ok",
        "redis": "disabled",
        "rq_worker": "disabled"
    })

@app.route('/casestrainer/api/analyze', methods=['POST'])
def analyze_document():
    """Analyze document for citations - direct processing without queues"""
    try:
        print(f"📄 [ANALYZE] Received request at {datetime.now()}")
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        text = data.get('text', '')
        source = data.get('source', 'Unknown')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        print(f"📄 [ANALYZE] Processing text ({len(text)} characters) from source: {source}")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        print(f"🆔 [ANALYZE] Generated task ID: {task_id}")
        
        # Extract citations directly
        print("🔍 [ANALYZE] Extracting citations...")
        start_time = time.time()
        
        citations = citation_extractor.extract_citations(text)
        extraction_time = time.time() - start_time
        
        print(f"✅ [ANALYZE] Extracted {len(citations)} citations in {extraction_time:.2f}s")
        
        # Verify citations directly
        print("🔍 [ANALYZE] Verifying citations...")
        verification_start = time.time()
        
        verified_citations = []
        for i, citation in enumerate(citations):
            print(f"🔍 [ANALYZE] Verifying citation {i+1}/{len(citations)}: {citation.get('citation', 'Unknown')}")
            
            try:
                # Use the correct verification method
                verification_result = verifier.verify_citation_unified_workflow(citation)
                citation.update(verification_result)
                verified_citations.append(citation)
                
                print(f"✅ [ANALYZE] Citation {i+1} verified: {verification_result.get('verified', False)}")
                
            except Exception as e:
                print(f"❌ [ANALYZE] Error verifying citation {i+1}: {e}")
                citation['verified'] = False
                citation['error'] = str(e)
                verified_citations.append(citation)
        
        verification_time = time.time() - verification_start
        total_time = time.time() - start_time
        
        print(f"✅ [ANALYZE] Verification completed in {verification_time:.2f}s")
        print(f"✅ [ANALYZE] Total processing time: {total_time:.2f}s")
        
        # Count verified citations
        verified_count = sum(1 for c in verified_citations if c.get('verified', False))
        
        # Prepare response
        response = {
            "task_id": task_id,
            "status": "completed",
            "citations": verified_citations,
            "total_citations": len(verified_citations),
            "verified_citations": verified_count,
            "processing_time": total_time,
            "source": source,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"✅ [ANALYZE] Returning response with {len(verified_citations)} citations")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ [ANALYZE] Error processing request: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}",
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/casestrainer/api/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Task status endpoint (always returns completed for direct processing)"""
    return jsonify({
        "task_id": task_id,
        "status": "completed",
        "message": "Direct processing completed"
    })

@app.route('/casestrainer/api/version', methods=['GET'])
def version():
    """Version endpoint"""
    return jsonify({
        "version": "0.5.8",
        "build": "clean-server",
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Clean CaseStrainer Server...")
    print("=" * 60)
    print("✅ No worker threads")
    print("✅ No queues")
    print("✅ Direct processing")
    print("✅ Fast responses")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    ) 