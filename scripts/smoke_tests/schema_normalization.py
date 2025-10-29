import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from src.schemas import normalize_citation_dict
import json

if __name__ == "__main__":
    data = {'citation': '521 U.S. 811', 'extracted_case_name': 'Raines v. Byrd'}
    print(json.dumps(normalize_citation_dict(data), ensure_ascii=False))
