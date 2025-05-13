from flask import Flask, request, render_template, jsonify, Response, send_from_directory
import os
import re
import json
import time
import uuid
import sys
import io
import subprocess
import threading
import traceback
from werkzeug.utils import secure_filename
import docx
import requests

# Import eyecite for better citation extraction
from eyecite import get_citations
from eyecite.tokenizers import HyperscanTokenizer, AhocorasickTokenizer

# Import our robust PDF handler
from pdf_handler import extract_text_from_pdf

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
COURTLISTENER_API_URL = 'https://www.courtlistener.com/api/rest/v3/citation-lookup/'

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load API keys from config.json if available
DEFAULT_API_KEY = None
LANGSEARCH_API_KEY = None
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        DEFAULT_API_KEY = config.get('courtlistener_api_key')
        LANGSEARCH_API_KEY = config.get('langsearch_api_key')
        print(f"Loaded CourtListener API key from config.json: {DEFAULT_API_KEY[:5]}..." if DEFAULT_API_KEY else "No CourtListener API key found in config.json")
        print(f"Loaded LangSearch API key from config.json: {LANGSEARCH_API_KEY[:5]}..." if LANGSEARCH_API_KEY else "No LangSearch API key found in config.json")
except Exception as e:
    print(f"Error loading config.json: {e}")

# Dictionary to store analysis results
analysis_results = {}

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from different file types
def extract_text_from_file(file_path):
    """Extract text from a file based on its extension."""
    print(f"Extracting text from file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    # Get file extension
    file_extension = file_path.split('.')[-1].lower()
    print(f"File extension: {file_extension}")
    
    try:
        # Extract text based on file extension
        if file_extension == 'txt':
            # For .txt files, just read the content
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                    print(f"Successfully extracted {len(text)} characters from TXT")
                    return text
            except UnicodeDecodeError:
                # Try with a different encoding if utf-8 fails
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read()
                    print(f"Successfully extracted {len(text)} characters from TXT (latin-1 encoding)")
                    return text
        
        elif file_extension == 'pdf':
            # Use our robust PDF handler for all PDF files
            print(f"Using robust PDF handler for: {file_path}")
            text = extract_text_from_pdf(file_path)
            
            # Check if extraction was successful
            if text and isinstance(text, str):
                if text.startswith("Error:"):
                    print(f"PDF extraction failed: {text}")
                    return None
                else:
                    print(f"Successfully extracted {len(text)} characters from PDF")
                    return text
            else:
                print(f"PDF extraction returned invalid result: {type(text)}")
                return None
        
        elif file_extension in ['docx', 'doc']:
            # For .docx files, use python-docx
            try:
                # Check if file exists and is readable
                if not os.path.isfile(file_path):
                    error_msg = f"File not found: {file_path}"
                    print(error_msg)
                    return f"Error: {error_msg}"
                
                # Check file size
                try:
                    file_size = os.path.getsize(file_path)
                    print(f"DOCX file size: {file_size} bytes")
                    if file_size == 0:
                        error_msg = f"File is empty: {file_path}"
                        print(error_msg)
                        return f"Error: {error_msg}"
                    elif file_size > 50 * 1024 * 1024:  # 50MB limit
                        error_msg = f"File is too large ({file_size} bytes): {file_path}"
                        print(error_msg)
                        return f"Error: {error_msg}"
                except Exception as e:
                    print(f"Error checking file size: {e}")
                
                # Open the document
                doc = docx.Document(file_path)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                print(f"Successfully extracted {len(text)} characters from DOCX")
                return text
            except Exception as e:
                print(f"Error extracting text from DOCX: {e}")
                traceback.print_exc()
                return None
        
        else:
            print(f"Unsupported file extension: {file_extension}")
            return None
    
    except Exception as e:
        print(f"Error extracting text from file: {e}")
        traceback.print_exc()
        return None

# Function to extract citations from text
def extract_citations(text):
    """
    Extract legal citations from text using eyecite library.
    This provides more accurate and comprehensive citation extraction than regex patterns.
    """
    print(f"Extracting citations from text of length: {len(text)}")
    citations = []
    
    # Try using eyecite first
    try:
        print("Extracting citations using eyecite...")
        # Try to use the faster HyperscanTokenizer first
        try:
            tokenizer = HyperscanTokenizer()
        except Exception:
            # Fall back to AhocorasickTokenizer if HyperscanTokenizer fails
            print("Falling back to AhocorasickTokenizer...")
            tokenizer = AhocorasickTokenizer()
            
        # Get citations using eyecite
        citation_objects = get_citations(text, tokenizer=tokenizer)
        
        # Extract the citation strings
        for citation in citation_objects:
            citation_str = citation.corrected_citation() if hasattr(citation, 'corrected_citation') else str(citation)
            if citation_str not in citations:
                citations.append(citation_str)
        
        print(f"Found {len(citations)} citations using eyecite")
    except Exception as e:
        print(f"Error using eyecite: {e}")
        traceback.print_exc()
        
        # Fall back to regex patterns if eyecite fails
        print("Falling back to regex patterns...")
        # Normalize the text to make citation matching more reliable
        text = re.sub(r'\s+', ' ', text)
        
        # Example patterns for common citation formats
        patterns = [
            # US Reports (e.g., 347 U.S. 483)
            r'\b\d+\s+U\.?\s*S\.?\s+\d+\b',
            
            # Supreme Court Reporter (e.g., 98 S.Ct. 2733)
            r'\b\d+\s+S\.?\s*Ct\.?\s+\d+\b',
            
            # Federal Reporter (e.g., 410 F.2d 701, 723 F.3d 1067)
            r'\b\d+\s+F\.?\s*(?:2d|3d)?\s+\d+\b',
            
            # Federal Supplement (e.g., 595 F.Supp.2d 735)
            r'\b\d+\s+F\.?\s*Supp\.?\s*(?:2d|3d)?\s+\d+\b',
            
            # Westlaw citations (e.g., 2011 WL 2160468)
            r'\b\d{4}\s+WL\s+\d+\b',
        ]
        
        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    citation = match.group(0).strip()
                    if citation not in citations:
                        citations.append(citation)
            except Exception as e:
                print(f"Error searching for pattern {pattern}: {e}")
    
    print(f"Total citations extracted: {len(citations)}")
    if citations:
        print(f"Extracted citations: {citations}")
        
        # Save the extracted citations to a file for inspection
        try:
            with open('extracted_citations.txt', 'w', encoding='utf-8') as f:
                for i, citation in enumerate(citations):
                    f.write(f"{i+1}. {citation}\n")
            print(f"Extracted citations saved to extracted_citations.txt")
        except Exception as e:
            print(f"Error saving extracted citations to file: {e}")
    
    return citations

# Function to check case using LangSearch API
def check_case_with_langsearch(citation_text):
    """Check if a case is real by asking LangSearch to summarize it twice and comparing the summaries."""
    print(f"Checking case with LangSearch API: {citation_text}")
    
    if not LANGSEARCH_API_KEY:
        print("No LangSearch API key provided")
        return {
            'is_real': False,
            'confidence': 0.5,
            'explanation': "No LangSearch API key provided, unable to verify citation"
        }
    
    try:
        # Prepare the request
        headers = {
            'Authorization': f'Bearer {LANGSEARCH_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # First summary request
        first_prompt = f"Summarize the legal case {citation_text} in 3-5 sentences. Include the main legal issue and holding."
        first_data = {
            'prompt': first_prompt,
            'max_tokens': 300
        }
        
        # Make the first request
        print(f"Requesting first summary for: {citation_text}")
        first_response = requests.post('https://api.langsearch.ai/v1/generate', headers=headers, json=first_data)
        
        # Check the response
        if first_response.status_code != 200:
            print(f"First LangSearch API request failed with status code {first_response.status_code}")
            print(f"Response: {first_response.text}")
            return {
                'is_real': False,
                'confidence': 0.6,
                'explanation': f"Error checking citation: API request failed with status code {first_response.status_code}"
            }
        
        first_result = first_response.json()
        first_summary = first_result.get('text', '')
        print(f"First summary: {first_summary}")
        
        # If the first summary indicates the case doesn't exist
        if 'unable to find' in first_summary.lower() or 'no information' in first_summary.lower() or 'not a valid' in first_summary.lower():
            return {
                'is_real': False,
                'confidence': 0.8,
                'explanation': f"LangSearch could not find information about this citation: {first_summary}"
            }
        
        # Second summary request with different wording
        second_prompt = f"Provide a brief overview of the case {citation_text}. What were the key facts and the court's decision?"
        second_data = {
            'prompt': second_prompt,
            'max_tokens': 300
        }
        
        # Make the second request
        print(f"Requesting second summary for: {citation_text}")
        second_response = requests.post('https://api.langsearch.ai/v1/generate', headers=headers, json=second_data)
        
        # Check the response
        if second_response.status_code != 200:
            print(f"Second LangSearch API request failed with status code {second_response.status_code}")
            print(f"Response: {second_response.text}")
            # If first summary worked but second failed, use just the first
            if first_summary:
                return {
                    'is_real': True,
                    'confidence': 0.7,
                    'explanation': f"Case appears to be real based on first summary: {first_summary}"
                }
            return {
                'is_real': False,
                'confidence': 0.6,
                'explanation': f"Error checking citation: Second API request failed"
            }
        
        second_result = second_response.json()
        second_summary = second_result.get('text', '')
        print(f"Second summary: {second_summary}")
        
        # If the second summary indicates the case doesn't exist
        if 'unable to find' in second_summary.lower() or 'no information' in second_summary.lower() or 'not a valid' in second_summary.lower():
            return {
                'is_real': False,
                'confidence': 0.8,
                'explanation': f"LangSearch could not find information about this citation: {second_summary}"
            }
        
        # Compare the two summaries
        # If both summaries are substantial and have some similarity, the case is likely real
        if len(first_summary) > 50 and len(second_summary) > 50:
            # Very basic similarity check - look for common phrases or words
            first_words = set(first_summary.lower().split())
            second_words = set(second_summary.lower().split())
            common_words = first_words.intersection(second_words)
            similarity_score = len(common_words) / max(len(first_words), len(second_words))
            
            print(f"Similarity score: {similarity_score}")
            
            if similarity_score > 0.3:  # Threshold for similarity
                return {
                    'is_real': True,
                    'confidence': 0.8 + (similarity_score * 0.2),  # Higher similarity = higher confidence
                    'explanation': f"Case appears to be real. LangSearch provided consistent information across two queries.",
                    'summaries': [first_summary, second_summary]
                }
            else:
                return {
                    'is_real': False,
                    'confidence': 0.7,
                    'explanation': f"Case may be hallucinated. LangSearch provided inconsistent information across two queries.",
                    'summaries': [first_summary, second_summary]
                }
        elif len(first_summary) > 50 or len(second_summary) > 50:
            # At least one summary is substantial
            return {
                'is_real': True,
                'confidence': 0.7,
                'explanation': f"Case appears to be real based on LangSearch response, but with limited information.",
                'summaries': [first_summary, second_summary]
            }
        else:
            # Both summaries are too short
            return {
                'is_real': False,
                'confidence': 0.6,
                'explanation': f"LangSearch provided limited information about this citation, suggesting it may be hallucinated.",
                'summaries': [first_summary, second_summary]
            }
    
    except Exception as e:
        print(f"Error checking case with LangSearch API: {e}")
        traceback.print_exc()
        return {
            'is_real': False,
            'confidence': 0.5,
            'explanation': f"Error checking citation: {str(e)}"
        }

# Function to query the CourtListener API
def query_courtlistener_api(text, api_key):
    """Query the CourtListener API to verify citations in the text.
    
    Instead of sending the full text, we extract citations first and then
    send only the citations to the API. This is more efficient and avoids
    the 64,000 character limit of the API.
    """
    print(f"Processing text of length: {len(text)} for CourtListener API")
    
    if not api_key:
        print("No API key provided")
        return {'error': 'No API key provided'}
    
    try:
        # Extract citations from the text using eyecite
        citations = extract_citations(text)
        
        if not citations:
            print("No citations found in the text")
            return {'error': 'No citations found in the text'}
        
        print(f"Found {len(citations)} citations to verify with CourtListener API")
        
        # Prepare the request
        headers = {
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Join citations with newlines to create a compact text
        # This is much more efficient than sending the full text
        citations_text = "\n".join(citations)
        print(f"Citations text length: {len(citations_text)} characters")
        
        data = {
            'text': citations_text
        }
        
        # Make the request
        print(f"Sending request to {COURTLISTENER_API_URL}")
        response = requests.post(COURTLISTENER_API_URL, headers=headers, json=data)
        
        # Check the response
        if response.status_code == 200:
            print("API request successful")
            result = response.json()
            
            # Save the API response to a file for inspection
            try:
                with open('api_response.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                print("API response saved to api_response.json")
            except Exception as e:
                print(f"Error saving API response to file: {e}")
            
            return result
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return {'error': f"API request failed with status code {response.status_code}: {response.text}"}
    
    except Exception as e:
        print(f"Error querying CourtListener API: {e}")
        traceback.print_exc()
        return {'error': f"Error querying CourtListener API: {str(e)}"}

# Function to generate a unique analysis ID
def generate_analysis_id():
    return str(uuid.uuid4())

# Function to run the analysis with CourtListener API
def run_analysis(analysis_id, brief_text=None, file_path=None, api_key=None):
    print(f"Starting analysis for ID: {analysis_id}")
    print(f"API key: {api_key[:5]}..." if api_key else "No API key provided")
    print(f"File path: {file_path}" if file_path else "No file path provided")
    print(f"Brief text length: {len(brief_text)}" if brief_text else "No brief text provided")
    
    try:
        # Initialize the results for this analysis
        analysis_results[analysis_id] = {
            'status': 'running',
            'progress': 0,
            'total_steps': 3,
            'message': 'Analysis started',
            'completed': False,
            'results': None,
            'error': None,
            'extracted_citations': [],
            'citation_results': []
        }
        
        # Get text from file if provided
        if file_path and not brief_text:
            print(f"Extracting text from file: {file_path}")
            
            # Verify file exists and is readable
            if not os.path.isfile(file_path):
                error_msg = f"File not found: {file_path}"
                print(error_msg)
                analysis_results[analysis_id]['status'] = 'error'
                analysis_results[analysis_id]['error'] = error_msg
                analysis_results[analysis_id]['completed'] = True
                return
            
            try:
                file_size = os.path.getsize(file_path)
                print(f"File size: {file_size} bytes")
                
                # Check if file is empty
                if file_size == 0:
                    error_msg = f"File is empty: {file_path}"
                    print(error_msg)
                    analysis_results[analysis_id]['status'] = 'error'
                    analysis_results[analysis_id]['error'] = error_msg
                    analysis_results[analysis_id]['completed'] = True
                    return
            except Exception as e:
                error_msg = f"Error checking file: {str(e)}"
                print(error_msg)
                analysis_results[analysis_id]['status'] = 'error'
                analysis_results[analysis_id]['error'] = error_msg
                analysis_results[analysis_id]['completed'] = True
                return
            
            # Update progress - Step 1: Extracting text
            analysis_results[analysis_id]['progress'] = 1
            analysis_results[analysis_id]['message'] = f'Extracting text from file: {os.path.basename(file_path)}'
            
            # Extract text from file
            brief_text = extract_text_from_file(file_path)
            
            if not brief_text:
                error_msg = f"Failed to extract text from file: {file_path}"
                print(error_msg)
                analysis_results[analysis_id]['status'] = 'error'
                analysis_results[analysis_id]['error'] = error_msg
                analysis_results[analysis_id]['completed'] = True
                return
                
            # Update progress after extraction
            analysis_results[analysis_id]['message'] = f'Successfully extracted {len(brief_text)} characters from {os.path.basename(file_path)}'
            
            # Save extracted text to a file for debugging
            try:
                debug_file = f'extracted_text_{analysis_id}.txt'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(brief_text)
                print(f"Saved extracted text to {debug_file}")
            except Exception as e:
                print(f"Error saving extracted text to file: {e}")
        
        # Use default text if none provided
        if not brief_text:
            brief_text = "2016 WL 165971"
            citations = [brief_text]
            # Update with default citation
            analysis_results[analysis_id]['message'] = 'Using default citation for testing'
        else:
            # Update progress - Step 2: Extracting citations
            analysis_results[analysis_id]['progress'] = 2
            analysis_results[analysis_id]['message'] = 'Extracting citations from document text...'
            
            # Extract citations from the text
            citations = extract_citations(brief_text)
            
            # Update with extracted citations
            analysis_results[analysis_id]['extracted_citations'] = citations
            
            if citations:
                analysis_results[analysis_id]['message'] = f'Successfully extracted {len(citations)} citations from document'
            else:
                # If no citations found, treat the entire text as one citation
                citations = [brief_text[:100] + "..." if len(brief_text) > 100 else brief_text]
                analysis_results[analysis_id]['message'] = 'No specific citations found, treating entire text as one citation'
                analysis_results[analysis_id]['extracted_citations'] = citations
        
        # Query the CourtListener API
        if api_key:
            # Update progress - Step 3: Querying API
            analysis_results[analysis_id]['progress'] = 3
            analysis_results[analysis_id]['message'] = 'Querying CourtListener API...'
            
            # Query the API with the entire text
            api_response = query_courtlistener_api(brief_text, api_key)
            
            # Update with API response
            if 'error' in api_response:
                analysis_results[analysis_id]['status'] = 'error'
                analysis_results[analysis_id]['error'] = f"Error querying CourtListener API: {api_response['error']}"
                analysis_results[analysis_id]['completed'] = True
                return
            
            # Process the API response
            hallucinated_count = 0
            citation_results = []
            
            # Debug the API response structure
            print(f"API response type: {type(api_response)}")
            if isinstance(api_response, list):
                print(f"API response is a list with {len(api_response)} items")
                for i, item in enumerate(api_response):
                    print(f"Item {i} keys: {item.keys() if isinstance(item, dict) else 'not a dict'}")
            elif isinstance(api_response, dict):
                print(f"API response is a dict with keys: {api_response.keys()}")
            
            # Process each citation from our extraction
            for i, citation in enumerate(citations):
                # Check if this citation is in the API response
                found = False
                court_listener_url = None
                case_name = None
                
                # The API response can be a list of citation objects
                if isinstance(api_response, list):
                    for api_item in api_response:
                        if isinstance(api_item, dict) and 'citation' in api_item:
                            if citation.lower() in api_item['citation'].lower():
                                found = True
                                # Check if there are clusters with URLs
                                if 'clusters' in api_item and api_item['clusters']:
                                    cluster = api_item['clusters'][0]  # Get the first cluster
                                    court_listener_url = cluster.get('absolute_url', None)
                                    if court_listener_url and not court_listener_url.startswith('http'):
                                        court_listener_url = f"https://www.courtlistener.com{court_listener_url}"
                                    case_name = cluster.get('case_name', 'Unknown case')
                                break
                elif isinstance(api_response, dict) and 'citations' in api_response:
                    # Traditional structure with citations dictionary
                    api_citations = api_response['citations']
                    print(f"API returned citations dictionary with keys: {api_citations.keys() if isinstance(api_citations, dict) else 'not a dict'}")
                    
                    # Check if citation is in the citations dictionary
                    for citation_key, citation_data in api_citations.items():
                        if citation.lower() in citation_key.lower():
                            found = True
                            case_name = citation_data.get('name', 'Unknown case')
                            # Try to find URL in the citation data
                            if 'match_url' in citation_data:
                                court_listener_url = citation_data['match_url']
                                if not court_listener_url.startswith('http'):
                                    court_listener_url = f"https://www.courtlistener.com{court_listener_url}"
                            break
                    
                    if found:
                        # Only consider it truly found if we have a URL AND a proper case name
                        if court_listener_url and case_name and case_name != 'Unknown case':
                            confidence = 0.9  # High confidence for exact match
                            explanation = f"Citation confirmed: {case_name} - {court_listener_url}"
                        else:
                            # If we don't have both a URL and a proper case name, treat as potential hallucination
                            found = False
                            hallucinated_count += 1
                            confidence = 0.7
                            if court_listener_url:
                                explanation = f"Citation format recognized but case name unknown - potential hallucination"
                            elif case_name and case_name != 'Unknown case':
                                explanation = f"Citation format recognized but no URL found - potential hallucination"
                            else:
                                explanation = f"Citation format recognized but case details unknown - potential hallucination"
                    
                    # If not found, check with LangSearch API
                    if not found:
                        hallucinated_count += 1
                        
                        # Check with LangSearch API
                        print(f"Citation not found in CourtListener database, checking with LangSearch: {citation}")
                        langsearch_result = check_case_with_langsearch(citation)
                        
                        if langsearch_result['is_real']:
                            # If LangSearch says it's real, reduce the hallucination count
                            hallucinated_count -= 1
                            found = True
                            confidence = langsearch_result['confidence']
                            explanation = langsearch_result['explanation']
                            
                            # Add summaries if available
                            if 'summaries' in langsearch_result:
                                summaries = langsearch_result['summaries']
                            else:
                                summaries = []
                        else:
                            # If LangSearch also says it's hallucinated
                            confidence = langsearch_result['confidence']
                            explanation = langsearch_result['explanation']
                            
                            # Add summaries if available
                            if 'summaries' in langsearch_result:
                                summaries = langsearch_result['summaries']
                            else:
                                summaries = []
                    else:
                        # Citation found in CourtListener
                        summaries = []
                    
                    # Add result
                    result_data = {
                        'citation_text': citation,
                        'is_hallucinated': not found,
                        'confidence': confidence,
                        'explanation': explanation
                    }
                    
                    # Add CourtListener URL if available
                    if found and court_listener_url:
                        result_data['court_listener_url'] = court_listener_url
                        result_data['case_name'] = case_name or 'Unknown case'
                    
                    # Add summaries if available
                    if summaries:
                        result_data['summaries'] = summaries
                    
                    citation_results.append(result_data)
            # If we haven't processed any citations yet, it means the API response format wasn't recognized
            if not citation_results:
                print("API response format not recognized or no citations found")
                print(f"API response: {api_response}")
                
                # Try one more approach - if the API response is a list of items with citation info
                if isinstance(api_response, list):
                    for i, citation in enumerate(citations):
                        found = False
                        court_listener_url = None
                        case_name = None
                        
                        # Check each item in the response list
                        for api_item in api_response:
                            # Look for the citation in normalized_citations if available
                            if isinstance(api_item, dict) and 'normalized_citations' in api_item:
                                # First check exact match in normalized_citations
                                for norm_citation in api_item['normalized_citations']:
                                    if citation.lower() == norm_citation.lower():
                                        found = True
                                        # Get case info from clusters if available
                                        if 'clusters' in api_item and api_item['clusters']:
                                            cluster = api_item['clusters'][0]
                                            court_listener_url = cluster.get('absolute_url', None)
                                            if court_listener_url and not court_listener_url.startswith('http'):
                                                court_listener_url = f"https://www.courtlistener.com{court_listener_url}"
                                            case_name = cluster.get('case_name', 'Unknown case')
                                        break
                                
                                # If not found, check if this is an alternative citation format
                                if not found and 'clusters' in api_item and api_item['clusters']:
                                    cluster = api_item['clusters'][0]
                                    if 'citations' in cluster:
                                        # Check all alternative citations for this case
                                        for alt_citation in cluster['citations']:
                                            # Construct the citation string in various formats
                                            volume = str(alt_citation.get('volume', ''))
                                            reporter = alt_citation.get('reporter', '')
                                            page = alt_citation.get('page', '')
                                            
                                            # Format 1: "550 U.S. 544"
                                            alt_format1 = f"{volume} {reporter} {page}"
                                            # Format 2: "550 U. S. 544"
                                            alt_format2 = alt_format1.replace('.', '. ')
                                            # Format 3: "550U.S.544"
                                            alt_format3 = f"{volume}{reporter}{page}"
                                            
                                            # Compare with our citation
                                            citation_clean = citation.replace(' ', '').replace('.', '')
                                            alt_format1_clean = alt_format1.replace(' ', '').replace('.', '')
                                            alt_format2_clean = alt_format2.replace(' ', '').replace('.', '')
                                            alt_format3_clean = alt_format3.replace(' ', '').replace('.', '')
                                            
                                            if (citation_clean == alt_format1_clean or 
                                                citation_clean == alt_format2_clean or 
                                                citation_clean == alt_format3_clean):
                                                found = True
                                                court_listener_url = cluster.get('absolute_url', None)
                                                if court_listener_url and not court_listener_url.startswith('http'):
                                                    court_listener_url = f"https://www.courtlistener.com{court_listener_url}"
                                                case_name = cluster.get('case_name', 'Unknown case')
                                                break
                            if found:
                                break
                                
                        # Add result for this citation
                        if found:
                            result_data = {
                                'citation_text': citation,
                                'is_hallucinated': False,
                                'confidence': 0.9,
                                'explanation': f"Citation confirmed: {case_name or 'Unknown case'}{' - ' + court_listener_url if court_listener_url else ''}"
                            }
                            
                            # Add CourtListener URL if available
                            if court_listener_url:
                                result_data['court_listener_url'] = court_listener_url
                                result_data['case_name'] = case_name or 'Unknown case'
                                
                            citation_results.append(result_data)
                        else:
                            # Check with LangSearch API
                            print(f"Citation not found in CourtListener database, checking with LangSearch: {citation}")
                            langsearch_result = check_case_with_langsearch(citation)
                            
                            if langsearch_result['is_real']:
                                # LangSearch says it's real
                                result_data = {
                                    'citation_text': citation,
                                    'is_hallucinated': False,
                                    'confidence': langsearch_result['confidence'],
                                    'explanation': langsearch_result['explanation']
                                }
                                
                                # Add summaries if available
                                if 'summaries' in langsearch_result:
                                    result_data['summaries'] = langsearch_result['summaries']
                            else:
                                # LangSearch also says it's hallucinated
                                hallucinated_count += 1
                                result_data = {
                                    'citation_text': citation,
                                    'is_hallucinated': True,
                                    'confidence': langsearch_result['confidence'],
                                    'explanation': langsearch_result['explanation']
                                }
                                
                                # Add summaries if available
                                if 'summaries' in langsearch_result:
                                    result_data['summaries'] = langsearch_result['summaries']
                                    
                            citation_results.append(result_data)
                else:
                    # Mark all citations as potentially hallucinated if we can't process the API response
                    for i, citation in enumerate(citations):
                        hallucinated_count += 1
                        citation_results.append({
                            'citation_text': citation,
                            'is_hallucinated': True,
                            'confidence': 0.7,
                            'explanation': "Citation not verified by CourtListener API"
                        })
            
            # Group parallel citations to the same case
            grouped_citations = {}
            
            for result in citation_results:
                # Use the court_listener_url as the key for grouping
                case_key = result.get('court_listener_url', None)
                case_name = result.get('case_name', None)
                
                # Only group citations that have BOTH a valid URL AND a proper case name and are not hallucinated
                if (case_key and case_key.startswith('http') and 
                    case_name and case_name != 'Unknown case' and 
                    not result['is_hallucinated']):
                    # This is a verified citation with both URL and case name - check if we already have this case
                    if case_key in grouped_citations:
                        # Add this citation as a parallel citation
                        grouped_citations[case_key]['parallel_citations'].append(result['citation_text'])
                    else:
                        # Create a new group for this case
                        grouped_citations[case_key] = {
                            'case_name': case_name,
                            'court_listener_url': case_key,
                            'primary_citation': result['citation_text'],
                            'parallel_citations': [],
                            'is_hallucinated': False,
                            'confidence': result['confidence'],
                            'explanation': result['explanation']
                        }
                        # Add any summaries if available
                        if 'summaries' in result:
                            grouped_citations[case_key]['summaries'] = result['summaries']
                else:
                    # This is either a hallucinated citation or one without a URL
                    # Use the citation text as the key
                    citation_key = f"citation_{result['citation_text']}"
                    grouped_citations[citation_key] = {
                        'primary_citation': result['citation_text'],
                        'parallel_citations': [],
                        'is_hallucinated': result['is_hallucinated'],
                        'confidence': result['confidence'],
                        'explanation': result['explanation']
                    }
                    # Add any summaries if available
                    if 'summaries' in result:
                        grouped_citations[citation_key]['summaries'] = result['summaries']
            
            # Convert the grouped citations back to a list
            grouped_citation_results = list(grouped_citations.values())
            
            # Update with grouped citation results
            analysis_results[analysis_id]['citation_results'] = grouped_citation_results
            
            # Complete the analysis
            analysis_results[analysis_id]['status'] = 'complete'
            analysis_results[analysis_id]['message'] = f"Analysis complete. Found {len(citations)} citations, {hallucinated_count} potentially hallucinated."
            analysis_results[analysis_id]['completed'] = True
            analysis_results[analysis_id]['results'] = {
                'total_citations': len(citations),
                'hallucinated_citations': hallucinated_count,
                'verified_citations': len(citations) - hallucinated_count,
                'unique_cases': len([c for c in grouped_citation_results if not c['is_hallucinated']])
            }
        else:
            # No API key provided, mark all citations as unverified
            analysis_results[analysis_id]['message'] = 'No CourtListener API key provided, unable to verify citations'
            
            # Check citations with LangSearch even if no CourtListener API key
            citation_results = []
            for i, citation in enumerate(citations):
                # Check with LangSearch API
                print(f"No CourtListener API key, checking with LangSearch: {citation}")
                langsearch_result = check_case_with_langsearch(citation)
                
                result_data = {
                    'citation_text': citation,
                    'is_hallucinated': not langsearch_result['is_real'],
                    'confidence': langsearch_result['confidence'],
                    'explanation': langsearch_result['explanation']
                }
                
                # Add summaries if available
                if 'summaries' in langsearch_result:
                    result_data['summaries'] = langsearch_result['summaries']
                
                citation_results.append(result_data)
                
                # Update hallucinated count
                if not langsearch_result['is_real']:
                    hallucinated_count += 1
            
            # Update with citation results
            analysis_results[analysis_id]['citation_results'] = citation_results
            
            # Complete the analysis
            analysis_results[analysis_id]['status'] = 'complete'
            analysis_results[analysis_id]['message'] = f"Analysis complete without API verification. Found {len(citations)} citations."
            analysis_results[analysis_id]['completed'] = True
            analysis_results[analysis_id]['results'] = {
                'total_citations': len(citations),
                'hallucinated_citations': len(citations),
                'verified_citations': 0
            }
    
    except Exception as e:
        print(f"Error running analysis: {e}")
        traceback.print_exc()
        
        # Update with error
        analysis_results[analysis_id]['status'] = 'error'
        analysis_results[analysis_id]['error'] = f"Error running analysis: {str(e)}"
        analysis_results[analysis_id]['completed'] = True

# Routes
@app.route('/')
def index():
    return render_template('fixed_form_ajax.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'POST':
        print("\n\n==== ANALYZE ENDPOINT CALLED =====")
        print(f"Request method: {request.method}")
        print(f"Request headers: {request.headers}")
        print(f"Request form data: {request.form}")
        print(f"Request files: {request.files}")
        
        try:
            # Generate a unique analysis ID
            analysis_id = generate_analysis_id()
            print(f"Generated analysis ID: {analysis_id}")
            
            # Initialize variables
            brief_text = None
            file_path = None
        
            # Get the API key if provided, otherwise use the default from config.json
            api_key = DEFAULT_API_KEY  # Use the default API key loaded from config.json
            if 'api_key' in request.form and request.form['api_key'].strip():
                api_key = request.form['api_key'].strip()
                print(f"API key provided in form: {api_key[:5]}...")
            else:
                print(f"Using default API key from config.json: {api_key[:5]}..." if api_key else "No API key provided or found in config.json")
        
            # Check if a file was uploaded
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename and allowed_file(file.filename):
                    print(f"File uploaded: {file.filename}")
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    print(f"File saved to: {file_path}")
                    
                    # Debug: Print file size and first few bytes
                    try:
                        file_size = os.path.getsize(file_path)
                        print(f"File size: {file_size} bytes")
                        with open(file_path, 'rb') as f:
                            first_bytes = f.read(100)
                            print(f"First few bytes: {first_bytes}")
                    except Exception as e:
                        print(f"Error reading file: {e}")
        
            # Check if a file path was provided
            elif 'file_path' in request.form:
                file_path = request.form['file_path'].strip()
                print(f"File path provided: {file_path}")
                
                # Handle file:/// URLs
                if file_path.startswith('file:///'):
                    file_path = file_path[8:]  # Remove 'file:///' prefix
                
                # Check if the file exists
                if not os.path.isfile(file_path):
                    print(f"File not found: {file_path}")
                    return jsonify({
                        'status': 'error',
                        'message': f'File not found: {file_path}'
                    }), 404
                
                # Check if the file extension is allowed
                if not allowed_file(file_path):
                    print(f"File extension not allowed: {file_path}")
                    return jsonify({
                        'status': 'error',
                        'message': f'File extension not allowed: {file_path}'
                    }), 400
                
                print(f"Using file from path: {file_path}")
                
                # Debug: Print file size and first few bytes
                try:
                    file_size = os.path.getsize(file_path)
                    print(f"File size: {file_size} bytes")
                    with open(file_path, 'rb') as f:
                        first_bytes = f.read(100)
                        print(f"First few bytes: {first_bytes}")
                except Exception as e:
                    print(f"Error reading file: {e}")
        
            # Get the text input if provided
            if 'text' in request.form:
                brief_text = request.form['text']
                print(f"Text from form: {brief_text[:100]}...")
            elif 'briefText' in request.form:  # For backward compatibility
                brief_text = request.form['briefText']
                print(f"Brief text from form: {brief_text[:100]}...")
        
            # Check if we have either text or a file
            if not brief_text and not file_path:
                print("No text or file provided")
                return jsonify({
                    'status': 'error',
                    'message': 'No text or file provided'
                }), 400
            
            # Start the analysis in a background thread
            threading.Thread(target=run_analysis, args=(analysis_id, brief_text, file_path, api_key)).start()
            
            # Return the analysis ID to the client
            return jsonify({
                'status': 'success',
                'message': 'Analysis started',
                'analysis_id': analysis_id
            })
        except Exception as e:
            print(f"Error in analyze endpoint: {e}")
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': f'Error: {str(e)}'
            }), 500
    else:
        # For GET requests, just return an empty response
        return jsonify({})

@app.route('/status')
def status():
    """Get the status of an analysis."""
    print("\n\n==== STATUS ENDPOINT CALLED =====")
    
    # Get the analysis ID from the query string
    analysis_id = request.args.get('id')
    if not analysis_id:
        return jsonify({'status': 'error', 'message': 'No analysis ID provided'}), 400
    
    # Check if the analysis exists
    if analysis_id not in analysis_results:
        return jsonify({'status': 'error', 'message': 'Analysis not found'}), 404
    
    # Return the current status
    response = jsonify(analysis_results[analysis_id])
    
    # Add CORS headers to allow cross-origin requests
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Cache-Control', 'no-cache')
    
    return response

if __name__ == '__main__':
    # Check if we should run with Cheroot (production) or Flask's dev server
    use_cheroot = os.environ.get('USE_CHEROOT', 'True').lower() in ('true', '1', 't')
    
    if use_cheroot:
        try:
            from cheroot.wsgi import Server as WSGIServer
            print("Starting with Cheroot WSGI server (production mode)")
            
            # Check if we should use a Unix socket (for Nginx)
            unix_socket = os.environ.get('UNIX_SOCKET')
            
            if unix_socket:
                # Use Unix socket for Nginx
                from cheroot.wsgi import PathInfoDispatcher
                from cheroot.server import HTTPServer
                
                # Create a dispatcher
                d = PathInfoDispatcher({'/': app})
                
                # Create and start the server
                server = HTTPServer(bind_addr=unix_socket, wsgi_app=d)
                
                try:
                    # Make sure the socket is accessible by Nginx
                    if os.path.exists(unix_socket):
                        os.unlink(unix_socket)
                    
                    print(f"Server starting on Unix socket: {unix_socket}")
                    server.start()
                    
                    # Set socket permissions for Nginx
                    import stat
                    os.chmod(unix_socket, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                    print(f"Socket permissions set for Nginx access")
                    
                except KeyboardInterrupt:
                    server.stop()
                    print("Server stopped.")
                    if os.path.exists(unix_socket):
                        os.unlink(unix_socket)
            else:
                # Use TCP socket
                host = os.environ.get('HOST', '127.0.0.1')
                port = int(os.environ.get('PORT', 8000))
                
                server = WSGIServer((host, port), app)
                try:
                    print(f"Server started on http://{host}:{port}")
                    server.start()
                except KeyboardInterrupt:
                    server.stop()
                    print("Server stopped.")
        except ImportError:
            print("Cheroot not installed. Installing now...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "cheroot"])
                print("Cheroot installed. Please restart the application.")
                sys.exit(0)
            except Exception as e:
                print(f"Failed to install Cheroot: {e}")
                print("Falling back to Flask development server")
                app.run(debug=True, host='127.0.0.1', port=8000)
    else:
        print("Starting with Flask development server (debug mode)")
        app.run(debug=True, host='127.0.0.1', port=8000)
