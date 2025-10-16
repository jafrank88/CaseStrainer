#!/usr/bin/env python
"""Test Web Search + Ollama concept for citation verification"""

import requests
from urllib.parse import quote

def test_web_search_availability():
    """Test different web search APIs"""
    
    print("="*70)
    print("WEB SEARCH OPTIONS FOR CITATION VERIFICATION")
    print("="*70)
    
    print("\n1. DUCKDUCKGO (No API Key Required)")
    print("   - Free HTML scraping")
    print("   - Instant Answer API for some queries")
    print("   - No rate limits on basic usage")
    
    citation = "410 U.S. 113"
    query = f"{citation} case name"
    
    try:
        # DuckDuckGo Instant Answer API
        url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   Status: {response.status_code}")
            print(f"   Abstract: {data.get('Abstract', 'N/A')[:100]}...")
            
            if data.get('Abstract'):
                print("   ✅ DuckDuckGo Instant Answer API works!")
            else:
                print("   ⚠️  No instant answer (may need scraping)")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2. BING SEARCH API")
    print("   - Requires Azure subscription")
    print("   - Free tier: 3 searches/second, 1000/month")
    print("   - Structured JSON results")
    
    print("\n3. GOOGLE CUSTOM SEARCH")
    print("   - Requires API key")
    print("   - Free tier: 100 queries/day")
    print("   - Can restrict to legal sites")
    
    print("\n4. SERPER.DEV")
    print("   - Google search API proxy")
    print("   - Free tier: 2500 searches")
    print("   - Simple API, no Google account needed")

def test_ollama_availability():
    """Test if Ollama is available locally"""
    
    print("\n" + "="*70)
    print("OLLAMA LOCAL LLM INTEGRATION")
    print("="*70)
    
    print("\nChecking if Ollama is running locally...")
    
    try:
        # Try to connect to Ollama (default port 11434)
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running!")
            print(f"   Available models: {len(models)}")
            
            if models:
                print(f"   Models:")
                for model in models[:5]:
                    print(f"      - {model.get('name', 'N/A')}")
            
            return True
        else:
            print(f"⚠️  Ollama responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Ollama not running on localhost:11434")
        print("\n   To install Ollama:")
        print("   1. Download from: https://ollama.ai/")
        print("   2. Install and run: ollama serve")
        print("   3. Pull a model: ollama pull llama2")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def explain_websearch_ollama_approach():
    """Explain how web search + Ollama could work"""
    
    print("\n" + "="*70)
    print("HOW WEB SEARCH + OLLAMA COULD WORK")
    print("="*70)
    
    print("""
CONCEPT:
────────
Use web search to find citation information, then use local LLM (Ollama)
to intelligently parse and validate the results.

WORKFLOW:
────────
1. Search web for citation (e.g., "410 U.S. 113 case name")
2. Get search results (titles, snippets, URLs)
3. Send results to Ollama with prompt:
   "Extract the case name from these search results for citation 410 U.S. 113"
4. Ollama parses results and returns structured data
5. Validate and return verification result

ADVANTAGES:
──────────
✅ Access to entire web (not limited to specific sites)
✅ Local LLM = no API costs for processing
✅ Intelligent parsing of unstructured results
✅ Can handle variations in result formatting
✅ Privacy (processing happens locally)

DISADVANTAGES:
─────────────
❌ Requires Ollama installed locally
❌ Web search may have rate limits
❌ LLM responses can be inconsistent
❌ Slower than direct URL access
❌ Quality depends on search results

COMPARISON TO CURRENT APPROACH:
──────────────────────────────
Current: Direct URL to known sources (fast, reliable)
Web Search + Ollama: Flexible but slower and less reliable

RECOMMENDATION:
──────────────
Use as LAST RESORT fallback:
1. CourtListener API
2. Justia Direct URL
3. OpenJurist Direct URL  
4. Cornell LII Direct URL
5. Web Search + Ollama (if above fail)

This gives maximum coverage while keeping reliability high.
""")

def test_simple_duckduckgo_search():
    """Test a simple DuckDuckGo search for citation info"""
    
    print("\n" + "="*70)
    print("TESTING DUCKDUCKGO SEARCH")
    print("="*70)
    
    citation = "410 U.S. 113"
    
    # Try different search approaches
    queries = [
        f'"{citation}" case name',
        f'{citation} supreme court',
        f'Roe v Wade {citation}',
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        
        try:
            url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for useful information
                abstract = data.get('Abstract', '')
                heading = data.get('Heading', '')
                
                if abstract or heading:
                    print(f"  Heading: {heading}")
                    print(f"  Abstract: {abstract[:100]}...")
                    
                    if 'Roe' in abstract or 'Wade' in abstract:
                        print("  ✅ Found case name in results!")
                else:
                    print("  ⚠️  No instant answer")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")

def recommendation():
    """Provide recommendation"""
    
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    
    print("""
VERDICT: NOT RECOMMENDED as primary source

REASONS:
────────
1. You already have 4 reliable sources working
2. Web search adds latency and uncertainty
3. LLM parsing can be inconsistent
4. Requires local Ollama installation
5. Direct URL access is faster and more reliable

ALTERNATIVE IDEA - Better Use Cases:
────────────────────────────────────
Instead of verification, use Ollama for:

1. **Smart Citation Extraction** (from messy documents)
   - LLM can find citations in unstructured text
   - Better than regex for complex formats
   
2. **Citation Format Normalization**
   - "Vol. 410, United States Reports, page 113" → "410 U.S. 113"
   - LLM handles variations better than rules
   
3. **Case Name Disambiguation**
   - When multiple possible case names found
   - LLM can reason about which is correct
   
4. **Quality Checking**
   - Validate if extracted citation makes sense
   - Check for obvious errors before verification

BEST APPROACH:
─────────────
Keep your current 4-source system for verification.
Consider adding Ollama for EXTRACTION improvements, not verification.

This gives you:
✅ Fast, reliable verification (4 sources)
✅ Smart extraction (Ollama for complex cases)
✅ Best of both worlds
""")

if __name__ == '__main__':
    print("\n🔍 Investigating Web Search + Ollama for Citation Verification\n")
    
    test_web_search_availability()
    ollama_available = test_ollama_availability()
    explain_websearch_ollama_approach()
    test_simple_duckduckgo_search()
    recommendation()
