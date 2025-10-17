#!/usr/bin/env python3
"""Check Redis for cached task results"""
import redis

# Connect to all Redis databases
for db in [0, 1, 2, 3]:
    print(f"\n{'='*80}")
    print(f"Redis Database {db}:")
    print(f"{'='*80}")
    
    r = redis.Redis(host='localhost', port=6379, db=db, decode_responses=True)
    keys = r.keys('*')
    
    print(f"Total keys: {len(keys)}")
    
    # Show keys related to the PDF
    pdf_keys = [k for k in keys if '1034300' in k or 'Hamaatsa' in k]
    if pdf_keys:
        print(f"\nPDF/Hamaatsa related keys:")
        for key in pdf_keys[:10]:
            print(f"  - {key}")
    
    # Show some sample keys
    if len(keys) > 0 and len(keys) <= 20:
        print(f"\nAll keys:")
        for key in keys:
            print(f"  - {key}")
