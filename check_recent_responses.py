#!/usr/bin/env python3
"""
Script to check the most recent JSON responses from the logs
to see if the backend is now delivering case/citation information.
"""

import re
import json
import os
from datetime import datetime
import ast

def extract_recent_responses(log_file_path, max_entries=5):
    """Extract the most recent JSON responses from the log file."""
    
    if not os.path.exists(log_file_path):
        print(f"Log file not found: {log_file_path}")
        return []
    
    responses = []
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(log_file_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading log file: {e}")
            return []

    # Go forward through the log to collect multi-line JSON/dict blocks
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if '[ANALYZE] Response to frontend:' in line:
            # Start collecting lines for this response
            json_lines = []
            # Find the first '{'
            json_start = line.find('{')
            if json_start != -1:
                json_lines.append(line[json_start:].rstrip())
            i += 1
            # Collect until next timestamped log entry or end of file
            while i < n and not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \|', lines[i]):
                json_lines.append(lines[i].rstrip())
                i += 1
            json_str = '\n'.join(json_lines)
            # Try to parse as JSON, then as Python dict
            try:
                response_data = json.loads(json_str)
                responses.append({
                    'timestamp': line.split('|')[0].strip(),
                    'data': response_data
                })
            except Exception as e:
                try:
                    response_data = ast.literal_eval(json_str)
                    responses.append({
                        'timestamp': line.split('|')[0].strip(),
                        'data': response_data
                    })
                except Exception as e2:
                    print(f"Could not parse multi-line JSON or Python dict: {e2}\nFirst 100 chars: {json_str[:100]}...")
            if len(responses) >= max_entries:
                break
        else:
            i += 1
    return responses

def analyze_responses(responses):
    """Analyze the responses to see if they contain citation data."""
    
    print(f"Analyzing {len(responses)} recent responses:\n")
    
    for i, response in enumerate(responses, 1):
        print(f"=== Response {i} ({response['timestamp']}) ===")
        
        data = response['data']
        
        # Check for key fields
        status = data.get('status', 'unknown')
        results = data.get('results', [])
        citations = data.get('citations', [])
        
        print(f"Status: {status}")
        print(f"Results count: {len(results)}")
        print(f"Citations count: {len(citations)}")
        
        # Check if we have actual citation data
        if results:
            print("✅ RESULTS FOUND!")
            print(f"First result keys: {list(results[0].keys()) if results else 'N/A'}")
            if results and 'citation' in results[0]:
                print(f"Sample citation: {results[0]['citation']}")
        elif citations:
            print("✅ CITATIONS FOUND!")
            print(f"First citation keys: {list(citations[0].keys()) if citations else 'N/A'}")
            if citations and 'citation' in citations[0]:
                print(f"Sample citation: {citations[0]['citation']}")
        else:
            print("❌ NO RESULTS OR CITATIONS FOUND")
        
        # Show other important fields
        if 'current_step' in data:
            print(f"Current step: {data['current_step']}")
        if 'progress' in data:
            print(f"Progress: {data['progress']}%")
        if 'elapsed_time' in data:
            print(f"Elapsed time: {data['elapsed_time']}s")
        
        print()

def main():
    """Main function to check recent responses."""
    
    log_file = "logs/casestrainer.log"
    
    print("Checking recent JSON responses from the backend...")
    print(f"Log file: {log_file}")
    print("=" * 60)
    
    responses = extract_recent_responses(log_file, max_entries=5)
    
    if not responses:
        print("No recent responses found in the log file.")
        return
    
    analyze_responses(responses)
    
    # Summary
    print("=" * 60)
    print("SUMMARY:")
    
    total_responses = len(responses)
    responses_with_data = sum(1 for r in responses if r['data'].get('results') or r['data'].get('citations'))
    
    print(f"Total responses analyzed: {total_responses}")
    print(f"Responses with citation data: {responses_with_data}")
    print(f"Success rate: {responses_with_data/total_responses*100:.1f}%")
    
    if responses_with_data > 0:
        print("✅ The fix appears to be working - citation data is being delivered!")
    else:
        print("❌ The fix may not be working - no citation data found in recent responses.")

if __name__ == "__main__":
    main() 