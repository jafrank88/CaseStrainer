import requests
import sys

API_URL = 'https://www.courtlistener.com/api/rest/v3/citation-lookup/'

# Example usage: python check_courtlistener_batch.py citations.txt

def load_citations(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def check_citation(citation):
    resp = requests.get(API_URL, params={'citation': citation})
    if resp.status_code == 200:
        data = resp.json()
        return bool(data.get('results'))
    return False

def main():
    if len(sys.argv) < 2:
        print('Usage: python check_courtlistener_batch.py citations.txt')
        sys.exit(1)
    citations = load_citations(sys.argv[1])
    found = []
    missing = []
    for citation in citations:
        result = check_citation(citation)
        if result:
            print(f'FOUND:    {citation}')
            found.append(citation)
        else:
            print(f'MISSING:  {citation}')
            missing.append(citation)
    print('\nSummary:')
    print(f'  Found:   {len(found)}')
    print(f'  Missing: {len(missing)}')
    if missing:
        print('Missing citations:')
        for c in missing:
            print('  ', c)

if __name__ == '__main__':
    main() 