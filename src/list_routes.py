from app_final_vue import app

if __name__ == "__main__":
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} -> {rule}")
