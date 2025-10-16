"""Check which routes are available in vue_api_endpoints.py"""
from src.vue_api_endpoints import vue_api

print("=== ROUTES IN vue_api_endpoints.py ===\n")
for rule in vue_api.deferred_functions:
    print(f"- {rule}")

print("\n=== TOTAL ROUTES ===")
print(f"Count: {len(list(vue_api.deferred_functions))}")
