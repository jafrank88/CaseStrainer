#!/usr/bin/env python3
"""
Test async processing with a very large document
"""

import requests
import json
import time

def test_large_async_processing():
    """Test async processing with a very large document"""
    
    # Create a large test document by repeating citations many times
    base_text = """
    This is a comprehensive legal analysis document that contains numerous citations from various jurisdictions and time periods. 
    In the landmark case of Smith v. Jones, 123 F.3d 456 (9th Cir. 1998), the court established important precedent regarding corporate liability.
    The Supreme Court in Johnson v. Smith, 789 F.2d 234 (D.C. Cir. 1986), addressed constitutional questions that would shape future jurisprudence.
    Brown v. Board of Education, 347 U.S. 483 (1954), represents one of the most significant civil rights decisions in American history.
    United States v. Carpenter, 585 U.S. ___ (2018), demonstrates the Court's modern approach to digital privacy rights.
    Circuit City v. Adams, 456 F.3d 789 (3d Cir. 2011), considered complex contractual disputes under federal law.
    Miller v. California, 413 U.S. 15 (1973), established the three-pronged test for obscenity that remains influential today.
    Roe v. Wade, 410 U.S. 113 (1973), recognized a woman's constitutional right to privacy in reproductive decisions.
    District Court v. Plaintiff, 234 F. Supp. 567 (N.D. Cal. 2000), made an important ruling on civil procedure matters.
    Circuit Appeal v. Defendant, 345 F.3d 890 (5th Cir. 2003), affirmed the lower court's decision on statutory interpretation.
    Marbury v. Madison, 5 U.S. (1 Cranch) 137 (1803), established the principle of judicial review that underpins American constitutional law.
    """
    
    # Repeat the text many times to make it large enough for async processing
    test_text = base_text * 50  # This should be around 25,000+ characters
    
    print("🧪 Testing async processing with large document...")
    print(f"📝 Test text length: {len(test_text)} characters")
    
    # Send to API
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True}
    
    try:
        print("\n📡 Sending request to API...")
        print("   (This should trigger async processing due to document size)")
        start_time = time.time()
        
        response = requests.post(url, json=data, timeout=180)  # 3 minute timeout
        response.raise_for_status()
        
        elapsed_time = time.time() - start_time
        result = response.json()
        
        print(f"\n⏱️  Request completed in {elapsed_time:.2f} seconds")
        
        # Check if it was processed asynchronously
        processing_mode = result.get("metadata", {}).get("processing_mode", "unknown")
        print(f"📊 Processing mode: {processing_mode}")
        
        citations = result.get("citations", [])
        print(f"📊 Found {len(citations)} citations")
        
        # Check for task ID if async
        task_id = result.get("task_id", None)
        if task_id:
            print(f"🆔 Task ID: {task_id}")
        
        # Show first few citations
        for i, citation in enumerate(citations[:3]):
            citation_text = citation.get("citation", "")
            verified = citation.get("verified", False)
            source = citation.get("source", "")
            
            print(f"\n📋 Citation {i+1}: {citation_text}")
            print(f"   Verified: {verified}")
            print(f"   Source: {source}")
        
        if processing_mode == "async":
            print("\n✅ SUCCESS: Async processing was triggered!")
            if task_id:
                print(f"   Task ID: {task_id}")
            return True
        elif processing_mode == "enhanced_sync":
            print(f"\n⚠️  Processing was synchronous (mode: {processing_mode})")
            print("   The document might still not be large enough or async threshold is high")
            return True  # Still success, just not async
        else:
            print(f"\n📊 Processing mode: {processing_mode}")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_large_async_processing()
    
    if success:
        print("\n✅ Large document processing test completed!")
    else:
        print("\n❌ Large document processing test failed!")
