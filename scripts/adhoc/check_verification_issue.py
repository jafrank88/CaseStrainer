import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test the verification issue
print("=" * 80)
print("VERIFICATION ISSUE INVESTIGATION")
print("=" * 80)

# Check the default value in unified_processing_pipeline.py
print("\n1. CHECKING unified_processing_pipeline.py:")
with open('D:/dev/casestrainer/src/unified_processing_pipeline.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[90:95], 91):
        if 'enable_verification' in line:
            print(f"   Line {i}: {line.strip()}")

# Check how the API calls this
print("\n2. CHECKING vue_api_endpoints_updated.py:")
with open('D:/dev/casestrainer/src/vue_api_endpoints_updated.py', 'r', encoding='utf-8') as f:
    content = f.read()
    import re
    
    # Look for process_citation_task_direct calls
    matches = re.findall(r'process_citation_task_direct\([^)]+\)', content)
    if matches:
        print(f"   Found {len(matches)} calls to process_citation_task_direct")
        for match in matches[:3]:
            print(f"   - {match}")
    
    # Look for enable_verification parameter
    if 'enable_verification=True' in content:
        print("   ✅ Found enable_verification=True in API")
    elif 'enable_verification=False' in content:
        print("   ❌ Found enable_verification=False in API")
    else:
        print("   ⚠️  enable_verification parameter not explicitly set in API calls")

# Check rq_worker.py
print("\n3. CHECKING rq_worker.py:")
with open('D:/dev/casestrainer/src/rq_worker.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'enable_verification=False' in content:
        print("   ❌ rq_worker explicitly sets enable_verification=False")
    elif 'enable_verification=True' in content:
        print("   ✅ rq_worker explicitly sets enable_verification=True")
    else:
        print("   ⚠️  rq_worker doesn't explicitly set enable_verification")

print("\n" + "=" * 80)
print("ROOT CAUSE:")
print("-" * 40)
print("The unified_processing_pipeline.py has enable_verification=False by default")
print("This means ALL citation processing through the pipeline skips verification!")
print("\nTO FIX:")
print("1. Change default in unified_processing_pipeline.py from False to True")
print("2. OR explicitly pass enable_verification=True in API calls")
print("3. OR check rq_worker.py which handles async processing")
print("=" * 80)
