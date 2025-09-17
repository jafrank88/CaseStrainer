import requests
import json
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('citation_paragraph_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_citation_paragraph():
    """Test the specific paragraph provided by the user."""
    
    # The production API endpoint
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    # The specific paragraph from the user
    test_text = """'[A]gency interpretations of statutes are accorded deference only if "(1) the particular agency is charged with the administration and enforcement of the statute, (2) the statute is ambiguous, and (3) the statute falls within the agency's special expertise."' Lucid Grp. USA, Inc., 33 Wn. App. 2d at 80 (emphasis omitted) (quoting Fode v. Dep't of Ecology, 22 Wn. App. 2d 22, 33, 509 P.3d 325 (2022) (quoting Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007))). However, courts are not bound by agency interpretation as courts have the '"ultimate authority to interpret a statute."' Id. (quoting Port of Tacoma v. Sacks, 19 Wn. App. 2d 295, 304, 495 P.3d 866 No. 103394-0 12 (2021) (quoting Bostain, 159 Wn.2d at 716))."""
    
    logger.info("Testing specific paragraph for citation extraction and clustering")
    logger.info(f"Text length: {len(test_text)} characters")
    
    # Request headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'CaseStrainer-Test/1.0'
    }
    
    # Form data for text analysis
    data = {
        'text': test_text,
        'type': 'text'
    }
    
    try:
        logger.info("Sending text analysis request...")
        response = requests.post(url, headers=headers, data=data, timeout=60)
        
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                
                # Save the full response
                with open('paragraph_analysis_response.json', 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2, ensure_ascii=False)
                
                logger.info("Response saved to paragraph_analysis_response.json")
                
                # Check the response structure
                logger.info(f"Response keys: {list(response_data.keys())}")
                
                # Look for citations in different possible locations
                citations = []
                clusters = []
                
                if 'citations' in response_data:
                    citations = response_data['citations']
                elif 'result' in response_data and 'citations' in response_data['result']:
                    citations = response_data['result']['citations']
                
                if 'clusters' in response_data:
                    clusters = response_data['clusters']
                elif 'result' in response_data and 'clusters' in response_data['result']:
                    clusters = response_data['result']['clusters']
                
                logger.info("=" * 80)
                logger.info("ANALYSIS RESULTS")
                logger.info("=" * 80)
                
                logger.info(f"📄 Citations found: {len(citations)}")
                logger.info(f"🔗 Clusters found: {len(clusters)}")
                
                if citations:
                    logger.info("\n📋 CITATIONS DETAILS:")
                    for i, citation in enumerate(citations, 1):
                        logger.info(f"\nCitation {i}:")
                        logger.info(f"  📝 Text/Citation: {citation.get('text', citation.get('citation', 'N/A'))}")
                        logger.info(f"  ⚖️  Case Name: {citation.get('extracted_case_name', citation.get('case_name', 'N/A'))}")
                        logger.info(f"  📅 Year: {citation.get('extracted_date', citation.get('year', 'N/A'))}")
                        logger.info(f"  ✅ Verified: {citation.get('is_verified', citation.get('verified', False))}")
                        logger.info(f"  🔍 Method: {citation.get('method', 'N/A')}")
                        logger.info(f"  📊 Confidence: {citation.get('confidence', 'N/A')}")
                        logger.info(f"  🏛️  Court: {citation.get('court', 'N/A')}")
                        logger.info(f"  🔗 Canonical URL: {citation.get('canonical_url', 'N/A')}")
                        
                        # Check for parallel citations
                        if citation.get('is_parallel'):
                            logger.info(f"  🔄 Parallel Citation: Yes")
                else:
                    logger.warning("❌ No citations found!")
                
                if clusters:
                    logger.info(f"\n🔗 CLUSTERS DETAILS:")
                    for i, cluster in enumerate(clusters, 1):
                        logger.info(f"\nCluster {i}:")
                        logger.info(f"  📝 Description: {cluster}")
                else:
                    logger.warning("❌ No clusters found!")
                
                # Check metadata
                metadata = response_data.get('result', {}).get('metadata', {})
                if metadata:
                    logger.info(f"\n📊 METADATA:")
                    logger.info(f"  🔍 Processing mode: {metadata.get('processing_mode', 'N/A')}")
                    logger.info(f"  ⚡ Processing strategy: {metadata.get('processing_strategy', 'N/A')}")
                    logger.info(f"  📏 Text length: {metadata.get('text_length', 'N/A')}")
                    logger.info(f"  🎯 Input type: {metadata.get('input_type', 'N/A')}")
                
                # Check processing time
                processing_time = response_data.get('processing_time_ms', response_data.get('result', {}).get('processing_time'))
                if processing_time:
                    logger.info(f"  ⏱️  Processing time: {processing_time}ms")
                
                logger.info("=" * 80)
                
                # Analyze why clustering might not have occurred
                if len(citations) > 1 and len(clusters) == 0:
                    logger.warning("🤔 ANALYSIS: Multiple citations found but no clusters created")
                    logger.info("Possible reasons:")
                    logger.info("  • Citations may not be similar enough to cluster")
                    logger.info("  • Clustering algorithm may require minimum similarity threshold")
                    logger.info("  • Processing strategy may have disabled clustering")
                    
                    # Check if citations are from the same case
                    case_names = set()
                    for citation in citations:
                        case_name = citation.get('extracted_case_name', citation.get('case_name', ''))
                        if case_name and case_name.strip():
                            case_names.add(case_name.strip())
                    
                    logger.info(f"  • Unique case names found: {len(case_names)}")
                    if case_names:
                        for case_name in case_names:
                            logger.info(f"    - {case_name}")
                
                # Analyze verification status
                verified_count = sum(1 for c in citations if c.get('is_verified', c.get('verified', False)))
                if verified_count == 0 and len(citations) > 0:
                    logger.warning("🤔 ANALYSIS: No citations were verified")
                    logger.info("Possible reasons:")
                    logger.info("  • Citations may not exist in the verification database")
                    logger.info("  • Verification service may be unavailable")
                    logger.info("  • Citation format may not match database entries")
                    logger.info("  • API key for verification service may be missing/invalid")
                
                return response_data
                
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse JSON response: {je}")
                logger.error(f"Response content: {response.text[:1000]}")
                
        else:
            logger.error(f"HTTP Error: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            
    except requests.exceptions.RequestException as re:
        logger.error(f"Request failed: {re}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    
    return None

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🔍 CaseStrainer Citation Paragraph Analysis")
    logger.info("=" * 80)
    
    result = test_citation_paragraph()
    
    if result:
        logger.info("✅ Analysis completed successfully")
    else:
        logger.error("❌ Analysis failed")
    
    logger.info("=" * 80)
