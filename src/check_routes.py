from app_final_vue import create_app

app = create_app()
print("\n=== Registered Routes ===")
with app.app_context():
    for rule in app.url_map.iter_rules():
        methods = list(rule.methods)
        if "HEAD" in methods:
            methods.remove("HEAD")
        if "OPTIONS" in methods:
            methods.remove("OPTIONS")
        print(f"{rule.rule} -> {rule.endpoint} [{', '.join(methods)}]")
