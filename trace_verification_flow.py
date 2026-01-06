"""
Check if verification is actually being called in the pipeline
"""

print("=" * 80)
print("CHECKING VERIFICATION CONFIGURATION IN PIPELINE")
print("=" * 80)

# Let's trace through the code path
print("\n1. FILE PROCESSING FLOW:")
print("   File upload → CitationService → should_process_immediately()")
print("   If immediate → UnifiedInputProcessor → process_citations_unified")
print("   → UnifiedCitationProcessorV2 with config")

print("\n2. CHECKING UNIFIED INPUT PROCESSOR:")
with open('D:/dev/casestrainer/src/unified_input_processor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
    # Find the process_any_input method
    for i, line in enumerate(lines):
        if 'def process_any_input(' in line:
            # Check default parameters
            j = i
            while j < i + 10:
                if 'enable_verification' in lines[j]:
                    print(f"   Line {j+1}: {lines[j].strip()}")
                    break
                j += 1
            break

print("\n3. CHECKING HOW UNIFIED INPUT PROCESSOR CALLS THE PIPELINE:")
# Look for the immediate processing section
for i, line in enumerate(lines):
    if 'process_citations_unified' in line:
        # Show context around this call
        start = max(0, i - 5)
        end = min(len(lines), i + 10)
        print(f"   Lines {start+1}-{end}:")
        for j in range(start, end):
            print(f"   {j+1}: {lines[j].rstrip()}")
        break

print("\n4. CHECKING CITATION SERVICE IMMEDIATE PROCESSING:")
with open('D:/dev/casestrainer/src/api/services/citation_service.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
    # Look for should_process_immediately
    if 'should_process_immediately' in content:
        print("   ✅ Found should_process_immediately check")
        
    # Check what happens in immediate processing
    import re
    # Look for the immediate processing section
    match = re.search(r'def.*immediate.*:.*?(?=\n    def|\nclass|\Z)', content, re.DOTALL)
    if match:
        print("   Found immediate processing method")

print("\n" + "=" * 80)
print("NEXT DEBUG STEP:")
print("-" * 40)
print("Need to add debug logging to see what enable_verification value")
print("is actually being passed through the call chain")
print("=" * 80)
