from app_final_vue import create_app

app = create_app()
print("\n=== Registered Routes ===")
print("=" * 80)
print(f"{'ENDPOINT':<50} {'METHODS':<20} {'URL RULE'}")
print("=" * 80)

with app.app_context():
    routes = []
    for rule in app.url_map.iter_rules():
        methods = list(rule.methods - {'OPTIONS', 'HEAD'})
        routes.append((rule.endpoint, methods, str(rule)))
    
    # Sort routes by URL rule
    routes.sort(key=lambda x: x[2])
    
    for endpoint, methods, rule in routes:
        print(f"{endpoint:<50} {', '.join(methods):<20} {rule}")

print("\n=== Registered Blueprints ===")
for name, bp in app.blueprints.items():
    print(f"- {name}: {bp}")
