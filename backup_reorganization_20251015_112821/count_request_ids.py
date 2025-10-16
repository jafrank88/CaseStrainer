"""Quick count of request_id mentions."""
files = ['src/vue_api_endpoints.py', 'src/unified_input_processor.py']
for f in files:
    count = len([line for line in open(f, encoding='utf-8') if 'request_id' in line])
    print(f"{f}: {count} lines with 'request_id'")
