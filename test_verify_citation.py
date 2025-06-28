from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

verifier = EnhancedMultiSourceVerifier()

# Test a valid citation
print("=== Testing Valid Citation ===")
citation = "534 F.3d 1290"
result = verifier.verify_citation(citation)

print("Citation Verification Result:")
for key, value in result.items():
    print(f"{key}: {value}")

print("\n=== Testing Invalid Citation ===")
# Test an invalid citation
invalid_citation = "999 F.999 999999"
invalid_result = verifier.verify_citation(invalid_citation)

print("Invalid Citation Verification Result:")
for key, value in invalid_result.items():
    print(f"{key}: {value}") 