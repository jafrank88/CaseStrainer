from app_final_vue import create_app

app = create_app()
with open("routes.txt", "w") as f:
    f.write("=== Registered Routes ===\n")
    with app.app_context():
        for rule in app.url_map.iter_rules():
            methods = list(rule.methods)
            if "HEAD" in methods:
                methods.remove("HEAD")
            if "OPTIONS" in methods:
                methods.remove("OPTIONS")
            f.write(f"{rule.rule} -> {rule.endpoint} [{', '.join(methods)}]\n")
print("Routes written to routes.txt")
